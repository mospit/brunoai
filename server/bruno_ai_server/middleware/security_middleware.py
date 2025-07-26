"""
Comprehensive security middleware for Bruno AI Server.
Integrates CSRF protection, cookie security, input sanitization, and security logging.
"""

import time
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..services.security_service import security_service
from ..services.cookie_service import cookie_service
from ..config import settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware for the application."""
    
    def __init__(self, app, enable_csrf: bool = True):
        super().__init__(app)
        self.enable_csrf = enable_csrf
        
        # Paths that don't require CSRF protection
        self.csrf_exempt_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/auth/login",
            "/auth/register",
            "/auth/csrf-token",
            "/auth/refresh"
        }
        
        # State-changing methods that require CSRF
        self.csrf_required_methods = {"POST", "PUT", "PATCH", "DELETE"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware."""
        start_time = time.time()
        
        try:
            # Validate cookie security in production
            cookie_service.validate_cookie_security(request)
            
            # Apply CSRF protection if enabled
            if self.enable_csrf:
                self._check_csrf_protection(request)
            
            # Process request
            response = await call_next(request)
            
            # Add security timing header
            process_time = time.time() - start_time
            response.headers["X-Security-Process-Time"] = str(process_time)
            
            # Add additional security headers
            self._add_security_headers(response)
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log unexpected security errors
            security_service.logger.log_suspicious_activity(
                request,
                "security_middleware_error",
                {"error": str(e), "type": type(e).__name__}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Security validation failed"
            )
    
    def _check_csrf_protection(self, request: Request):
        """Check CSRF protection for state-changing requests."""
        # Skip CSRF for safe methods and exempt paths
        if (request.method not in self.csrf_required_methods or
            self._is_csrf_exempt_path(request.url.path)):
            return
        
        # Skip CSRF for API requests with proper authentication
        # (Bearer token auth is considered sufficient CSRF protection)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return
        
        # For cookie-based authentication, require CSRF token
        has_auth_cookies = any([
            cookie_service.get_access_token_from_cookie(request),
            cookie_service.get_refresh_token_from_cookie(request),
            cookie_service.get_session_id_from_cookie(request)
        ])
        
        if has_auth_cookies:
            cookie_service.validate_csrf_protection(request)
    
    def _is_csrf_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from CSRF protection."""
        # Check exact matches
        if path in self.csrf_exempt_paths:
            return True
        
        # Check prefixes for documentation and static paths
        exempt_prefixes = ["/docs", "/redoc", "/static", "/api/docs"]
        return any(path.startswith(prefix) for prefix in exempt_prefixes)
    
    def _add_security_headers(self, response: Response):
        """Add additional security headers to response."""
        # HSTS (HTTP Strict Transport Security) - only in production with HTTPS
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), ambient-light-sensor=(), autoplay=(), "
            "battery=(), camera=(), cross-origin-isolated=(), "
            "display-capture=(), document-domain=(), encrypted-media=(), "
            "execution-while-not-rendered=(), execution-while-out-of-viewport=(), "
            "fullscreen=(), geolocation=(), gyroscope=(), "
            "keyboard-map=(), magnetometer=(), microphone=(), "
            "midi=(), navigation-override=(), payment=(), "
            "picture-in-picture=(), publickey-credentials-get=(), "
            "screen-wake-lock=(), sync-xhr=(), usb=(), "
            "web-share=(), xr-spatial-tracking=()"
        )
        
        # Cross-Origin Embedder Policy
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        
        # Cross-Origin Opener Policy
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        
        # Cross-Origin Resource Policy
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Server header removal (security by obscurity)
        if "Server" in response.headers:
            del response.headers["Server"]
        
        # X-Powered-By header removal
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic input sanitization."""
    
    def __init__(self, app, sanitize_json: bool = True, sanitize_form: bool = True):
        super().__init__(app)
        self.sanitize_json = sanitize_json
        self.sanitize_form = sanitize_form
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through input sanitization."""
        # Only sanitize for state-changing methods
        if request.method in {"POST", "PUT", "PATCH"}:
            await self._sanitize_request_body(request)
        
        return await call_next(request)
    
    async def _sanitize_request_body(self, request: Request):
        """Sanitize request body data."""
        content_type = request.headers.get("Content-Type", "")
        
        try:
            if self.sanitize_json and "application/json" in content_type:
                # For JSON data, we would need to parse and sanitize
                # This is complex due to FastAPI's request parsing
                # In practice, this is better handled at the route level
                pass
            elif self.sanitize_form and "application/x-www-form-urlencoded" in content_type:
                # For form data, similar complexity
                # Better handled at route level with Pydantic models
                pass
        except Exception as e:
            security_service.logger.log_suspicious_activity(
                request,
                "input_sanitization_error",
                {"error": str(e), "content_type": content_type}
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware specifically for security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add comprehensive security headers."""
        response = await call_next(request)
        
        # Enhanced CSP for different environments
        if settings.is_production:
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # More relaxed CSP for development
            csp = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "img-src 'self' data: https: http:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none'"
            )
        
        response.headers["Content-Security-Policy"] = csp
        
        # Additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Cache control for sensitive responses
        if request.url.path.startswith("/auth/") or request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response


# Factory function to create security middleware stack
def create_security_middleware_stack():
    """Create a comprehensive security middleware stack."""
    def middleware_factory(app):
        # Apply middleware in reverse order (last applied = first executed)
        app = SecurityHeadersMiddleware(app)
        app = InputSanitizationMiddleware(app)
        app = SecurityMiddleware(app, enable_csrf=settings.is_production)
        return app
    
    return middleware_factory

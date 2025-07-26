"""
Authentication middleware for Bruno AI Server.
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from ..auth import verify_token
from ..models.user import User


class RateLimiter:
    """Enhanced in-memory rate limiter with multiple time windows."""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
        # Failed authentication attempts tracking
        self.failed_attempts: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(
        self,
        key: str,
        max_requests: int = 60,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Unique identifier (e.g., IP address, user ID)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            bool: True if request is allowed
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        
        return False
    
    def is_auth_allowed(self, key: str) -> bool:
        """
        Check if authentication request is allowed (5 attempts per 15 minutes).
        
        Args:
            key: Unique identifier (e.g., IP address)
            
        Returns:
            bool: True if auth request is allowed
        """
        now = time.time()
        window_start = now - 900  # 15 minutes in seconds
        
        # Remove old failed attempts
        self.failed_attempts[key] = [
            req_time for req_time in self.failed_attempts[key]
            if req_time > window_start
        ]
        
        # Check if under limit (5 attempts per 15 minutes)
        return len(self.failed_attempts[key]) < 5
    
    def record_failed_auth(self, key: str):
        """Record a failed authentication attempt."""
        self.failed_attempts[key].append(time.time())
    
    def get_reset_time(self, key: str, window_seconds: int = 60) -> float:
        """Get time when rate limit resets for a key."""
        if key not in self.requests or not self.requests[key]:
            return time.time()
        
        oldest_request = min(self.requests[key])
        return oldest_request + window_seconds
    
    def get_auth_reset_time(self, key: str) -> float:
        """Get time when auth rate limit resets for a key."""
        if key not in self.failed_attempts or not self.failed_attempts[key]:
            return time.time()
        
        oldest_attempt = min(self.failed_attempts[key])
        return oldest_attempt + 900  # 15 minutes


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and security."""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.security = HTTPBearer(auto_error=False)
        
        # Paths that don't require authentication
        self.public_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/users/register",
            "/users/login",
            "/users/refresh",
            "/users/verify-email",
            "/users/request-password-reset",
            "/users/reset-password"
        }
        
        # Paths with special rate limits
        self.auth_paths = {
            "/users/login",
            "/users/refresh",
            "/users/register"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through authentication middleware."""
        start_time = time.time()
        
        # Add security headers
        response = await self._add_security_headers(request, call_next)
        
        # Add timing header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    async def _add_security_headers(self, request: Request, call_next):
        """Add security headers to response."""
        # Apply rate limiting
        if not self._check_rate_limit(request):
            reset_time = self.rate_limiter.get_reset_time(
                self._get_client_ip(request)
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={
                    "Retry-After": str(int(reset_time - time.time())),
                    "X-RateLimit-Limit": "60",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time))
                }
            )
        
        # Check authentication for protected routes
        if not self._is_public_path(request.url.path):
            await self._validate_authentication(request)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        # Add rate limit headers
        client_ip = self._get_client_ip(request)
        remaining = max(0, 60 - len(self.rate_limiter.requests[client_ip]))
        reset_time = self.rate_limiter.get_reset_time(client_ip)
        
        response.headers["X-RateLimit-Limit"] = "60"
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require authentication)."""
        # Check exact matches
        if path in self.public_paths:
            return True
        
        # Check prefixes for documentation paths
        public_prefixes = ["/docs", "/redoc", "/static"]
        return any(path.startswith(prefix) for prefix in public_prefixes)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        forwarded = request.headers.get("X-Forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client address
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limit(self, request: Request) -> bool:
        """Check if request is within rate limits."""
        client_ip = self._get_client_ip(request)
        path = request.url.path
        
        # Special auth rate limiting (5 attempts per 15 minutes)
        if path in self.auth_paths:
            # Check if IP is allowed to make auth requests
            if not self.rate_limiter.is_auth_allowed(client_ip):
                from ..services.security_service import security_service
                security_service.logger.log_rate_limit_exceeded(request, "auth_attempts")
                
                reset_time = self.rate_limiter.get_auth_reset_time(client_ip)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many authentication attempts. Please try again later.",
                    headers={
                        "Retry-After": str(int(reset_time - time.time())),
                        "X-RateLimit-Limit": "5",
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(reset_time)),
                        "X-RateLimit-Type": "auth"
                    }
                )
            
            # Also apply general rate limit
            return self.rate_limiter.is_allowed(
                f"auth:{client_ip}",
                max_requests=10,  # 10 requests per minute for auth endpoints
                window_seconds=60
            )
        
        # General rate limit
        return self.rate_limiter.is_allowed(
            client_ip,
            max_requests=60,  # 60 requests per minute
            window_seconds=60
        )
    
    async def _validate_authentication(self, request: Request):
        """Validate authentication for protected routes."""
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Parse bearer token
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise ValueError("Invalid scheme")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Add user info to request state
        request.state.user_id = payload.get("sub")
        request.state.token_payload = payload


class RequireAuth:
    """Dependency to require authentication."""
    
    def __init__(self, require_verified: bool = False):
        self.require_verified = require_verified
        self.security = HTTPBearer()
    
    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials,
        request: Request
    ) -> Dict:
        """Validate authentication and return user info."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization credentials missing",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return payload


class RequireRole:
    """Dependency to require specific user role."""
    
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
        self.security = HTTPBearer()
    
    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials,
        request: Request
    ) -> Dict:
        """Validate authentication and role."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization credentials missing",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check role (if present in token)
        user_roles = payload.get("roles", [])
        if not any(role in user_roles for role in self.required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return payload


class RequireActiveUser:
    """Dependency to require active and verified user."""
    
    def __init__(self, require_verified: bool = True):
        self.require_verified = require_verified
        self.security = HTTPBearer()
    
    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials,
        request: Request
    ) -> Dict:
        """Validate authentication and user status."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization credentials missing",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if user is active (would need database lookup in real implementation)
        # This is a simplified version - in practice, you'd query the database
        user_active = payload.get("active", True)
        if not user_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        # Check if user is verified
        if self.require_verified:
            user_verified = payload.get("verified", False)
            if not user_verified:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email verification required"
                )
        
        return payload


# Utility functions for common auth patterns
def get_optional_user(request: Request) -> Optional[Dict]:
    """Get user info from request if authenticated."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    try:
        scheme, token = auth_header.split(" ", 1)
        if scheme.lower() != "bearer":
            return None
        
        payload = verify_token(token)
        return payload
    except (ValueError, AttributeError):
        return None


def require_auth_dependency():
    """Create a FastAPI dependency for authentication."""
    return RequireAuth()


def require_verified_user_dependency():
    """Create a FastAPI dependency for verified users."""
    return RequireActiveUser(require_verified=True)


def require_admin_dependency():
    """Create a FastAPI dependency for admin users."""
    return RequireRole(["admin"])


# Security configuration
class SecurityConfig:
    """Security configuration constants."""
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = 60  # requests per minute
    AUTH_RATE_LIMIT = 10     # requests per minute for auth endpoints
    
    # Token settings
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Password settings
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    
    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
    }

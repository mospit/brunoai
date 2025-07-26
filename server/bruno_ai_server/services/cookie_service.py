"""
Secure cookie handling service for Bruno AI Server.
Provides HttpOnly cookies with HTTPS enforcement and secure token management.
"""

from datetime import datetime, timedelta
from typing import Optional
import secrets
import json

from fastapi import Request, Response, HTTPException, status
from ..config import settings
from .security_service import security_service


class SecureCookieService:
    """Service for handling secure cookies with proper security attributes."""
    
    def __init__(self):
        self.cookie_name_prefix = "brunoai_"
        self.access_token_cookie = f"{self.cookie_name_prefix}access_token"
        self.refresh_token_cookie = f"{self.cookie_name_prefix}refresh_token"
        self.csrf_token_cookie = f"{self.cookie_name_prefix}csrf_token"
        self.session_cookie = f"{self.cookie_name_prefix}session"
    
    def set_auth_cookies(
        self,
        response: Response,
        request: Request,
        access_token: str,
        refresh_token: str,
        access_expires_minutes: int = 15,
        refresh_expires_days: int = 7
    ):
        """
        Set secure authentication cookies.
        
        Args:
            response: FastAPI response object
            request: FastAPI request object (for HTTPS check)
            access_token: JWT access token
            refresh_token: JWT refresh token
            access_expires_minutes: Access token expiration in minutes
            refresh_expires_days: Refresh token expiration in days
        """
        is_https = security_service.is_https_request(request)
        
        # Set access token cookie (shorter expiration)
        response.set_cookie(
            key=self.access_token_cookie,
            value=access_token,
            max_age=access_expires_minutes * 60,  # Convert to seconds
            httponly=True,  # Prevent XSS access
            secure=is_https,  # Only send over HTTPS in production
            samesite="strict",  # CSRF protection
            path="/",
        )
        
        # Set refresh token cookie (longer expiration)
        response.set_cookie(
            key=self.refresh_token_cookie,
            value=refresh_token,
            max_age=refresh_expires_days * 24 * 60 * 60,  # Convert to seconds
            httponly=True,  # Prevent XSS access
            secure=is_https,  # Only send over HTTPS in production
            samesite="strict",  # CSRF protection
            path="/auth/refresh",  # Restrict to refresh endpoint
        )
        
        # Set CSRF token cookie (accessible to JavaScript for headers)
        csrf_token = security_service.generate_csrf_token()
        response.set_cookie(
            key=self.csrf_token_cookie,
            value=csrf_token,
            max_age=access_expires_minutes * 60,  # Same as access token
            httponly=False,  # Needs to be accessible to JavaScript
            secure=is_https,
            samesite="strict",
            path="/",
        )
        
        # Set session identifier for CSRF validation
        session_id = secrets.token_urlsafe(32)
        response.set_cookie(
            key=self.session_cookie,
            value=session_id,
            max_age=refresh_expires_days * 24 * 60 * 60,
            httponly=True,
            secure=is_https,
            samesite="strict",
            path="/",
        )
    
    def get_access_token_from_cookie(self, request: Request) -> Optional[str]:
        """Get access token from cookie."""
        return request.cookies.get(self.access_token_cookie)
    
    def get_refresh_token_from_cookie(self, request: Request) -> Optional[str]:
        """Get refresh token from cookie."""
        return request.cookies.get(self.refresh_token_cookie)
    
    def get_csrf_token_from_cookie(self, request: Request) -> Optional[str]:
        """Get CSRF token from cookie."""
        return request.cookies.get(self.csrf_token_cookie)
    
    def get_session_id_from_cookie(self, request: Request) -> Optional[str]:
        """Get session ID from cookie."""
        return request.cookies.get(self.session_cookie)
    
    def validate_csrf_protection(self, request: Request) -> bool:
        """
        Validate CSRF protection for state-changing requests.
        
        Args:
            request: FastAPI request object
            
        Returns:
            bool: True if CSRF validation passes
            
        Raises:
            HTTPException: If CSRF validation fails
        """
        # Skip CSRF validation for GET, HEAD, OPTIONS requests
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        
        # Get CSRF token from header or form data
        csrf_token_header = request.headers.get("X-CSRF-Token")
        
        # For form data, we would need to parse the body (implementation depends on use case)
        csrf_token = csrf_token_header
        
        if not csrf_token:
            security_service.logger.log_csrf_violation(
                request, "CSRF token missing from request"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token required"
            )
        
        # Validate the token
        session_id = self.get_session_id_from_cookie(request)
        if not security_service.validate_csrf_token(request, csrf_token):
            security_service.logger.log_csrf_violation(
                request, "Invalid CSRF token"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )
        
        return True
    
    def clear_auth_cookies(self, response: Response, request: Request):
        """Clear all authentication cookies."""
        is_https = security_service.is_https_request(request)
        
        cookies_to_clear = [
            self.access_token_cookie,
            self.refresh_token_cookie,
            self.csrf_token_cookie,
            self.session_cookie
        ]
        
        for cookie_name in cookies_to_clear:
            response.set_cookie(
                key=cookie_name,
                value="",
                max_age=0,  # Expire immediately
                httponly=True,
                secure=is_https,
                samesite="strict",
                path="/",
            )
    
    def set_secure_cookie(
        self,
        response: Response,
        request: Request,
        name: str,
        value: str,
        max_age_seconds: int = 3600,
        httponly: bool = True,
        path: str = "/"
    ):
        """
        Set a secure cookie with proper security attributes.
        
        Args:
            response: FastAPI response object
            request: FastAPI request object
            name: Cookie name
            value: Cookie value
            max_age_seconds: Cookie expiration in seconds
            httponly: Whether cookie should be HttpOnly
            path: Cookie path
        """
        is_https = security_service.is_https_request(request)
        
        response.set_cookie(
            key=f"{self.cookie_name_prefix}{name}",
            value=value,
            max_age=max_age_seconds,
            httponly=httponly,
            secure=is_https,
            samesite="strict",
            path=path,
        )
    
    def get_secure_cookie(self, request: Request, name: str) -> Optional[str]:
        """Get a secure cookie value."""
        return request.cookies.get(f"{self.cookie_name_prefix}{name}")
    
    def validate_cookie_security(self, request: Request):
        """
        Validate that cookies are sent over secure connections in production.
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: If security requirements not met
        """
        if settings.is_production and not security_service.is_https_request(request):
            # Check if any authentication cookies are present
            auth_cookies = [
                self.access_token_cookie,
                self.refresh_token_cookie,
                self.session_cookie
            ]
            
            has_auth_cookies = any(
                request.cookies.get(cookie) for cookie in auth_cookies
            )
            
            if has_auth_cookies:
                security_service.logger.log_suspicious_activity(
                    request,
                    "insecure_auth_cookies",
                    {"message": "Authentication cookies sent over HTTP in production"}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Secure connection required"
                )


# Global cookie service instance
cookie_service = SecureCookieService()

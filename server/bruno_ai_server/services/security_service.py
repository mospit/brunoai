"""
Security service for Bruno AI Server.
Provides CSRF protection, security logging, and enhanced input sanitization.
"""

import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings

# Configure security logger (separate from application logs)
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# Create a separate handler for security events
security_handler = logging.StreamHandler()
security_formatter = logging.Formatter(
    '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)
security_logger.propagate = False  # Don't propagate to root logger


class CSRFProtection:
    """CSRF token generation and validation."""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or settings.app_secret_key
        self.token_lifetime = 3600  # 1 hour
    
    def generate_token(self, session_id: str = None) -> str:
        """
        Generate a CSRF token.
        
        Args:
            session_id: Optional session identifier
            
        Returns:
            str: CSRF token
        """
        if not session_id:
            session_id = secrets.token_urlsafe(32)
        
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{session_id}:{timestamp}:{signature}"
    
    def validate_token(self, token: str, session_id: str = None) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token: CSRF token to validate
            session_id: Optional session identifier for validation
            
        Returns:
            bool: True if token is valid
        """
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False
            
            token_session_id, timestamp, signature = parts
            
            # If session_id provided, ensure it matches
            if session_id and token_session_id != session_id:
                return False
            
            # Check if token has expired
            token_time = int(timestamp)
            if time.time() - token_time > self.token_lifetime:
                return False
            
            # Verify signature
            message = f"{token_session_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False


class SecurityLogger:
    """Enhanced security logging with structured events."""
    
    @staticmethod
    def log_auth_attempt(
        request: Request,
        email: str,
        success: bool,
        reason: str = None,
        user_id: str = None
    ):
        """Log authentication attempt."""
        client_ip = SecurityService.get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "Unknown")
        
        event_data = {
            "event": "auth_attempt",
            "success": success,
            "email": email,  # Consider hashing this in production
            "client_ip": client_ip,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id
        }
        
        if reason:
            event_data["reason"] = reason
        
        if success:
            security_logger.info(f"Authentication success: {event_data}")
        else:
            security_logger.warning(f"Authentication failed: {event_data}")
    
    @staticmethod
    def log_rate_limit_exceeded(request: Request, limit_type: str = "general"):
        """Log rate limit exceeded event."""
        client_ip = SecurityService.get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "Unknown")
        
        event_data = {
            "event": "rate_limit_exceeded",
            "limit_type": limit_type,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        security_logger.warning(f"Rate limit exceeded: {event_data}")
    
    @staticmethod
    def log_csrf_violation(request: Request, reason: str):
        """Log CSRF token validation failure."""
        client_ip = SecurityService.get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "Unknown")
        
        event_data = {
            "event": "csrf_violation",
            "reason": reason,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        security_logger.warning(f"CSRF violation: {event_data}")
    
    @staticmethod
    def log_suspicious_activity(
        request: Request,
        activity_type: str,
        details: Dict[str, Any]
    ):
        """Log suspicious activity."""
        client_ip = SecurityService.get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "Unknown")
        
        event_data = {
            "event": "suspicious_activity",
            "activity_type": activity_type,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat(),
            **details
        }
        
        security_logger.error(f"Suspicious activity: {event_data}")


class InputSanitizer:
    """Enhanced input sanitization and validation."""
    
    # Patterns for detecting potential injection attacks
    SQL_INJECTION_PATTERNS = [
        r"(?i)(union|select|insert|update|delete|drop|create|alter)\s+",
        r"(?i)(script|javascript|vbscript|onload|onerror)",
        r"(?i)(eval|exec|system|cmd|shell)",
        r"['\";](\s)*(union|select|insert|update|delete)",
        r"(?i)(or|and)\s+\d+\s*=\s*\d+",
        r"(?i)(or|and)\s+['\"]([^'\"]*)['\"]",
        r"(?i)\/\*.*\*\/",  # SQL comments
        r"(?i)--[^\r\n]*",  # SQL comments
        r"(?i)#[^\r\n]*",   # MySQL comments
    ]
    
    XSS_PATTERNS = [
        r"(?i)<script[^>]*>.*?</script>",
        r"(?i)<iframe[^>]*>.*?</iframe>",
        r"(?i)<object[^>]*>.*?</object>",
        r"(?i)<embed[^>]*>",
        r"(?i)<link[^>]*>",
        r"(?i)<meta[^>]*>",
        r"(?i)javascript:",
        r"(?i)vbscript:",
        r"(?i)data:text/html",
        r"(?i)on\w+\s*=",  # Event handlers
    ]
    
    @classmethod
    def sanitize_string(
        cls,
        value: str,
        max_length: int = 255,
        allow_html: bool = False,
        check_injection: bool = True
    ) -> str:
        """
        Comprehensive string sanitization.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags
            check_injection: Whether to check for injection patterns
            
        Returns:
            str: Sanitized string
            
        Raises:
            HTTPException: If potential injection attack detected
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', value)
        
        # Normalize whitespace
        value = re.sub(r'\s+', ' ', value).strip()
        
        # Check for injection patterns if enabled
        if check_injection:
            cls._check_injection_patterns(value)
        
        # Remove HTML if not allowed
        if not allow_html:
            value = cls._strip_html_tags(value)
        else:
            value = cls._sanitize_html(value)
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """Sanitize email address."""
        if not email:
            return ""
        
        email = cls.sanitize_string(email, max_length=254, check_injection=False)
        email = email.lower().strip()
        
        # Basic email format validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        return email
    
    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """Sanitize URL and validate against allowed schemes."""
        if not url:
            return ""
        
        url = cls.sanitize_string(url, max_length=2048, check_injection=True)
        
        # Parse URL to validate components
        try:
            parsed = urlparse(url)
            
            # Only allow safe schemes
            allowed_schemes = {'http', 'https', 'ftp', 'ftps'}
            if parsed.scheme and parsed.scheme.lower() not in allowed_schemes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="URL scheme not allowed"
                )
            
            return url
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL format"
            )
    
    @classmethod
    def _check_injection_patterns(cls, value: str):
        """Check for SQL injection and XSS patterns."""
        # Check SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Potentially malicious input detected"
                )
        
        # Check XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Potentially malicious input detected"
                )
    
    @classmethod
    def _strip_html_tags(cls, value: str) -> str:
        """Remove all HTML tags."""
        return re.sub(r'<[^>]+>', '', value)
    
    @classmethod
    def _sanitize_html(cls, value: str) -> str:
        """Sanitize HTML, allowing only safe tags."""
        # This is a basic implementation - consider using bleach library for production
        safe_tags = ['b', 'i', 'u', 'strong', 'em', 'p', 'br']
        
        # Remove all tags except safe ones
        pattern = r'<(?!\/?(?:' + '|'.join(safe_tags) + r')\b)[^>]*>'
        return re.sub(pattern, '', value, flags=re.IGNORECASE)


class SecurityService:
    """Main security service orchestrating all security features."""
    
    def __init__(self):
        self.csrf = CSRFProtection()
        self.sanitizer = InputSanitizer()
        self.logger = SecurityLogger()
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
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
    
    def validate_csrf_token(self, request: Request, token: str) -> bool:
        """Validate CSRF token from request."""
        return self.csrf.validate_token(token)
    
    def generate_csrf_token(self, session_id: str = None) -> str:
        """Generate new CSRF token."""
        return self.csrf.generate_token(session_id)
    
    def sanitize_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize all string values in request data."""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Special handling for different field types
                if key.lower() == 'email':
                    sanitized[key] = self.sanitizer.sanitize_email(value)
                elif key.lower() in ['url', 'website', 'homepage']:
                    sanitized[key] = self.sanitizer.sanitize_url(value)
                else:
                    sanitized[key] = self.sanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_request_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitizer.sanitize_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def is_https_request(self, request: Request) -> bool:
        """Check if request is made over HTTPS."""
        # Check direct scheme
        if request.url.scheme == "https":
            return True
        
        # Check forwarded proto header (for reverse proxy)
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        if forwarded_proto and forwarded_proto.lower() == "https":
            return True
        
        return False
    
    def validate_password_not_logged(self, password: str):
        """Ensure password meets security requirements and won't be logged."""
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required"
            )
        
        # Note: We don't log the actual password value anywhere
        # This method exists to remind developers about password security
        
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        if len(password) > 128:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is too long"
            )


# Global security service instance
security_service = SecurityService()

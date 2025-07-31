"""
Validation utilities for Bruno AI Server.
"""

import re
from typing import List, Optional
from pydantic import field_validator, BaseModel


class ValidationError(Exception):
    """Custom validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class PasswordValidationResult:
    """Result of password validation."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, strength_score: int = 0):
        self.is_valid = is_valid
        self.errors = errors or []
        self.strength_score = strength_score  # 0-100


def validate_email_format(email: str) -> bool:
    """
    Validate email format with comprehensive checks.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email format is valid
        
    Raises:
        ValidationError: If email format is invalid
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email is required", "email")
    
    email = email.strip().lower()
    
    # Basic format check
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format", "email")
    
    # Length checks
    if len(email) > 254:  # RFC 5321 limit
        raise ValidationError("Email address is too long", "email")
    
    local_part, domain = email.rsplit('@', 1)
    
    if len(local_part) > 64:  # RFC 5321 limit
        raise ValidationError("Email local part is too long", "email")
    
    if len(domain) > 253:  # RFC 1035 limit
        raise ValidationError("Email domain is too long", "email")
    
    # Domain validation
    if domain.startswith('.') or domain.endswith('.'):
        raise ValidationError("Invalid email domain format", "email")
    
    if '..' in domain:
        raise ValidationError("Invalid email domain format", "email")
    
    return True


def validate_password_strength(password: str, min_length: int = 8) -> PasswordValidationResult:
    """
    Validate password strength with comprehensive checks.
    
    Args:
        password: Password to validate
        min_length: Minimum password length (default 8, frontend uses 6)
        
    Returns:
        PasswordValidationResult: Validation result with score and errors
    """
    if not password or not isinstance(password, str):
        return PasswordValidationResult(
            is_valid=False,
            errors=["Password is required"],
            strength_score=0
        )
    
    errors = []
    strength_score = 0
    
    # Length requirements - flexible minimum
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters long")
    elif len(password) >= min_length:
        # Base score for meeting minimum length
        strength_score += 15
        # Additional score for longer passwords
        if len(password) >= 8:
            strength_score += 10
        if len(password) >= 12:
            strength_score += 10
        if len(password) >= 16:
            strength_score += 10
    
    if len(password) > 128:
        errors.append("Password is too long (maximum 128 characters)")
    
    # Character type requirements
    has_lower = bool(re.search(r'[a-z]', password))
    has_upper = bool(re.search(r'[A-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    if not has_lower:
        errors.append("Password must contain at least one lowercase letter")
    else:
        strength_score += 15
    
    if not has_upper:
        errors.append("Password must contain at least one uppercase letter")
    else:
        strength_score += 15
    
    if not has_digit:
        errors.append("Password must contain at least one number")
    else:
        strength_score += 15
    
    if not has_special:
        errors.append("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
    else:
        strength_score += 15
    
    # Complexity checks
    unique_chars = len(set(password))
    if unique_chars >= 8:
        strength_score += 10
    
    # Common password patterns
    common_patterns = [
        r'(.)\1{2,}',  # Repeated characters (3+ times)
        r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
        r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
        r'(qwerty|asdfgh|zxcvbn)',  # Keyboard patterns
    ]
    
    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            errors.append("Password contains common patterns and is not secure")
            strength_score = max(0, strength_score - 20)
            break
    
    # Common passwords check (simplified)
    common_passwords = {
        'password', '12345678', 'qwerty123', 'password123', 'admin123',
        '123456789', 'welcome123', 'letmein123', 'monkey123'
    }
    
    if password.lower() in common_passwords:
        errors.append("Password is too common and easily guessable")
        strength_score = 0
    
    # Minimum requirements for validity
    min_requirements_met = len(errors) == 0 and len(password) >= min_length
    
    return PasswordValidationResult(
        is_valid=min_requirements_met,
        errors=errors,
        strength_score=min(100, strength_score)
    )


def validate_name(name: str) -> bool:
    """
    Validate name format.
    
    Args:
        name: Name to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    if not name or not isinstance(name, str):
        raise ValidationError("Name is required", "name")
    
    name = name.strip()
    
    if len(name) < 2:
        raise ValidationError("Name must be at least 2 characters long", "name")
    
    if len(name) > 100:
        raise ValidationError("Name is too long (maximum 100 characters)", "name")
    
    # Allow letters, spaces, hyphens, apostrophes, dots, and unicode letters
    if not re.match(r"^[\w\s\-'.]+$", name, re.UNICODE):
        raise ValidationError("Name can only contain letters, spaces, hyphens, apostrophes, and dots", "name")
    
    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', name):
        raise ValidationError("Name must contain at least one letter", "name")
    
    return True


class SecureUserCreate(BaseModel):
    """Enhanced user creation schema with comprehensive validation."""
    
    email: str
    name: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format."""
        validate_email_format(v)
        return v.strip().lower()
    
    @field_validator('name')
    @classmethod
    def validate_user_name(cls, v):
        """Validate name."""
        validate_name(v)
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        result = validate_password_strength(v)
        if not result.is_valid:
            raise ValueError('; '.join(result.errors))
        return v


def sanitize_user_input(value: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        value: Input value to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized value
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes and control characters
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    
    # Trim whitespace
    value = value.strip()
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value

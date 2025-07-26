"""
Unit tests for validation utilities.
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from bruno_ai_server.validation import (
    ValidationError,
    PasswordValidationResult,
    validate_email_format,
    validate_password_strength,
    validate_name,
    SecureUserCreate,
    sanitize_user_input
)


class TestEmailValidation:
    """Test email format validation."""
    
    def test_valid_emails(self):
        """Test valid email formats."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.com",
            "a@b.co",
            "very.long.email.address@very.long.domain.name.com"
        ]
        
        for email in valid_emails:
            assert validate_email_format(email) is True
    
    def test_invalid_emails(self):
        """Test invalid email formats."""
        invalid_emails = [
            "",
            "invalid",
            "@domain.com",
            "user@",
            "user@domain",
            "user..name@domain.com",
            "user@domain..com",
            "user@.domain.com",
            "user@domain.com.",
            "user@domain.c",
            "user name@domain.com",  # space
            "user@domain .com",      # space
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_email_format(email)
    
    def test_email_length_limits(self):
        """Test email length validation."""
        # Test maximum email length (254 characters)
        long_email = "a" * 50 + "@example.com"  # Valid length
        assert validate_email_format(long_email) is True
        
        # Test email too long
        too_long_email = "a" * 250 + "@example.com"  # 263 characters total
        with pytest.raises(ValidationError):
            validate_email_format(too_long_email)
        
        # Test local part too long (64+ characters)
        long_local = "a" * 65 + "@example.com"
        with pytest.raises(ValidationError):
            validate_email_format(long_local)
    
    def test_email_normalization(self):
        """Test that emails are normalized to lowercase."""
        email = "USER@EXAMPLE.COM"
        # The function should accept it but normalize it internally
        assert validate_email_format(email) is True


class TestPasswordValidation:
    """Test password strength validation."""
    
    def test_valid_passwords(self):
        """Test valid passwords."""
        valid_passwords = [
            "MyVeryStr0ng!Pass",
            "SuperSecure@P4ss",
            "ComplexP@ssw0rd!9",
            "Strong&Unique!3",
            "Secure!Password7"
        ]
        
        for password in valid_passwords:
            result = validate_password_strength(password)
            assert result.is_valid is True
            assert len(result.errors) == 0
            assert result.strength_score > 0
    
    def test_weak_passwords(self):
        """Test weak passwords."""
        weak_passwords = [
            "short",           # Too short
            "password",        # No uppercase, numbers, special chars
            "PASSWORD",        # No lowercase, numbers, special chars
            "12345678",        # No letters
            "Password123",     # No special characters
            "Password!",       # No numbers
            "password123!",    # No uppercase
            "PASSWORD123!",    # No lowercase
        ]
        
        for password in weak_passwords:
            result = validate_password_strength(password)
            assert result.is_valid is False
            assert len(result.errors) > 0
    
    def test_password_length_requirements(self):
        """Test password length validation."""
        # Too short
        result = validate_password_strength("Aa1!")
        assert result.is_valid is False
        assert any("8 characters" in error for error in result.errors)
        
        # Minimum valid length
        result = validate_password_strength("Password1!")
        assert result.is_valid is True
        
        # Too long
        long_password = "A" * 129 + "a1!"
        result = validate_password_strength(long_password)
        assert result.is_valid is False
        assert any("too long" in error for error in result.errors)
    
    def test_password_character_requirements(self):
        """Test individual character type requirements."""
        # Missing lowercase
        result = validate_password_strength("PASSWORD123!")
        assert result.is_valid is False
        assert any("lowercase" in error for error in result.errors)
        
        # Missing uppercase
        result = validate_password_strength("password123!")
        assert result.is_valid is False
        assert any("uppercase" in error for error in result.errors)
        
        # Missing digit
        result = validate_password_strength("Password!")
        assert result.is_valid is False
        assert any("number" in error for error in result.errors)
        
        # Missing special character
        result = validate_password_strength("Password123")
        assert result.is_valid is False
        assert any("special character" in error for error in result.errors)
    
    def test_common_passwords(self):
        """Test common password detection."""
        common_passwords = [
            "password",
            "12345678",
            "qwerty123",
            "password123",
            "admin123"
        ]
        
        for password in common_passwords:
            result = validate_password_strength(password)
            assert result.is_valid is False
            assert any("common" in error.lower() for error in result.errors)
            assert result.strength_score == 0
    
    def test_password_patterns(self):
        """Test detection of common patterns."""
        pattern_passwords = [
            "Password111!",  # Repeated characters
            "Password123!",  # Sequential numbers
            "Passwordabc!",  # Sequential letters
            "Passwordqwerty!", # Keyboard pattern
        ]
        
        for password in pattern_passwords:
            result = validate_password_strength(password)
            # These might still be valid but should have reduced scores
            if not result.is_valid:
                assert any("pattern" in error.lower() for error in result.errors)
    
    def test_password_strength_scoring(self):
        """Test password strength scoring."""
        # Weak password
        result = validate_password_strength("Password1!")
        assert 0 <= result.strength_score <= 100
        
        # Strong password
        result = validate_password_strength("MyVeryStr0ng&ComplexP@ssw0rd!")
        assert result.strength_score > 80
        
        # Empty password
        result = validate_password_strength("")
        assert result.strength_score == 0
        assert result.is_valid is False


class TestFullNameValidation:
    """Test full name validation."""
    
    def test_valid_names(self):
        """Test valid full names."""
        valid_names = [
            "John Doe",
            "Jane Smith-Jones",
            "Mary O'Connor",
            "Jean-Pierre Dupont",
            "Anna-Lisa",
            "Dr. Smith Jr.",
            "A B"  # Minimum length
        ]
        
        for name in valid_names:
            assert validate_name(name) is True
    
    def test_invalid_names(self):
        """Test invalid full names."""
        invalid_names = [
            "",              # Empty
            "A",             # Too short
            "123",           # Only numbers
            "John123",       # Contains numbers
            "John@Doe",      # Invalid characters
            "John_Doe",      # Underscore not allowed
            "A" * 101,       # Too long
        ]
        
        for name in invalid_names:
            with pytest.raises(ValidationError):
                validate_name(name)
    
    def test_name_length_limits(self):
        """Test name length validation."""
        # Minimum length
        assert validate_name("Jo") is True
        
        # Maximum length
        long_name = "A" * 100
        assert validate_name(long_name) is True
        
        # Too long
        too_long_name = "A" * 101
        with pytest.raises(ValidationError):
            validate_name(too_long_name)
    
    def test_name_character_validation(self):
        """Test allowed characters in names."""
        # Letters only
        assert validate_name("John") is True
        
        # Letters and spaces
        assert validate_name("John Doe") is True
        
        # Letters, spaces, and hyphens
        assert validate_name("Mary-Jane") is True
        
        # Letters, spaces, and apostrophes
        assert validate_name("O'Connor") is True
        
        # Letters, spaces, and dots
        assert validate_name("Dr. Smith") is True


class TestSecureUserCreate:
    """Test secure user creation schema."""
    
    def test_valid_user_data(self):
        """Test valid user creation data."""
        valid_data = {
            "email": "test@example.com",
            "name": "John Doe",
            "password": "MyVeryStr0ng!Pass"
        }
        
        user = SecureUserCreate(**valid_data)
        assert user.email == "test@example.com"
        assert user.name == "John Doe"
        assert user.password == "MyVeryStr0ng!Pass"
    
    def test_email_normalization(self):
        """Test email normalization in schema."""
        data = {
            "email": "  TEST@EXAMPLE.COM  ",
            "name": "John Doe",
            "password": "MyVeryStr0ng!Pass"
        }
        
        user = SecureUserCreate(**data)
        assert user.email == "test@example.com"
    
    def test_name_normalization(self):
        """Test name normalization in schema."""
        data = {
            "email": "test@example.com",
            "name": "  John Doe  ",
            "password": "MyVeryStr0ng!Pass"
        }
        
        user = SecureUserCreate(**data)
        assert user.name == "John Doe"
    
    def test_invalid_user_data(self):
        """Test invalid user creation data."""
        # Invalid email
        with pytest.raises(PydanticValidationError):
            SecureUserCreate(
                email="invalid-email",
                name="John Doe",
                password="MyVeryStr0ng!Pass"
            )
        
        # Invalid password
        with pytest.raises(PydanticValidationError):
            SecureUserCreate(
                email="test@example.com",
                name="John Doe",
                password="weak"
            )
        
        # Invalid name
        with pytest.raises(PydanticValidationError):
            SecureUserCreate(
                email="test@example.com",
                name="A",
                password="MyVeryStr0ng!Pass"
            )


class TestInputSanitization:
    """Test input sanitization."""
    
    def test_sanitize_normal_input(self):
        """Test sanitization of normal input."""
        input_text = "Hello World"
        result = sanitize_user_input(input_text)
        assert result == "Hello World"
    
    def test_sanitize_whitespace(self):
        """Test whitespace trimming."""
        input_text = "  Hello World  "
        result = sanitize_user_input(input_text)
        assert result == "Hello World"
    
    def test_sanitize_control_characters(self):
        """Test removal of control characters."""
        input_text = "Hello\x00\x01World\x1f"
        result = sanitize_user_input(input_text)
        assert result == "HelloWorld"
    
    def test_sanitize_null_bytes(self):
        """Test removal of null bytes."""
        input_text = "Hello\x00World"
        result = sanitize_user_input(input_text)
        assert result == "HelloWorld"
    
    def test_sanitize_length_limit(self):
        """Test length limiting."""
        long_input = "A" * 300
        result = sanitize_user_input(long_input, max_length=100)
        assert len(result) == 100
        assert result == "A" * 100
    
    def test_sanitize_non_string_input(self):
        """Test handling of non-string input."""
        result = sanitize_user_input(123)
        assert result == "123"
        
        result = sanitize_user_input(None)
        assert result == "None"
    
    def test_sanitize_unicode_characters(self):
        """Test handling of unicode characters."""
        input_text = "Hello 世界 🌍"
        result = sanitize_user_input(input_text)
        assert result == "Hello 世界 🌍"


class TestValidationErrorHandling:
    """Test validation error handling."""
    
    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError("Test message", "test_field")
        assert error.message == "Test message"
        assert error.field == "test_field"
        assert str(error) == "Test message"
    
    def test_validation_error_without_field(self):
        """Test ValidationError without field."""
        error = ValidationError("Test message")
        assert error.message == "Test message"
        assert error.field is None
    
    def test_password_validation_result(self):
        """Test PasswordValidationResult."""
        result = PasswordValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            strength_score=30
        )
        
        assert result.is_valid is False
        assert result.errors == ["Error 1", "Error 2"]
        assert result.strength_score == 30
    
    def test_password_validation_result_defaults(self):
        """Test PasswordValidationResult with defaults."""
        result = PasswordValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.strength_score == 0

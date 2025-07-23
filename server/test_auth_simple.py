#!/usr/bin/env python3
"""
Simple test script to validate JWT authentication implementation.
This script tests the authentication functionality without database dependencies.
"""

import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Mock settings to avoid database connection issues
class MockSettings:
    jwt_secret = "test-secret-key-for-jwt-authentication-testing"
    debug = False
    db_url = "postgresql://test:test@localhost/test"  # Mock DB URL

# Mock the settings import
import bruno_ai_server.config
bruno_ai_server.config.settings = MockSettings()

# Mock database to avoid import issues
sys.modules['bruno_ai_server.database'] = Mock()

# Import auth functions after mocking settings
from bruno_ai_server.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

def test_password_hashing():
    """Test password hashing functionality."""
    print("Testing password hashing...")
    
    # Test password hashing
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password, "Password should be hashed"
    assert isinstance(hashed, str), "Hashed password should be string"
    assert len(hashed) > 0, "Hashed password should not be empty"
    
    # Test password verification
    assert verify_password(password, hashed) is True, "Password verification should succeed"
    assert verify_password("wrongpassword", hashed) is False, "Wrong password should fail"
    
    print("✓ Password hashing tests passed")

def test_jwt_tokens():
    """Test JWT token creation and verification."""
    print("Testing JWT tokens...")
    
    # Test access token creation
    data = {"sub": "123"}
    access_token = create_access_token(data)
    
    assert isinstance(access_token, str), "Access token should be string"
    assert len(access_token) > 0, "Access token should not be empty"
    
    # Verify access token
    payload = verify_token(access_token)
    assert payload is not None, "Access token should be valid"
    assert payload["sub"] == "123", "Access token should contain correct subject"
    assert "exp" in payload, "Access token should have expiration"
    
    # Test refresh token creation
    refresh_token = create_refresh_token(data)
    
    assert isinstance(refresh_token, str), "Refresh token should be string"
    assert len(refresh_token) > 0, "Refresh token should not be empty"
    
    # Verify refresh token
    payload = verify_token(refresh_token)
    assert payload is not None, "Refresh token should be valid"
    assert payload["sub"] == "123", "Refresh token should contain correct subject"
    assert payload["type"] == "refresh", "Refresh token should have correct type"
    assert "exp" in payload, "Refresh token should have expiration"
    
    print("✓ JWT token tests passed")

def test_token_expiration():
    """Test token expiration settings."""
    print("Testing token expiration...")
    
    # Test access token expiration (15 minutes)
    data = {"sub": "123"}
    access_token = create_access_token(data)
    payload = verify_token(access_token)
    
    exp_time = datetime.utcfromtimestamp(payload["exp"])
    expected_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    time_diff = abs((exp_time - expected_time).total_seconds())
    
    assert time_diff < 2, f"Access token expiration should be ~{ACCESS_TOKEN_EXPIRE_MINUTES} minutes"
    assert ACCESS_TOKEN_EXPIRE_MINUTES == 15, "Access token should expire in 15 minutes"
    
    # Test refresh token expiration (7 days)
    refresh_token = create_refresh_token(data)
    payload = verify_token(refresh_token)
    
    exp_time = datetime.utcfromtimestamp(payload["exp"])
    expected_time = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    time_diff = abs((exp_time - expected_time).total_seconds())
    
    assert time_diff < 2, f"Refresh token expiration should be ~{REFRESH_TOKEN_EXPIRE_DAYS} days"
    assert REFRESH_TOKEN_EXPIRE_DAYS == 7, "Refresh token should expire in 7 days"
    
    print("✓ Token expiration tests passed")

def test_invalid_tokens():
    """Test invalid token handling."""
    print("Testing invalid token handling...")
    
    # Test invalid token
    invalid_token = "invalid.token.here"
    payload = verify_token(invalid_token)
    assert payload is None, "Invalid token should return None"
    
    # Test expired token
    data = {"sub": "123"}
    expired_token = create_access_token(data, timedelta(seconds=-1))
    payload = verify_token(expired_token)
    assert payload is None, "Expired token should return None"
    
    print("✓ Invalid token tests passed")

def main():
    """Run all tests."""
    print("Running JWT Authentication Module Tests")
    print("=" * 50)
    
    try:
        test_password_hashing()
        test_jwt_tokens()
        test_token_expiration()
        test_invalid_tokens()
        
        print("=" * 50)
        print("✅ All tests passed! JWT authentication module is working correctly.")
        print(f"✅ Password hashing using passlib with bcrypt: IMPLEMENTED")
        print(f"✅ 15-minute access tokens: IMPLEMENTED")
        print(f"✅ 7-day refresh tokens: IMPLEMENTED")
        print(f"✅ JWT token verification: IMPLEMENTED")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

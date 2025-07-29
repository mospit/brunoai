"""
Unit tests for authentication middleware.
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from bruno_ai_server.middleware.auth_middleware import (
    RateLimiter,
    AuthenticationMiddleware,
    RequireAuth,
    RequireRole,
    RequireActiveUser,
    get_optional_user,
    SecurityConfig
)


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance."""
        return RateLimiter()
    
    def test_rate_limiter_allows_initial_requests(self, rate_limiter):
        """Test that initial requests are allowed."""
        for i in range(5):
            assert rate_limiter.is_allowed("test_key", max_requests=10) is True
    
    def test_rate_limiter_blocks_excess_requests(self, rate_limiter):
        """Test that excess requests are blocked."""
        # Fill up the quota
        for i in range(10):
            assert rate_limiter.is_allowed("test_key", max_requests=10) is True
        
        # Next request should be blocked
        assert rate_limiter.is_allowed("test_key", max_requests=10) is False
    
    def test_rate_limiter_separate_keys(self, rate_limiter):
        """Test that different keys have separate limits."""
        # Fill up quota for key1
        for i in range(10):
            assert rate_limiter.is_allowed("key1", max_requests=10) is True
        
        # key2 should still be allowed
        assert rate_limiter.is_allowed("key2", max_requests=10) is True
        assert rate_limiter.is_allowed("key1", max_requests=10) is False
    
    def test_rate_limiter_window_expiration(self, rate_limiter):
        """Test that rate limit window expires."""
        # Mock time to control window expiration
        with patch('time.time') as mock_time:
            # Start at time 0
            mock_time.return_value = 0
            
            # Fill up quota
            for i in range(10):
                assert rate_limiter.is_allowed("test_key", max_requests=10, window_seconds=60) is True
            
            # Should be blocked
            assert rate_limiter.is_allowed("test_key", max_requests=10, window_seconds=60) is False
            
            # Move time forward past window
            mock_time.return_value = 61
            
            # Should be allowed again
            assert rate_limiter.is_allowed("test_key", max_requests=10, window_seconds=60) is True
    
    def test_get_reset_time(self, rate_limiter):
        """Test getting reset time."""
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000
            
            # Make a request
            rate_limiter.is_allowed("test_key", window_seconds=60)
            
            # Reset time should be request time + window
            reset_time = rate_limiter.get_reset_time("test_key", window_seconds=60)
            assert reset_time == 1060
    
    def test_get_reset_time_no_requests(self, rate_limiter):
        """Test getting reset time for key with no requests."""
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000
            
            reset_time = rate_limiter.get_reset_time("new_key", window_seconds=60)
            assert reset_time == 1000


class TestAuthenticationMiddleware:
    """Test authentication middleware functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        
        @app.get("/public")
        async def public_endpoint():
            return {"message": "public"}
        
        @app.get("/protected")
        async def protected_endpoint():
            return {"message": "protected"}
        
        return app
    
    @pytest.fixture
    def app_with_middleware(self, app):
        """Create app with authentication middleware."""
        app.add_middleware(AuthenticationMiddleware)
        return app
    
    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client."""
        return TestClient(app_with_middleware)
    
    def test_public_path_access(self, client):
        """Test access to public paths."""
        # Health endpoint should be accessible
        response = client.get("/health")
        assert response.status_code == 404  # Endpoint doesn't exist but middleware allows it
        
        # Docs should be accessible
        response = client.get("/docs")
        assert response.status_code == 404  # Endpoint doesn't exist but middleware allows it
    
    def test_security_headers(self, client):
        """Test that security headers are added."""
        response = client.get("/public")
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        
        assert "Content-Security-Policy" in response.headers
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    
    def test_rate_limit_headers(self, client):
        """Test that rate limit headers are added."""
        response = client.get("/public")
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_process_time_header(self, client):
        """Test that process time header is added."""
        response = client.get("/public")
        
        assert "X-Process-Time" in response.headers
        assert float(response.headers["X-Process-Time"]) >= 0
    
    @patch('bruno_ai_server.middleware.auth_middleware.verify_token')
    def test_protected_route_with_valid_token(self, mock_verify_token, client):
        """Test access to protected route with valid token."""
        mock_verify_token.return_value = {"sub": "123", "exp": time.time() + 3600}
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.get("/protected", headers=headers)
        
        # Should pass middleware validation (endpoint doesn't exist but middleware allows)
        assert response.status_code == 404
    
    def test_protected_route_without_token(self, client):
        """Test access to protected route without token."""
        response = client.get("/protected")
        
        assert response.status_code == 401
        assert "Authorization header missing" in response.json()["detail"]
    
    def test_protected_route_with_invalid_token(self, client):
        """Test access to protected route with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token', return_value=None):
            response = client.get("/protected", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]
    
    def test_malformed_authorization_header(self, client):
        """Test handling of malformed authorization header."""
        headers = {"Authorization": "InvalidFormat"}
        response = client.get("/protected", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid authorization header format" in response.json()["detail"]
    
    def test_non_bearer_token(self, client):
        """Test handling of non-bearer token."""
        headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        response = client.get("/protected", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid authorization header format" in response.json()["detail"]
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # This is a simplified test - in practice, we'd need to mock the rate limiter
        # to avoid actually hitting rate limits during tests
        
        # Make multiple requests quickly
        responses = []
        for i in range(5):
            response = client.get("/public")
            responses.append(response)
        
        # All should succeed (under rate limit)
        for response in responses:
            assert response.status_code == 200
            assert "X-RateLimit-Remaining" in response.headers
    
    def test_client_ip_extraction(self):
        """Test client IP extraction logic."""
        middleware = AuthenticationMiddleware(None)
        
        # Test X-Forwarded-For header
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client = None
        
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.1"
        
        # Test X-Real-IP header
        request.headers = {"X-Real-IP": "192.168.1.2"}
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.2"
        
        # Test fallback to client.host
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.3"
        
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.3"
        
        # Test fallback when no client
        request.client = None
        ip = middleware._get_client_ip(request)
        assert ip == "unknown"
    
    def test_public_path_detection(self):
        """Test public path detection logic."""
        middleware = AuthenticationMiddleware(None)
        
        # Test exact matches
        assert middleware._is_public_path("/docs") is True
        assert middleware._is_public_path("/health") is True
        assert middleware._is_public_path("/api/users/login") is True  # Fixed path
        
        # Test prefix matches
        assert middleware._is_public_path("/docs/swagger") is True
        assert middleware._is_public_path("/static/css/style.css") is True
        
        # Test non-public paths
        assert middleware._is_public_path("/api/pantry") is False
        assert middleware._is_public_path("/api/protected") is False
    
    def test_public_path_trailing_slash_edge_cases(self):
        """Test trailing slash edge cases for public path detection."""
        middleware = AuthenticationMiddleware(None)
        
        # Test exact match paths with trailing slashes
        assert middleware._is_public_path("/docs/") is True
        assert middleware._is_public_path("/redoc/") is True
        assert middleware._is_public_path("/health/") is True
        assert middleware._is_public_path("/") is True  # root path
        
        # Test prefix matches with trailing slashes
        assert middleware._is_public_path("/docs/") is True
        assert middleware._is_public_path("/redoc/") is True
        assert middleware._is_public_path("/static/") is True
        
        # Test prefix matches - paths that start with public prefixes
        assert middleware._is_public_path("/docs/swagger/") is True
        assert middleware._is_public_path("/docs/swagger/ui") is True
        assert middleware._is_public_path("/redoc/assets/") is True
        assert middleware._is_public_path("/static/css/") is True
        assert middleware._is_public_path("/static/js/app.js") is True
        
        # Test edge case: prefix with trailing slash in the path being checked
        # These should match because /docs/ starts with /docs
        assert middleware._is_public_path("/docs/") is True
        assert middleware._is_public_path("/redoc/") is True
        assert middleware._is_public_path("/static/") is True
        
        # Test paths that should NOT match
        assert middleware._is_public_path("/documents") is False  # doesn't start with /docs
        assert middleware._is_public_path("/redocument") is False  # doesn't start with /redoc
        assert middleware._is_public_path("/stationary") is False  # doesn't start with /static
        
        # Test paths with multiple trailing slashes (edge case)
        assert middleware._is_public_path("/docs//") is True
        assert middleware._is_public_path("/static//css/") is True
    
    def test_public_path_boundary_cases(self):
        """Test boundary cases to ensure prefixes don't match incorrectly."""
        middleware = AuthenticationMiddleware(None)
        
        # These paths should NOT be considered public because they don't match
        # the prefix boundaries correctly (this was the main bug)
        assert middleware._is_public_path("/documents") is False     # not /docs
        assert middleware._is_public_path("/redocument") is False    # not /redoc  
        assert middleware._is_public_path("/stationary") is False    # not /static
        assert middleware._is_public_path("/documentation") is False # not /docs
        assert middleware._is_public_path("/redistribute") is False  # not /redoc
        assert middleware._is_public_path("/statistics") is False    # not /static
        
        # These should still work correctly (proper prefix matches)
        assert middleware._is_public_path("/docs") is True
        assert middleware._is_public_path("/docs/") is True
        assert middleware._is_public_path("/docs/anything") is True
        assert middleware._is_public_path("/redoc") is True
        assert middleware._is_public_path("/redoc/") is True
        assert middleware._is_public_path("/redoc/anything") is True
        assert middleware._is_public_path("/static") is True
        assert middleware._is_public_path("/static/") is True
        assert middleware._is_public_path("/static/anything") is True


class TestRequireAuth:
    """Test RequireAuth dependency."""
    
    @pytest.fixture
    def require_auth(self):
        """Create RequireAuth instance."""
        return RequireAuth()
    
    @pytest.mark.asyncio
    async def test_require_auth_with_valid_token(self, require_auth):
        """Test RequireAuth with valid token."""
        credentials = MagicMock()
        credentials.credentials = "valid_token"
        
        request = MagicMock()
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "123"}
            
            result = await require_auth(credentials, request)
            assert result == {"sub": "123"}
    
    @pytest.mark.asyncio
    async def test_require_auth_with_invalid_token(self, require_auth):
        """Test RequireAuth with invalid token."""
        credentials = MagicMock()
        credentials.credentials = "invalid_token"
        
        request = MagicMock()
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await require_auth(credentials, request)
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_require_auth_no_credentials(self, require_auth):
        """Test RequireAuth with no credentials."""
        request = MagicMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await require_auth(None, request)
        
        assert exc_info.value.status_code == 401


class TestRequireRole:
    """Test RequireRole dependency."""
    
    @pytest.fixture
    def require_admin(self):
        """Create RequireRole instance for admin."""
        return RequireRole(["admin"])
    
    @pytest.mark.asyncio
    async def test_require_role_with_correct_role(self, require_admin):
        """Test RequireRole with correct role."""
        credentials = MagicMock()
        credentials.credentials = "valid_token"
        
        request = MagicMock()
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "123", "roles": ["admin", "user"]}
            
            result = await require_admin(credentials, request)
            assert result == {"sub": "123", "roles": ["admin", "user"]}
    
    @pytest.mark.asyncio
    async def test_require_role_with_wrong_role(self, require_admin):
        """Test RequireRole with wrong role."""
        credentials = MagicMock()
        credentials.credentials = "valid_token"
        
        request = MagicMock()
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "123", "roles": ["user"]}
            
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(credentials, request)
            
            assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_require_role_no_roles(self, require_admin):
        """Test RequireRole with no roles in token."""
        credentials = MagicMock()
        credentials.credentials = "valid_token"
        
        request = MagicMock()
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(credentials, request)
            
            assert exc_info.value.status_code == 403


class TestRequireActiveUser:
    """Test RequireActiveUser dependency."""
    
    @pytest.fixture
    def require_active_user(self):
        """Create RequireActiveUser instance."""
        return RequireActiveUser(require_verified=True)
    
    @pytest.mark.asyncio
    async def test_require_active_user_success(self, require_active_user):
        """Test RequireActiveUser with active and verified user."""
        credentials = MagicMock()
        credentials.credentials = "valid_token"
        
        request = MagicMock()
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "123",
                "active": True,
                "verified": True
            }
            
            result = await require_active_user(credentials, request)
            assert result["sub"] == "123"
    
    @pytest.mark.asyncio
    async def test_require_active_user_inactive(self, require_active_user):
        """Test RequireActiveUser with inactive user."""
        credentials = MagicMock()
        credentials.credentials = "valid_token"
        
        request = MagicMock()
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "123",
                "active": False,
                "verified": True
            }
            
            with pytest.raises(HTTPException) as exc_info:
                await require_active_user(credentials, request)
            
            assert exc_info.value.status_code == 403
            assert "deactivated" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_active_user_unverified(self, require_active_user):
        """Test RequireActiveUser with unverified user."""
        credentials = MagicMock()
        credentials.credentials = "valid_token"
        
        request = MagicMock()
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "123",
                "active": True,
                "verified": False
            }
            
            with pytest.raises(HTTPException) as exc_info:
                await require_active_user(credentials, request)
            
            assert exc_info.value.status_code == 403
            assert "verification required" in exc_info.value.detail


class TestOptionalUser:
    """Test optional user utility function."""
    
    def test_get_optional_user_with_token(self):
        """Test getting optional user with valid token."""
        request = MagicMock()
        request.headers = {"Authorization": "Bearer valid_token"}
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "123"}
            
            result = get_optional_user(request)
            assert result == {"sub": "123"}
    
    def test_get_optional_user_no_token(self):
        """Test getting optional user without token."""
        request = MagicMock()
        request.headers = {}
        
        result = get_optional_user(request)
        assert result is None
    
    def test_get_optional_user_invalid_token(self):
        """Test getting optional user with invalid token."""
        request = MagicMock()
        request.headers = {"Authorization": "Bearer invalid_token"}
        
        with patch('bruno_ai_server.middleware.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = None
            
            result = get_optional_user(request)
            assert result is None
    
    def test_get_optional_user_malformed_header(self):
        """Test getting optional user with malformed header."""
        request = MagicMock()
        request.headers = {"Authorization": "InvalidFormat"}
        
        result = get_optional_user(request)
        assert result is None


class TestSecurityConfig:
    """Test security configuration constants."""
    
    def test_security_config_values(self):
        """Test that security config has expected values."""
        assert SecurityConfig.DEFAULT_RATE_LIMIT == 60
        assert SecurityConfig.AUTH_RATE_LIMIT == 10
        assert SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES == 15
        assert SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert SecurityConfig.MIN_PASSWORD_LENGTH == 8
        assert SecurityConfig.MAX_PASSWORD_LENGTH == 128
        
        # Test security headers
        headers = SecurityConfig.SECURITY_HEADERS
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "Content-Security-Policy" in headers
        assert headers["X-Frame-Options"] == "DENY"

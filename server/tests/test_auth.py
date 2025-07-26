"""
Unit tests for authentication endpoints.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from bruno_ai_server.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from bruno_ai_server.config import settings
from bruno_ai_server.models.user import User


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test failed password verification."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "123"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token structure
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        assert payload["sub"] == "123"
        assert "exp" in payload

    def test_create_access_token_with_expiry(self):
        """Test access token creation with custom expiry."""
        data = {"sub": "123"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)

        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + expires_delta

        # Allow 1 second tolerance
        assert abs((exp_time - expected_time).total_seconds()) < 1

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "123"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token structure
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        assert payload["sub"] == "123"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_create_refresh_token_with_expiry(self):
        """Test refresh token creation with custom expiry."""
        data = {"sub": "123"}
        expires_delta = timedelta(days=14)
        token = create_refresh_token(data, expires_delta)

        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + expires_delta

        # Allow 1 second tolerance
        assert abs((exp_time - expected_time).total_seconds()) < 1

    def test_verify_token_valid(self):
        """Test verifying a valid token."""
        data = {"sub": "123"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "123"

    def test_verify_token_invalid(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"

        payload = verify_token(invalid_token)
        assert payload is None

    def test_verify_token_expired(self):
        """Test verifying an expired token."""
        data = {"sub": "123"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta)

        payload = verify_token(token)
        assert payload is None


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        return User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_verified=False,
        )

    def test_register_user_success(self, mock_db_session, client):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "newpassword123"
        }

        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.get_async_session") as mock_get_session:

            mock_get_user.return_value = None  # User doesn't exist
            mock_get_session.return_value = mock_db_session
            mock_db_session.add = AsyncMock()
            mock_db_session.commit = AsyncMock()
            mock_db_session.refresh = AsyncMock()
            mock_db_session.execute = AsyncMock()
            mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

            response = client.post("/users/register", json=user_data)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["email"] == user_data["email"]
            assert response_data["full_name"] == user_data["full_name"]
            assert "id" in response_data

    def test_register_user_duplicate_email(self, mock_db_session, client, sample_user):
        """Test registration with duplicate email."""
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "testpassword123"
        }

        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.get_async_session") as mock_get_session:

            mock_get_user.return_value = sample_user  # User already exists
            mock_get_session.return_value = mock_db_session

            response = client.post("/users/register", json=user_data)

            assert response.status_code == 400
            assert "Email already registered" in response.json()["detail"]

    def test_register_user_weak_password(self, client):
        """Test registration with weak password."""
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "weak"  # Less than 8 characters
        }

        response = client.post("/users/register", json=user_data)

        assert response.status_code == 422  # Validation error

    def test_login_user_success(self, mock_db_session, client, sample_user):
        """Test successful user login."""
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }

        with patch("bruno_ai_server.routes.auth.authenticate_user") as mock_auth, \
             patch("bruno_ai_server.routes.auth.get_async_session") as mock_get_session:

            mock_auth.return_value = sample_user
            mock_get_session.return_value = mock_db_session

            response = client.post("/users/login", json=login_data)

            assert response.status_code == 200
            response_data = response.json()
            assert "access_token" in response_data
            assert "refresh_token" in response_data
            assert response_data["token_type"] == "bearer"

            # Verify token validity
            access_token = response_data["access_token"]
            payload = verify_token(access_token)
            assert payload is not None
            assert payload["sub"] == str(sample_user.id)

    def test_login_user_invalid_credentials(self, mock_db_session, client):
        """Test login with invalid credentials."""
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }

        with patch("bruno_ai_server.routes.auth.authenticate_user") as mock_auth, \
             patch("bruno_ai_server.routes.auth.get_async_session") as mock_get_session:

            mock_auth.return_value = False  # Invalid credentials
            mock_get_session.return_value = mock_db_session

            response = client.post("/users/login", json=login_data)

            assert response.status_code == 401
            assert "Incorrect email or password" in response.json()["detail"]

    def test_login_user_inactive(self, mock_db_session, client, sample_user):
        """Test login with inactive user."""
        sample_user.is_active = False
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }

        with patch("bruno_ai_server.routes.auth.authenticate_user") as mock_auth, \
             patch("bruno_ai_server.routes.auth.get_async_session") as mock_get_session:

            mock_auth.return_value = sample_user
            mock_get_session.return_value = mock_db_session

            response = client.post("/users/login", json=login_data)

            assert response.status_code == 400
            assert "Inactive user" in response.json()["detail"]

    def test_refresh_token_success(self, mock_db_session, client, sample_user):
        """Test successful token refresh."""
        refresh_token = create_refresh_token({"sub": str(sample_user.id)})
        refresh_data = {"refresh_token": refresh_token}

        with patch("bruno_ai_server.routes.auth.get_user_from_refresh_token") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.get_async_session") as mock_get_session:

            mock_get_user.return_value = sample_user
            mock_get_session.return_value = mock_db_session

            response = client.post("/users/refresh", json=refresh_data)

            assert response.status_code == 200
            response_data = response.json()
            assert "access_token" in response_data
            assert response_data["token_type"] == "bearer"

            # Verify new access token
            access_token = response_data["access_token"]
            payload = verify_token(access_token)
            assert payload is not None
            assert payload["sub"] == str(sample_user.id)

    def test_refresh_token_invalid(self, mock_db_session, client):
        """Test refresh with invalid token."""
        refresh_data = {"refresh_token": "invalid.refresh.token"}

        with patch("bruno_ai_server.routes.auth.get_user_from_refresh_token") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.get_async_session") as mock_get_session:

            mock_get_user.side_effect = Exception("Invalid refresh token")
            mock_get_session.return_value = mock_db_session

            response = client.post("/users/refresh", json=refresh_data)

            assert response.status_code == 401

    def test_get_current_user_success(self, mock_db_session, client, sample_user):
        """Test getting current user info."""
        access_token = create_access_token({"sub": str(sample_user.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        with patch("bruno_ai_server.routes.auth.get_current_active_user") as mock_get_user:
            mock_get_user.return_value = sample_user

            response = client.get("/users/me", headers=headers)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["id"] == sample_user.id
            assert response_data["email"] == sample_user.email
            assert response_data["full_name"] == sample_user.full_name

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/users/me")

        assert response.status_code == 403  # No authorization header

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}

        response = client.get("/users/me", headers=headers)

        assert response.status_code == 401


class TestTokenExpiration:
    """Test token expiration behavior."""

    def test_access_token_default_expiration(self):
        """Test access token default expiration time."""
        data = {"sub": "123"}
        token = create_access_token(data)

        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        # Allow 1 second tolerance
        assert abs((exp_time - expected_time).total_seconds()) < 1

    def test_refresh_token_default_expiration(self):
        """Test refresh token default expiration time."""
        data = {"sub": "123"}
        token = create_refresh_token(data)

        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        # Allow 1 second tolerance
        assert abs((exp_time - expected_time).total_seconds()) < 1


class TestAuthenticationDependencies:
    """Test authentication dependencies."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        return User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_verified=False,
        )

    def test_protected_endpoint_success(self, mock_db_session, client, sample_user):
        """Test accessing protected endpoint with valid token."""
        access_token = create_access_token({"sub": str(sample_user.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        with patch("bruno_ai_server.auth.get_async_session") as mock_get_session, \
             patch("bruno_ai_server.auth.select") as mock_select:

            mock_get_session.return_value = mock_db_session
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = sample_user
            mock_db_session.execute.return_value = mock_result

            response = client.get("/users/me", headers=headers)

            assert response.status_code == 200

    def test_protected_endpoint_inactive_user(self, mock_db_session, client, sample_user):
        """Test accessing protected endpoint with inactive user."""
        sample_user.is_active = False
        access_token = create_access_token({"sub": str(sample_user.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        with patch("bruno_ai_server.auth.get_async_session") as mock_get_session, \
             patch("bruno_ai_server.auth.select") as mock_select:

            mock_get_session.return_value = mock_db_session
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = sample_user
            mock_db_session.execute.return_value = mock_result

            response = client.get("/users/me", headers=headers)

            assert response.status_code == 400
            assert "Inactive user" in response.json()["detail"]


@pytest.fixture
def client():
    """Test client fixture."""
    from bruno_ai_server.main import app
    return TestClient(app)

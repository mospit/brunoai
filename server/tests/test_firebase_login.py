"""
Unit tests for Firebase-integrated user login.
"""

import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from bruno_ai_server.models.user import User
from bruno_ai_server.routes.auth import login_user
from bruno_ai_server.schemas import UserLogin


class TestFirebaseLogin:
    """Test Firebase-integrated user login."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        mock_session = AsyncMock(spec=AsyncSession)
        return mock_session

    @pytest.fixture
    def user_login_data(self):
        """Sample user login data."""
        return UserLogin(
            email="test@example.com",
            password="testpassword123"
        )

    @pytest.fixture
    def mock_firebase_service(self):
        """Mock Firebase service."""
        mock_service = MagicMock()
        mock_service.is_initialized.return_value = True
        mock_service.authenticate_user_with_password = AsyncMock()
        return mock_service

    @pytest.fixture
    def mock_user(self):
        """Mock user instance."""
        user = User(
            email="test@example.com",
            name="Test User",
            firebase_uid="firebase_uid_123",
            is_active=True,
            is_verified=True
        )
        user.id = uuid.uuid4()
        return user

    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request."""
        mock_request = MagicMock(spec=Request)
        return mock_request

    @pytest.fixture
    def mock_response(self):
        """Mock FastAPI response."""
        mock_response = MagicMock(spec=Response)
        return mock_response

    @pytest.fixture
    def mock_security_service(self):
        """Mock security service."""
        mock_service = MagicMock()
        mock_service.get_client_ip.return_value = "127.0.0.1"
        mock_service.sanitize_request_data.return_value = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        return mock_service

    @pytest.fixture
    def mock_cookie_service(self):
        """Mock cookie service."""
        mock_service = MagicMock()
        mock_service.set_auth_cookies = MagicMock()
        return mock_service

    async def test_login_user_success_with_firebase(
        self,
        mock_db_session,
        user_login_data,
        mock_firebase_service,
        mock_user,
        mock_request,
        mock_response,
        mock_security_service,
        mock_cookie_service
    ):
        """Test successful user login with Firebase integration."""
        
        # Setup Firebase authentication result
        firebase_auth_result = {
            'uid': 'firebase_uid_123',
            'email': 'test@example.com',
            'verified': True,
            'id_token': 'test_id_token',
            'refresh_token': 'test_refresh_token'
        }
        mock_firebase_service.authenticate_user_with_password.return_value = firebase_auth_result

        with patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.create_access_token") as mock_create_access, \
             patch("bruno_ai_server.routes.auth.create_refresh_token") as mock_create_refresh, \
             patch("bruno_ai_server.routes.auth.security_service", mock_security_service), \
             patch("bruno_ai_server.routes.auth.cookie_service", mock_cookie_service):

            # Setup returns
            mock_get_user.return_value = mock_user
            mock_create_access.return_value = "test_access_token"
            mock_create_refresh.return_value = "test_refresh_token"

            # Call the function
            result = await login_user(user_login_data, mock_request, mock_response, mock_db_session)

            # Assertions
            assert result["access_token"] == "test_access_token"
            assert result["refresh_token"] == "test_refresh_token"
            assert result["token_type"] == "bearer"

            # Verify Firebase authentication was called
            mock_firebase_service.authenticate_user_with_password.assert_called_once_with(
                "test@example.com", "testpassword123"
            )

            # Verify token creation
            mock_create_access.assert_called_once()
            mock_create_refresh.assert_called_once()

            # Verify cookies were set
            mock_cookie_service.set_auth_cookies.assert_called_once()

    async def test_login_user_firebase_authentication_fails(
        self,
        mock_db_session,
        user_login_data,
        mock_firebase_service,
        mock_request,
        mock_response,
        mock_security_service,
        mock_cookie_service
    ):
        """Test login when Firebase authentication fails."""
        
        # Setup Firebase to fail authentication
        mock_firebase_service.authenticate_user_with_password.return_value = None

        with patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.security_service", mock_security_service), \
             patch("bruno_ai_server.routes.auth.cookie_service", mock_cookie_service):

            with pytest.raises(HTTPException) as exc_info:
                await login_user(user_login_data, mock_request, mock_response, mock_db_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Incorrect email or password" in str(exc_info.value.detail)

    async def test_login_user_email_not_verified(
        self,
        mock_db_session,
        user_login_data,
        mock_firebase_service,
        mock_request,
        mock_response,
        mock_security_service,
        mock_cookie_service
    ):
        """Test login when email is not verified."""
        
        # Setup Firebase authentication with unverified email
        firebase_auth_result = {
            'uid': 'firebase_uid_123',
            'email': 'test@example.com',
            'verified': False,  # Email not verified
            'id_token': 'test_id_token'
        }
        mock_firebase_service.authenticate_user_with_password.return_value = firebase_auth_result

        with patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.security_service", mock_security_service), \
             patch("bruno_ai_server.routes.auth.cookie_service", mock_cookie_service):

            with pytest.raises(HTTPException) as exc_info:
                await login_user(user_login_data, mock_request, mock_response, mock_db_session)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Email not verified" in str(exc_info.value.detail)

    async def test_login_user_not_found_in_database(
        self,
        mock_db_session,
        user_login_data,
        mock_firebase_service,
        mock_request,
        mock_response,
        mock_security_service,
        mock_cookie_service
    ):
        """Test login when user exists in Firebase but not in database."""
        
        # Setup Firebase authentication success
        firebase_auth_result = {
            'uid': 'firebase_uid_123',
            'email': 'test@example.com',
            'verified': True,
            'id_token': 'test_id_token'
        }
        mock_firebase_service.authenticate_user_with_password.return_value = firebase_auth_result

        with patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.security_service", mock_security_service), \
             patch("bruno_ai_server.routes.auth.cookie_service", mock_cookie_service):

            # User not found in database
            mock_get_user.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await login_user(user_login_data, mock_request, mock_response, mock_db_session)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "User not found" in str(exc_info.value.detail)

    async def test_login_user_inactive_user(
        self,
        mock_db_session,
        user_login_data,
        mock_firebase_service,
        mock_user,
        mock_request,
        mock_response,
        mock_security_service,
        mock_cookie_service
    ):
        """Test login with inactive user."""
        
        # Setup Firebase authentication success
        firebase_auth_result = {
            'uid': 'firebase_uid_123',
            'email': 'test@example.com',
            'verified': True,
            'id_token': 'test_id_token'
        }
        mock_firebase_service.authenticate_user_with_password.return_value = firebase_auth_result

        # Make user inactive
        mock_user.is_active = False

        with patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.security_service", mock_security_service), \
             patch("bruno_ai_server.routes.auth.cookie_service", mock_cookie_service):

            mock_get_user.return_value = mock_user

            with pytest.raises(HTTPException) as exc_info:
                await login_user(user_login_data, mock_request, mock_response, mock_db_session)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Inactive user" in str(exc_info.value.detail)

    async def test_login_user_without_firebase_integration(
        self,
        mock_db_session,
        user_login_data,
        mock_firebase_service,
        mock_user,
        mock_request,
        mock_response,
        mock_security_service,
        mock_cookie_service
    ):
        """Test login when Firebase is not initialized."""
        
        # Setup Firebase as not initialized
        mock_firebase_service.is_initialized.return_value = False

        with patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.create_access_token") as mock_create_access, \
             patch("bruno_ai_server.routes.auth.create_refresh_token") as mock_create_refresh, \
             patch("bruno_ai_server.routes.auth.security_service", mock_security_service), \
             patch("bruno_ai_server.routes.auth.cookie_service", mock_cookie_service), \
             patch("bruno_ai_server.routes.auth.logging") as mock_logging:

            # Setup returns
            mock_get_user.return_value = mock_user
            mock_create_access.return_value = "test_access_token"
            mock_create_refresh.return_value = "test_refresh_token"

            # Call the function
            result = await login_user(user_login_data, mock_request, mock_response, mock_db_session)

            # Assertions
            assert result["access_token"] == "test_access_token"
            assert result["refresh_token"] == "test_refresh_token"
            assert result["token_type"] == "bearer"

            # Verify Firebase authentication was not called
            mock_firebase_service.authenticate_user_with_password.assert_not_called()

            # Verify warning was logged
            mock_logging.getLogger.return_value.warning.assert_called_once()

    async def test_login_user_token_creation_parameters(
        self,
        mock_db_session,
        user_login_data,
        mock_firebase_service,
        mock_user,
        mock_request,
        mock_response,
        mock_security_service,
        mock_cookie_service
    ):
        """Test that tokens are created with correct parameters."""
        
        # Setup Firebase authentication success
        firebase_auth_result = {
            'uid': 'firebase_uid_123',
            'email': 'test@example.com',
            'verified': True,
            'id_token': 'test_id_token'
        }
        mock_firebase_service.authenticate_user_with_password.return_value = firebase_auth_result

        with patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.create_access_token") as mock_create_access, \
             patch("bruno_ai_server.routes.auth.create_refresh_token") as mock_create_refresh, \
             patch("bruno_ai_server.routes.auth.security_service", mock_security_service), \
             patch("bruno_ai_server.routes.auth.cookie_service", mock_cookie_service):

            mock_get_user.return_value = mock_user
            mock_create_access.return_value = "test_access_token"
            mock_create_refresh.return_value = "test_refresh_token"

            # Call the function
            await login_user(user_login_data, mock_request, mock_response, mock_db_session)

            # Verify access token creation
            mock_create_access.assert_called_once()
            access_call_args = mock_create_access.call_args
            assert access_call_args[1]["data"]["sub"] == str(mock_user.id)
            assert access_call_args[1]["expires_delta"] == timedelta(minutes=15)

            # Verify refresh token creation
            mock_create_refresh.assert_called_once()
            refresh_call_args = mock_create_refresh.call_args
            assert refresh_call_args[1]["data"]["sub"] == str(mock_user.id)
            assert refresh_call_args[1]["expires_delta"] == timedelta(days=7)

    async def test_login_user_security_data_sanitization(
        self,
        mock_db_session,
        user_login_data,
        mock_firebase_service,
        mock_user,
        mock_request,
        mock_response,
        mock_security_service,
        mock_cookie_service
    ):
        """Test that user input is properly sanitized."""
        
        # Setup Firebase authentication success
        firebase_auth_result = {
            'uid': 'firebase_uid_123',
            'email': 'test@example.com',
            'verified': True,
            'id_token': 'test_id_token'
        }
        mock_firebase_service.authenticate_user_with_password.return_value = firebase_auth_result

        with patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.create_access_token") as mock_create_access, \
             patch("bruno_ai_server.routes.auth.create_refresh_token") as mock_create_refresh, \
             patch("bruno_ai_server.routes.auth.security_service", mock_security_service), \
             patch("bruno_ai_server.routes.auth.cookie_service", mock_cookie_service):

            mock_get_user.return_value = mock_user
            mock_create_access.return_value = "test_access_token"
            mock_create_refresh.return_value = "test_refresh_token"

            # Call the function
            await login_user(user_login_data, mock_request, mock_response, mock_db_session)

            # Verify data sanitization was called
            mock_security_service.sanitize_request_data.assert_called_once_with({
                "email": user_login_data.email,
                "password": user_login_data.password
            })

            # Verify client IP was retrieved
            mock_security_service.get_client_ip.assert_called_once_with(mock_request)

    async def test_login_user_cookie_management(
        self,
        mock_db_session,
        user_login_data,
        mock_firebase_service,
        mock_user,
        mock_request,
        mock_response,
        mock_security_service,
        mock_cookie_service
    ):
        """Test that cookies are properly managed during login."""
        
        # Setup Firebase authentication success
        firebase_auth_result = {
            'uid': 'firebase_uid_123',
            'email': 'test@example.com',
            'verified': True,
            'id_token': 'test_id_token'
        }
        mock_firebase_service.authenticate_user_with_password.return_value = firebase_auth_result

        with patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.create_access_token") as mock_create_access, \
             patch("bruno_ai_server.routes.auth.create_refresh_token") as mock_create_refresh, \
             patch("bruno_ai_server.routes.auth.security_service", mock_security_service), \
             patch("bruno_ai_server.routes.auth.cookie_service", mock_cookie_service):

            mock_get_user.return_value = mock_user
            mock_create_access.return_value = "test_access_token"
            mock_create_refresh.return_value = "test_refresh_token"

            # Call the function
            await login_user(user_login_data, mock_request, mock_response, mock_db_session)

            # Verify cookies were set with correct tokens
            mock_cookie_service.set_auth_cookies.assert_called_once_with(
                mock_response, mock_request, "test_access_token", "test_refresh_token"
            )


class TestFirebaseServiceIntegration:
    """Test Firebase service integration in login."""

    @pytest.fixture
    def mock_firebase_service(self):
        """Mock Firebase service for isolated testing."""
        with patch("bruno_ai_server.routes.auth.firebase_service") as mock_service:
            yield mock_service

    async def test_firebase_authentication_call_parameters(self, mock_firebase_service):
        """Test that Firebase authentication is called with correct parameters."""
        mock_firebase_service.is_initialized.return_value = True
        mock_firebase_service.authenticate_user_with_password.return_value = {
            'uid': 'test_uid',
            'email': 'test@example.com',
            'verified': True
        }

        user_data = UserLogin(email="test@example.com", password="testpassword123")
        mock_db = AsyncMock()
        mock_request = MagicMock()
        mock_response = MagicMock()

        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.create_access_token") as mock_create_access, \
             patch("bruno_ai_server.routes.auth.create_refresh_token") as mock_create_refresh, \
             patch("bruno_ai_server.routes.auth.security_service") as mock_security, \
             patch("bruno_ai_server.routes.auth.cookie_service") as mock_cookie:

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.is_active = True
            mock_get_user.return_value = mock_user
            mock_create_access.return_value = "test_access_token"
            mock_create_refresh.return_value = "test_refresh_token"
            mock_security.get_client_ip.return_value = "127.0.0.1"
            mock_security.sanitize_request_data.return_value = {
                "email": "test@example.com",
                "password": "testpassword123"
            }

            await login_user(user_data, mock_request, mock_response, mock_db)

            # Verify Firebase authentication was called with sanitized data
            mock_firebase_service.authenticate_user_with_password.assert_called_once_with(
                "test@example.com", "testpassword123"
            )

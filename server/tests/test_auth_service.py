"""
Unit tests for authentication service layer.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from bruno_ai_server.services.auth_service import AuthenticationService, auth_service
from bruno_ai_server.models.user import User
from bruno_ai_server.models.auth import EmailVerification, RefreshToken
from bruno_ai_server.validation import ValidationError


class TestAuthenticationService:
    """Test authentication service functionality."""
    
    @pytest.fixture
    def auth_service_instance(self):
        """Create authentication service instance."""
        return AuthenticationService()
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        return User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            password_hash="$2b$12$dummy_hash",
            is_active=True,
            is_verified=False,
            verification_token="test_token"
        )
    
    def test_password_hashing(self, auth_service_instance):
        """Test password hashing functionality."""
        password = "TestPassword123!"
        hashed = auth_service_instance.hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        assert len(hashed) > 0
    
    def test_password_verification_success(self, auth_service_instance):
        """Test successful password verification."""
        password = "TestPassword123!"
        hashed = auth_service_instance.hash_password(password)
        
        assert auth_service_instance.verify_password(password, hashed) is True
    
    def test_password_verification_failure(self, auth_service_instance):
        """Test failed password verification."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = auth_service_instance.hash_password(password)
        
        assert auth_service_instance.verify_password(wrong_password, hashed) is False
    
    def test_password_verification_empty_inputs(self, auth_service_instance):
        """Test password verification with empty inputs."""
        assert auth_service_instance.verify_password("", "hash") is False
        assert auth_service_instance.verify_password("password", "") is False
        assert auth_service_instance.verify_password("", "") is False
    
    def test_generate_verification_token(self, auth_service_instance):
        """Test verification token generation."""
        token1 = auth_service_instance.generate_verification_token()
        token2 = auth_service_instance.generate_verification_token()
        
        assert isinstance(token1, str)
        assert isinstance(token2, str)
        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2  # Should be unique
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_service_instance, mock_db_session):
        """Test successful user creation."""
        with patch.object(auth_service_instance, 'get_user_by_email', return_value=None):
            user = await auth_service_instance.create_user(
                mock_db_session,
                "test@example.com",
                "TestPassword123!",
                "Test User"
            )
            
            assert user.email == "test@example.com"
            assert user.full_name == "Test User"
            assert user.is_active is True
            assert user.is_verified is False
            assert user.password_hash != "TestPassword123!"
            assert user.verification_token is not None
            
            # Verify database operations
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, auth_service_instance, mock_db_session, sample_user):
        """Test user creation with duplicate email."""
        with patch.object(auth_service_instance, 'get_user_by_email', return_value=sample_user):
            with pytest.raises(ValueError, match="User with this email already exists"):
                await auth_service_instance.create_user(
                    mock_db_session,
                    "test@example.com",
                    "TestPassword123!",
                    "Test User"
                )
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, auth_service_instance, mock_db_session):
        """Test user creation with invalid email."""
        with pytest.raises(ValidationError):
            await auth_service_instance.create_user(
                mock_db_session,
                "invalid-email",
                "TestPassword123!",
                "Test User"
            )
    
    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, auth_service_instance, mock_db_session):
        """Test user creation with weak password."""
        with patch.object(auth_service_instance, 'get_user_by_email', return_value=None):
            with pytest.raises(ValidationError):
                await auth_service_instance.create_user(
                    mock_db_session,
                    "test@example.com",
                    "weak",
                    "Test User"
                )
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, auth_service_instance, mock_db_session, sample_user):
        """Test getting user by email."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db_session.execute.return_value = mock_result
        
        user = await auth_service_instance.get_user_by_email(mock_db_session, "test@example.com")
        
        assert user == sample_user
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, auth_service_instance, mock_db_session):
        """Test getting non-existent user by email."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        user = await auth_service_instance.get_user_by_email(mock_db_session, "nonexistent@example.com")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_empty_input(self, auth_service_instance, mock_db_session):
        """Test getting user with empty email."""
        user = await auth_service_instance.get_user_by_email(mock_db_session, "")
        assert user is None
        
        user = await auth_service_instance.get_user_by_email(mock_db_session, None)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, auth_service_instance, mock_db_session, sample_user):
        """Test getting user by ID."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db_session.execute.return_value = mock_result
        
        user = await auth_service_instance.get_user_by_id(mock_db_session, 1)
        
        assert user == sample_user
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service_instance, mock_db_session, sample_user):
        """Test successful user authentication."""
        # Hash a test password
        test_password = "TestPassword123!"
        sample_user.password_hash = auth_service_instance.hash_password(test_password)
        
        with patch.object(auth_service_instance, 'get_user_by_email', return_value=sample_user):
            user = await auth_service_instance.authenticate_user(
                mock_db_session,
                "test@example.com",
                test_password
            )
            
            assert user == sample_user
            mock_db_session.commit.assert_called_once()
            assert user.last_login is not None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service_instance, mock_db_session, sample_user):
        """Test authentication with wrong password."""
        sample_user.password_hash = auth_service_instance.hash_password("correct_password")
        
        with patch.object(auth_service_instance, 'get_user_by_email', return_value=sample_user):
            user = await auth_service_instance.authenticate_user(
                mock_db_session,
                "test@example.com",
                "wrong_password"
            )
            
            assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, auth_service_instance, mock_db_session):
        """Test authentication with nonexistent user."""
        with patch.object(auth_service_instance, 'get_user_by_email', return_value=None):
            user = await auth_service_instance.authenticate_user(
                mock_db_session,
                "nonexistent@example.com",
                "password"
            )
            
            assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_empty_inputs(self, auth_service_instance, mock_db_session):
        """Test authentication with empty inputs."""
        user = await auth_service_instance.authenticate_user(mock_db_session, "", "password")
        assert user is None
        
        user = await auth_service_instance.authenticate_user(mock_db_session, "email@test.com", "")
        assert user is None
        
        user = await auth_service_instance.authenticate_user(mock_db_session, "", "")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_create_email_verification(self, auth_service_instance, mock_db_session):
        """Test email verification creation."""
        verification = await auth_service_instance.create_email_verification(
            mock_db_session,
            1,
            "test@example.com",
            "email_verify",
            24
        )
        
        assert verification.user_id == 1
        assert verification.email == "test@example.com"
        assert verification.token_type == "email_verify"
        assert verification.verification_token is not None
        assert verification.expires_at > datetime.utcnow()
        
        mock_db_session.execute.assert_called_once()  # Delete old tokens
        mock_db_session.add.assert_called_once()
        assert mock_db_session.commit.call_count == 2
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_email_token_success(self, auth_service_instance, mock_db_session, sample_user):
        """Test successful email token verification."""
        verification = EmailVerification(
            id=1,
            user_id=1,
            verification_token="test_token",
            email="test@example.com",
            token_type="email_verify",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        verification.user = sample_user
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = verification
        mock_db_session.execute.return_value = mock_result
        
        result = await auth_service_instance.verify_email_token(
            mock_db_session,
            "test_token",
            "email_verify"
        )
        
        assert result is not None
        user, ver = result
        assert user == sample_user
        assert ver == verification
        assert sample_user.is_verified is True
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_email_token_not_found(self, auth_service_instance, mock_db_session):
        """Test email token verification with invalid token."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        result = await auth_service_instance.verify_email_token(
            mock_db_session,
            "invalid_token",
            "email_verify"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_verify_email_token_expired(self, auth_service_instance, mock_db_session, sample_user):
        """Test email token verification with expired token."""
        verification = EmailVerification(
            id=1,
            user_id=1,
            verification_token="expired_token",
            email="test@example.com",
            token_type="email_verify",
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )
        verification.user = sample_user
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = verification
        mock_db_session.execute.return_value = mock_result
        
        result = await auth_service_instance.verify_email_token(
            mock_db_session,
            "expired_token",
            "email_verify"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self, auth_service_instance, mock_db_session):
        """Test refresh token creation."""
        device_info = {"device": "iPhone", "os": "iOS 15"}
        
        refresh_token = await auth_service_instance.create_refresh_token(
            mock_db_session,
            1,
            "jwt_token_string",
            device_info,
            7
        )
        
        assert refresh_token.user_id == 1
        assert refresh_token.token == "jwt_token_string"
        assert refresh_token.device_info == device_info
        assert refresh_token.expires_at > datetime.utcnow()
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_refresh_token_success(self, auth_service_instance, mock_db_session, sample_user):
        """Test getting valid refresh token."""
        refresh_token = RefreshToken(
            id=1,
            user_id=1,
            token="valid_token",
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_revoked=False
        )
        refresh_token.user = sample_user
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = refresh_token
        mock_db_session.execute.return_value = mock_result
        
        result = await auth_service_instance.get_refresh_token(mock_db_session, "valid_token")
        
        assert result == refresh_token
    
    @pytest.mark.asyncio
    async def test_get_refresh_token_expired(self, auth_service_instance, mock_db_session):
        """Test getting expired refresh token."""
        refresh_token = RefreshToken(
            id=1,
            user_id=1,
            token="expired_token",
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
            is_revoked=False
        )
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = refresh_token
        mock_db_session.execute.return_value = mock_result
        
        result = await auth_service_instance.get_refresh_token(mock_db_session, "expired_token")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_refresh_token_not_found(self, auth_service_instance, mock_db_session):
        """Test getting non-existent refresh token."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        result = await auth_service_instance.get_refresh_token(mock_db_session, "nonexistent_token")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_revoke_refresh_token_success(self, auth_service_instance, mock_db_session):
        """Test successful refresh token revocation."""
        refresh_token = RefreshToken(
            id=1,
            user_id=1,
            token="token_to_revoke",
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_revoked=False
        )
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = refresh_token
        mock_db_session.execute.return_value = mock_result
        
        result = await auth_service_instance.revoke_refresh_token(mock_db_session, "token_to_revoke")
        
        assert result is True
        assert refresh_token.is_revoked is True
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_refresh_token_not_found(self, auth_service_instance, mock_db_session):
        """Test revoking non-existent refresh token."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        result = await auth_service_instance.revoke_refresh_token(mock_db_session, "nonexistent_token")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens(self, auth_service_instance, mock_db_session):
        """Test revoking all user tokens."""
        token1 = RefreshToken(id=1, user_id=1, token="token1", is_revoked=False)
        token2 = RefreshToken(id=2, user_id=1, token="token2", is_revoked=False)
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [token1, token2]
        mock_db_session.execute.return_value = mock_result
        
        count = await auth_service_instance.revoke_all_user_tokens(mock_db_session, 1)
        
        assert count == 2
        assert token1.is_revoked is True
        assert token2.is_revoked is True
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens_none_found(self, auth_service_instance, mock_db_session):
        """Test revoking all user tokens when none exist."""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        count = await auth_service_instance.revoke_all_user_tokens(mock_db_session, 1)
        
        assert count == 0
        mock_db_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, auth_service_instance, mock_db_session):
        """Test cleanup of expired tokens."""
        mock_refresh_result = MagicMock()
        mock_refresh_result.rowcount = 3
        
        mock_verification_result = MagicMock()
        mock_verification_result.rowcount = 2
        
        mock_db_session.execute.side_effect = [mock_refresh_result, mock_verification_result]
        
        result = await auth_service_instance.cleanup_expired_tokens(mock_db_session)
        
        assert result["refresh_tokens_deleted"] == 3
        assert result["email_verifications_deleted"] == 2
        assert mock_db_session.execute.call_count == 2
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service_instance, mock_db_session, sample_user):
        """Test successful password change."""
        old_password = "OldPassword123!"
        new_password = "NewPassword456!"
        sample_user.password_hash = auth_service_instance.hash_password(old_password)
        
        with patch.object(auth_service_instance, 'get_user_by_id', return_value=sample_user), \
             patch.object(auth_service_instance, 'revoke_all_user_tokens', return_value=2):
            
            result = await auth_service_instance.change_password(
                mock_db_session,
                1,
                old_password,
                new_password
            )
            
            assert result is True
            assert auth_service_instance.verify_password(new_password, sample_user.password_hash)
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, auth_service_instance, mock_db_session, sample_user):
        """Test password change with wrong current password."""
        old_password = "OldPassword123!"
        wrong_password = "WrongPassword123!"
        new_password = "NewPassword456!"
        sample_user.password_hash = auth_service_instance.hash_password(old_password)
        
        with patch.object(auth_service_instance, 'get_user_by_id', return_value=sample_user):
            with pytest.raises(ValueError, match="Current password is incorrect"):
                await auth_service_instance.change_password(
                    mock_db_session,
                    1,
                    wrong_password,
                    new_password
                )
    
    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(self, auth_service_instance, mock_db_session, sample_user):
        """Test password change with weak new password."""
        old_password = "OldPassword123!"
        weak_password = "weak"
        sample_user.password_hash = auth_service_instance.hash_password(old_password)
        
        with patch.object(auth_service_instance, 'get_user_by_id', return_value=sample_user):
            with pytest.raises(ValidationError):
                await auth_service_instance.change_password(
                    mock_db_session,
                    1,
                    old_password,
                    weak_password
                )
    
    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self, auth_service_instance, mock_db_session):
        """Test password change for non-existent user."""
        with patch.object(auth_service_instance, 'get_user_by_id', return_value=None):
            result = await auth_service_instance.change_password(
                mock_db_session,
                999,
                "current_password",
                "NewPassword123!"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self, auth_service_instance, mock_db_session, sample_user):
        """Test successful password reset."""
        new_password = "NewPassword456!"
        verification = EmailVerification(
            id=1,
            user_id=1,
            verification_token="reset_token",
            email="test@example.com",
            token_type="password_reset"
        )
        
        with patch.object(auth_service_instance, 'verify_email_token', return_value=(sample_user, verification)), \
             patch.object(auth_service_instance, 'revoke_all_user_tokens', return_value=1):
            
            result = await auth_service_instance.reset_password(
                mock_db_session,
                "reset_token",
                new_password
            )
            
            assert result is True
            assert auth_service_instance.verify_password(new_password, sample_user.password_hash)
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, auth_service_instance, mock_db_session):
        """Test password reset with invalid token."""
        with patch.object(auth_service_instance, 'verify_email_token', return_value=None):
            with pytest.raises(ValueError, match="Invalid or expired reset token"):
                await auth_service_instance.reset_password(
                    mock_db_session,
                    "invalid_token",
                    "NewPassword123!"
                )
    
    @pytest.mark.asyncio
    async def test_reset_password_weak_password(self, auth_service_instance, mock_db_session, sample_user):
        """Test password reset with weak password."""
        verification = EmailVerification(
            id=1,
            user_id=1,
            verification_token="reset_token",
            email="test@example.com",
            token_type="password_reset"
        )
        
        with patch.object(auth_service_instance, 'verify_email_token', return_value=(sample_user, verification)):
            with pytest.raises(ValidationError):
                await auth_service_instance.reset_password(
                    mock_db_session,
                    "reset_token",
                    "weak"
                )
    
    def test_global_auth_service_instance(self):
        """Test that global auth service instance exists."""
        assert auth_service is not None
        assert isinstance(auth_service, AuthenticationService)

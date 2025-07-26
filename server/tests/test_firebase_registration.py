"""
Unit tests for Firebase-integrated user registration.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from bruno_ai_server.models.user import Household, HouseholdMember, User
from bruno_ai_server.routes.auth import register_user
from bruno_ai_server.schemas import UserCreate


class TestFirebaseRegistration:
    """Test Firebase-integrated user registration."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.execute = AsyncMock()
        return mock_session

    @pytest.fixture
    def user_create_data(self):
        """Sample user creation data."""
        return UserCreate(
            email="test@example.com",
            name="Test User",
            password="testpassword123"
        )

    @pytest.fixture
    def mock_firebase_service(self):
        """Mock Firebase service."""
        mock_service = MagicMock()
        mock_service.is_initialized.return_value = True
        mock_service.create_user = AsyncMock()
        mock_service.delete_user = AsyncMock()
        return mock_service

    @pytest.fixture
    def mock_user(self):
        """Mock user instance."""
        user = User(
            email="test@example.com",
            name="Test User",
            firebase_uid="firebase_uid_123",
            is_active=True,
            is_verified=False
        )
        user.id = uuid.uuid4()
        return user

    @pytest.fixture
    def mock_household(self):
        """Mock household instance."""
        household = Household(
            name="Test User's Household",
            invite_code="12345678",
            admin_user_id=uuid.uuid4()
        )
        household.id = uuid.uuid4()
        return household

    @pytest.fixture  
    def mock_household_member(self):
        """Mock household member instance."""
        member = HouseholdMember(
            user_id=uuid.uuid4(),
            household_id=uuid.uuid4(),
            role="admin"
        )
        member.id = uuid.uuid4()
        return member

    async def test_register_user_success_with_firebase(
        self, 
        mock_db_session, 
        user_create_data, 
        mock_firebase_service,
        mock_user,
        mock_household,
        mock_household_member
    ):
        """Test successful user registration with Firebase integration."""
        
        # Setup mocks
        firebase_uid = "firebase_uid_123"
        mock_firebase_service.create_user.return_value = firebase_uid
        
        # Mock database queries
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Mock user creation and refresh
        def mock_refresh(obj):
            if isinstance(obj, User):
                obj.id = mock_user.id
            elif isinstance(obj, Household):
                obj.id = mock_household.id
            elif isinstance(obj, HouseholdMember):
                obj.id = mock_household_member.id
                
        mock_db_session.refresh.side_effect = mock_refresh

        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.User") as mock_user_class, \
             patch("bruno_ai_server.routes.auth.Household") as mock_household_class, \
             patch("bruno_ai_server.routes.auth.HouseholdMember") as mock_member_class:

            # Setup returns
            mock_get_user.return_value = None
            mock_user_class.return_value = mock_user
            mock_household_class.return_value = mock_household
            mock_member_class.return_value = mock_household_member

            # Call the function
            result = await register_user(user_create_data, mock_db_session)

            # Assertions
            assert result == mock_user
            mock_firebase_service.create_user.assert_called_once_with(
                email=user_create_data.email,
                password=user_create_data.password,
                name=user_create_data.name
            )
            
            # Verify database operations
            assert mock_db_session.add.call_count == 3  # user, household, member
            assert mock_db_session.commit.call_count == 3
            assert mock_db_session.refresh.call_count == 3

    async def test_register_user_duplicate_email(
        self, 
        mock_db_session, 
        user_create_data, 
        mock_user
    ):
        """Test registration with duplicate email."""
        
        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user:
            mock_get_user.return_value = mock_user  # User already exists

            with pytest.raises(HTTPException) as exc_info:
                await register_user(user_create_data, mock_db_session)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Email already registered" in str(exc_info.value.detail)

    async def test_register_user_firebase_creation_fails(
        self, 
        mock_db_session, 
        user_create_data, 
        mock_firebase_service
    ):
        """Test registration when Firebase user creation fails."""
        
        # Setup Firebase to fail
        mock_firebase_service.create_user.return_value = None
        
        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service):

            mock_get_user.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await register_user(user_create_data, mock_db_session)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Failed to create user in Firebase Authentication" in str(exc_info.value.detail)

    async def test_register_user_without_firebase_integration(
        self, 
        mock_db_session, 
        user_create_data, 
        mock_firebase_service,
        mock_user,
        mock_household,
        mock_household_member
    ):
        """Test registration when Firebase is not initialized."""
        
        # Setup Firebase as not initialized
        mock_firebase_service.is_initialized.return_value = False
        
        # Mock database queries
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Mock user creation and refresh
        def mock_refresh(obj):
            if isinstance(obj, User):
                obj.id = mock_user.id
            elif isinstance(obj, Household):
                obj.id = mock_household.id
            elif isinstance(obj, HouseholdMember):
                obj.id = mock_household_member.id
                
        mock_db_session.refresh.side_effect = mock_refresh

        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.User") as mock_user_class, \
             patch("bruno_ai_server.routes.auth.Household") as mock_household_class, \
             patch("bruno_ai_server.routes.auth.HouseholdMember") as mock_member_class, \
             patch("bruno_ai_server.routes.auth.logging") as mock_logging:

            # Setup returns
            mock_get_user.return_value = None
            mock_user_class.return_value = mock_user
            mock_household_class.return_value = mock_household
            mock_member_class.return_value = mock_household_member

            # Call the function
            result = await register_user(user_create_data, mock_db_session)

            # Assertions
            assert result == mock_user
            mock_firebase_service.create_user.assert_not_called()
            
            # Verify warning was logged
            mock_logging.getLogger.return_value.warning.assert_called_once()
            
            # Verify user was created with None firebase_uid
            mock_user_class.assert_called_once()
            call_args = mock_user_class.call_args
            assert call_args[1]["firebase_uid"] is None

    async def test_register_user_db_creation_fails_with_firebase_cleanup(
        self, 
        mock_db_session, 
        user_create_data, 
        mock_firebase_service,
        mock_user
    ):
        """Test registration when database creation fails and Firebase user needs cleanup."""
        
        firebase_uid = "firebase_uid_123"
        mock_firebase_service.create_user.return_value = firebase_uid
        
        # Mock database failure
        mock_db_session.commit.side_effect = Exception("Database error")
        
        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.User") as mock_user_class:

            mock_get_user.return_value = None
            mock_user_class.return_value = mock_user

            with pytest.raises(HTTPException) as exc_info:
                await register_user(user_create_data, mock_db_session)

            # Verify Firebase cleanup was called
            mock_firebase_service.delete_user.assert_called_once_with(firebase_uid)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create user" in str(exc_info.value.detail)

    async def test_register_user_creates_default_household(
        self, 
        mock_db_session, 
        user_create_data, 
        mock_firebase_service,
        mock_user,
        mock_household,
        mock_household_member
    ):
        """Test that registration creates a default household for the user."""
        
        firebase_uid = "firebase_uid_123"
        mock_firebase_service.create_user.return_value = firebase_uid
        
        # Mock database queries
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Mock user creation and refresh
        def mock_refresh(obj):
            if isinstance(obj, User):
                obj.id = mock_user.id
            elif isinstance(obj, Household):
                obj.id = mock_household.id
            elif isinstance(obj, HouseholdMember):
                obj.id = mock_household_member.id
                
        mock_db_session.refresh.side_effect = mock_refresh

        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.User") as mock_user_class, \
             patch("bruno_ai_server.routes.auth.Household") as mock_household_class, \
             patch("bruno_ai_server.routes.auth.HouseholdMember") as mock_member_class, \
             patch("bruno_ai_server.routes.auth.generate_invite_code") as mock_generate_code:

            # Setup returns
            mock_get_user.return_value = None
            mock_user_class.return_value = mock_user
            mock_household_class.return_value = mock_household
            mock_member_class.return_value = mock_household_member
            mock_generate_code.return_value = "12345678"

            # Call the function
            result = await register_user(user_create_data, mock_db_session)

            # Verify household creation
            mock_household_class.assert_called_once()
            household_call_args = mock_household_class.call_args[1]
            assert household_call_args["name"] == f"{mock_user.name}'s Household"
            assert household_call_args["invite_code"] == "12345678"
            assert household_call_args["admin_user_id"] == mock_user.id

            # Verify household member creation
            mock_member_class.assert_called_once()
            member_call_args = mock_member_class.call_args[1]
            assert member_call_args["user_id"] == mock_user.id
            assert member_call_args["household_id"] == mock_household.id
            assert member_call_args["role"] == "admin"

    async def test_register_user_ensures_unique_invite_code(
        self, 
        mock_db_session, 
        user_create_data, 
        mock_firebase_service,
        mock_user,
        mock_household,
        mock_household_member
    ):
        """Test that registration ensures unique invite codes."""
        
        firebase_uid = "firebase_uid_123"
        mock_firebase_service.create_user.return_value = firebase_uid
        
        # Mock database queries - first call returns existing household, second returns None
        mock_existing_household = MagicMock()
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            mock_existing_household,  # First invite code already exists
            None,  # Second invite code is unique
        ]
        
        # Mock user creation and refresh
        def mock_refresh(obj):
            if isinstance(obj, User):
                obj.id = mock_user.id
            elif isinstance(obj, Household):
                obj.id = mock_household.id
            elif isinstance(obj, HouseholdMember):
                obj.id = mock_household_member.id
                
        mock_db_session.refresh.side_effect = mock_refresh

        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.firebase_service", mock_firebase_service), \
             patch("bruno_ai_server.routes.auth.User") as mock_user_class, \
             patch("bruno_ai_server.routes.auth.Household") as mock_household_class, \
             patch("bruno_ai_server.routes.auth.HouseholdMember") as mock_member_class, \
             patch("bruno_ai_server.routes.auth.generate_invite_code") as mock_generate_code:

            # Setup returns
            mock_get_user.return_value = None
            mock_user_class.return_value = mock_user
            mock_household_class.return_value = mock_household
            mock_member_class.return_value = mock_household_member
            mock_generate_code.side_effect = ["11111111", "22222222"]  # Two different codes

            # Call the function
            result = await register_user(user_create_data, mock_db_session)

            # Verify generate_invite_code was called twice
            assert mock_generate_code.call_count == 2
            
            # Verify database was queried twice for invite code uniqueness
            assert mock_db_session.execute.call_count >= 2


class TestFirebaseService:
    """Test Firebase service integration."""

    @pytest.fixture
    def mock_firebase_service(self):
        """Mock Firebase service for isolated testing."""
        with patch("bruno_ai_server.routes.auth.firebase_service") as mock_service:
            yield mock_service

    async def test_firebase_service_initialized_check(self, mock_firebase_service):
        """Test that the registration correctly checks Firebase initialization."""
        mock_firebase_service.is_initialized.return_value = False
        
        user_data = UserCreate(
            email="test@example.com",
            name="Test User", 
            password="testpassword123"
        )
        mock_db = AsyncMock()
        
        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.User") as mock_user_class, \
             patch("bruno_ai_server.routes.auth.Household"), \
             patch("bruno_ai_server.routes.auth.HouseholdMember"), \
             patch("bruno_ai_server.routes.auth.logging"):

            mock_get_user.return_value = None
            mock_user_class.return_value = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_db.refresh.return_value = None

            await register_user(user_data, mock_db)

            # Verify initialization was checked
            mock_firebase_service.is_initialized.assert_called_once()
            # Verify create_user was not called since Firebase is not initialized
            mock_firebase_service.create_user.assert_not_called()

    async def test_firebase_user_creation_parameters(self, mock_firebase_service):
        """Test that Firebase user creation is called with correct parameters."""
        mock_firebase_service.is_initialized.return_value = True
        mock_firebase_service.create_user.return_value = "test_firebase_uid"
        
        user_data = UserCreate(
            email="test@example.com",
            name="Test User",
            password="testpassword123"
        )
        mock_db = AsyncMock()
        
        with patch("bruno_ai_server.routes.auth.get_user_by_email") as mock_get_user, \
             patch("bruno_ai_server.routes.auth.User") as mock_user_class, \
             patch("bruno_ai_server.routes.auth.Household"), \
             patch("bruno_ai_server.routes.auth.HouseholdMember"):

            mock_get_user.return_value = None
            mock_user_class.return_value = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_db.refresh.return_value = None

            await register_user(user_data, mock_db)

            # Verify Firebase user creation was called with correct parameters
            mock_firebase_service.create_user.assert_called_once_with(
                email="test@example.com",
                password="testpassword123",
                name="Test User"
            )

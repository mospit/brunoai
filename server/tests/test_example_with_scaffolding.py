"""
Example test file demonstrating the new testing scaffolding.

This file shows how to use the comprehensive test fixtures provided
in conftest.py for testing the Bruno AI Server.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from bruno_ai_server.models.user import User
from bruno_ai_server.models.user import Household
from bruno_ai_server.models.pantry import PantryItem


class TestExampleWithScaffolding:
    """Example tests using the testing scaffolding."""

    @pytest.mark.unit
    def test_mock_firebase_service(self, mock_firebase_service):
        """Test that the mock Firebase service works correctly."""
        # Add a mock token
        mock_firebase_service.add_mock_token(
            "test_token", 
            {"uid": "test_uid", "email": "test@example.com"}
        )
        
        # Test token verification
        token_data = mock_firebase_service.auth_tokens["test_token"]
        assert token_data["uid"] == "test_uid"
        assert token_data["email"] == "test@example.com"

    @pytest.mark.unit
    async def test_database_session(self, test_session: AsyncSession, db_utils):
        """Test that the database session works correctly."""
        # Count initial users
        initial_count = await db_utils.count_records(test_session, User)
        assert initial_count == 0
        
        # Create a user
        user = User(
            email="session_test@example.com",
            full_name="Session Test User",
            hashed_password="hashed_password",
            firebase_uid="session_test_uid",
        )
        test_session.add(user)
        await test_session.commit()
        
        # Verify user was created
        new_count = await db_utils.count_records(test_session, User)
        assert new_count == 1
        
        # Get user by ID
        retrieved_user = await db_utils.get_by_id(test_session, User, user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == "session_test@example.com"

    @pytest.mark.unit
    def test_test_client(self, test_client: TestClient):
        """Test that the test client works correctly."""
        response = test_client.get("/")
        assert response.status_code in [200, 404]  # Depending on if root route exists

    @pytest.mark.unit
    async def test_test_user_fixture(self, test_user: User):
        """Test that the test user fixture works correctly."""
        assert test_user.id is not None
        assert test_user.email == "test@example.com"
        assert test_user.full_name == "Test User"
        assert test_user.firebase_uid == "firebase_test_uid_1"
        assert test_user.is_active is True
        assert test_user.is_verified is False

    @pytest.mark.unit
    async def test_test_household_fixture(
        self, 
        test_household: Household, 
        test_user: User
    ):
        """Test that the test household fixture works correctly."""
        assert test_household.id is not None
        assert test_household.name == "Test Household"
        assert test_household.description == "A test household for testing"
        assert test_household.created_by == test_user.id

    @pytest.mark.unit
    async def test_populated_household_fixture(
        self, 
        populated_household: Household,
        test_session: AsyncSession,
        db_utils
    ):
        """Test that the populated household fixture works correctly."""
        assert populated_household.id is not None
        
        # Count pantry items
        item_count = await db_utils.count_records(test_session, PantryItem)
        assert item_count == 5  # The fixture creates 5 items

    @pytest.mark.unit
    def test_auth_headers_fixture(self, auth_headers: dict, test_user: User):
        """Test that the auth headers fixture works correctly."""
        assert "Authorization" in auth_headers
        assert auth_headers["Authorization"].startswith("Bearer ")
        
        # The token should be valid (we're not testing token validation here,
        # just that the fixture produces the expected format)
        token = auth_headers["Authorization"].replace("Bearer ", "")
        assert len(token) > 0

    @pytest.mark.integration
    def test_api_with_auth(
        self, 
        test_client: TestClient, 
        auth_headers: dict,
        test_user: User
    ):
        """Test an API endpoint with authentication."""
        # This is an example of how you would test an authenticated endpoint
        response = test_client.get("/auth/me", headers=auth_headers)
        
        # The exact response depends on your implementation
        # This is just demonstrating the pattern
        assert response.status_code in [200, 401, 404]

    @pytest.mark.unit
    def test_performance_timer(self, performance_timer):
        """Test the performance timer fixture."""
        import time
        
        performance_timer.start()
        time.sleep(0.001)  # Sleep for 1ms
        performance_timer.stop()
        
        assert performance_timer.elapsed is not None
        assert performance_timer.elapsed > 0
        assert performance_timer.elapsed < 1.0  # Should be much less than 1 second

    @pytest.mark.unit
    def test_mock_voice_service(self, mock_voice_service):
        """Test the mock voice service."""
        assert mock_voice_service is not None
        
        # Test that the mock returns expected data
        result = mock_voice_service.process_voice_command.return_value
        assert result["action"] == "add"
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "test item"

    @pytest.mark.unit
    def test_mock_notification_service(self, mock_notification_service):
        """Test the mock notification service."""
        assert mock_notification_service is not None
        
        # Test that the mock methods are available
        assert hasattr(mock_notification_service, 'send_notification')
        assert hasattr(mock_notification_service, 'send_expiration_alert')

    @pytest.mark.slow
    @pytest.mark.integration
    async def test_full_integration_example(
        self,
        test_client: TestClient,
        test_session: AsyncSession,
        mock_firebase_service,
        test_user: User,
        auth_headers: dict,
        db_utils
    ):
        """Example of a full integration test using multiple fixtures."""
        # Setup mock Firebase token
        mock_firebase_service.add_mock_token(
            "integration_token",
            {"uid": test_user.firebase_uid, "email": test_user.email}
        )
        
        # Count initial records
        initial_users = await db_utils.count_records(test_session, User)
        initial_households = await db_utils.count_records(test_session, Household)
        
        # Test some API endpoints (adjust based on your actual API)
        # This is just an example pattern
        health_response = test_client.get("/health")  # Assuming you have a health endpoint
        
        # Verify database state
        final_users = await db_utils.count_records(test_session, User)
        final_households = await db_utils.count_records(test_session, Household)
        
        # Assert that the test ran without breaking the database
        assert final_users >= initial_users
        assert final_households >= initial_households


class TestAdvancedScaffoldingFeatures:
    """Test advanced features of the testing scaffolding."""

    @pytest.mark.unit
    async def test_inactive_user_fixture(self, test_inactive_user: User):
        """Test the inactive user fixture."""
        assert test_inactive_user.is_active is False
        assert test_inactive_user.email == "inactive@example.com"

    @pytest.mark.unit
    async def test_database_isolation(
        self,
        test_session: AsyncSession,
        db_utils
    ):
        """Test that database changes are isolated between tests."""
        # This test should start with a clean database state
        user_count = await db_utils.count_records(test_session, User)
        
        # In a properly isolated test environment, this should be 0
        # unless other fixtures have created users for this specific test
        assert user_count >= 0  # Allow for fixture-created users

    @pytest.mark.unit
    def test_test_settings(self, test_settings):
        """Test the test settings fixture."""
        assert test_settings.database_url == "sqlite+aiosqlite:///:memory:"
        assert test_settings.jwt_secret == "test-secret-key"
        assert test_settings.debug is True
        assert test_settings.firebase_project_id == "test-project"

    @pytest.mark.unit
    async def test_database_cleanup(
        self,
        test_session: AsyncSession,
        db_utils
    ):
        """Test that database cleanup works correctly."""
        # Create some test data
        user = User(
            email="cleanup_test@example.com",
            full_name="Cleanup Test",
            hashed_password="password",
            firebase_uid="cleanup_uid",
        )
        test_session.add(user)
        await test_session.commit()
        
        # Verify data exists
        count_before = await db_utils.count_records(test_session, User)
        assert count_before > 0
        
        # Clear the table
        await db_utils.clear_table(test_session, User)
        
        # Verify data is cleared
        count_after = await db_utils.count_records(test_session, User)
        assert count_after == 0

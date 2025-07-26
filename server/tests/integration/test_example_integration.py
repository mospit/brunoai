"""
Example integration test demonstrating the use of test fixtures.

This module shows how to use the integration test fixtures:
- test_app: FastAPI TestClient with dependency overrides
- db_session: SQLAlchemy session bound to in-memory DB with rollback
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from bruno_ai_server.models.user import User


@pytest.mark.integration
async def test_health_endpoint_integration(test_app: TestClient):
    """Test the health endpoint using the integration test client."""
    response = test_app.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "bruno-ai-server"}


@pytest.mark.integration  
async def test_root_endpoint_integration(test_app: TestClient):
    """Test the root endpoint using the integration test client."""
    response = test_app.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}


@pytest.mark.integration
async def test_database_session_integration(db_session: AsyncSession):
    """Test that the database session fixture works correctly with rollback."""
    # Create a test user
    user = User(
        email="integration.test@example.com",
        full_name="Integration Test User",
        hashed_password="hashed_password_123",
        firebase_uid="integration_firebase_uid",
        is_active=True,
        is_verified=False,
    )
    
    # Add to session and commit
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Verify user was created
    assert user.id is not None
    assert user.email == "integration.test@example.com"
    assert user.full_name == "Integration Test User"
    
    # The session will automatically rollback after this test,
    # ensuring test isolation


@pytest.mark.integration
async def test_combined_fixtures_integration(test_app: TestClient, db_session: AsyncSession):
    """Test using both test_app and db_session fixtures together."""
    # First, verify database is clean
    from sqlalchemy import select, func
    result = await db_session.execute(select(func.count(User.id)))
    user_count_before = result.scalar()
    
    # Create a user in the database
    user = User(
        email="combined.test@example.com",
        full_name="Combined Test User", 
        hashed_password="hashed_password_456",
        firebase_uid="combined_firebase_uid",
        is_active=True,
        is_verified=False,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Verify user was created in database
    result = await db_session.execute(select(func.count(User.id)))
    user_count_after = result.scalar()
    assert user_count_after == user_count_before + 1
    
    # Test an API endpoint (this will use the same in-memory database)
    response = test_app.get("/health")
    assert response.status_code == 200
    
    # Both fixtures work together and will clean up automatically


@pytest.mark.integration
@pytest.mark.slow
async def test_firebase_mock_integration(test_app: TestClient, mock_firebase_service_integration):
    """Test that Firebase service is properly mocked in integration tests."""
    # Test that Firebase service is initialized
    assert mock_firebase_service_integration.is_initialized() is True
    
    # Test creating a mock user
    firebase_uid = await mock_firebase_service_integration.create_user(
        email="firebase.test@example.com",
        password="test_password",
        name="Firebase Test User"
    )
    
    assert firebase_uid is not None
    assert firebase_uid.startswith("firebase_uid_")
    
    # Test retrieving the mock user
    user_data = await mock_firebase_service_integration.get_user_by_email("firebase.test@example.com")
    assert user_data is not None
    assert user_data["email"] == "firebase.test@example.com"
    assert user_data["display_name"] == "Firebase Test User"
    assert user_data["uid"] == firebase_uid


@pytest.mark.integration
async def test_database_isolation_integration(db_session: AsyncSession):
    """Test that database isolation works between tests."""
    # This test should start with a clean database every time
    from sqlalchemy import select, func
    result = await db_session.execute(select(func.count(User.id)))
    user_count = result.scalar()
    
    # The count should be 0 because each test gets a clean database
    # due to the rollback in the db_session fixture
    assert user_count == 0
    
    # Create a user to demonstrate the test has a working database
    user = User(
        email="isolation.test@example.com",
        full_name="Isolation Test User",
        hashed_password="hashed_password_789",
        firebase_uid="isolation_firebase_uid",
        is_active=True,
        is_verified=False,
    )
    
    db_session.add(user)
    await db_session.commit()
    
    # Verify user was created
    result = await db_session.execute(select(func.count(User.id)))
    user_count_after = result.scalar()
    assert user_count_after == 1
    
    # This change will be rolled back automatically after the test

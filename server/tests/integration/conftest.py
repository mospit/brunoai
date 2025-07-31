"""
Integration test configuration and fixtures for Bruno AI Server.

This module provides integration test fixtures including:
- test_app: FastAPI TestClient with dependency overrides for DB session (SQLite) and Firebase service mock
- db_session: SQLAlchemy session bound to in-memory DB, rolling back after each test
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import application modules
from bruno_ai_server.config import Settings, settings
from bruno_ai_server.database import Base, get_async_session
from bruno_ai_server.main import app
from bruno_ai_server.services.firebase_service import FirebaseService


# Test database configuration for integration tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


class MockFirebaseServiceForIntegration:
    """Mock Firebase service for integration testing."""
    
    def __init__(self):
        self.users = {}  # Store mock Firebase users
        self.auth_tokens = {}  # Store mock auth tokens
        self._initialized = True
        
    def is_initialized(self) -> bool:
        """Check if Firebase is properly initialized."""
        return self._initialized
        
    async def verify_id_token(self, id_token: str) -> dict:
        """Mock token verification."""
        if id_token in self.auth_tokens:
            return self.auth_tokens[id_token]
        raise Exception("Invalid token")
    
    async def create_user(self, email: str, password: str, name: str, email_verified: bool = True) -> str:
        """Mock user creation."""
        user_id = f"firebase_uid_{len(self.users) + 1}"
        user_data = {
            "uid": user_id,
            "email": email,
            "display_name": name,
            "password": password,  # Store password for authentication
            "email_verified": email_verified,
            "disabled": False,
            "creation_timestamp": 1640995200000,  # Mock timestamp
            "last_sign_in_timestamp": None,
        }
        self.users[user_id] = user_data
        return user_id
    
    async def authenticate_user_with_password(self, email: str, password: str) -> dict:
        """Mock user authentication with password."""
        # Find user by email and check password
        for uid, user_data in self.users.items():
            if user_data["email"] == email:
                # If password matches (or if password wasn't stored), allow authentication
                stored_password = user_data.get("password")
                if stored_password is None or stored_password == password:
                    return {
                        "uid": uid,
                        "email": email,
                        "id_token": f"mock_id_token_{uid}",
                        "refresh_token": f"mock_refresh_token_{uid}",
                        "verified": user_data.get("email_verified", True)
                    }
        return None
    
    async def get_user_by_email(self, email: str) -> dict:
        """Mock get user by email."""
        for uid, user_data in self.users.items():
            if user_data["email"] == email:
                return user_data
        return None
    
    async def update_user(self, uid: str, **kwargs) -> bool:
        """Mock user update."""
        if uid in self.users:
            self.users[uid].update(kwargs)
            return True
        return False
    
    async def delete_user(self, uid: str) -> bool:
        """Mock user deletion."""
        if uid in self.users:
            del self.users[uid]
            return True
        return False
    
    def add_mock_token(self, token: str, user_data: dict):
        """Add a mock auth token for testing."""
        self.auth_tokens[token] = user_data


@pytest.fixture(scope="session")
def integration_event_loop():
    """Create an instance of the default event loop for integration test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def integration_test_settings() -> Settings:
    """Create test settings for integration tests with in-memory SQLite database."""
    return Settings(
        db_url=TEST_DATABASE_URL,  # This is the main database URL setting
        jwt_secret="integration-test-secret-key",
        app_secret_key="integration-test-app-secret-key",
        debug=True,
        environment="development",
        # Override other settings as needed for testing
        gcp_credentials_json='{"project_id": "integration-test-project"}',
        firebase_web_api_key="integration-test-api-key",
    )


@pytest_asyncio.fixture(scope="session")
async def integration_test_engine():
    """Create a test database engine for integration tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(integration_test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session bound to in-memory DB, rolling back after each test.
    
    This fixture provides a clean database session for each test that automatically
    rolls back all changes at the end of the test, ensuring test isolation.
    """
    async with integration_test_engine.begin() as connection:
        # Create a nested transaction that will be rolled back after the test
        async with AsyncSession(
            bind=connection,
            expire_on_commit=False,
        ) as session:
            yield session
            # Rollback transaction after test - this ensures test isolation
            await session.rollback()


@pytest.fixture
def mock_firebase_service_integration() -> MockFirebaseServiceForIntegration:
    """Create a mock Firebase service for integration tests."""
    return MockFirebaseServiceForIntegration()


@pytest.fixture
def test_app(
    integration_test_settings: Settings,
    db_session: AsyncSession,
    mock_firebase_service_integration: MockFirebaseServiceForIntegration
) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI TestClient with dependency overrides for DB session (SQLite) and Firebase service mock.
    
    This fixture provides a fully configured test client with:
    - In-memory SQLite database session override
    - Mock Firebase service to avoid external calls
    - Test-specific settings configuration
    
    Returns:
        TestClient: Configured FastAPI test client for integration testing
    """
    
    # Override database session dependency
    app.dependency_overrides[get_async_session] = lambda: db_session
    
    # Patch settings at the module level to use test settings
    with patch('bruno_ai_server.config.settings', integration_test_settings):
        # Also patch settings in main module
        with patch('bruno_ai_server.main.settings', integration_test_settings):
            # Mock Firebase service at the module level
            with patch('bruno_ai_server.services.firebase_service.firebase_service', mock_firebase_service_integration):
                # Also patch any other places where firebase_service might be imported
                with patch('bruno_ai_server.routes.auth.firebase_service', mock_firebase_service_integration):
                    client = TestClient(app)
                    yield client
    
    # Clean up dependency overrides after test
    app.dependency_overrides.clear()


# Additional integration test utilities
@pytest.fixture
def integration_auth_headers():
    """Create authentication headers for integration API requests."""
    # This can be enhanced to create actual JWT tokens if needed
    return {"Authorization": "Bearer integration_test_token"}


@pytest_asyncio.fixture
async def clean_database(db_session: AsyncSession):
    """Fixture to ensure database is clean before test runs."""
    # This fixture can be used when you need to explicitly clean the database
    # The db_session fixture already provides rollback, but this can be used
    # for additional cleanup if needed
    yield
    # Any cleanup logic can go here if needed




def pytest_configure(config):
    """Configure pytest with integration test markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow integration tests")
    config.addinivalue_line("markers", "auth_integration: marks auth integration tests")
    config.addinivalue_line("markers", "pantry_integration: marks pantry integration tests")
    config.addinivalue_line("markers", "api_integration: marks API integration tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark integration tests."""
    for item in items:
        # Mark all tests in integration folder as integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark specific integration test types
        if "auth" in str(item.fspath).lower() or "auth" in item.name.lower():
            item.add_marker(pytest.mark.auth_integration)
        
        if "pantry" in str(item.fspath).lower() or "pantry" in item.name.lower():
            item.add_marker(pytest.mark.pantry_integration)
        
        if "api" in str(item.fspath).lower() or "api" in item.name.lower():
            item.add_marker(pytest.mark.api_integration)

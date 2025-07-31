"""
Pytest configuration and fixtures for Bruno AI Server tests.

This module provides comprehensive test fixtures including:
- In-memory SQLite database for testing
- Mock Firebase service to avoid external calls
- Test client setup
- Database session management
- Test user and household fixtures
"""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import your application modules
from bruno_ai_server.config import Settings, settings
from bruno_ai_server.database import Base, get_async_session
from bruno_ai_server.main import app
from bruno_ai_server.models.user import User
from bruno_ai_server.models.user import Household
from bruno_ai_server.models.pantry import PantryItem, PantryCategory
from bruno_ai_server.services.firebase_service import FirebaseService
from bruno_ai_server.auth import get_password_hash, create_access_token


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


class MockFirebaseService:
    """Mock Firebase service to avoid external calls during testing."""
    
    def __init__(self):
        self.users = {}  # Store mock Firebase users
        self.auth_tokens = {}  # Store mock auth tokens
        self._initialized = True
        
    async def verify_token(self, token: str) -> dict:
        """Mock token verification."""
        if token in self.auth_tokens:
            return self.auth_tokens[token]
        raise Exception("Invalid token")
    
    async def create_user(self, email: str, password: str) -> dict:
        """Mock user creation."""
        user_id = f"firebase_uid_{len(self.users) + 1}"
        user_data = {
            "uid": user_id,
            "email": email,
            "email_verified": False,
        }
        self.users[user_id] = user_data
        return user_data
    
    async def update_user(self, uid: str, **kwargs) -> dict:
        """Mock user update."""
        if uid in self.users:
            self.users[uid].update(kwargs)
            return self.users[uid]
        raise Exception("User not found")
    
    async def delete_user(self, uid: str) -> bool:
        """Mock user deletion."""
        if uid in self.users:
            del self.users[uid]
            return True
        return False
    
    def add_mock_token(self, token: str, user_data: dict):
        """Add a mock auth token for testing."""
        self.auth_tokens[token] = user_data
    
    def is_initialized(self) -> bool:
        """Check if Firebase is properly initialized."""
        return self._initialized


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings with in-memory database."""
    return Settings(
        db_url=TEST_DATABASE_URL,
        jwt_secret="test-secret-key",
        app_secret_key="test-app-secret-key",
        debug=True,
        environment="development",
        # Override other settings as needed for testing
        gcp_credentials_json='{"project_id": "test-project"}',
        firebase_web_api_key="test-api-key",
    )


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
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
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as connection:
        # Use nested transaction for isolation
        async with AsyncSession(
            bind=connection,
            expire_on_commit=False,
        ) as session:
            yield session
            # Rollback transaction after test
            await session.rollback()


@pytest.fixture
def mock_firebase_service() -> MockFirebaseService:
    """Create a mock Firebase service."""
    return MockFirebaseService()


@pytest.fixture
def test_client(test_settings, test_session, mock_firebase_service) -> TestClient:
    """Create a test client with mocked dependencies."""
    
    # Override database session dependency
    app.dependency_overrides[get_async_session] = lambda: test_session
    
    # Patch settings at the module level to use test settings
    with patch('bruno_ai_server.config.settings', test_settings):
        # Also patch settings in main module
        with patch('bruno_ai_server.main.settings', test_settings):
            # Mock Firebase service
            with patch('bruno_ai_server.services.firebase_service.firebase_service', mock_firebase_service):
                client = TestClient(app)
                yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()


# Test data fixtures
@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create a test user in the database."""
    import uuid
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        name="Test User",
        firebase_uid="firebase_test_uid_1",
        is_active=True,
        is_verified=False,
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_inactive_user(test_session: AsyncSession) -> User:
    """Create an inactive test user."""
    import uuid
    user = User(
        id=uuid.uuid4(),
        email="inactive@example.com",
        name="Inactive User",
        firebase_uid="firebase_test_uid_inactive",
        is_active=False,
        is_verified=False,
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_household(test_session: AsyncSession, test_user: User) -> Household:
    """Create a test household."""
    household = Household(
        name="Test Household",
        description="A test household for testing",
        created_by=test_user.id,
    )
    
    test_session.add(household)
    await test_session.commit()
    await test_session.refresh(household)
    
    return household


@pytest_asyncio.fixture
async def test_pantry_category(test_session: AsyncSession) -> PantryCategory:
    """Create a test pantry category."""
    category = PantryCategory(
        name="Test Category",
        description="A test category for testing",
        icon="test-icon",
        color="#FF5733",
    )
    
    test_session.add(category)
    await test_session.commit()
    await test_session.refresh(category)
    
    return category


@pytest_asyncio.fixture
async def test_pantry_item(
    test_session: AsyncSession,
    test_household: Household,
    test_user: User,
    test_pantry_category: PantryCategory,
) -> PantryItem:
    """Create a test pantry item."""
    item = PantryItem(
        name="Test Item",
        quantity=2.0,
        unit="pieces",
        household_id=test_household.id,
        category_id=test_pantry_category.id,
        added_by=test_user.id,
    )
    
    test_session.add(item)
    await test_session.commit()
    await test_session.refresh(item)
    
    return item


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for API requests."""
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mock_auth_token() -> str:
    """Create a mock auth token."""
    return "mock_auth_token_12345"


# Helper fixtures for common test scenarios
@pytest_asyncio.fixture
async def populated_household(
    test_session: AsyncSession,
    test_household: Household,
    test_user: User,
    test_pantry_category: PantryCategory,
) -> Household:
    """Create a household with multiple pantry items."""
    items = [
        PantryItem(
            name=f"Test Item {i}",
            quantity=float(i),
            unit="pieces",
            household_id=test_household.id,
            category_id=test_pantry_category.id,
            added_by=test_user.id,
        )
        for i in range(1, 6)
    ]
    
    for item in items:
        test_session.add(item)
    
    await test_session.commit()
    
    # Refresh to get updated relationships
    await test_session.refresh(test_household)
    
    return test_household


# Mock external service fixtures
@pytest.fixture
def mock_voice_service():
    """Mock voice processing service."""
    with patch('bruno_ai_server.services.voice_service.VoiceService') as mock:
        mock_instance = Mock()
        mock_instance.process_voice_command = AsyncMock(return_value={
            "action": "add",
            "items": [{"name": "test item", "quantity": 1, "unit": "piece"}]
        })
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_notification_service():
    """Mock notification service."""
    with patch('bruno_ai_server.services.notification_service.NotificationService') as mock:
        mock_instance = Mock()
        mock_instance.send_notification = AsyncMock(return_value=True)
        mock_instance.send_expiration_alert = AsyncMock(return_value=True)
        mock.return_value = mock_instance
        yield mock_instance


# Database utilities for testing
class DatabaseTestUtils:
    """Utility class for database testing operations."""
    
    @staticmethod
    async def count_records(session: AsyncSession, model_class) -> int:
        """Count records in a table."""
        from sqlalchemy import select, func
        result = await session.execute(select(func.count(model_class.id)))
        return result.scalar()
    
    @staticmethod
    async def clear_table(session: AsyncSession, model_class):
        """Clear all records from a table."""
        from sqlalchemy import delete
        await session.execute(delete(model_class))
        await session.commit()
    
    @staticmethod
    async def get_by_id(session: AsyncSession, model_class, record_id):
        """Get a record by ID."""
        from sqlalchemy import select
        result = await session.execute(
            select(model_class).where(model_class.id == record_id)
        )
        return result.scalar_one_or_none()


@pytest.fixture
def db_utils():
    """Provide database testing utilities."""
    return DatabaseTestUtils


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Simple performance timer for tests."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Configuration for pytest plugins
pytest_plugins = [
    "pytest_asyncio",
]

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "auth: marks tests related to authentication")
    config.addinivalue_line("markers", "pantry: marks tests related to pantry functionality")
    config.addinivalue_line("markers", "voice: marks tests related to voice processing")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark unit tests
        if "unit" in str(item.fspath) or "test_unit" in item.name:
            item.add_marker(pytest.mark.unit)
        
        # Mark auth tests
        if "auth" in str(item.fspath) or "test_auth" in item.name:
            item.add_marker(pytest.mark.auth)
        
        # Mark pantry tests
        if "pantry" in str(item.fspath) or "test_pantry" in item.name:
            item.add_marker(pytest.mark.pantry)
        
        # Mark voice tests
        if "voice" in str(item.fspath) or "test_voice" in item.name:
            item.add_marker(pytest.mark.voice)

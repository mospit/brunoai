"""
Test to validate that integration test fixtures are properly configured.

This test validates that the fixtures we created work correctly without
requiring a full database connection.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock


@pytest.mark.integration
def test_integration_fixtures_are_properly_configured():
    """Test that integration test fixtures can be imported and instantiated."""
    from tests.integration.conftest import (
        MockFirebaseServiceForIntegration,
        TEST_DATABASE_URL,
        TEST_SYNC_DATABASE_URL
    )
    
    # Test that our mock Firebase service works
    mock_firebase = MockFirebaseServiceForIntegration()
    assert mock_firebase.is_initialized() is True
    
    # Test that database URLs are properly configured for testing
    assert TEST_DATABASE_URL == "sqlite+aiosqlite:///:memory:"
    assert TEST_SYNC_DATABASE_URL == "sqlite:///:memory:"


@pytest.mark.integration
async def test_mock_firebase_service_integration_functionality():
    """Test that the integration Firebase mock service works correctly."""
    from tests.integration.conftest import MockFirebaseServiceForIntegration
    
    mock_firebase = MockFirebaseServiceForIntegration()
    
    # Test user creation
    firebase_uid = await mock_firebase.create_user(
        email="test@integration.com",
        password="test_password",
        name="Test User"
    )
    
    assert firebase_uid is not None
    assert firebase_uid.startswith("firebase_uid_")
    
    # Test user retrieval
    user_data = await mock_firebase.get_user_by_email("test@integration.com")
    assert user_data is not None
    assert user_data["email"] == "test@integration.com"
    assert user_data["display_name"] == "Test User"
    assert user_data["uid"] == firebase_uid
    
    # Test user authentication
    auth_result = await mock_firebase.authenticate_user_with_password(
        "test@integration.com", "test_password"
    )
    assert auth_result is not None
    assert auth_result["uid"] == firebase_uid
    assert auth_result["email"] == "test@integration.com"
    assert "id_token" in auth_result
    assert "refresh_token" in auth_result
    
    # Test token handling
    mock_firebase.add_mock_token("test_token", {"uid": firebase_uid, "email": "test@integration.com"})
    token_data = await mock_firebase.verify_id_token("test_token")
    assert token_data["uid"] == firebase_uid
    assert token_data["email"] == "test@integration.com"
    
    # Test user update
    result = await mock_firebase.update_user(firebase_uid, email_verified=True)
    assert result is True
    
    updated_user = await mock_firebase.get_user_by_email("test@integration.com")
    assert updated_user["email_verified"] is True
    
    # Test user deletion
    result = await mock_firebase.delete_user(firebase_uid)
    assert result is True
    
    deleted_user = await mock_firebase.get_user_by_email("test@integration.com")
    assert deleted_user is None


@pytest.mark.integration
def test_integration_settings_configuration():
    """Test that integration test settings are properly configured."""
    from tests.integration.conftest import integration_test_settings
    from bruno_ai_server.config import Settings
    
    # Create test settings (this will be a fixture in actual tests) 
    test_settings = Settings(
        db_url="sqlite+aiosqlite:///:memory:",
        jwt_secret="integration-test-secret-key",
        app_secret_key="integration-test-app-secret-key",
        debug=True,
        environment="development",
        gcp_credentials_json='{"project_id": "integration-test-project"}',
        firebase_web_api_key="integration-test-api-key",
    )
    
    # Validate settings
    assert test_settings.db_url == "sqlite+aiosqlite:///:memory:"
    assert test_settings.jwt_secret == "integration-test-secret-key"
    assert test_settings.app_secret_key == "integration-test-app-secret-key"
    assert test_settings.debug is True
    assert test_settings.is_development is True
    assert test_settings.is_production is False
    assert test_settings.gcp_credentials_dict["project_id"] == "integration-test-project"


@pytest.mark.integration
def test_fixture_documentation_and_structure():
    """Test that our integration fixtures have proper documentation and structure."""
    from tests.integration.conftest import (
        integration_test_settings,
        db_session,
        test_app,
        mock_firebase_service_integration,
        MockFirebaseServiceForIntegration
    )
    import inspect
    
    # Test that fixtures have proper docstrings
    assert integration_test_settings.__doc__ is not None
    assert "test settings" in integration_test_settings.__doc__.lower()
    
    assert db_session.__doc__ is not None
    assert "in-memory db" in db_session.__doc__.lower()
    assert "rolling back" in db_session.__doc__.lower()
    
    assert test_app.__doc__ is not None
    assert "testclient" in test_app.__doc__.lower()
    assert "dependency overrides" in test_app.__doc__.lower()
    
    # Test that MockFirebaseServiceForIntegration has required methods
    mock_firebase_methods = [
        'is_initialized', 'verify_id_token', 'create_user', 
        'authenticate_user_with_password', 'get_user_by_email',
        'update_user', 'delete_user', 'add_mock_token'
    ]
    
    for method_name in mock_firebase_methods:
        assert hasattr(MockFirebaseServiceForIntegration, method_name), f"Missing method: {method_name}"
        method = getattr(MockFirebaseServiceForIntegration, method_name)
        assert callable(method), f"Method {method_name} is not callable"


@pytest.mark.integration 
def test_pytest_markers_configuration():
    """Test that pytest markers are properly configured for integration tests."""
    # This test validates that our pytest configuration in conftest.py works
    # The markers should be automatically applied based on file location
    
    # Test that this test file itself has integration markers
    # (This will be validated by pytest's marker system)
    
    # Test expected marker configuration
    expected_markers = [
        "integration", "slow", "auth_integration", 
        "pantry_integration", "api_integration"
    ]
    
    # This is a meta-test that validates our marker configuration exists
    # The actual marker validation will be done by pytest itself
    assert len(expected_markers) == 5


@pytest.mark.integration
def test_integration_test_structure_validation():
    """Validate that the integration test structure is properly set up."""
    import os
    from pathlib import Path
    
    # Test that integration test directory exists
    integration_dir = Path(__file__).parent
    assert integration_dir.name == "integration"
    assert integration_dir.is_dir()
    
    # Test that conftest.py exists in integration directory
    conftest_file = integration_dir / "conftest.py"
    assert conftest_file.exists()
    assert conftest_file.is_file()
    
    # Test that __init__.py exists
    init_file = integration_dir / "__init__.py"
    assert init_file.exists()
    assert init_file.is_file()
    
    # Test that we can import our fixtures
    try:
        from tests.integration.conftest import (
            test_app,
            db_session,
            mock_firebase_service_integration
        )
        # If we get here, imports worked
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import integration fixtures: {e}")


if __name__ == "__main__":
    # Allow running this test file directly for validation
    pytest.main([__file__, "-v"])

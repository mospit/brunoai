"""
Integration test for user registration without authentication middleware.

This test temporarily removes the AuthenticationMiddleware to determine if the
middleware path matching is causing the registration issue. If registration
succeeds without middleware, it confirms the bug is in middleware path matching.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from unittest.mock import patch

from bruno_ai_server.models.user import User, Household, HouseholdMember
from bruno_ai_server.main import app
from bruno_ai_server.database import get_async_session
from bruno_ai_server.middleware.auth_middleware import AuthenticationMiddleware
from .conftest import MockFirebaseServiceForIntegration


def create_test_app_without_auth_middleware(db_session: AsyncSession, mock_firebase: MockFirebaseServiceForIntegration):
    """
    Create a TestClient with AuthenticationMiddleware removed.
    
    This recreates the app without adding the AuthenticationMiddleware to isolate
    whether the middleware is causing the registration issue.
    """
    from bruno_ai_server.config import Settings
    
    # Create test settings
    test_settings = Settings(
        db_url="sqlite+aiosqlite:///:memory:",
        jwt_secret="test-secret-key",
        app_secret_key="test-app-secret-key",
        debug=True,
        environment="development",
        gcp_credentials_json='{"project_id": "test-project"}',
        firebase_web_api_key="test-api-key",
    )
    
    # Create a new FastAPI app instance (similar to main.py but without AuthenticationMiddleware)
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from bruno_ai_server.middleware.security_middleware import SecurityHeadersMiddleware
    from bruno_ai_server.routes import auth_router, pantry_router, voice_router, categories_router
    from bruno_ai_server.routes.auth import compat_router
    from bruno_ai_server.routes.expiration import router as expiration_router
    
    test_app = FastAPI(
        title="Bruno AI Server Test",
        description="Test FastAPI backend without AuthenticationMiddleware",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "User-Agent",
            "X-Requested-With",
            "X-CSRF-Token",
        ],
        expose_headers=["X-Total-Count", "X-Page-Count"],
    )
    
    # Add security headers middleware
    test_app.add_middleware(SecurityHeadersMiddleware)
    
    # INTENTIONALLY SKIP: AuthenticationMiddleware
    # This is the key difference - we're not adding the AuthenticationMiddleware
    
    # Include routers
    test_app.include_router(auth_router, prefix="/api")
    test_app.include_router(pantry_router, prefix="/api")
    test_app.include_router(categories_router, prefix="/api")
    test_app.include_router(voice_router, prefix="/api")
    test_app.include_router(expiration_router, prefix="/api")
    test_app.include_router(compat_router, prefix="/api")
    
    # Health check endpoints
    @test_app.get("/")
    async def root():
        return {"message": "pong"}
        
    @test_app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "bruno-ai-server-test"}
    
    # Override dependencies
    test_app.dependency_overrides[get_async_session] = lambda: db_session
    
    # Patch settings and Firebase service
    with patch('bruno_ai_server.config.settings', test_settings):
        with patch('bruno_ai_server.routes.auth.firebase_service', mock_firebase):
            return TestClient(test_app)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_registration_without_auth_middleware(db_session: AsyncSession):
    """
    Test user registration without AuthenticationMiddleware to isolate middleware issues.
    
    This test:
    1. Creates a TestClient without AuthenticationMiddleware
    2. Attempts user registration
    3. Verifies if registration succeeds without middleware
    4. If successful, confirms the bug is in middleware path matching
    """
    # Create mock Firebase service
    mock_firebase = MockFirebaseServiceForIntegration()
    
    # Create test client without AuthenticationMiddleware
    client = create_test_app_without_auth_middleware(db_session, mock_firebase)
    
    print("\n=== Testing Registration WITHOUT AuthenticationMiddleware ===")
    
    # Test registration data
    registration_data = {
        "email": "test-no-middleware@example.com",
        "name": "Test User No Middleware",
        "password": "ValidPassword123"
    }
    
    print(f"Attempting registration with data: {registration_data}")
    
    # Attempt registration
    response = client.post("/api/users/register", json=registration_data)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    if response.status_code != 200:
        print(f"Response headers: {response.headers}")
        try:
            print(f"Response JSON: {response.json()}")
        except:
            print("Could not parse response as JSON")
    
    # Check if registration succeeded
    if response.status_code == 200:
        print("✅ SUCCESS: Registration worked WITHOUT AuthenticationMiddleware!")
        print("🔍 CONCLUSION: The bug is definitely in AuthenticationMiddleware path matching")
        
        # Verify user was created
        response_data = response.json()
        assert "id" in response_data
        assert response_data["email"] == "test-no-middleware@example.com"
        assert response_data["name"] == "Test User No Middleware"
        
        user_id = uuid.UUID(response_data["id"])
        
        # Verify user exists in database
        result = await db_session.execute(select(User).where(User.id == user_id))
        created_user = result.scalar_one_or_none()
        
        assert created_user is not None
        assert created_user.email == "test-no-middleware@example.com"
        assert created_user.is_active is True
        
        # Verify household was created
        household_result = await db_session.execute(
            select(Household).where(Household.admin_user_id == user_id)
        )
        household = household_result.scalar_one_or_none()
        
        assert household is not None
        assert household.admin_user_id == user_id
        
        print("✅ All database validations passed - registration fully successful")
        
    else:
        print("❌ FAILURE: Registration failed even WITHOUT AuthenticationMiddleware")
        print("🔍 CONCLUSION: The bug is NOT in AuthenticationMiddleware path matching")
        print("   The issue is likely in the route handler, validation, or another component")
        
        # Still assert to make the test fail and provide details
        assert False, f"Registration failed without middleware: {response.status_code} - {response.content}"


@pytest.mark.integration
@pytest.mark.asyncio 
async def test_registration_with_auth_middleware_for_comparison(db_session: AsyncSession):
    """
    Test user registration WITH AuthenticationMiddleware for comparison.
    
    This test uses the normal app setup with AuthenticationMiddleware to compare
    the behavior and confirm the middleware is causing the issue.
    """
    # Create mock Firebase service
    mock_firebase = MockFirebaseServiceForIntegration()
    
    print("\n=== Testing Registration WITH AuthenticationMiddleware (for comparison) ===")
    
    # Use the standard test_app fixture setup (which includes AuthenticationMiddleware)
    from bruno_ai_server.config import Settings
    
    test_settings = Settings(
        db_url="sqlite+aiosqlite:///:memory:",
        jwt_secret="test-secret-key", 
        app_secret_key="test-app-secret-key",
        debug=True,
        environment="development",
        gcp_credentials_json='{"project_id": "test-project"}',
        firebase_web_api_key="test-api-key",
    )
    
    # Override dependencies on the main app (which includes AuthenticationMiddleware)
    app.dependency_overrides[get_async_session] = lambda: db_session
    
    with patch('bruno_ai_server.config.settings', test_settings):
        with patch('bruno_ai_server.routes.auth.firebase_service', mock_firebase):
            client = TestClient(app)
            
            # Test registration data
            registration_data = {
                "email": "test-with-middleware@example.com",
                "name": "Test User With Middleware", 
                "password": "ValidPassword123"
            }
            
            print(f"Attempting registration with data: {registration_data}")
            
            # Attempt registration
            response = client.post("/api/users/register", json=registration_data)
            
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.content}")
            
            if response.status_code != 200:
                print(f"Response headers: {response.headers}")
                try:
                    print(f"Response JSON: {response.json()}")
                except:
                    print("Could not parse response as JSON")
                    
                print("❌ CONFIRMED: Registration fails WITH AuthenticationMiddleware")
                print("🔍 This confirms the middleware is the problem")
            else:
                print("⚠️  UNEXPECTED: Registration succeeded with AuthenticationMiddleware")
                print("   This might indicate the issue was fixed or is intermittent")
    
    # Clean up
    app.dependency_overrides.clear()


if __name__ == "__main__":
    # Run the test directly for debugging
    print("Running registration test without middleware...")
    import asyncio
    import sys
    import os
    
    # Add the project root to the Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # For direct execution, we'd need to set up the test environment manually
    print("This test should be run via pytest:")
    print("pytest test_registration_without_middleware.py -v -s")

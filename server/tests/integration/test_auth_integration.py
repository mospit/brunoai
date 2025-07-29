"""
Integration tests for authentication endpoints.

Tests the complete authentication flow including:
- AC 2: System prevents registration with duplicate email
- AC 4: System returns error for invalid login credentials  
- AC 5: User receives secure JWT token upon successful login

These tests use real database transactions and API endpoints.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bruno_ai_server.models.user import User, Household, HouseholdMember
from bruno_ai_server.auth import verify_token, get_password_hash


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_duplicate_email_integration(test_app: TestClient, db_session: AsyncSession):
    """
    Integration test for AC 2: System prevents registration with duplicate email.
    
    Tests the complete flow from API endpoint to database validation.
    """
    # Create an existing user in the database
    existing_user = User(
        id=uuid.uuid4(),  # Assign UUID
        email="duplicate@example.com",
        name="Existing User",
        firebase_uid="existing_firebase_uid",
        is_active=True,
        is_verified=False,
    )
    
    db_session.add(existing_user)
    await db_session.commit()
    
    # Attempt to register with the same email
    registration_data = {
        "email": "duplicate@example.com",
        "name": "New User",
        "password": "ValidPassword123"
    }
    
    response = test_app.post("/api/users/register", json=registration_data)
    
    # Verify the system prevents duplicate registration
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]
    
    # Verify only one user exists in database
    result = await db_session.execute(select(User).where(User.email == "duplicate@example.com"))
    users = result.scalars().all()
    assert len(users) == 1
    assert users[0].name == "Existing User"  # Original user unchanged


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_invalid_credentials_integration(test_app: TestClient, db_session: AsyncSession, mock_firebase_service_integration):
    """
    Integration test for AC 4: System returns error for invalid login credentials.
    
    Tests complete authentication flow with invalid credentials.
    """
    # Create a valid user in the database
    valid_user = User(
        id=uuid.uuid4(),  # Assign UUID
        email="valid@example.com",
        name="Valid User", 
        firebase_uid="valid_firebase_uid",
        is_active=True,
        is_verified=True,
    )
    
    db_session.add(valid_user) 
    await db_session.commit()
    
    # Set up Firebase mock to simulate valid user creation
    await mock_firebase_service_integration.create_user(
        email="valid@example.com",
        password="CorrectPassword123",
        name="Valid User"
    )
    
    # Test Case 1: Wrong password
    login_data_wrong_password = {
        "email": "valid@example.com",
        "password": "WrongPassword123"
    }
    
    response = test_app.post("/api/users/login", json=login_data_wrong_password)
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
    
    # Test Case 2: Non-existent email  
    login_data_wrong_email = {
        "email": "nonexistent@example.com",
        "password": "AnyPassword123"
    }
    
    response = test_app.post("/api/users/login", json=login_data_wrong_email)
    
    # Firebase authentication will fail for non-existent email, returning 401
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
    
    # Test Case 3: Inactive user
    inactive_user = User(
        id=uuid.uuid4(),  # Assign UUID
        email="inactive@example.com",
        name="Inactive User",
        firebase_uid="inactive_firebase_uid", 
        is_active=False,  # User is inactive
        is_verified=True,
    )
    
    db_session.add(inactive_user)
    await db_session.commit()
    
    # Set up Firebase for inactive user
    await mock_firebase_service_integration.create_user(
        email="inactive@example.com",
        password="ValidPassword123",
        name="Inactive User"
    )
    
    login_data_inactive = {
        "email": "inactive@example.com", 
        "password": "ValidPassword123"
    }
    
    response = test_app.post("/api/users/login", json=login_data_inactive)
    
    assert response.status_code == 400
    assert "Inactive user" in response.json()["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_jwt_token_integration(test_app: TestClient, db_session: AsyncSession, mock_firebase_service_integration):
    """
    Integration test for AC 5: User receives secure JWT token upon successful login.
    
    Tests complete authentication flow and JWT token validation.
    """
    # Create a valid active user in the database
    valid_user = User(
        id=uuid.uuid4(),  # Assign UUID
        email="jwt@example.com",
        name="JWT Test User",
        firebase_uid="jwt_firebase_uid",
        is_active=True,
        is_verified=True,
    )
    
    db_session.add(valid_user)
    await db_session.commit()
    await db_session.refresh(valid_user)
    
    # Set up Firebase mock for authentication
    await mock_firebase_service_integration.create_user(
        email="jwt@example.com",
        password="ValidPassword123",
        name="JWT Test User"
    )
    
    # Perform login
    login_data = {
        "email": "jwt@example.com",
        "password": "ValidPassword123"
    }
    
    response = test_app.post("/api/users/login", json=login_data)
    
    # Verify successful login
    assert response.status_code == 200
    
    response_data = response.json()
    
    # Verify JWT tokens are returned
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert response_data["token_type"] == "bearer"
    
    # Verify access token is valid and contains correct user info
    access_token = response_data["access_token"]
    access_payload = verify_token(access_token)
    
    assert access_payload is not None
    assert access_payload["sub"] == str(valid_user.id)
    assert "exp" in access_payload  # Has expiration
    
    # Verify refresh token is valid and marked as refresh type
    refresh_token = response_data["refresh_token"] 
    refresh_payload = verify_token(refresh_token)
    
    assert refresh_payload is not None
    assert refresh_payload["sub"] == str(valid_user.id)
    assert refresh_payload.get("type") == "refresh"
    assert "exp" in refresh_payload
    
    # Verify token can be used to access protected endpoints
    headers = {"Authorization": f"Bearer {access_token}"}
    
    protected_response = test_app.get("/api/users/me", headers=headers)
    
    assert protected_response.status_code == 200
    user_data = protected_response.json()
    assert user_data["id"] == str(valid_user.id)
    assert user_data["email"] == "jwt@example.com"
    assert user_data["name"] == "JWT Test User"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_registration_login_flow_integration(test_app: TestClient, db_session: AsyncSession, mock_firebase_service_integration):
    """
    Integration test for complete user registration and login flow.
    
    Tests the entire user journey from registration to authentication.
    """
    # Test user registration
    registration_data = {
        "email": "complete@example.com",
        "name": "Complete Test User",
        "password": "ValidPassword123"
    }
    
    register_response = test_app.post("/api/users/register", json=registration_data)
    
    assert register_response.status_code == 200
    
    register_data = register_response.json()
    assert register_data["email"] == "complete@example.com"
    assert register_data["name"] == "Complete Test User"
    assert "id" in register_data
    
    user_id_str = register_data["id"]
    user_id = uuid.UUID(user_id_str)  # Convert string to UUID
    
    # Verify user was created in database
    result = await db_session.execute(select(User).where(User.id == user_id))
    created_user = result.scalar_one_or_none()
    
    assert created_user is not None
    assert created_user.email == "complete@example.com"
    assert created_user.is_active is True
    
    # Verify household was created for the user
    household_result = await db_session.execute(
        select(Household).where(Household.admin_user_id == user_id)
    )
    household = household_result.scalar_one_or_none()
    
    assert household is not None
    assert household.name == "Complete Test User's Household"
    assert household.admin_user_id == user_id
    assert len(household.invite_code) == 8
    
    # Verify user is a member of their household
    member_result = await db_session.execute(
        select(HouseholdMember).where(
            HouseholdMember.user_id == user_id,
            HouseholdMember.household_id == household.id
        )
    )
    membership = member_result.scalar_one_or_none()
    
    assert membership is not None
    assert membership.role == "admin"
    
    # Now test login with the registered user
    # Set up Firebase authentication
    await mock_firebase_service_integration.create_user(
        email="complete@example.com",
        password="ValidPassword123", 
        name="Complete Test User"
    )
    
    login_data = {
        "email": "complete@example.com",
        "password": "ValidPassword123"
    }
    
    login_response = test_app.post("/api/users/login", json=login_data)
    
    assert login_response.status_code == 200
    
    login_response_data = login_response.json()
    assert "access_token" in login_response_data
    assert "refresh_token" in login_response_data
    
    # Verify the token works for accessing user data
    access_token = login_response_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    me_response = test_app.get("/api/users/me", headers=headers)
    assert me_response.status_code == 200
    
    me_data = me_response.json()
    assert me_data["id"] == user_id_str  # Compare string to string
    assert me_data["email"] == "complete@example.com"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_password_validation_integration(test_app: TestClient):
    """
    Integration test for password strength validation.
    
    Tests that weak passwords are rejected during registration.
    """
    # Test Case 1: Password too short
    registration_data_short = {
        "email": "short@example.com",
        "name": "Short Password User",
        "password": "weak"  # Less than 8 characters
    }
    
    response = test_app.post("/api/users/register", json=registration_data_short)
    
    assert response.status_code == 422  # Validation error
    
    # Test Case 2: Empty password
    registration_data_empty = {
        "email": "empty@example.com", 
        "name": "Empty Password User",
        "password": ""
    }
    
    response = test_app.post("/api/users/register", json=registration_data_empty)
    
    assert response.status_code == 422  # Validation error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_token_refresh_integration(test_app: TestClient, db_session: AsyncSession, mock_firebase_service_integration):
    """
    Integration test for JWT token refresh functionality.
    
    Tests that refresh tokens can be used to get new access tokens.
    """
    # Create and authenticate a user
    user = User(
        id=uuid.uuid4(),  # Assign UUID
        email="refresh@example.com",
        name="Refresh Test User",
        firebase_uid="refresh_firebase_uid",
        is_active=True,
        is_verified=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Set up Firebase
    await mock_firebase_service_integration.create_user(
        email="refresh@example.com",
        password="ValidPassword123", 
        name="Refresh Test User"
    )
    
    # Login to get tokens
    login_data = {
        "email": "refresh@example.com",
        "password": "ValidPassword123"
    }
    
    login_response = test_app.post("/api/users/login", json=login_data)
    assert login_response.status_code == 200
    
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]
    
    # Use refresh token to get new access token
    refresh_data = {"refresh_token": refresh_token}
    
    refresh_response = test_app.post("/api/users/refresh", json=refresh_data)
    
    assert refresh_response.status_code == 200
    
    refresh_response_data = refresh_response.json()
    assert "access_token" in refresh_response_data
    assert refresh_response_data["token_type"] == "bearer"
    
    # Verify new access token works
    new_access_token = refresh_response_data["access_token"]
    headers = {"Authorization": f"Bearer {new_access_token}"}
    
    me_response = test_app.get("/api/users/me", headers=headers)
    assert me_response.status_code == 200
    
    me_data = me_response.json()
    assert me_data["id"] == str(user.id)

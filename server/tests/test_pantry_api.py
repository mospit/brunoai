#!/usr/bin/env python3
"""
Comprehensive test suite for pantry management API endpoints
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from bruno_ai_server.main import app
from bruno_ai_server.database import get_async_session
from bruno_ai_server.models.base import Base
from bruno_ai_server.models.user import User, Household, HouseholdMember
from bruno_ai_server.models.pantry import PantryItem, PantryCategory


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_pantry.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)


class TestPantryAPI:
    """Test suite for pantry management API endpoints."""
    
    @pytest.fixture(scope="function")
    def db_session(self):
        """Create a test database session."""
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def client(self, db_session):
        """Create a test client with database dependency override."""
        def override_get_db():
            try:
                yield db_session
            finally:
                db_session.close()
        
        app.dependency_overrides[get_async_session] = override_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def test_user_and_household(self, db_session):
        """Create test user and household data."""
        # Create household
        household = Household(
            id=str(uuid4()),
            name="Test Household",
            invite_code="TEST123"
        )
        db_session.add(household)
        
        # Create user
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            name="Test User",
            firebase_uid="test_firebase_id",
            household_id=household.id
        )
        db_session.add(user)
        
        # Set household admin
        household.admin_user_id = user.id
        
        # Create household membership
        membership = HouseholdMember(
            user_id=user.id,
            household_id=household.id,
            role="admin"
        )
        db_session.add(membership)
        
        # Create pantry category
        category = PantryCategory(
            id=str(uuid4()),
            name="Dairy",
            description="Dairy products",
            icon="milk",
            color="#FFFFFF"
        )
        db_session.add(category)
        
        db_session.commit()
        
        return {
            "user": user,
            "household": household,
            "category": category
        }
    
    @pytest.fixture
    def auth_headers(self, test_user_and_household):
        """Mock authentication headers."""
        # In a real test, you'd generate a proper JWT token
        # For now, we'll assume the auth middleware is bypassed in tests
        return {"Authorization": "Bearer test_token"}
    
    def test_create_pantry_item(self, client, test_user_and_household, auth_headers):
        """Test creating a new pantry item."""
        data = test_user_and_household
        
        item_data = {
            "name": "Milk",
            "quantity": 1.0,
            "unit": "gallon",
            "location": "Refrigerator",
            "notes": "Organic whole milk",
            "expiration_date": (date.today() + timedelta(days=7)).isoformat(),
            "category_id": data["category"].id
        }
        
        response = client.post(
            "/api/pantry/items/",
            json=item_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Milk"
        assert result["quantity"] == 1.0
        assert result["unit"] == "gallon"
        assert result["household_id"] == data["household"].id
    
    def test_get_pantry_items(self, client, test_user_and_household, auth_headers):
        """Test retrieving pantry items."""
        data = test_user_and_household
        
        # Create test items first
        items_data = [
            {
                "name": "Milk",
                "quantity": 1.0,
                "unit": "gallon",
                "expiration_date": (date.today() + timedelta(days=7)).isoformat(),
                "category_id": data["category"].id
            },
            {
                "name": "Bread",
                "quantity": 1.0,
                "unit": "loaf",
                "expiration_date": (date.today() + timedelta(days=3)).isoformat(),
                "category_id": data["category"].id
            }
        ]
        
        for item_data in items_data:
            client.post("/api/pantry/items/", json=item_data, headers=auth_headers)
        
        # Test getting all items
        response = client.get("/api/pantry/items/", headers=auth_headers)
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
    
    def test_get_pantry_items_with_filters(self, client, test_user_and_household, auth_headers):
        """Test retrieving pantry items with filters."""
        data = test_user_and_household
        
        # Create items with different expiration dates
        today = date.today()
        items_data = [
            {
                "name": "Expired Milk",
                "quantity": 1.0,
                "expiration_date": (today - timedelta(days=1)).isoformat(),  # Expired
                "category_id": data["category"].id
            },
            {
                "name": "Fresh Bread",
                "quantity": 1.0,
                "expiration_date": (today + timedelta(days=10)).isoformat(),  # Fresh
                "category_id": data["category"].id
            },
            {
                "name": "Expiring Soon Cheese",
                "quantity": 1.0,
                "expiration_date": (today + timedelta(days=2)).isoformat(),  # Expiring soon
                "category_id": data["category"].id
            }
        ]
        
        for item_data in items_data:
            client.post("/api/pantry/items/", json=item_data, headers=auth_headers)
        
        # Test expired filter
        response = client.get(
            "/api/pantry/items/?expiration_status=expired", 
            headers=auth_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["name"] == "Expired Milk"
        
        # Test expiring soon filter
        response = client.get(
            "/api/pantry/items/?expiration_status=expiring_soon", 
            headers=auth_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["name"] == "Expiring Soon Cheese"
        
        # Test search
        response = client.get(
            "/api/pantry/items/?search=bread", 
            headers=auth_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["name"] == "Fresh Bread"
    
    def test_update_pantry_item(self, client, test_user_and_household, auth_headers):
        """Test updating a pantry item."""
        data = test_user_and_household
        
        # Create item first
        item_data = {
            "name": "Milk",
            "quantity": 1.0,
            "unit": "gallon",
            "category_id": data["category"].id
        }
        
        create_response = client.post(
            "/api/pantry/items/", 
            json=item_data, 
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Update item
        update_data = {
            "name": "Organic Milk",
            "quantity": 2.0,
            "notes": "Updated notes"
        }
        
        response = client.put(
            f"/api/pantry/items/{item_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Organic Milk"
        assert result["quantity"] == 2.0
        assert result["notes"] == "Updated notes"
    
    def test_delete_pantry_item(self, client, test_user_and_household, auth_headers):
        """Test deleting a pantry item."""
        data = test_user_and_household
        
        # Create item first
        item_data = {
            "name": "Milk",
            "quantity": 1.0,
            "category_id": data["category"].id
        }
        
        create_response = client.post(
            "/api/pantry/items/", 
            json=item_data, 
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Delete item
        response = client.delete(
            f"/api/pantry/items/{item_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify item is deleted
        get_response = client.get("/api/pantry/items/", headers=auth_headers)
        items = get_response.json()
        assert len(items) == 0
    
    def test_increment_quantity(self, client, test_user_and_household, auth_headers):
        """Test incrementing pantry item quantity."""
        data = test_user_and_household
        
        # Create item first
        item_data = {
            "name": "Milk",
            "quantity": 1.0,
            "category_id": data["category"].id
        }
        
        create_response = client.post(
            "/api/pantry/items/", 
            json=item_data, 
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Increment quantity
        response = client.patch(
            f"/api/pantry/items/{item_id}/increment?amount=0.5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["quantity"] == 1.5
    
    def test_decrement_quantity(self, client, test_user_and_household, auth_headers):
        """Test decrementing pantry item quantity."""
        data = test_user_and_household
        
        # Create item first
        item_data = {
            "name": "Milk",
            "quantity": 2.0,
            "category_id": data["category"].id
        }
        
        create_response = client.post(
            "/api/pantry/items/", 
            json=item_data, 
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Decrement quantity
        response = client.patch(
            f"/api/pantry/items/{item_id}/decrement?amount=0.5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["quantity"] == 1.5
    
    def test_set_quantity(self, client, test_user_and_household, auth_headers):
        """Test setting exact pantry item quantity."""
        data = test_user_and_household
        
        # Create item first
        item_data = {
            "name": "Milk",
            "quantity": 1.0,
            "category_id": data["category"].id
        }
        
        create_response = client.post(
            "/api/pantry/items/", 
            json=item_data, 
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Set quantity
        response = client.patch(
            f"/api/pantry/items/{item_id}/set-quantity?quantity=3.0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["quantity"] == 3.0
    
    def test_unauthorized_access(self, client):
        """Test that API endpoints require authentication."""
        response = client.get("/api/pantry/items/")
        assert response.status_code == 401
        
        response = client.post("/api/pantry/items/", json={"name": "Test"})
        assert response.status_code == 401
    
    def test_household_isolation(self, client, db_session, auth_headers):
        """Test that users can only access their own household's pantry items."""
        # This would require setting up multiple households and users
        # and ensuring proper isolation - implementation depends on auth system
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

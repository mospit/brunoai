"""
Integration tests for pantry API endpoints.
"""

import pytest
from datetime import date, datetime
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from bruno_ai_server.models.user import User, Household, HouseholdMember
from bruno_ai_server.models.pantry import PantryItem, PantryCategory
from bruno_ai_server.auth import create_access_token


class TestPantryAPI:
    """Test pantry CRUD endpoints."""
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        return User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_verified=True,
        )
    
    @pytest.fixture
    def sample_household(self):
        """Sample household for testing."""
        return Household(
            id=1,
            name="Test Household",
            invite_code="123456",
            owner_id=1,
        )
    
    @pytest.fixture
    def sample_category(self):
        """Sample pantry category for testing."""
        return PantryCategory(
            id=1,
            name="Vegetables",
            description="Fresh vegetables",
            icon="vegetable",
            color="#00FF00",
        )
    
    @pytest.fixture
    def sample_pantry_item(self, sample_user, sample_household, sample_category):
        """Sample pantry item for testing."""
        return PantryItem(
            id=1,
            name="Carrots",
            quantity=2.0,
            unit="pounds",
            location="Fridge",
            notes="Fresh organic carrots",
            barcode="123456789",
            expiration_date=date(2024, 12, 31),
            purchase_date=date(2024, 12, 1),
            household_id=sample_household.id,
            category_id=sample_category.id,
            added_by_user_id=sample_user.id,
            item_metadata={"brand": "Organic Farm"},
            category=sample_category,
            added_by_user=sample_user,
        )
    
    @pytest.fixture
    def auth_token(self, sample_user):
        """Authentication token for testing."""
        return create_access_token(data={"sub": str(sample_user.id)})
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Authentication headers for testing."""
        return {"Authorization": f"Bearer {auth_token}"}


class TestGetPantryItems(TestPantryAPI):
    """Test GET /pantry/items endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_pantry_items_success(
        self, sample_user, sample_household, sample_pantry_item, auth_headers
    ):
        """Test successful retrieval of pantry items."""
        from bruno_ai_server.main import app
        
        with patch("bruno_ai_server.routes.pantry.get_current_active_user") as mock_auth, \
             patch("bruno_ai_server.routes.pantry.get_user_household_id") as mock_household, \
             patch("bruno_ai_server.routes.pantry.get_async_session") as mock_session:
            
            # Mock authentication
            mock_auth.return_value = sample_user
            mock_household.return_value = sample_household.id
            
            # Mock database query
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = [sample_pantry_item]
            mock_db.execute.return_value = mock_result
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/pantry/items", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Carrots"
            assert data[0]["quantity"] == 2.0
            assert data[0]["unit"] == "pounds"
    
    @pytest.mark.asyncio
    async def test_get_pantry_items_with_category_filter(
        self, sample_user, sample_household, sample_pantry_item, auth_headers
    ):
        """Test retrieval with category filter."""
        from bruno_ai_server.main import app
        
        with patch("bruno_ai_server.routes.pantry.get_current_active_user") as mock_auth, \
             patch("bruno_ai_server.routes.pantry.get_user_household_id") as mock_household, \
             patch("bruno_ai_server.routes.pantry.get_async_session") as mock_session:
            
            mock_auth.return_value = sample_user
            mock_household.return_value = sample_household.id
            
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = [sample_pantry_item]
            mock_db.execute.return_value = mock_result
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/pantry/items?category=Vegetables", 
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
    
    @pytest.mark.asyncio
    async def test_get_pantry_items_with_search_filter(
        self, sample_user, sample_household, sample_pantry_item, auth_headers
    ):
        """Test retrieval with search filter."""
        from bruno_ai_server.main import app
        
        with patch("bruno_ai_server.routes.pantry.get_current_active_user") as mock_auth, \
             patch("bruno_ai_server.routes.pantry.get_user_household_id") as mock_household, \
             patch("bruno_ai_server.routes.pantry.get_async_session") as mock_session:
            
            mock_auth.return_value = sample_user
            mock_household.return_value = sample_household.id
            
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = [sample_pantry_item]
            mock_db.execute.return_value = mock_result
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/pantry/items?search=Carrots", 
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
    
    @pytest.mark.asyncio
    async def test_get_pantry_items_no_household(self, sample_user, auth_headers):
        """Test retrieval when user has no household."""
        from bruno_ai_server.main import app
        
        with patch("bruno_ai_server.routes.pantry.get_current_active_user") as mock_auth, \
             patch("bruno_ai_server.routes.pantry.get_user_household_id") as mock_household, \
             patch("bruno_ai_server.routes.pantry.get_async_session") as mock_session:
            
            mock_auth.return_value = sample_user
            mock_household.return_value = None  # No household
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/pantry/items", headers=auth_headers)
            
            assert response.status_code == 400
            data = response.json()
            assert "not a member of any household" in data["detail"]


class TestCreatePantryItem(TestPantryAPI):
    """Test POST /pantry/items endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_pantry_item_success(
        self, sample_user, sample_household, auth_headers
    ):
        """Test successful creation of pantry item."""
        from bruno_ai_server.main import app
        
        item_data = {
            "name": "Apples",
            "quantity": 5.0,
            "unit": "pieces",
            "location": "Counter",
            "notes": "Red delicious apples",
            "barcode": "987654321",
            "expiration_date": "2024-12-15",
            "category_id": 1,
        }
        
        with patch("bruno_ai_server.routes.pantry.get_current_active_user") as mock_auth, \
             patch("bruno_ai_server.routes.pantry.get_user_household_id") as mock_household, \
             patch("bruno_ai_server.routes.pantry.get_async_session") as mock_session:
            
            mock_auth.return_value = sample_user
            mock_household.return_value = sample_household.id
            
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            mock_db.add = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            # Mock the created item to return in refresh
            created_item = PantryItem(
                id=2,
                name=item_data["name"],
                quantity=item_data["quantity"],
                unit=item_data["unit"],
                location=item_data["location"],
                notes=item_data["notes"],
                barcode=item_data["barcode"],
                expiration_date=date(2024, 12, 15),
                household_id=sample_household.id,
                added_by_user_id=sample_user.id,
                category_id=item_data["category_id"],
            )
            
            def mock_refresh(item):
                for key, value in created_item.__dict__.items():
                    if not key.startswith('_'):
                        setattr(item, key, value)
            
            mock_db.refresh.side_effect = mock_refresh
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/pantry/items", 
                    json=item_data, 
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Apples"
            assert data["quantity"] == 5.0
            assert data["household_id"] == sample_household.id
            assert data["added_by_user_id"] == sample_user.id
    
    @pytest.mark.asyncio
    async def test_create_pantry_item_no_household(self, sample_user, auth_headers):
        """Test creation when user has no household."""
        from bruno_ai_server.main import app
        
        item_data = {
            "name": "Apples",
            "quantity": 5.0,
        }
        
        with patch("bruno_ai_server.routes.pantry.get_current_active_user") as mock_auth, \
             patch("bruno_ai_server.routes.pantry.get_user_household_id") as mock_household:
            
            mock_auth.return_value = sample_user
            mock_household.return_value = None
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/pantry/items", 
                    json=item_data, 
                    headers=auth_headers
                )
            
            assert response.status_code == 400
            data = response.json()
            assert "not a member of any household" in data["detail"]


class TestUpdatePantryItem(TestPantryAPI):
    """Test PUT /pantry/items/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_pantry_item_success(
        self, sample_user, sample_household, sample_pantry_item, auth_headers
    ):
        """Test successful update of pantry item."""
        from bruno_ai_server.main import app
        
        update_data = {
            "name": "Updated Carrots",
            "quantity": 3.0,
            "notes": "Updated notes",
        }
        
        with patch("bruno_ai_server.routes.pantry.get_current_active_user") as mock_auth, \
             patch("bruno_ai_server.routes.pantry.get_user_household_id") as mock_household, \
             patch("bruno_ai_server.routes.pantry.get_async_session") as mock_session:
            
            mock_auth.return_value = sample_user
            mock_household.return_value = sample_household.id
            
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            
            # Mock finding the existing item
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = sample_pantry_item
            mock_db.execute.return_value = mock_result
            
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(
                    f"/pantry/items/{sample_pantry_item.id}", 
                    json=update_data, 
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            # Verify the item was updated
            assert sample_pantry_item.name == "Updated Carrots"
            assert sample_pantry_item.quantity == 3.0
            assert sample_pantry_item.notes == "Updated notes"
    
    @pytest.mark.asyncio
    async def test_update_pantry_item_not_found(
        self, sample_user, sample_household, auth_headers
    ):
        """Test update of non-existent pantry item."""
        from bruno_ai_server.main import app
        
        update_data = {"name": "Updated Item"}
        
        with patch("bruno_ai_server.routes.pantry.get_current_active_user") as mock_auth, \
             patch("bruno_ai_server.routes.pantry.get_user_household_id") as mock_household, \
             patch("bruno_ai_server.routes.pantry.get_async_session") as mock_session:
            
            mock_auth.return_value = sample_user
            mock_household.return_value = sample_household.id
            
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            
            # Mock item not found
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(
                    "/pantry/items/999", 
                    json=update_data, 
                    headers=auth_headers
                )
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]


class TestDeletePantryItem(TestPantryAPI):
    """Test DELETE /pantry/items/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_pantry_item_success(
        self, sample_user, sample_household, sample_pantry_item, auth_headers
    ):
        """Test successful deletion of pantry item."""
        from bruno_ai_server.main import app
        
        with patch("bruno_ai_server.routes.pantry.get_current_active_user") as mock_auth, \
             patch("bruno_ai_server.routes.pantry.get_user_household_id") as mock_household, \
             patch("bruno_ai_server.routes.pantry.get_async_session") as mock_session:
            
            mock_auth.return_value = sample_user
            mock_household.return_value = sample_household.id
            
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            
            # Mock finding the existing item
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = sample_pantry_item
            mock_db.execute.return_value = mock_result
            
            mock_db.delete = AsyncMock()
            mock_db.commit = AsyncMock()
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete(
                    f"/pantry/items/{sample_pantry_item.id}", 
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            data = response.json()
            assert "deleted successfully" in data["message"]
            
            # Verify delete was called
            mock_db.delete.assert_called_once_with(sample_pantry_item)
    
    @pytest.mark.asyncio
    async def test_delete_pantry_item_not_found(
        self, sample_user, sample_household, auth_headers
    ):
        """Test deletion of non-existent pantry item."""
        from bruno_ai_server.main import app
        
        with patch("bruno_ai_server.routes.pantry.get_current_active_user") as mock_auth, \
             patch("bruno_ai_server.routes.pantry.get_user_household_id") as mock_household, \
             patch("bruno_ai_server.routes.pantry.get_async_session") as mock_session:
            
            mock_auth.return_value = sample_user
            mock_household.return_value = sample_household.id
            
            mock_db = AsyncMock()
            mock_session.return_value = mock_db
            
            # Mock item not found
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete(
                    "/pantry/items/999", 
                    headers=auth_headers
                )
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]


class TestAuthenticationAndOwnership(TestPantryAPI):
    """Test authentication and ownership enforcement."""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self):
        """Test access without authentication token."""
        from bruno_ai_server.main import app
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/pantry/items")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Test access with invalid authentication token."""
        from bruno_ai_server.main import app
        
        headers = {"Authorization": "Bearer invalid_token"}
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/pantry/items", headers=headers)
        
        assert response.status_code == 401

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from bruno_ai_server.schemas import PantryItemCreate, PantryItemUpdate
from bruno_ai_server.models.pantry import PantryItem

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_pantry_item(test_app: TestClient, db_session, integration_auth_headers):
    """Test creating a new pantry item."""
    item_data = {
        "name": "Test Item",
        "quantity": 5,
        "unit": "pieces",
        "barcode": "123456789012",
    }

    response = test_app.post("/pantry/items/", json=item_data, headers=integration_auth_headers)
    assert response.status_code == 201, response.text

    data = response.json()
    assert data["name"] == "Test Item"
    assert data["quantity"] == 5

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_pantry_items(test_app: TestClient, db_session, integration_auth_headers):
    """Test retrieving pantry items."""
    response = test_app.get("/pantry/items/", headers=integration_auth_headers)
    assert response.status_code == 200, response.text

    data = response.json()
    assert isinstance(data, list)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_pantry_item(test_app: TestClient, db_session, integration_auth_headers, test_pantry_item: PantryItem):
    """Test updating an existing pantry item."""
    update_data = {
        "name": "Updated Test Item",
        "quantity": 10,
    }

    response = test_app.put(f"/pantry/items/{test_pantry_item.id}", json=update_data, headers=integration_auth_headers)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["name"] == "Updated Test Item"
    assert data["quantity"] == 10

@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_pantry_item(test_app: TestClient, db_session, integration_auth_headers, test_pantry_item: PantryItem):
    """Test deleting a pantry item."""
    response = test_app.delete(f"/pantry/items/{test_pantry_item.id}", headers=integration_auth_headers)
    assert response.status_code == 200, response.text
    
    data = response.json()
    assert data["message"] == "Pantry item deleted successfully."



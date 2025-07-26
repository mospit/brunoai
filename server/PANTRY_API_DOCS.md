# Pantry Management API Documentation

## Overview
The Pantry Management API provides comprehensive CRUD operations for managing household pantry items, including expiration tracking, categorization, and quantity management.

## Base URL
```
/api/pantry/items
```

## Authentication
All endpoints require Firebase JWT authentication via Bearer token:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### 1. List Pantry Items
**GET** `/api/pantry/items/`

Retrieve all pantry items for the authenticated user's household with optional filtering and sorting.

#### Query Parameters
- `category_id` (optional): Filter by category UUID
- `category` (optional): Filter by category name  
- `search` (optional): Search by item name
- `expiration_status` (optional): Filter by expiration status
  - `expired`: Items past expiration date
  - `expiring_soon`: Items expiring within 3 days
  - `fresh`: Items expiring in more than 3 days
- `sort_by` (optional): Sort field (`name`, `expiration_date`, `created_at`)
- `sort_order` (optional): Sort order (`asc`, `desc`)

#### Example Request
```bash
curl -X GET "/api/pantry/items/?expiration_status=expiring_soon&sort_by=expiration_date" \
  -H "Authorization: Bearer <token>"
```

#### Example Response
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Milk",
    "quantity": 1.0,
    "unit": "gallon",
    "expiration_date": "2025-01-30",
    "purchase_date": "2025-01-23",
    "location": "Refrigerator",
    "notes": "Organic whole milk",
    "household_id": "550e8400-e29b-41d4-a716-446655440001",
    "category_id": "550e8400-e29b-41d4-a716-446655440002",
    "added_by_user_id": "550e8400-e29b-41d4-a716-446655440003",
    "item_metadata": {},
    "created_at": "2025-01-25T10:00:00Z",
    "category": {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Dairy",
      "description": "Dairy products",
      "icon": "milk",
      "color": "#FFFFFF"
    },
    "added_by_user": {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
]
```

### 2. Create Pantry Item
**POST** `/api/pantry/items/`

Create a new pantry item in the user's household.

#### Request Body
```json
{
  "name": "Milk",
  "quantity": 1.0,
  "unit": "gallon",
  "location": "Refrigerator",
  "notes": "Organic whole milk",
  "expiration_date": "2025-01-30",
  "category_id": "550e8400-e29b-41d4-a716-446655440002",
  "barcode": "123456789012"
}
```

#### Required Fields
- `name`: Item name (string)

#### Optional Fields
- `quantity`: Quantity amount (float, default: 1.0)
- `unit`: Unit of measurement (string, default: "piece")
- `location`: Storage location (string)
- `notes`: Additional notes (string)
- `expiration_date`: Expiration date (date, ISO format)
- `category_id`: Category UUID (string)
- `barcode`: Product barcode (string)

#### Response
Returns the created item with generated UUID and metadata.

### 3. Update Pantry Item
**PUT** `/api/pantry/items/{item_id}`

Update an existing pantry item.

#### Request Body
```json
{
  "name": "Organic Milk",
  "quantity": 2.0,
  "notes": "Updated to organic brand"
}
```

All fields are optional - only provided fields will be updated.

### 4. Delete Pantry Item
**DELETE** `/api/pantry/items/{item_id}`

Delete a pantry item from the household.

#### Response
```json
{
  "message": "Pantry item deleted successfully."
}
```

### 5. Increment Quantity
**PATCH** `/api/pantry/items/{item_id}/increment`

Increase the quantity of a pantry item.

#### Query Parameters
- `amount`: Amount to increment by (float, default: 1.0)

#### Example Request
```bash
curl -X PATCH "/api/pantry/items/550e8400-e29b-41d4-a716-446655440000/increment?amount=0.5" \
  -H "Authorization: Bearer <token>"
```

### 6. Decrement Quantity
**PATCH** `/api/pantry/items/{item_id}/decrement`

Decrease the quantity of a pantry item (cannot go below 0).

#### Query Parameters
- `amount`: Amount to decrement by (float, default: 1.0)

### 7. Set Exact Quantity
**PATCH** `/api/pantry/items/{item_id}/set-quantity`

Set the exact quantity of a pantry item.

#### Query Parameters
- `quantity`: New quantity value (float, required)

## Error Responses

### 400 Bad Request
```json
{
  "detail": "User is not a member of any household"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 404 Not Found
```json
{
  "detail": "Pantry item not found."
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "quantity"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": {"limit_value": 0}
    }
  ]
}
```

## Data Models

### PantryItem
- `id`: UUID (auto-generated)
- `name`: string (required)
- `quantity`: float (default: 1.0)
- `unit`: string (default: "piece")
- `expiration_date`: date (optional)
- `purchase_date`: date (auto-set to today)
- `location`: string (optional)
- `notes`: string (optional)
- `barcode`: string (optional)
- `household_id`: UUID (auto-set)
- `category_id`: UUID (optional)
- `added_by_user_id`: UUID (auto-set)
- `item_metadata`: JSON object (extensible metadata)
- `created_at`: datetime (auto-generated)
- `updated_at`: datetime (auto-updated)

### PantryCategory
- `id`: UUID (auto-generated)
- `name`: string (required)
- `description`: string (optional)
- `icon`: string (optional)
- `color`: string (optional, hex color)

## Business Logic

### Expiration Status Calculation
- **Expired**: `expiration_date < today`
- **Expiring Soon**: `today <= expiration_date <= today + 3 days`
- **Fresh**: `expiration_date > today + 3 days`

### Auto-Expiration Suggestions
When creating items without expiration dates, the system can suggest dates based on:
- Item name pattern matching
- Category defaults
- Barcode lookups (if available)

### Household Isolation
- Users can only access pantry items from their household
- All operations are automatically scoped to the user's household
- Household membership validation occurs on every request

## Integration Points

### Voice Commands
The pantry API integrates with voice processing endpoints for:
- Adding items via voice ("Add 2 gallons of milk to pantry")
- Updating quantities ("We used 1 cup of flour")
- Checking inventory ("What do we have in the dairy category?")

### Expiration Alerts
Background services monitor expiration dates and trigger:
- Push notifications for expiring items
- Email summaries of expired items
- Shopping list suggestions for replacements

### Shopping Lists
Pantry items can be automatically added to shopping lists when:
- Quantity reaches zero
- Items expire
- Manual user requests

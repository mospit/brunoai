# Pantry CRUD API Implementation

## Overview
This document describes the completed implementation of the Pantry CRUD API for Bruno AI, a household food management application. The API provides comprehensive pantry item management with authentication, ownership enforcement, filtering capabilities, and full CRUD operations.

## Features Implemented

### 1. REST API Endpoints
The API provides the following endpoints under `/pantry/items`:

- **GET /pantry/items** - Retrieve all pantry items for the user's household
- **POST /pantry/items** - Create a new pantry item
- **PUT /pantry/items/{id}** - Update an existing pantry item
- **DELETE /pantry/items/{id}** - Delete a pantry item

### 2. Authentication & Authorization
- **JWT Token Authentication**: All endpoints require valid authentication tokens
- **Household Ownership Enforcement**: Users can only access/modify items in their own household
- **Automatic User Household Resolution**: The system automatically determines the user's primary household

### 3. Filtering & Query Parameters
- **Category Filter**: `?category=Vegetables` - Filter items by category name
- **Search Filter**: `?search=carrots` - Search items by name (case-insensitive partial match)
- **Combined Filters**: Both filters can be used together

### 4. Data Validation
- **Pydantic Schemas**: All input/output uses validated Pydantic models
- **Type Safety**: Proper type validation for dates, numbers, and strings
- **Optional Fields**: Support for optional fields like expiration dates, categories, etc.

## Technical Implementation

### File Structure
```
bruno_ai_server/
├── routes/
│   ├── __init__.py          # Updated to include pantry router
│   ├── auth.py              # Existing authentication routes
│   └── pantry.py            # NEW: Pantry CRUD operations
├── models/
│   ├── pantry.py            # Existing pantry models
│   └── user.py              # Existing user/household models
├── schemas.py               # Updated with pantry schemas
└── auth.py                  # Existing authentication utilities

tests/
└── test_pantry.py           # NEW: Comprehensive integration tests

main.py                      # Updated to include pantry router
```

### Key Components

#### 1. Pantry Router (`bruno_ai_server/routes/pantry.py`)
```python
router = APIRouter(prefix="/pantry/items", tags=["pantry"])

# Helper function to resolve user's household
async def get_user_household_id(user: User, db: AsyncSession) -> Optional[int]

# CRUD Operations
- get_pantry_items()    # GET /
- create_pantry_item()  # POST /
- update_pantry_item()  # PUT /{id}
- delete_pantry_item()  # DELETE /{id}
```

#### 2. Pydantic Schemas (`bruno_ai_server/schemas.py`)
```python
# Input schemas
class PantryItemCreate(PantryItemBase)
class PantryItemUpdate(BaseModel)

# Output schemas  
class PantryItemResponse(PantryItemBase)
class PantryCategoryResponse(BaseModel)
```

#### 3. Database Models (Existing)
The API leverages existing models:
- `PantryItem`: Main pantry item model with expiration tracking
- `PantryCategory`: Categories for organizing items
- `User`: User authentication and profile
- `Household`: Shared household spaces
- `HouseholdMember`: User-household relationships

### Authentication Flow
1. User provides JWT token in Authorization header
2. `get_current_active_user()` validates token and retrieves user
3. `get_user_household_id()` determines user's primary household
4. All operations are scoped to that household ID

### Household Resolution Logic
```python
async def get_user_household_id(user: User, db: AsyncSession):
    # 1. First try household where user is admin (most likely primary)
    # 2. If none, get any household where user is a member
    # 3. Return None if user has no household memberships
```

## API Usage Examples

### 1. Get All Pantry Items
```http
GET /pantry/items
Authorization: Bearer <jwt_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Carrots",
    "quantity": 2.0,
    "unit": "pounds",
    "location": "Fridge",
    "notes": "Fresh organic carrots",
    "expiration_date": "2024-12-31",
    "purchase_date": "2024-12-01",
    "household_id": 1,
    "category_id": 1,
    "added_by_user_id": 1,
    "item_metadata": {"brand": "Organic Farm"},
    "created_at": "2024-12-01T10:00:00Z",
    "category": {
      "id": 1,
      "name": "Vegetables",
      "description": "Fresh vegetables"
    },
    "added_by_user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe"
    }
  }
]
```

### 2. Create New Pantry Item
```http
POST /pantry/items
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Apples",
  "quantity": 5.0,
  "unit": "pieces",
  "location": "Counter",
  "notes": "Red delicious apples",
  "barcode": "987654321",
  "expiration_date": "2024-12-15",
  "category_id": 1
}
```

### 3. Update Pantry Item
```http
PUT /pantry/items/1
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "quantity": 1.5,
  "notes": "Used some for cooking"
}
```

### 4. Filter by Category
```http
GET /pantry/items?category=Vegetables
Authorization: Bearer <jwt_token>
```

### 5. Search Items
```http
GET /pantry/items?search=apple
Authorization: Bearer <jwt_token>
```

## Testing

### Integration Tests (`tests/test_pantry.py`)
Comprehensive test suite covering:

#### Test Classes:
- `TestGetPantryItems`: GET endpoint tests
- `TestCreatePantryItem`: POST endpoint tests  
- `TestUpdatePantryItem`: PUT endpoint tests
- `TestDeletePantryItem`: DELETE endpoint tests
- `TestAuthenticationAndOwnership`: Security tests

#### Test Coverage:
- ✅ Successful CRUD operations
- ✅ Category and search filtering
- ✅ Authentication enforcement
- ✅ Household ownership validation
- ✅ Error handling (404, 400, 401)
- ✅ Input validation
- ✅ Database interaction mocking

#### Running Tests:
```bash
pytest tests/test_pantry.py -v
```

## Error Handling

### HTTP Status Codes:
- **200**: Successful operation
- **400**: Bad request (user has no household, validation errors)
- **401**: Unauthorized (invalid/missing token)
- **404**: Not found (item doesn't exist or doesn't belong to user's household)

### Example Error Responses:
```json
// No household membership
{
  "detail": "User is not a member of any household"
}

// Item not found
{
  "detail": "Pantry item not found."
}

// Unauthorized access
{
  "detail": "Could not validate credentials"
}
```

## Security Features

### 1. Authentication Required
All endpoints require valid JWT authentication tokens.

### 2. Household Isolation
Users can only access pantry items from their own household(s), ensuring complete data isolation between different households.

### 3. Automatic Ownership Assignment
When creating items, the system automatically:
- Sets `household_id` from user's household membership
- Sets `added_by_user_id` from authenticated user

### 4. Input Validation
All inputs are validated using Pydantic schemas with:
- Type checking
- Required field validation
- Optional field handling
- Date format validation

## Database Schema Alignment

The API works with existing database models:

```sql
-- Core tables used
pantry_items (
  id, name, quantity, unit, location, notes,
  barcode, expiration_date, purchase_date,
  household_id, category_id, added_by_user_id,
  item_metadata, created_at, updated_at
)

pantry_categories (
  id, name, description, icon, color
)

users (
  id, email, full_name, is_active, is_verified
)

households (
  id, name, invite_code, owner_id
)

household_members (
  user_id, household_id, role
)
```

## Performance Considerations

### 1. Database Queries
- Uses SQLAlchemy async sessions for non-blocking operations
- Implements proper relationship loading with `selectinload()`
- Scoped queries to user's household for efficiency

### 2. Authentication
- JWT tokens cached in memory for request duration
- Household resolution cached per request

### 3. Filtering
- Database-level filtering (not in-memory) for efficiency
- Uses proper SQL WHERE clauses and JOINs

## Future Enhancements

The implementation provides a solid foundation for future features:

1. **Batch Operations**: Bulk create/update/delete operations
2. **Advanced Search**: Full-text search, barcode lookup
3. **Expiration Notifications**: Push notifications for expiring items
4. **Inventory Tracking**: Quantity management and low-stock alerts
5. **Category Management**: CRUD operations for pantry categories
6. **Item Sharing**: Share items between household members
7. **Shopping List Integration**: Convert low-stock items to shopping lists

## Conclusion

The Pantry CRUD API implementation successfully provides:
- ✅ Complete CRUD operations for pantry items
- ✅ JWT authentication and household-based authorization
- ✅ Pydantic input/output validation
- ✅ Filtering and search capabilities  
- ✅ Comprehensive integration tests
- ✅ Proper error handling and HTTP status codes
- ✅ Secure, production-ready implementation

The API integrates seamlessly with the existing Bruno AI architecture and provides a robust foundation for the household food management features described in the PRD.

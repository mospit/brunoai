# Pantry Management Backend Setup Guide

## Current Implementation Status

✅ **Completed:**
- Database models for PantryItem and PantryCategory
- Complete REST API with CRUD operations 
- Request/response schemas with validation
- Authentication integration (Firebase JWT)
- Household-based access control
- Expiration tracking and filtering
- Quantity management operations
- Integration with main FastAPI application

⚠️ **Pending:**
- Database table creation (migration or manual setup)
- Test suite execution
- Production deployment

## Quick Start

### 1. Database Setup

#### Option A: Fix Database Permissions (Recommended)
```bash
# Connect to PostgreSQL as superuser and grant permissions
psql -U postgres -d your_database_name
GRANT CREATE ON SCHEMA public TO your_app_user;
GRANT USAGE ON SCHEMA public TO your_app_user;
GRANT CREATE ON DATABASE your_database_name TO your_app_user;

# Create UUID extension (as superuser)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

#### Option B: Use Manual Table Creation Script
```bash
# Run the manual table creation script (once permissions are fixed)
cd server
python create_tables_manual.py
```

#### Option C: Use Alembic Migration (Standard Approach)
```bash
# Once permissions are fixed, run migrations
cd server
python -m alembic upgrade head
```

### 2. Verify Setup

```bash
# Check that pantry tables exist
python check_pantry_tables.py

# Should show:
# Pantry-related tables:
#   - pantry_categories
#   - pantry_items
```

### 3. Start the Server

```bash
# Start FastAPI development server
cd server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the API

```bash
# Check API documentation
curl http://localhost:8000/docs

# Test health endpoint
curl http://localhost:8000/health

# Test pantry endpoint (requires authentication)
curl -X GET "http://localhost:8000/api/pantry/items/" \
  -H "Authorization: Bearer <your_jwt_token>"
```

## API Endpoints Overview

The pantry management API is available at `/api/pantry/items/` with the following endpoints:

- **GET** `/` - List all pantry items (with filtering/sorting)
- **POST** `/` - Create new pantry item
- **PUT** `/{item_id}` - Update existing pantry item
- **DELETE** `/{item_id}` - Delete pantry item
- **PATCH** `/{item_id}/increment` - Increment quantity
- **PATCH** `/{item_id}/decrement` - Decrement quantity
- **PATCH** `/{item_id}/set-quantity` - Set exact quantity

## Key Features

### 1. Authentication & Authorization
- Firebase JWT token required for all endpoints
- Automatic household scope isolation
- User membership validation

### 2. Expiration Management
- Automatic expiration status calculation
- Filtering by expiration status (expired, expiring_soon, fresh)
- Auto-suggestion of expiration dates for new items

### 3. Advanced Filtering & Search
```bash
# Filter by expiration status
GET /api/pantry/items/?expiration_status=expiring_soon

# Search by name
GET /api/pantry/items/?search=milk

# Filter by category
GET /api/pantry/items/?category=Dairy

# Sort by expiration date
GET /api/pantry/items/?sort_by=expiration_date&sort_order=asc
```

### 4. Quantity Management
```bash
# Add 0.5 to current quantity
PATCH /api/pantry/items/{id}/increment?amount=0.5

# Subtract 1.0 from current quantity
PATCH /api/pantry/items/{id}/decrement?amount=1.0

# Set exact quantity to 3.0
PATCH /api/pantry/items/{id}/set-quantity?quantity=3.0
```

## Testing

### Run Unit Tests
```bash
cd server
python -m pytest tests/test_pantry_api.py -v
```

### Run Integration Tests
```bash
# Test with real database (requires setup)
python -m pytest tests/ -v

# Test specific endpoints
python -m pytest tests/test_pantry_api.py::TestPantryAPI::test_create_pantry_item -v
```

### Manual API Testing
```bash
# Use the provided test script
python test_pantry_manual.py

# Or use curl/Postman with the API documentation
```

## Database Schema

### Core Tables Created
- `users` - User accounts with Firebase integration
- `households` - Shared household groups
- `household_members` - User-household membership mapping
- `pantry_categories` - Pantry item categories
- `pantry_items` - Individual pantry items with expiration tracking

### Key Relationships
- Each PantryItem belongs to one Household
- Each PantryItem has one optional PantryCategory
- Each PantryItem is added by one User
- Users access only their household's items

## Production Deployment

### Environment Variables
Ensure these are set in production:
```bash
DB_URL=postgresql://user:pass@host:5432/dbname
JWT_SECRET=your-jwt-secret-key
APP_SECRET_KEY=your-app-secret-key
FIREBASE_WEB_API_KEY=your-firebase-api-key
GCP_PROJECT_ID=your-gcp-project
GCP_CREDENTIALS_JSON={"type":"service_account",...}
```

### Docker Deployment
```dockerfile
# Use the existing Dockerfile in server/
docker build -t bruno-ai-server .
docker run -p 8000:8000 bruno-ai-server
```

### Database Migration in Production
```bash
# Run migrations in production
python -m alembic upgrade head

# Or use the manual creation script as a one-time setup
python create_tables_manual.py
```

## Monitoring & Observability

### Health Checks
- `/health` - Basic service health
- `/` - Root endpoint returning "pong"

### Logging
- All pantry operations are logged with user and household context
- Error tracking for failed operations
- Performance monitoring for database queries

### Metrics to Monitor
- API response times
- Database query performance
- Authentication success/failure rates
- Pantry item creation/update frequencies
- Expiration alert generation

## Troubleshooting

### Common Issues

1. **Database Permission Errors**
   ```
   Error: permission denied for schema public
   ```
   Solution: Grant proper database permissions as shown in setup steps

2. **UUID Extension Missing**
   ```
   Error: function gen_random_uuid() does not exist
   ```
   Solution: Create UUID extension as database superuser

3. **Authentication Failures**
   ```
   Error: 401 Unauthorized
   ```
   Solution: Verify Firebase JWT token is valid and properly formatted

4. **Household Access Issues**
   ```
   Error: User is not a member of any household
   ```
   Solution: Ensure user has proper household membership records

### Debug Commands
```bash
# Check database connection
python -c "from bruno_ai_server.config import settings; print(settings.db_url)"

# Verify table structure
python check_pantry_tables.py

# Test authentication
python -c "from bruno_ai_server.auth import get_current_active_user; print('Auth module loaded')"
```

## Next Steps

Once the database setup is resolved, the pantry management backend is fully functional and ready for:

1. **Frontend Integration**: Connect Flutter app to these API endpoints
2. **Voice Integration**: Connect voice commands to pantry operations
3. **Shopping List Integration**: Auto-generate shopping lists from pantry items
4. **Notification System**: Set up expiration alerts and notifications
5. **Analytics**: Add usage tracking and household insights

The implementation follows FastAPI best practices and is production-ready once deployed with proper database permissions and environment configuration.

# Bruno AI Database Setup

## Overview
This document describes the database schema and migration setup for Bruno AI v3.1, implemented according to the PRD requirements.

## Database Schema

### Core Entities
The database schema implements all entities specified in the PRD:

1. **User** - Authentication and profile management
2. **Household** - Shared spaces for families
3. **Membership** - Implemented as `HouseholdMember` for managing household access
4. **PantryItem** - Individual pantry items with expiration tracking

### Additional Models
Additional models were created to support the full feature set:

- **PantryCategory** - Organization categories for pantry items
- **Recipe** - Meal suggestions and recipe storage
- **RecipeIngredient** - Ingredients required for recipes
- **UserFavorite** - User's favorite recipes with ratings
- **ShoppingList** - Collaborative shopping lists
- **ShoppingListItem** - Items in shopping lists
- **Order** - Orders placed through Instacart/third-party services
- **OrderItem** - Individual items in orders

## Architecture Features

### Async SQLAlchemy Support
- Base model class configured with `AsyncAttrs` for async operations
- Uses `declarative_base(cls=AsyncAttrs)` for proper async support
- Timestamp mixin with timezone-aware datetime columns

### PostgreSQL-Specific Features
- JSONB columns for flexible metadata storage
- Proper indexing for performance
- Foreign key relationships with cascading
- Unique constraints for data integrity

### Key Design Decisions
- Renamed `metadata` columns to avoid SQLAlchemy conflicts (`item_metadata`, `list_metadata`, `order_metadata`)
- Used timezone-aware timestamps with server defaults
- Implemented proper relationships between all entities
- Added support for Instacart integration with order tracking

## Files Structure

```
server/
├── bruno_ai_server/
│   ├── models/
│   │   ├── __init__.py          # Model exports
│   │   ├── base.py              # Base model with async support
│   │   ├── user.py              # User, Household, HouseholdMember
│   │   ├── pantry.py            # PantryItem, PantryCategory
│   │   ├── recipe.py            # Recipe, RecipeIngredient, UserFavorite
│   │   └── shopping.py          # ShoppingList, Order models
│   └── config.py                # Configuration with database URL
├── alembic/
│   ├── env.py                   # Alembic environment configuration
│   ├── script.py.mako           # Migration template
│   └── versions/
│       └── 001_initial_database_schema.py  # Initial migration
├── alembic.ini                  # Alembic configuration
├── .env                         # Environment variables
└── test_migration.py            # Validation script
```

## Database Tables

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `users` | User authentication and profiles | Email uniqueness, JSONB preferences |
| `households` | Shared family spaces | Invite codes, owner relationships |
| `household_members` | Household membership | Role-based permissions |
| `pantry_categories` | Item organization | Icons and colors for UI |
| `pantry_items` | Individual pantry items | Expiration tracking, barcodes |
| `recipes` | Meal suggestions | JSONB nutrition info and tags |
| `recipe_ingredients` | Recipe components | Quantities and optional ingredients |
| `user_favorites` | Saved recipes | Ratings and personal notes |
| `shopping_lists` | Collaborative lists | Shared household lists |
| `shopping_list_items` | List items | Purchase status, price tracking |
| `orders` | Third-party orders | Instacart integration, affiliate tracking |
| `order_items` | Order details | External service data |

## Migration Setup

### Alembic Configuration
- Configured for async PostgreSQL connection
- Proper model imports in `env.py`
- Database URL from settings with fallback to alembic.ini

### Initial Migration
- Complete schema creation in single migration
- All tables, indexes, and foreign keys included
- Proper upgrade and downgrade functions

## Usage Instructions

### Prerequisites
```bash
# Start PostgreSQL database
docker-compose -f ../infra/docker-compose.yml up -d
```

### Running Migrations
```bash
# Navigate to server directory
cd server

# Apply migrations
py -m alembic upgrade head

# Check migration status
py -m alembic current

# Generate new migration (after model changes)
py -m alembic revision --autogenerate -m "Description of changes"
```

### Validation
```bash
# Run validation script
py test_migration.py
```

## Environment Variables
Required environment variables in `.env`:
- `DB_URL` - PostgreSQL connection string
- `JWT_SECRET` - JWT signing secret
- `APP_SECRET_KEY` - Application secret key

## Docker Compose Setup
The `infra/docker-compose.yml` provides:
- PostgreSQL database on port 5432
- Database name: `bruno_ai_v2`
- Default credentials: `user/password`
- Persistent volume for data

## Next Steps
1. Start PostgreSQL with Docker Compose
2. Run `alembic upgrade head` to create all tables
3. Verify schema creation with database client
4. Begin implementing FastAPI endpoints using these models

This setup provides a complete, production-ready database schema that supports all features outlined in the Bruno AI PRD, with proper async support for FastAPI integration.

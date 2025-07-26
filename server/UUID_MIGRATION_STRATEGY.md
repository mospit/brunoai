# UUID Migration Strategy & Backward-Compatibility Plan

## Analysis & Decision

### Current State Assessment
Based on the codebase analysis:

- **Environment**: Development environment (`.env.example` shows `ENVIRONMENT="development"`)
- **Database**: PostgreSQL with AsyncSQL/Alembic migrations
- **Migration Status**: Single initial migration (`001_initial_database_schema.py`) - appears to be a fresh project
- **Production Data**: No evidence of production deployment or data
- **Tables Affected**: 12 tables with integer primary keys and foreign key relationships

### Affected Tables & Relationships
```
Primary Key Tables:
- users (id) → households.owner_id, household_members.user_id, pantry_items.added_by_user_id, etc.
- households (id) → household_members.household_id, pantry_items.household_id, etc.
- pantry_categories (id) → pantry_items.category_id
- recipes (id) → recipe_ingredients.recipe_id, user_favorites.recipe_id, etc.
- pantry_items (id)
- recipe_ingredients (id)
- user_favorites (id)
- shopping_lists (id) → shopping_list_items.shopping_list_id, orders.shopping_list_id
- shopping_list_items (id) → order_items.shopping_list_item_id
- orders (id) → order_items.order_id
- order_items (id)
- household_members (id)
```

## **RECOMMENDED STRATEGY: Plan A - Clean Break Migration**

### Decision Rationale
**Plan A (Clean Break)** is chosen because:

1. **No Production Data**: This appears to be a development project with no production deployment
2. **Single Migration**: Only one initial migration exists, indicating fresh schema
3. **Development Environment**: Configuration shows development setup
4. **Simplicity**: Cleaner implementation without migration complexity
5. **Performance**: UUID columns from the start avoid dual-column overhead
6. **Maintainability**: No legacy integer ID cleanup needed

### Plan A Implementation Strategy

#### Phase 1: Update Base Model & Schema
```python
# bruno_ai_server/models/base.py
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

class TimestampMixin:
    """Mixin to add UUID primary key and timestamps to models."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
```

#### Phase 2: Update All Foreign Key References
Update all foreign key columns in models:
```python
# Example updates needed:
# households.owner_id: Integer → UUID
# household_members.user_id: Integer → UUID
# household_members.household_id: Integer → UUID
# pantry_items.household_id: Integer → UUID
# pantry_items.category_id: Integer → UUID
# pantry_items.added_by_user_id: Integer → UUID
# ... (all foreign key columns)
```

#### Phase 3: Generate New Migration
```bash
# Drop current database (development only!)
alembic downgrade base

# Generate new migration with UUID schema
alembic revision --autogenerate -m "Migrate to UUID primary keys"

# Apply new migration
alembic upgrade head
```

#### Phase 4: Update Application Code
- Update all API responses to handle UUID format
- Update serializers/schemas for UUID fields
- Update any hardcoded ID references in tests
- Update frontend integration to handle UUID format

### Advantages of Plan A (Clean Break)
✅ **Simplicity**: Single migration, no dual-column complexity
✅ **Performance**: No overhead from maintaining two ID systems
✅ **Clean Schema**: UUIDs from the start, no legacy remnants
✅ **No Data Loss Risk**: No production data to preserve
✅ **Faster Development**: No complex migration logic needed
✅ **Better Long-term Maintainability**: Clean UUID implementation

### Disadvantages of Plan A
❌ **Development Data Loss**: Any test/development data will be lost
❌ **API Breaking Change**: Requires coordinated frontend updates
❌ **One-time Migration**: Cannot be gradually rolled out

## Alternative: Plan B - In-Place Dual-Column Migration

### When to Use Plan B
Plan B should only be considered if:
- Production data exists that must be preserved
- Gradual rollout is required
- API backward compatibility is critical

### Plan B Implementation Overview
```sql
-- Phase 1: Add UUID columns
ALTER TABLE users ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid();
ALTER TABLE households ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid();
-- ... for all tables

-- Phase 2: Backfill UUIDs
UPDATE users SET uuid_id = gen_random_uuid() WHERE uuid_id IS NULL;
-- ... for all tables

-- Phase 3: Add UUID foreign key columns
ALTER TABLE households ADD COLUMN uuid_owner_id UUID;
-- ... for all foreign keys

-- Phase 4: Populate UUID foreign keys
UPDATE households SET uuid_owner_id = users.uuid_id 
FROM users WHERE households.owner_id = users.id;
-- ... for all foreign keys

-- Phase 5: Switch primary keys and constraints
ALTER TABLE users DROP CONSTRAINT users_pkey;
ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (uuid_id);
-- ... update all foreign key constraints

-- Phase 6: Drop integer columns
ALTER TABLE users DROP COLUMN id;
ALTER TABLE households DROP COLUMN owner_id;
-- ... drop all old integer columns
```

### Plan B Advantages
✅ **Data Preservation**: No data loss during migration
✅ **Gradual Rollout**: Can be done in phases
✅ **Rollback Capability**: Can revert during migration

### Plan B Disadvantages
❌ **Complexity**: Multiple migration steps, error-prone
❌ **Performance Impact**: Dual columns during migration
❌ **Extended Timeline**: Weeks of migration phases
❌ **Storage Overhead**: Temporary disk space increase
❌ **Risk of Inconsistency**: Data sync issues between columns

## Final Recommendation

**Execute Plan A (Clean Break Migration)** for this project because:

1. **Development Stage**: No production data to preserve
2. **Fresh Migration**: Single initial migration suggests early development
3. **Optimal Performance**: UUIDs from the start
4. **Simplified Maintenance**: No legacy migration complexity

## Implementation Timeline

### Week 1: Schema Updates
- [ ] Update `TimestampMixin` to use UUID primary keys
- [ ] Update all model foreign key references to UUID
- [ ] Update Pydantic schemas for UUID serialization

### Week 2: Migration & Testing  
- [ ] Generate new Alembic migration
- [ ] Test migration on development database
- [ ] Update test fixtures for UUID format
- [ ] Validate all relationships work correctly

### Week 3: Application Updates
- [ ] Update API endpoints to handle UUID parameters
- [ ] Update frontend integration (if applicable)
- [ ] Update documentation and API specs
- [ ] Perform end-to-end testing

### Risks & Mitigation
- **Risk**: Development data loss
  - **Mitigation**: Export any important test data before migration
- **Risk**: API compatibility issues  
  - **Mitigation**: Coordinate with frontend team on UUID format
- **Risk**: Performance impact
  - **Mitigation**: Monitor query performance after migration

This strategy provides the cleanest, most maintainable path forward for UUID adoption while minimizing complexity and technical debt.

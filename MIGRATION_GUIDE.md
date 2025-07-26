# Database Migration Guide

## ⚠️ BREAKING SCHEMA CHANGE ⚠️

This migration introduces significant database schema changes that are **NOT backward compatible**.

### What Changed

- **New Tables**: `users` and `households` tables with UUID primary keys
- **Firebase Integration**: Users now authenticate via Firebase with local database sync
- **Authentication Fields**: Added Firebase UID, email verification, and JWT token support
- **Relationship Changes**: Established proper foreign key relationships between users and households

### Required Actions

**BEFORE running the migration:**

1. **BACKUP YOUR LOCAL DATABASE**
   ```bash
   # From the server directory
   pg_dump bruno_ai > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Clear existing data** (if you have test data you want to preserve, export it first)
   ```bash
   # The migration will create new tables with different schemas
   # Existing data may not be compatible
   ```

### Running the Migration

```bash
cd server
alembic upgrade head
```

### Post-Migration

- All users will need to re-register as the authentication system has changed
- Any existing pantry/recipe data will need to be re-associated with new user UUIDs
- Test all authentication flows thoroughly

### Rollback (if needed)

```bash
# Restore from backup
psql bruno_ai < your_backup_file.sql
```

### Questions?

If you encounter issues, check:
1. Database connection settings in `.env`
2. Firebase configuration
3. Alembic migration logs

Contact the development team for assistance with complex migration scenarios.

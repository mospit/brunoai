# Authentication System Implementation

This document describes the enhanced authentication system for Bruno AI, including the ERD, database models, and migration implementation.

## Overview

The authentication system has been enhanced to support both Firebase authentication and traditional password-based authentication, with comprehensive token management and email verification capabilities.

## Database Schema

### Enhanced User Model
The `User` model now includes the following authentication-related fields:

- **password_hash**: Nullable field for traditional password authentication
- **last_login**: Timestamp of the user's last successful login
- **status**: User account status (active, suspended, pending, deactivated)
- **verification_token**: Token for email verification (legacy field)

### New Authentication Tables

#### RefreshTokens Table
Manages JWT refresh tokens for secure authentication:

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    device_info JSONB DEFAULT '{}'
);
```

#### EmailVerifications Table
Handles email verification and password reset tokens:

```sql
CREATE TABLE email_verifications (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    verification_token VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    token_type VARCHAR(50) NOT NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verified_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    attempts INTEGER DEFAULT 0
);
```

## File Structure

```
server/
├── bruno_ai_server/
│   ├── models/
│   │   ├── auth.py                 # New authentication models
│   │   ├── user.py                 # Enhanced user model
│   │   └── __init__.py            # Updated model exports
├── alembic/
│   └── versions/
│       └── 003_add_authentication_fields.py  # Migration script
├── docs/
│   └── database_erd.md            # Complete ERD documentation
├── test_auth_tables.py            # Test script for auth models
└── AUTH_SYSTEM_README.md          # This file
```

## Models and Relationships

### RefreshToken Model
```python
class RefreshToken(Base, TimestampMixin):
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    device_info = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    # Properties
    @property
    def is_valid(self):
        return not self.is_revoked and not self.is_expired
```

### EmailVerification Model
```python
class EmailVerification(Base, TimestampMixin):
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"))
    verification_token = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    token_type = Column(String(50), nullable=False)  # 'email_verify' or 'password_reset'
    requested_at = Column(DateTime(timezone=True), server_default="now()")
    verified_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, default=0)
    
    # Methods
    def mark_as_verified(self):
        self.verified_at = datetime.utcnow()
```

## Migration Instructions

### Prerequisites
1. Ensure PostgreSQL is running:
   ```bash
   docker-compose -f ../infra/docker-compose.yml up -d
   ```

2. Navigate to the server directory:
   ```bash
   cd server
   ```

### Running the Migration
```bash
# Apply the new authentication migration
py -m alembic upgrade head

# Verify migration status
py -m alembic current

# Check database schema
py -m alembic show head
```

### Testing the Implementation
```bash
# Run the authentication models test
python test_auth_tables.py
```

## Usage Examples

### Creating a User with Authentication
```python
from bruno_ai_server.models import User, RefreshToken, EmailVerification
from datetime import datetime, timedelta

# Create user
user = User(
    email="user@example.com",
    password_hash="$2b$12$...",  # Hashed password
    full_name="John Doe",
    status="pending"  # Pending email verification
)

# Create email verification
verification = EmailVerification(
    user_id=user.id,
    verification_token="unique_token_123",
    email=user.email,
    token_type="email_verify",
    expires_at=datetime.utcnow() + timedelta(hours=24)
)

# Create refresh token after login
refresh_token = RefreshToken(
    user_id=user.id,
    token="secure_refresh_token",
    expires_at=datetime.utcnow() + timedelta(days=30),
    device_info={"device": "mobile", "ip": "192.168.1.1"}
)
```

### Token Management
```python
# Check token validity
if refresh_token.is_valid:
    # Token is valid, proceed with refresh
    pass

# Revoke token
refresh_token.is_revoked = True

# Check expiration
if refresh_token.is_expired:
    # Handle expired token
    pass
```

### Email Verification Flow
```python
# Create verification request
verification = EmailVerification(
    user_id=user.id,
    verification_token=generate_token(),
    email=user.email,
    token_type="email_verify",
    expires_at=datetime.utcnow() + timedelta(hours=24)
)

# Process verification
if verification.is_valid:
    verification.mark_as_verified()
    user.is_verified = True
    user.status = "active"
```

## Security Features

### Constraints and Validations
- **Foreign Key Cascades**: Tokens are automatically deleted when users are deleted
- **Token Uniqueness**: All tokens have unique constraints
- **Expiration Checks**: Built-in expiration validation
- **Status Validation**: User status is constrained to valid values
- **Attempt Limiting**: Email verification attempts are tracked

### Indexes for Performance
- Primary keys on all tables
- Unique indexes on tokens and email addresses
- Performance indexes on foreign keys and date fields
- Status indexes for efficient filtering

## Migration Rollback

If you need to rollback the authentication enhancements:
```bash
# Rollback to previous migration
py -m alembic downgrade c3f6ba074872
```

This will:
- Drop the `refresh_tokens` and `email_verifications` tables
- Remove the new authentication columns from the `users` table
- Drop associated indexes and constraints

## Next Steps

1. **API Implementation**: Create FastAPI endpoints for authentication
2. **JWT Service**: Implement JWT token generation and validation
3. **Email Service**: Set up email verification sending
4. **Middleware**: Add authentication middleware for protected routes
5. **Testing**: Comprehensive integration tests for auth flows

## Files Modified/Created

### New Files
- `bruno_ai_server/models/auth.py` - Authentication models
- `alembic/versions/003_add_authentication_fields.py` - Migration script
- `docs/database_erd.md` - Complete ERD documentation
- `test_auth_tables.py` - Test script
- `AUTH_SYSTEM_README.md` - This documentation

### Modified Files
- `bruno_ai_server/models/user.py` - Enhanced with auth fields
- `bruno_ai_server/models/__init__.py` - Added auth model exports

The authentication system is now ready for use with comprehensive token management, email verification, and proper database constraints.

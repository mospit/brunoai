# Database Entity-Relationship Diagram (ERD)

## Core Authentication Entities

### User Entity
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| **id** | UUID | PRIMARY KEY | Unique identifier |
| **email** | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| **password_hash** | VARCHAR(255) | NULLABLE | Hashed password (nullable for Firebase users) |
| **full_name** | VARCHAR(255) | NOT NULL | User's full name |
| **created_at** | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation time |
| **updated_at** | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last profile update |
| **last_login** | TIMESTAMP | NULLABLE | Last successful login |
| **status** | VARCHAR(50) | NOT NULL, DEFAULT 'active' | User status (active, suspended, pending) |
| **verification_token** | VARCHAR(255) | NULLABLE | Email verification token |
| **is_active** | BOOLEAN | NOT NULL, DEFAULT TRUE | Account active status |
| **is_verified** | BOOLEAN | NOT NULL, DEFAULT FALSE | Email verification status |
| **dietary_preferences** | JSONB | DEFAULT '{}' | User dietary preferences |
| **voice_settings** | JSONB | DEFAULT '{}' | Voice interface settings |
| **notification_preferences** | JSONB | DEFAULT '{}' | Notification settings |

### RefreshTokens Entity
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| **id** | UUID | PRIMARY KEY | Unique identifier |
| **user_id** | UUID | FOREIGN KEY → users(id) | Token owner |
| **token** | VARCHAR(500) | UNIQUE, NOT NULL | Refresh token value |
| **created_at** | TIMESTAMP | NOT NULL, DEFAULT NOW() | Token creation time |
| **expires_at** | TIMESTAMP | NOT NULL | Token expiration time |
| **is_revoked** | BOOLEAN | NOT NULL, DEFAULT FALSE | Token revocation status |
| **device_info** | JSONB | DEFAULT '{}' | Device/client information |

### EmailVerifications Entity
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| **id** | UUID | PRIMARY KEY | Unique identifier |
| **user_id** | UUID | FOREIGN KEY → users(id) | User being verified |
| **verification_token** | VARCHAR(255) | UNIQUE, NOT NULL | Verification token |
| **email** | VARCHAR(255) | NOT NULL | Email being verified |
| **token_type** | VARCHAR(50) | NOT NULL | Type (email_verify, password_reset) |
| **requested_at** | TIMESTAMP | NOT NULL, DEFAULT NOW() | Verification request time |
| **verified_at** | TIMESTAMP | NULLABLE | Verification completion time |
| **expires_at** | TIMESTAMP | NOT NULL | Token expiration time |
| **attempts** | INTEGER | NOT NULL, DEFAULT 0 | Verification attempts count |

## Relationships

### One-to-Many Relationships
- **User → RefreshTokens**: One user can have multiple refresh tokens (different devices)
- **User → EmailVerifications**: One user can have multiple verification requests
- **User → Households**: One user can own multiple households
- **User → HouseholdMembers**: One user can be member of multiple households

### Many-to-Many Relationships
- **User ↔ Household**: Through HouseholdMember junction table

## Entity Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│      User       │────▶│  RefreshTokens   │     │EmailVerifications│
│                 │     │                  │     │                 │
│ • id (PK)       │     │ • id (PK)        │     │ • id (PK)       │
│ • email         │     │ • user_id (FK)   │     │ • user_id (FK)  │
│ • password_hash │     │ • token          │     │ • token         │
│ • full_name     │     │ • created_at     │     │ • email         │
│ • created_at    │     │ • expires_at     │     │ • token_type    │
│ • updated_at    │     │ • is_revoked     │     │ • requested_at  │
│ • last_login    │     │ • device_info    │     │ • verified_at   │
│ • status        │     └──────────────────┘     │ • expires_at    │
│ • verification_ │                              │ • attempts      │
│   token         │                              └─────────────────┘
│ • is_active     │                                       ▲
│ • is_verified   │                                       │
│ • dietary_      │                                       │
│   preferences   │     ┌──────────────────┐             │
│ • voice_settings│────▶│   Household      │             │
│ • notification_ │     │                  │             │
│   preferences   │     │ • id (PK)        │             │
└─────────────────┘     │ • name           │             │
          ▲             │ • invite_code    │             │
          │             │ • owner_id (FK)  │             │
          │             │ • settings       │             │
          │             └──────────────────┘             │
          │                       ▲                      │
          │                       │                      │
          │             ┌──────────────────┐             │
          └─────────────│ HouseholdMember  │─────────────┘
                        │                  │
                        │ • id (PK)        │
                        │ • user_id (FK)   │
                        │ • household_id   │
                        │   (FK)           │
                        │ • role           │
                        │ • joined_at      │
                        └──────────────────┘
```

## Indexes

### Primary Indexes
- `users.id` (Primary Key)
- `refresh_tokens.id` (Primary Key)  
- `email_verifications.id` (Primary Key)

### Unique Indexes  
- `users.email` (Unique)
- `refresh_tokens.token` (Unique)
- `email_verifications.verification_token` (Unique)

### Performance Indexes
- `refresh_tokens.user_id` (Foreign Key)
- `refresh_tokens.expires_at` (For cleanup queries)
- `email_verifications.user_id` (Foreign Key)
- `email_verifications.expires_at` (For cleanup queries)
- `users.status` (For status filtering)
- `users.last_login` (For analytics)

## Constraints

### Foreign Key Constraints
- `refresh_tokens.user_id` → `users.id` (ON DELETE CASCADE)
- `email_verifications.user_id` → `users.id` (ON DELETE CASCADE)

### Check Constraints
- `users.status` IN ('active', 'suspended', 'pending', 'deactivated')
- `email_verifications.token_type` IN ('email_verify', 'password_reset')
- `email_verifications.attempts` >= 0
- `refresh_tokens.expires_at` > `refresh_tokens.created_at`
- `email_verifications.expires_at` > `email_verifications.requested_at`

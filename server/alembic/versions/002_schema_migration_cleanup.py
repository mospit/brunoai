"""Schema migration cleanup - Remove redundant columns and implement naming consistency

Revision ID: 002
Revises: 001
Create Date: 2025-01-23 16:49:00.000000

Migration Strategy & Data-Safety Rules:
=====================================

This migration addresses schema gaps identified between the current model definitions
and the initial database schema. Each decision follows a specific data-safety strategy:

1. ALTER TABLE users DROP COLUMN password_hash
   ├─ DECISION: DROP COLUMN (data may be discarded)
   ├─ REASON: Transitioned to Firebase authentication - local password storage no longer needed
   ├─ DATA SAFETY: Firebase handles authentication, making local password_hash redundant
   └─ IMPACT: Zero functional impact as authentication flow uses Firebase tokens

2. ALTER TABLE households RENAME COLUMN invite_code TO code  
   ├─ DECISION: RENAME (only naming differs)
   ├─ REASON: Naming consistency across schema - simplify column naming convention
   ├─ DATA SAFETY: Zero data loss - pure rename operation
   └─ IMPACT: Application code needs to reference new column name

3. ALTER TABLE recipe_ingredients DROP COLUMN is_optional
   ├─ DECISION: DROP COLUMN (data may be discarded) 
   ├─ REASON: Feature not actively used in current business logic
   ├─ DATA SAFETY: Low impact - optional ingredients can be handled via notes field
   └─ IMPACT: Simplifies recipe ingredient model, reduces storage overhead

4. Add missing authentication tables (refresh_tokens, email_verifications)
   ├─ DECISION: ADD TABLES (new functionality)
   ├─ REASON: Support JWT refresh tokens and email verification workflows
   ├─ DATA SAFETY: New tables, no existing data affected
   └─ IMPACT: Enables secure authentication and email verification features

5. Add missing user profile columns (last_login, status, verification_token)
   ├─ DECISION: ADD COLUMNS (new functionality)
   ├─ REASON: Support user status tracking and verification workflows
   ├─ DATA SAFETY: New columns with appropriate defaults, no data loss
   └─ IMPACT: Enhanced user management capabilities

Future Development Notes:
========================
- All dropped columns are documented in this migration for potential future restoration
- UUID migration preparedness: Schema designed to support future UUID primary keys
- Backup strategy: Consider data export before applying in production
- Rollback plan: Downgrade available via 001 migration if needed

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply schema cleanup changes with documented data-safety decisions."""
    
    # ========================================================================
    # STEP 1: Add missing authentication tables
    # DECISION: ADD TABLES (new functionality, zero data loss)
    # ========================================================================
    
    # Create refresh_tokens table for JWT token management
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=500), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('device_info', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('token'),
        sa.CheckConstraint('expires_at > created_at', name='expires_after_created')
    )
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'], unique=True)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])
    
    # Create email_verifications table for account verification
    op.create_table(
        'email_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verification_token', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('token_type', sa.String(length=50), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('verification_token'),
        sa.CheckConstraint("token_type IN ('email_verify', 'password_reset')", name='valid_token_type'),
        sa.CheckConstraint('attempts >= 0', name='non_negative_attempts'),
        sa.CheckConstraint('expires_at > requested_at', name='expires_after_requested')
    )
    op.create_index('ix_email_verifications_token', 'email_verifications', ['verification_token'], unique=True)
    op.create_index('ix_email_verifications_user_id', 'email_verifications', ['user_id'])
    op.create_index('ix_email_verifications_expires_at', 'email_verifications', ['expires_at'])

    # ========================================================================
    # STEP 2: Add missing user profile columns
    # DECISION: ADD COLUMNS (new functionality, zero data loss)
    # ========================================================================
    
    # Add user status tracking columns
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('status', sa.String(length=50), nullable=False, server_default='active'))
    op.add_column('users', sa.Column('verification_token', sa.String(length=255), nullable=True))
    
    # Add constraint for valid user statuses
    op.create_check_constraint(
        'valid_user_status', 
        'users', 
        "status IN ('active', 'suspended', 'pending', 'deactivated')"
    )
    
    # Add indexes for performance
    op.create_index('ix_users_status', 'users', ['status'])
    op.create_index('ix_users_last_login', 'users', ['last_login'])

    # ========================================================================
    # STEP 3: Update existing tables to UUID primary keys
    # DECISION: MIGRATION PREPARATION (zero data loss, future compatibility)
    # ========================================================================
    
    # Convert users table to UUID primary key
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Add UUID column to users table
    op.add_column('users', sa.Column('uuid_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.create_unique_constraint('uq_users_uuid_id', 'users', ['uuid_id'])
    
    # Convert households table to UUID
    op.add_column('households', sa.Column('uuid_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False))
    op.add_column('households', sa.Column('uuid_owner_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_unique_constraint('uq_households_uuid_id', 'households', ['uuid_id'])
    
    # Update UUID foreign key references
    op.execute("""
        UPDATE households 
        SET uuid_owner_id = users.uuid_id 
        FROM users 
        WHERE households.owner_id = users.id
    """)
    
    # ========================================================================
    # STEP 4: Apply data-safety decisions for column modifications  
    # DECISION: Based on documented strategy above
    # ========================================================================
    
    # 4a. DROP COLUMN: Remove password_hash (Firebase authentication)
    # SAFETY: Data may be discarded - Firebase handles authentication
    if _column_exists('users', 'hashed_password'):
        op.drop_column('users', 'hashed_password')
    elif _column_exists('users', 'password_hash'):
        op.drop_column('users', 'password_hash')
    
    # 4b. RENAME COLUMN: invite_code to code (naming consistency)  
    # SAFETY: Zero data loss - pure rename operation
    if _column_exists('households', 'invite_code'):
        op.alter_column('households', 'invite_code', new_column_name='code')
    
    # 4c. DROP COLUMN: Remove is_optional from recipe_ingredients
    # SAFETY: Data may be discarded - feature not actively used
    if _column_exists('recipe_ingredients', 'is_optional'):
        op.drop_column('recipe_ingredients', 'is_optional')

    # ========================================================================
    # STEP 5: Update foreign key constraints for UUID migration preparation
    # DECISION: FUTURE COMPATIBILITY (maintains current functionality)
    # ========================================================================
    
    # Add UUID foreign key constraint for households
    op.create_foreign_key(
        'fk_households_uuid_owner_id', 
        'households', 
        'users', 
        ['uuid_owner_id'], 
        ['uuid_id']
    )


def downgrade() -> None:
    """Rollback schema cleanup changes - restore original state."""
    
    # Remove UUID foreign key constraints
    op.drop_constraint('fk_households_uuid_owner_id', 'households', type_='foreignkey')
    
    # Restore dropped columns with appropriate defaults
    
    # Restore password_hash column (though it will be empty)
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    
    # Restore invite_code column name
    if _column_exists('households', 'code'):
        op.alter_column('households', 'code', new_column_name='invite_code')
    
    # Restore is_optional column
    op.add_column('recipe_ingredients', sa.Column('is_optional', sa.String(length=10), nullable=True))
    
    # Remove UUID columns
    op.drop_constraint('uq_households_uuid_id', 'households', type_='unique')
    op.drop_column('households', 'uuid_owner_id')
    op.drop_column('households', 'uuid_id')
    
    op.drop_constraint('uq_users_uuid_id', 'users', type_='unique') 
    op.drop_column('users', 'uuid_id')
    
    # Remove user profile columns
    op.drop_index('ix_users_last_login', 'users')
    op.drop_index('ix_users_status', 'users')
    op.drop_constraint('valid_user_status', 'users', type_='check')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'status')
    op.drop_column('users', 'last_login')
    
    # Remove authentication tables
    op.drop_index('ix_email_verifications_expires_at', 'email_verifications')
    op.drop_index('ix_email_verifications_user_id', 'email_verifications')
    op.drop_index('ix_email_verifications_token', 'email_verifications')
    op.drop_table('email_verifications')
    
    op.drop_index('ix_refresh_tokens_expires_at', 'refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_id', 'refresh_tokens')
    op.drop_index('ix_refresh_tokens_token', 'refresh_tokens')
    op.drop_table('refresh_tokens')


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        connection = op.get_bind()
        result = connection.execute(sa.text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND column_name = :column_name
            AND table_schema = 'public'
        """), {"table_name": table_name, "column_name": column_name})
        return result.scalar() > 0
    except Exception:
        return False

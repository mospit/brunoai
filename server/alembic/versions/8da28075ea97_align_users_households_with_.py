"""align users & households with architecture v1 schema

Revision ID: 8da28075ea97
Revises: a4d1233f2b94
Create Date: 2025-07-25 11:54:18.996138

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '8da28075ea97'
down_revision = 'a4d1233f2b94'
branch_labels = None
depends_on = None


def upgrade():
    # Users table amendments
    # Rename full_name to name
    op.alter_column('users', 'full_name', new_column_name='name')
    
    # voice_settings and dietary_preferences columns already exist from previous migration,
    # but ensure they have proper server defaults
    op.alter_column('users', 'voice_settings', 
                   existing_type=sa.dialects.postgresql.JSONB(),
                   server_default='{}')
    op.alter_column('users', 'dietary_preferences', 
                   existing_type=sa.dialects.postgresql.JSONB(),
                   server_default='{}')
    
    # Add household_id column to users (foreign key to households)
    op.add_column('users', sa.Column('household_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_users_household_id', 'users', 'households', ['household_id'], ['id'])
    
    # Drop unneeded authentication columns (added in 003 migration)
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'status')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'verification_token')
    
    # Update timestamp defaults to use now() (they should already have this from UUID migration)
    op.alter_column('users', 'created_at', 
                   existing_type=sa.DateTime(timezone=True),
                   server_default=sa.text('now()'))
    op.alter_column('users', 'updated_at', 
                   existing_type=sa.DateTime(timezone=True),
                   server_default=sa.text('now()'))
    
    # Households table amendments
    # Rename owner_id to admin_user_id
    op.alter_column('households', 'owner_id', new_column_name='admin_user_id')
    
    # Change invite_code length from 6 to 8 characters
    op.alter_column('households', 'invite_code', 
                   existing_type=sa.String(length=6),
                   type_=sa.String(length=8),
                   nullable=False)
    
    # Create unique constraint for invite_code (might already exist from previous migration)
    try:
        op.create_unique_constraint('uq_households_invite_code', 'households', ['invite_code'])
    except Exception:
        # Constraint might already exist, continue
        pass
    
    # Update timestamp defaults for households
    op.alter_column('households', 'created_at', 
                   existing_type=sa.DateTime(timezone=True),
                   server_default=sa.text('now()'))
    op.alter_column('households', 'updated_at', 
                   existing_type=sa.DateTime(timezone=True), 
                   server_default=sa.text('now()'))
    
    # Index management
    # Ensure email has unique index (should already exist from UUID migration)
    try:
        op.create_index('ix_users_email', 'users', ['email'], unique=True)
    except Exception:
        # Index might already exist, continue
        pass
    
    # Create index for invite_code (should already exist from UUID migration)
    try:
        op.create_index('ix_households_invite_code', 'households', ['invite_code'])
    except Exception:
        # Index might already exist, continue
        pass


def downgrade():
    # Reverse the operations performed in upgrade()
    
    # Drop indexes
    try:
        op.drop_index('ix_households_invite_code', 'households')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_users_email', 'users')
    except Exception:
        pass
    
    # Reverse households table changes
    # Remove unique constraint for invite_code
    try:
        op.drop_constraint('uq_households_invite_code', 'households', type_='unique')
    except Exception:
        pass
    
    # Change invite_code length back from 8 to 6 characters
    op.alter_column('households', 'invite_code', 
                   existing_type=sa.String(length=8),
                   type_=sa.String(length=6),
                   nullable=False)
    
    # Rename admin_user_id back to owner_id
    op.alter_column('households', 'admin_user_id', new_column_name='owner_id')
    
    # Reverse users table changes
    # Add back authentication columns that were dropped
    op.add_column('users', sa.Column('verification_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('status', sa.String(length=50), nullable=False, server_default='active'))
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    
    # Add back check constraint for user status
    op.create_check_constraint(
        'valid_user_status',
        'users', 
        "status IN ('active', 'suspended', 'pending', 'deactivated')"
    )
    
    # Drop household_id foreign key and column from users
    try:
        op.drop_constraint('fk_users_household_id', 'users', type_='foreignkey')
    except Exception:
        pass
    op.drop_column('users', 'household_id')
    
    # Rename name back to full_name 
    op.alter_column('users', 'name', new_column_name='full_name')

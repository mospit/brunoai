"""add authentication fields and tables

Revision ID: 003_auth_enhancement
Revises: c3f6ba074872
Create Date: 2025-01-25 15:35:32.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_auth_enhancement'
down_revision = 'c3f6ba074872'
branch_labels = None
depends_on = None


def upgrade():
    """Add authentication fields to users table and create auth tables."""
    
    # Add new columns to users table
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('status', sa.String(length=50), nullable=False, server_default='active'))
    op.add_column('users', sa.Column('verification_token', sa.String(length=255), nullable=True))
    
    # Add check constraint for user status
    op.create_check_constraint(
        'valid_user_status',
        'users',
        "status IN ('active', 'suspended', 'pending', 'deactivated')"
    )
    
    # Create indexes for new columns
    op.create_index('ix_users_status', 'users', ['status'])
    op.create_index('ix_users_last_login', 'users', ['last_login'])
    
    # Create refresh_tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=500), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('device_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.CheckConstraint('expires_at > created_at', name='expires_after_created'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_refresh_tokens_id', 'refresh_tokens', ['id'])
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'], unique=True)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])
    
    # Create email_verifications table
    op.create_table('email_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.CheckConstraint("token_type IN ('email_verify', 'password_reset')", name='valid_token_type'),
        sa.CheckConstraint('attempts >= 0', name='non_negative_attempts'),
        sa.CheckConstraint('expires_at > requested_at', name='expires_after_requested'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_email_verifications_id', 'email_verifications', ['id'])
    op.create_index('ix_email_verifications_verification_token', 'email_verifications', ['verification_token'], unique=True)
    op.create_index('ix_email_verifications_user_id', 'email_verifications', ['user_id'])
    op.create_index('ix_email_verifications_expires_at', 'email_verifications', ['expires_at'])


def downgrade():
    """Remove authentication fields and tables."""
    
    # Drop the new tables
    op.drop_table('email_verifications')
    op.drop_table('refresh_tokens')
    
    # Remove indexes from users table
    op.drop_index('ix_users_last_login', 'users')
    op.drop_index('ix_users_status', 'users')
    
    # Remove check constraint
    op.drop_constraint('valid_user_status', 'users', type_='check')
    
    # Remove columns from users table
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'status')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'password_hash')

"""add_firebase_uid_to_users

Revision ID: 85f2a8c1d6e7
Revises: 8da28075ea97
Create Date: 2025-01-25 17:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85f2a8c1d6e7'
down_revision = '8da28075ea97'
branch_labels = None
depends_on = None


def upgrade():
    """Add firebase_uid column to users table."""
    # Add firebase_uid column
    op.add_column('users', sa.Column('firebase_uid', sa.String(length=128), nullable=True))
    
    # Create unique index on firebase_uid
    op.create_index('ix_users_firebase_uid', 'users', ['firebase_uid'], unique=True)


def downgrade():
    """Remove firebase_uid column from users table."""
    # Drop the index first
    op.drop_index('ix_users_firebase_uid', table_name='users')
    
    # Drop the column
    op.drop_column('users', 'firebase_uid')

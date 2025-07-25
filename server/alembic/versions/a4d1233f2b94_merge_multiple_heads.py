"""merge multiple heads

Revision ID: a4d1233f2b94
Revises: 002_downgrade_to_int, 002, 003_auth_enhancement
Create Date: 2025-07-25 11:54:14.782099

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4d1233f2b94'
down_revision = ('002_downgrade_to_int', '002', '003_auth_enhancement')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

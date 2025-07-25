"""
Downgrade UUID columns back to Integer columns for emergency rollback.

This migration provides a safe way to revert from UUID-based schema
back to the original Integer-based schema if issues arise.

Revision ID: 002_downgrade_to_int
Revises: 001
Create Date: 2025-07-23 04:30:00.000000
"""
import logging
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# Import our downgrade utility
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from bruno_ai_server.utils.downgrade_schema import SchemaDowngradeManager

# revision identifiers, used by Alembic.
revision = '002_downgrade_to_int'
down_revision = '001'
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade():
    """
    This migration only handles downgrade operations.
    The upgrade path should be handled by UUID upgrade migrations.
    """
    logger.warning("This migration is designed for downgrade only. Use UUID upgrade migrations for forward compatibility.")
    pass


def downgrade():
    """
    Execute complete downgrade from UUID to Integer schema.
    
    This operation:
    1. Backs up UUID data to a separate schema
    2. Drops UUID columns and constraints
    3. Restores original integer-based primary keys and foreign keys
    4. Validates the downgrade was successful
    """
    logger.info("Starting UUID to Integer schema downgrade migration...")
    
    try:
        # Use our comprehensive downgrade manager
        downgrade_manager = SchemaDowngradeManager()
        
        # Execute the full downgrade process
        success = downgrade_manager.execute_full_downgrade()
        
        if not success:
            raise Exception("Downgrade process failed - check logs for details")
        
        logger.info("UUID to Integer schema downgrade completed successfully")
        
    except Exception as e:
        logger.error(f"Error during schema downgrade: {e}")
        # Attempt to provide manual rollback instructions
        logger.error("""
        MANUAL ROLLBACK REQUIRED:
        
        If this migration fails, you may need to manually restore the schema.
        The following steps can help:
        
        1. Check the uuid_backup schema for backed up UUID data
        2. Restore integer primary keys if they were dropped
        3. Recreate foreign key constraints as needed
        4. Verify all tables have their expected integer ID columns
        
        Contact your database administrator for assistance.
        """)
        raise


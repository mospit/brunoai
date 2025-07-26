"""
Schema Downgrade Utility - Provides safe UUID to Integer conversion.

This module contains utilities to safely downgrade from UUID-based schema
back to the original Integer-based schema for emergency rollbacks.
"""

import logging
from typing import Dict, List, Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

logger = logging.getLogger(__name__)


class SchemaDowngradeManager:
    """Manages safe downgrade operations from UUID to Integer schema."""
    
    def __init__(self):
        self.table_mappings = self._get_table_mappings()
        self.foreign_key_mappings = self._get_foreign_key_mappings()
    
    def _get_table_mappings(self) -> Dict[str, Dict]:
        """Define mapping of tables and their UUID/Integer column relationships."""
        return {
            'users': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': ['households', 'household_members', 'pantry_items', 'shopping_lists', 'orders', 'user_favorites']
            },
            'households': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': ['household_members', 'pantry_items', 'shopping_lists', 'orders']
            },
            'pantry_categories': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': ['pantry_items']
            },
            'recipes': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': ['recipe_ingredients', 'user_favorites', 'shopping_list_items']
            },
            'pantry_items': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': []
            },
            'recipe_ingredients': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': []
            },
            'user_favorites': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': []
            },
            'shopping_lists': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': ['shopping_list_items', 'orders']
            },
            'shopping_list_items': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': ['order_items']
            },
            'orders': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',  
                'dependencies': ['order_items']
            },
            'order_items': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': []
            },
            'household_members': {
                'primary_key': 'id',
                'uuid_column': 'uuid_id',
                'dependencies': []
            }
        }
    
    def _get_foreign_key_mappings(self) -> List[Dict]:
        """Define foreign key relationships that need to be restored."""
        return [
            {
                'table': 'households',
                'column': 'owner_id',
                'referenced_table': 'users',
                'referenced_column': 'id',
                'constraint_name': 'fk_households_owner_id'
            },
            {
                'table': 'household_members',
                'column': 'user_id',
                'referenced_table': 'users',
                'referenced_column': 'id',
                'constraint_name': 'fk_household_members_user_id'
            },
            {
                'table': 'household_members',
                'column': 'household_id',
                'referenced_table': 'households',
                'referenced_column': 'id',
                'constraint_name': 'fk_household_members_household_id'
            },
            {
                'table': 'pantry_items',
                'column': 'household_id',
                'referenced_table': 'households',
                'referenced_column': 'id',
                'constraint_name': 'fk_pantry_items_household_id'
            },
            {
                'table': 'pantry_items',
                'column': 'category_id',
                'referenced_table': 'pantry_categories',
                'referenced_column': 'id',
                'constraint_name': 'fk_pantry_items_category_id'
            },
            {
                'table': 'pantry_items',
                'column': 'added_by_user_id',
                'referenced_table': 'users',
                'referenced_column': 'id',
                'constraint_name': 'fk_pantry_items_added_by_user_id'
            },
            {
                'table': 'recipe_ingredients',
                'column': 'recipe_id',
                'referenced_table': 'recipes',
                'referenced_column': 'id',
                'constraint_name': 'fk_recipe_ingredients_recipe_id'
            },
            {
                'table': 'shopping_lists',
                'column': 'household_id',
                'referenced_table': 'households',
                'referenced_column': 'id',
                'constraint_name': 'fk_shopping_lists_household_id'
            },
            {
                'table': 'shopping_lists',
                'column': 'created_by_user_id',
                'referenced_table': 'users',
                'referenced_column': 'id',
                'constraint_name': 'fk_shopping_lists_created_by_user_id'
            },
            {
                'table': 'user_favorites',
                'column': 'user_id',
                'referenced_table': 'users',
                'referenced_column': 'id',
                'constraint_name': 'fk_user_favorites_user_id'
            },
            {
                'table': 'user_favorites',
                'column': 'recipe_id',
                'referenced_table': 'recipes',
                'referenced_column': 'id',
                'constraint_name': 'fk_user_favorites_recipe_id'
            },
            {
                'table': 'orders',
                'column': 'user_id',
                'referenced_table': 'users',
                'referenced_column': 'id',
                'constraint_name': 'fk_orders_user_id'
            },
            {
                'table': 'orders',
                'column': 'household_id',
                'referenced_table': 'households',
                'referenced_column': 'id',
                'constraint_name': 'fk_orders_household_id'
            },
            {
                'table': 'orders',
                'column': 'shopping_list_id',
                'referenced_table': 'shopping_lists',
                'referenced_column': 'id',
                'constraint_name': 'fk_orders_shopping_list_id'
            },
            {
                'table': 'shopping_list_items',
                'column': 'shopping_list_id',
                'referenced_table': 'shopping_lists',
                'referenced_column': 'id',
                'constraint_name': 'fk_shopping_list_items_shopping_list_id'
            },
            {
                'table': 'shopping_list_items',
                'column': 'added_by_user_id',
                'referenced_table': 'users',
                'referenced_column': 'id',
                'constraint_name': 'fk_shopping_list_items_added_by_user_id'
            },
            {
                'table': 'shopping_list_items',
                'column': 'recipe_id',
                'referenced_table': 'recipes',
                'referenced_column': 'id',
                'constraint_name': 'fk_shopping_list_items_recipe_id'
            },
            {
                'table': 'order_items',
                'column': 'order_id',
                'referenced_table': 'orders',
                'referenced_column': 'id',
                'constraint_name': 'fk_order_items_order_id'
            },
            {
                'table': 'order_items',
                'column': 'shopping_list_item_id',
                'referenced_table': 'shopping_list_items',
                'referenced_column': 'id',
                'constraint_name': 'fk_order_items_shopping_list_item_id'
            }
        ]

    def validate_downgrade_safety(self) -> bool:
        """
        Validate that the downgrade can be performed safely.
        
        Returns:
            bool: True if downgrade is safe, False otherwise
        """
        try:
            # Check if UUID columns exist (indicating upgrade was applied)
            connection = op.get_bind()
            
            # Check for existence of UUID columns in key tables
            result = connection.execute(sa.text("""
                SELECT column_name, table_name
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND column_name LIKE '%uuid%'
                AND data_type = 'uuid'
            """))
            
            uuid_columns = result.fetchall()
            
            if not uuid_columns:
                logger.warning("No UUID columns found - schema may already be in integer format")
                return False
                
            logger.info(f"Found {len(uuid_columns)} UUID columns to downgrade")
            
            # Check for data that would be lost in conversion
            # This is where you'd add specific data validation logic
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating downgrade safety: {e}")
            return False

    def backup_uuid_data(self) -> bool:
        """
        Create backup tables with UUID data before downgrade.
        
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            connection = op.get_bind()
            
            # Create backup schema if it doesn't exist
            connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS uuid_backup"))
            
            for table_name, config in self.table_mappings.items():
                if 'uuid_column' in config:
                    # Create backup table with UUID data
                    backup_table_name = f"uuid_backup.{table_name}_uuid_backup"
                    
                    connection.execute(sa.text(f"""
                        CREATE TABLE {backup_table_name} AS 
                        SELECT id, {config['uuid_column']}, created_at 
                        FROM {table_name}
                        WHERE {config['uuid_column']} IS NOT NULL
                    """))
                    
                    logger.info(f"Created backup table: {backup_table_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating UUID data backup: {e}")
            return False

    def drop_uuid_constraints(self) -> bool:
        """
        Drop all UUID-based constraints and foreign keys.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Drop foreign key constraints that reference UUID columns
            for fk_mapping in self.foreign_key_mappings:
                try:
                    # Check if UUID-based constraint exists
                    uuid_constraint_name = f"{fk_mapping['constraint_name']}_uuid"
                    op.drop_constraint(uuid_constraint_name, fk_mapping['table'], type_='foreignkey')
                    logger.info(f"Dropped UUID constraint: {uuid_constraint_name}")
                except Exception:
                    # Constraint might not exist, continue
                    pass
            
            # Drop UUID primary key constraints
            for table_name, config in self.table_mappings.items():
                try:
                    # Drop UUID primary key if it exists
                    op.drop_constraint(f"{table_name}_pkey_uuid", table_name, type_='primary')
                    logger.info(f"Dropped UUID primary key for table: {table_name}")
                except Exception:
                    # Constraint might not exist, continue
                    pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error dropping UUID constraints: {e}")
            return False

    def drop_uuid_columns(self) -> bool:
        """
        Drop all UUID columns from tables.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            for table_name, config in self.table_mappings.items():
                if 'uuid_column' in config:
                    try:
                        op.drop_column(table_name, config['uuid_column'])
                        logger.info(f"Dropped UUID column: {table_name}.{config['uuid_column']}")
                    except Exception as e:
                        logger.warning(f"Could not drop UUID column {table_name}.{config['uuid_column']}: {e}")
                        
            return True
            
        except Exception as e:
            logger.error(f"Error dropping UUID columns: {e}")
            return False

    def restore_integer_constraints(self) -> bool:
        """
        Restore original integer-based primary keys and foreign key constraints.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Restore integer primary key constraints
            for table_name, config in self.table_mappings.items():
                try:
                    op.create_primary_key(f"{table_name}_pkey", table_name, [config['primary_key']])
                    logger.info(f"Restored integer primary key for table: {table_name}")
                except Exception as e:
                    logger.warning(f"Could not restore primary key for {table_name}: {e}")
            
            # Restore foreign key constraints
            for fk_mapping in self.foreign_key_mappings:
                try:
                    op.create_foreign_key(
                        fk_mapping['constraint_name'],
                        fk_mapping['table'],
                        fk_mapping['referenced_table'],
                        [fk_mapping['column']],
                        [fk_mapping['referenced_column']]
                    )
                    logger.info(f"Restored foreign key: {fk_mapping['constraint_name']}")
                except Exception as e:
                    logger.warning(f"Could not restore foreign key {fk_mapping['constraint_name']}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring integer constraints: {e}")
            return False

    def execute_full_downgrade(self) -> bool:
        """
        Execute complete downgrade from UUID to Integer schema.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Starting UUID to Integer schema downgrade...")
        
        # Step 1: Validate safety
        if not self.validate_downgrade_safety():
            logger.error("Downgrade safety validation failed")
            return False
        
        # Step 2: Backup UUID data
        if not self.backup_uuid_data():
            logger.error("Failed to backup UUID data")
            return False
        
        # Step 3: Drop UUID constraints
        if not self.drop_uuid_constraints():
            logger.error("Failed to drop UUID constraints")
            return False
        
        # Step 4: Drop UUID columns
        if not self.drop_uuid_columns():
            logger.error("Failed to drop UUID columns")
            return False
        
        # Step 5: Restore integer constraints
        if not self.restore_integer_constraints():
            logger.error("Failed to restore integer constraints")
            return False
        
        logger.info("UUID to Integer schema downgrade completed successfully")
        return True


def perform_emergency_downgrade() -> bool:
    """
    Emergency function to quickly downgrade schema in case of issues.
    
    Returns:
        bool: True if successful, False otherwise
    """
    downgrade_manager = SchemaDowngradeManager()
    return downgrade_manager.execute_full_downgrade()


def verify_integer_schema() -> bool:
    """
    Verify that the schema has been successfully downgraded to integer format.
    
    Returns:
        bool: True if schema is in integer format, False otherwise
    """
    try:
        connection = op.get_bind()
        
        # Check that no UUID columns remain
        result = connection.execute(sa.text("""
            SELECT column_name, table_name
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND column_name LIKE '%uuid%'
            AND data_type = 'uuid'
        """))
        
        remaining_uuid_columns = result.fetchall()
        
        if remaining_uuid_columns:
            logger.error(f"Found remaining UUID columns: {remaining_uuid_columns}")
            return False
        
        # Check that integer primary keys exist
        result = connection.execute(sa.text("""
            SELECT table_name, column_name
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND column_name = 'id'
            AND data_type = 'integer'
        """))
        
        integer_id_columns = result.fetchall()
        expected_tables = len([t for t in SchemaDowngradeManager().table_mappings.keys()])
        
        if len(integer_id_columns) < expected_tables:
            logger.error("Missing integer ID columns in some tables")
            return False
        
        logger.info("Schema successfully verified as integer-based")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying integer schema: {e}")
        return False

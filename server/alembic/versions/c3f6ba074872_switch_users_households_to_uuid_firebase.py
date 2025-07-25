"""switch users/households to UUID & firebase

Revision ID: c3f6ba074872
Revises: 001
Create Date: 2025-07-25 04:24:54.346644

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f6ba074872'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create UUID extension if it doesn't exist
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    
    # CLEAN BREAK STRATEGY: Drop and recreate tables with UUID primary keys
    # Since this is development environment with no production data to preserve
    
    # Step 1: Drop FK-dependent tables in reverse dependency order
    # Most dependent tables first, then their dependencies
    
    # Drop order_items (depends on orders, shopping_list_items)
    op.drop_table('order_items')
    
    # Drop orders (depends on users, households, shopping_lists)
    op.drop_table('orders')
    
    # Drop shopping_list_items (depends on shopping_lists, users, recipes)
    op.drop_table('shopping_list_items')
    
    # Drop shopping_lists (depends on households, users)
    op.drop_table('shopping_lists')
    
    # Drop user_favorites (depends on users, recipes)
    op.drop_table('user_favorites')
    
    # Drop pantry_items (depends on households, pantry_categories, users)
    op.drop_table('pantry_items')
    
    # Drop recipe_ingredients (depends on recipes)
    op.drop_table('recipe_ingredients')
    
    # Drop household_members (depends on users, households)
    op.drop_table('household_members')
    
    # Step 2: Drop core tables (households depends on users)
    op.drop_table('households')
    op.drop_table('users')
    
    # Step 3: Recreate core tables with UUID primary keys
    
    # Recreate users table with UUID PK and no hashed_password (Firebase auth)
    op.create_table('users',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), 
                 primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('dietary_preferences', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('voice_settings', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notification_preferences', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # Recreate households table with UUID PK and UUID FK to users
    op.create_table('households',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), 
                 primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('invite_code', sa.String(length=6), nullable=False),
        sa.Column('owner_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('settings', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.UniqueConstraint('invite_code')
    )
    op.create_index(op.f('ix_households_id'), 'households', ['id'], unique=False)
    op.create_index(op.f('ix_households_invite_code'), 'households', ['invite_code'], unique=True)
    
    # Step 4: Recreate dependent tables with UUID PKs and FKs
    
    # Recreate household_members with UUID references
    op.create_table('household_members',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), 
                 primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('household_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['household_id'], ['households.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id', 'household_id', name='unique_user_household')
    )
    op.create_index(op.f('ix_household_members_id'), 'household_members', ['id'], unique=False)
    
    # Recreate pantry_items with UUID references
    op.create_table('pantry_items',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), 
                 primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('barcode', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('expiration_date', sa.Date(), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('household_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),  # Keep Integer for pantry_categories
        sa.Column('added_by_user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_metadata', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['added_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['category_id'], ['pantry_categories.id']),
        sa.ForeignKeyConstraint(['household_id'], ['households.id'])
    )
    op.create_index(op.f('ix_pantry_items_barcode'), 'pantry_items', ['barcode'], unique=False)
    op.create_index(op.f('ix_pantry_items_id'), 'pantry_items', ['id'], unique=False)
    
    # Recreate recipe_ingredients with UUID reference to recipes
    op.create_table('recipe_ingredients',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), 
                 primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),  # Keep Integer for recipes
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('is_optional', sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'])
    )
    op.create_index(op.f('ix_recipe_ingredients_id'), 'recipe_ingredients', ['id'], unique=False)
    
    # Recreate shopping_lists with UUID references
    op.create_table('shopping_lists',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), 
                 primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('is_shared', sa.Boolean(), nullable=True),
        sa.Column('household_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('list_metadata', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['household_id'], ['households.id'])
    )
    op.create_index(op.f('ix_shopping_lists_id'), 'shopping_lists', ['id'], unique=False)
    
    # Recreate user_favorites with UUID user reference
    op.create_table('user_favorites',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), 
                 primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),  # Keep Integer for recipes
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id', 'recipe_id', name='unique_user_recipe_favorite')
    )
    op.create_index(op.f('ix_user_favorites_id'), 'user_favorites', ['id'], unique=False)
    
    # Recreate shopping_list_items with UUID references
    op.create_table('shopping_list_items',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), 
                 primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_purchased', sa.Boolean(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('estimated_price', sa.Float(), nullable=True),
        sa.Column('actual_price', sa.Float(), nullable=True),
        sa.Column('shopping_list_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_by_user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=True),  # Keep Integer for recipes
        sa.ForeignKeyConstraint(['added_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id']),
        sa.ForeignKeyConstraint(['shopping_list_id'], ['shopping_lists.id'])
    )
    op.create_index(op.f('ix_shopping_list_items_id'), 'shopping_list_items', ['id'], unique=False)
    
    # Recreate orders with UUID references
    op.create_table('orders',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), 
                 primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('external_order_id', sa.String(length=100), nullable=True),
        sa.Column('service_provider', sa.String(length=50), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=True),
        sa.Column('tax_amount', sa.Float(), nullable=True),
        sa.Column('delivery_fee', sa.Float(), nullable=True),
        sa.Column('tip_amount', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('estimated_delivery', sa.DateTime(), nullable=True),
        sa.Column('actual_delivery', sa.DateTime(), nullable=True),
        sa.Column('delivery_address', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('delivery_instructions', sa.Text(), nullable=True),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('household_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shopping_list_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('affiliate_tracking_id', sa.String(length=100), nullable=True),
        sa.Column('order_metadata', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['household_id'], ['households.id']),
        sa.ForeignKeyConstraint(['shopping_list_id'], ['shopping_lists.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('external_order_id')
    )
    op.create_index(op.f('ix_orders_external_order_id'), 'orders', ['external_order_id'], unique=True)
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    
    # Recreate order_items with UUID references
    op.create_table('order_items',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), 
                 primary_key=True, server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('total_price', sa.Float(), nullable=True),
        sa.Column('barcode', sa.String(length=50), nullable=True),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('size', sa.String(length=50), nullable=True),
        sa.Column('order_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shopping_list_item_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('external_item_data', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['shopping_list_item_id'], ['shopping_list_items.id'])
    )
    op.create_index(op.f('ix_order_items_id'), 'order_items', ['id'], unique=False)


def downgrade():
    # Mirror-reverse the upgrade() process:
    # 1. Drop all tables with UUID PKs in dependency order
    # 2. Recreate original integer-based tables
    # NOTE: This is a destructive operation that will lose all data
    
    # Step 1: Drop FK-dependent tables in reverse dependency order
    # Most dependent tables first, then their dependencies
    
    # Drop order_items (depends on orders, shopping_list_items)
    op.drop_table('order_items')
    
    # Drop orders (depends on users, households, shopping_lists)
    op.drop_table('orders')
    
    # Drop shopping_list_items (depends on shopping_lists, users, recipes)
    op.drop_table('shopping_list_items')
    
    # Drop shopping_lists (depends on households, users)
    op.drop_table('shopping_lists')
    
    # Drop user_favorites (depends on users, recipes)
    op.drop_table('user_favorites')
    
    # Drop pantry_items (depends on households, pantry_categories, users)
    op.drop_table('pantry_items')
    
    # Drop recipe_ingredients (depends on recipes)
    op.drop_table('recipe_ingredients')
    
    # Drop household_members (depends on users, households)
    op.drop_table('household_members')
    
    # Step 2: Drop core tables (households depends on users)
    op.drop_table('households')
    op.drop_table('users')
    
    # Step 3: Recreate original tables with integer primary keys
    
    # Recreate users table with integer PK and hashed_password (original auth)
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('dietary_preferences', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('voice_settings', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notification_preferences', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # Recreate households table with integer PK and integer FK to users
    op.create_table('households',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('invite_code', sa.String(length=6), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('settings', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.UniqueConstraint('invite_code')
    )
    op.create_index(op.f('ix_households_id'), 'households', ['id'], unique=False)
    op.create_index(op.f('ix_households_invite_code'), 'households', ['invite_code'], unique=True)
    
    # Step 4: Recreate dependent tables with integer PKs and FKs
    
    # Recreate household_members with integer references
    op.create_table('household_members',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('household_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['household_id'], ['households.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id', 'household_id', name='unique_user_household')
    )
    op.create_index(op.f('ix_household_members_id'), 'household_members', ['id'], unique=False)
    
    # Recreate pantry_items with integer references
    op.create_table('pantry_items',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('barcode', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('expiration_date', sa.Date(), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('household_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),  # Keep Integer for pantry_categories
        sa.Column('added_by_user_id', sa.Integer(), nullable=False),
        sa.Column('item_metadata', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['added_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['category_id'], ['pantry_categories.id']),
        sa.ForeignKeyConstraint(['household_id'], ['households.id'])
    )
    op.create_index(op.f('ix_pantry_items_barcode'), 'pantry_items', ['barcode'], unique=False)
    op.create_index(op.f('ix_pantry_items_id'), 'pantry_items', ['id'], unique=False)
    
    # Recreate recipe_ingredients with integer reference to recipes
    op.create_table('recipe_ingredients',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),  # Keep Integer for recipes
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('is_optional', sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'])
    )
    op.create_index(op.f('ix_recipe_ingredients_id'), 'recipe_ingredients', ['id'], unique=False)
    
    # Recreate shopping_lists with integer references
    op.create_table('shopping_lists',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('is_shared', sa.Boolean(), nullable=True),
        sa.Column('household_id', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('list_metadata', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['household_id'], ['households.id'])
    )
    op.create_index(op.f('ix_shopping_lists_id'), 'shopping_lists', ['id'], unique=False)
    
    # Recreate user_favorites with integer user reference
    op.create_table('user_favorites',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=False),  # Keep Integer for recipes
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id', 'recipe_id', name='unique_user_recipe_favorite')
    )
    op.create_index(op.f('ix_user_favorites_id'), 'user_favorites', ['id'], unique=False)
    
    # Recreate shopping_list_items with integer references
    op.create_table('shopping_list_items',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_purchased', sa.Boolean(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('estimated_price', sa.Float(), nullable=True),
        sa.Column('actual_price', sa.Float(), nullable=True),
        sa.Column('shopping_list_id', sa.Integer(), nullable=False),
        sa.Column('added_by_user_id', sa.Integer(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), nullable=True),  # Keep Integer for recipes
        sa.ForeignKeyConstraint(['added_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id']),
        sa.ForeignKeyConstraint(['shopping_list_id'], ['shopping_lists.id'])
    )
    op.create_index(op.f('ix_shopping_list_items_id'), 'shopping_list_items', ['id'], unique=False)
    
    # Recreate orders with integer references
    op.create_table('orders',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('external_order_id', sa.String(length=100), nullable=True),
        sa.Column('service_provider', sa.String(length=50), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=True),
        sa.Column('tax_amount', sa.Float(), nullable=True),
        sa.Column('delivery_fee', sa.Float(), nullable=True),
        sa.Column('tip_amount', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('estimated_delivery', sa.DateTime(), nullable=True),
        sa.Column('actual_delivery', sa.DateTime(), nullable=True),
        sa.Column('delivery_address', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('delivery_instructions', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('household_id', sa.Integer(), nullable=False),
        sa.Column('shopping_list_id', sa.Integer(), nullable=True),
        sa.Column('affiliate_tracking_id', sa.String(length=100), nullable=True),
        sa.Column('order_metadata', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['household_id'], ['households.id']),
        sa.ForeignKeyConstraint(['shopping_list_id'], ['shopping_lists.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('external_order_id')
    )
    op.create_index(op.f('ix_orders_external_order_id'), 'orders', ['external_order_id'], unique=True)
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    
    # Recreate order_items with integer references
    op.create_table('order_items',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('total_price', sa.Float(), nullable=True),
        sa.Column('barcode', sa.String(length=50), nullable=True),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('size', sa.String(length=50), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('shopping_list_item_id', sa.Integer(), nullable=True),
        sa.Column('external_item_data', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['shopping_list_item_id'], ['shopping_list_items.id'])
    )
    op.create_index(op.f('ix_order_items_id'), 'order_items', ['id'], unique=False)
    
    # Note: We don't drop the UUID extension as other migrations might depend on it
    # and it's safe to leave extensions in place

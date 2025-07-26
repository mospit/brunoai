-- Manual migration to create UUID-based schema
-- Based on c3f6ba074872_switch_users_households_to_uuid_firebase.py

-- Create UUID extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create alembic_version table to track migrations
CREATE TABLE alembic_version (
    version_num varchar(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Insert the current migration version
INSERT INTO alembic_version (version_num) VALUES ('c3f6ba074872');

-- Create pantry_categories table (not changed in UUID migration)
CREATE TABLE pantry_categories (
    id SERIAL PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    name varchar(100) NOT NULL UNIQUE,
    description text,
    icon varchar(50),
    color varchar(7)
);
CREATE INDEX ix_pantry_categories_id ON pantry_categories (id);

-- Create recipes table (not changed in UUID migration)
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    title varchar(255) NOT NULL,
    description text,
    instructions text NOT NULL,
    prep_time_minutes integer,
    cook_time_minutes integer,
    servings integer,
    difficulty_level varchar(20),
    nutrition_info jsonb,
    tags jsonb,
    cuisine_type varchar(100),
    external_source varchar(255),
    external_id varchar(100)
);
CREATE INDEX ix_recipes_id ON recipes (id);

-- Create users table with UUID PK and no hashed_password (Firebase auth)
CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    email varchar(255) NOT NULL UNIQUE,
    full_name varchar(255) NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    is_verified boolean NOT NULL DEFAULT false,
    dietary_preferences jsonb,
    voice_settings jsonb,
    notification_preferences jsonb
);
CREATE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_id ON users (id);

-- Create households table with UUID PK and UUID FK to users
CREATE TABLE households (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    name varchar(255) NOT NULL,
    invite_code varchar(6) NOT NULL UNIQUE,
    owner_id uuid NOT NULL REFERENCES users(id),
    settings jsonb
);
CREATE INDEX ix_households_id ON households (id);
CREATE INDEX ix_households_invite_code ON households (invite_code);

-- Create household_members with UUID references
CREATE TABLE household_members (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    user_id uuid NOT NULL REFERENCES users(id),
    household_id uuid NOT NULL REFERENCES households(id),
    role varchar(50) NOT NULL,
    joined_at timestamp NOT NULL,
    CONSTRAINT unique_user_household UNIQUE (user_id, household_id)
);
CREATE INDEX ix_household_members_id ON household_members (id);

-- Create pantry_items with UUID references
CREATE TABLE pantry_items (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    name varchar(255) NOT NULL,
    barcode varchar(50),
    quantity float NOT NULL,
    unit varchar(50),
    expiration_date date,
    purchase_date date,
    location varchar(100),
    notes text,
    household_id uuid NOT NULL REFERENCES households(id),
    category_id integer REFERENCES pantry_categories(id),
    added_by_user_id uuid NOT NULL REFERENCES users(id),
    item_metadata jsonb
);
CREATE INDEX ix_pantry_items_barcode ON pantry_items (barcode);
CREATE INDEX ix_pantry_items_id ON pantry_items (id);

-- Create recipe_ingredients with UUID reference to recipes
CREATE TABLE recipe_ingredients (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    recipe_id integer NOT NULL REFERENCES recipes(id),
    name varchar(255) NOT NULL,
    quantity float,
    unit varchar(50),
    notes varchar(255),
    is_optional varchar(10)
);
CREATE INDEX ix_recipe_ingredients_id ON recipe_ingredients (id);

-- Create shopping_lists with UUID references
CREATE TABLE shopping_lists (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    name varchar(255) NOT NULL,
    description text,
    status varchar(50),
    is_shared boolean,
    household_id uuid NOT NULL REFERENCES households(id),
    created_by_user_id uuid NOT NULL REFERENCES users(id),
    list_metadata jsonb
);
CREATE INDEX ix_shopping_lists_id ON shopping_lists (id);

-- Create user_favorites with UUID user reference
CREATE TABLE user_favorites (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    user_id uuid NOT NULL REFERENCES users(id),
    recipe_id integer NOT NULL REFERENCES recipes(id),
    rating integer,
    notes text,
    CONSTRAINT unique_user_recipe_favorite UNIQUE (user_id, recipe_id)
);
CREATE INDEX ix_user_favorites_id ON user_favorites (id);

-- Create shopping_list_items with UUID references
CREATE TABLE shopping_list_items (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    name varchar(255) NOT NULL,
    quantity float,
    unit varchar(50),
    notes text,
    is_purchased boolean,
    priority varchar(20),
    estimated_price float,
    actual_price float,
    shopping_list_id uuid NOT NULL REFERENCES shopping_lists(id),
    added_by_user_id uuid NOT NULL REFERENCES users(id),
    recipe_id integer REFERENCES recipes(id)
);
CREATE INDEX ix_shopping_list_items_id ON shopping_list_items (id);

-- Create orders with UUID references
CREATE TABLE orders (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    external_order_id varchar(100) UNIQUE,
    service_provider varchar(50),
    total_amount float,
    tax_amount float,
    delivery_fee float,
    tip_amount float,
    status varchar(50),
    estimated_delivery timestamp,
    actual_delivery timestamp,
    delivery_address jsonb,
    delivery_instructions text,
    user_id uuid NOT NULL REFERENCES users(id),
    household_id uuid NOT NULL REFERENCES households(id),
    shopping_list_id uuid REFERENCES shopping_lists(id),
    affiliate_tracking_id varchar(100),
    order_metadata jsonb
);
CREATE INDEX ix_orders_external_order_id ON orders (external_order_id);
CREATE INDEX ix_orders_id ON orders (id);

-- Create order_items with UUID references
CREATE TABLE order_items (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    name varchar(255) NOT NULL,
    quantity float NOT NULL,
    unit varchar(50),
    unit_price float,
    total_price float,
    barcode varchar(50),
    brand varchar(100),
    size varchar(50),
    order_id uuid NOT NULL REFERENCES orders(id),
    shopping_list_item_id uuid REFERENCES shopping_list_items(id),
    external_item_data jsonb
);
CREATE INDEX ix_order_items_id ON order_items (id);

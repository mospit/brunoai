#!/usr/bin/env python3
"""
Manually create tables for testing purposes - bypass Alembic for now
"""

from sqlalchemy import create_engine, text
from bruno_ai_server.config import settings

def main():
    """Create tables manually based on our models."""
    engine = create_engine(settings.db_url)
    
    with engine.connect() as conn:
        # Try to create UUID extension in a separate transaction
        try:
            with conn.begin():
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                print("UUID extension created/verified")
        except Exception as e:
            print(f"UUID extension creation failed (continuing): {e}")
            # Use gen_random_uuid() instead of uuid_generate_v4() from uuid-ossp
        
        # Start main transaction for table creation
        with conn.begin():
            
            # Create households table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS households (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    admin_user_id UUID NOT NULL,
                    invite_code VARCHAR(8) NOT NULL UNIQUE,
                    settings JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """))
            print("Households table created")
            
            # Create users table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    firebase_uid VARCHAR(128) UNIQUE,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
                    dietary_preferences JSONB DEFAULT '{}',
                    voice_settings JSONB DEFAULT '{}',
                    notification_preferences JSONB DEFAULT '{}',
                    household_id UUID REFERENCES households(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """))
            print("Users table created")
            
            # Create household_members table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS household_members (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    household_id UUID NOT NULL REFERENCES households(id),
                    role VARCHAR(50) DEFAULT 'member' NOT NULL,
                    joined_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, household_id)
                );
            """))
            print("Household members table created")
            
            # Create pantry_categories table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pantry_categories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    icon VARCHAR(50),
                    color VARCHAR(7),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """))
            print("Pantry categories table created")
            
            # Create pantry_items table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pantry_items (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    barcode VARCHAR(50),
                    quantity FLOAT DEFAULT 1.0 NOT NULL,
                    unit VARCHAR(50) DEFAULT 'piece',
                    expiration_date DATE,
                    purchase_date DATE DEFAULT CURRENT_DATE,
                    location VARCHAR(100),
                    notes TEXT,
                    household_id UUID NOT NULL REFERENCES households(id),
                    category_id UUID REFERENCES pantry_categories(id),
                    added_by_user_id UUID NOT NULL REFERENCES users(id),
                    item_metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """))
            print("Pantry items table created")
            
            # Create indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_households_invite_code ON households(invite_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pantry_items_barcode ON pantry_items(barcode);"))
            print("Indexes created")
            
            # Add foreign key constraint from households to users (admin)
            try:
                conn.execute(text("""
                    ALTER TABLE households 
                    ADD CONSTRAINT fk_admin_user 
                    FOREIGN KEY (admin_user_id) REFERENCES users(id) 
                    ON DELETE RESTRICT;
                """))
                print("Admin user foreign key constraint added")
            except Exception as e:
                print(f"Admin user foreign key constraint may already exist: {e}")
            
            # Create alembic_version table and set current version
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                );
            """))
            
            # Set the current version (use the head version from our migrations)
            current_version = "85f2a8c1d6e7"  # From the alembic history output
            conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{current_version}') ON CONFLICT DO NOTHING;"))
            print(f"Alembic version table created with version {current_version}")
            
            print("All tables created successfully!")
        
if __name__ == "__main__":
    main()

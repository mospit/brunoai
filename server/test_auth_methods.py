import asyncio
import asyncpg

async def test_auth_methods():
    print("Testing different authentication methods...")
    
    # Method 1: Try postgres with no password
    try:
        conn = await asyncpg.connect("postgresql://postgres@127.0.0.1:5432/postgres")
        print("✓ Connected as postgres with no password!")
        await conn.close()
        return "postgresql://postgres@127.0.0.1:5432/postgres"
    except Exception as e:
        print(f"✗ postgres with no password failed: {e}")
    
    # Method 2: Try postgres with empty password
    try:
        conn = await asyncpg.connect("postgresql://postgres:@127.0.0.1:5432/postgres")
        print("✓ Connected as postgres with empty password!")
        await conn.close()
        return "postgresql://postgres:@127.0.0.1:5432/postgres"
    except Exception as e:
        print(f"✗ postgres with empty password failed: {e}")
    
    # Method 3: Try with common default passwords
    common_passwords = ["postgres", "admin", "password", "123456"]
    for pwd in common_passwords:
        try:
            conn = await asyncpg.connect(f"postgresql://postgres:{pwd}@127.0.0.1:5432/postgres")
            print(f"✓ Connected as postgres with password '{pwd}'!")
            await conn.close()
            return f"postgresql://postgres:{pwd}@127.0.0.1:5432/postgres"
        except Exception as e:
            print(f"✗ postgres with password '{pwd}' failed: {e}")
    
    print("\n❌ All authentication methods failed.")
    print("You'll need to either:")
    print("1. Remember your postgres password set during installation")
    print("2. Reset the postgres password using pgAdmin or command line")
    print("3. Use integrated Windows authentication if available")
    return None

async def setup_database(working_connection_string):
    if not working_connection_string:
        return False
        
    try:
        conn = await asyncpg.connect(working_connection_string)
        print("\n🔧 Setting up database and user...")
        
        # Check if user 'user' exists
        result = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = 'user'")
        if not result:
            print("Creating user 'user'...")
            await conn.execute("CREATE USER \"user\" WITH PASSWORD 'Mc@042094' CREATEDB")
            print("✓ User 'user' created successfully!")
        else:
            print("✓ User 'user' already exists")
            # Update password just in case
            await conn.execute("ALTER USER \"user\" WITH PASSWORD 'Mc@042094'")
            print("✓ Password updated for user 'user'")
        
        # Check if bruno_db exists
        result = await conn.fetch("SELECT datname FROM pg_database WHERE datname = 'bruno_db'")
        if not result:
            print("Creating bruno_db database...")
            await conn.execute("CREATE DATABASE bruno_db OWNER \"user\"")
            print("✓ bruno_db database created successfully!")
        else:
            print("✓ bruno_db database already exists")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False

async def main():
    working_connection = await test_auth_methods()
    if working_connection:
        success = await setup_database(working_connection)
        if success:
            print("\n🎉 Database setup completed!")
            print("You can now test your application's database connection.")
        else:
            print("\n❌ Database setup failed.")
    else:
        print("\n❌ Could not establish connection to PostgreSQL.")
        print("Please check your PostgreSQL installation and credentials.")

if __name__ == "__main__":
    asyncio.run(main())

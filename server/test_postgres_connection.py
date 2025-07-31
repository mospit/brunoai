import asyncio
import asyncpg

async def test_postgres_connection():
    # Try connecting to the default postgres database with your credentials
    try:
        conn = await asyncpg.connect("postgresql://user:Mc%40042094@127.0.0.1:5432/postgres")
        print("✓ Connected to postgres database successfully!")
        
        # Check if bruno_db exists
        result = await conn.fetch("SELECT datname FROM pg_database WHERE datname = 'bruno_db'")
        if result:
            print("✓ bruno_db database exists")
        else:
            print("✗ bruno_db database does not exist")
            print("Creating bruno_db database...")
            await conn.execute("CREATE DATABASE bruno_db")
            print("✓ bruno_db database created successfully!")
        
        await conn.close()
        
    except Exception as e:
        print(f"✗ Connection to postgres database failed: {e}")
        print("This suggests the user 'user' doesn't exist or password is incorrect")
        
        # Try with postgres superuser (you'll need to enter password)
        print("\nTrying to connect as postgres superuser...")
        try:
            # This might prompt for password
            conn = await asyncpg.connect("postgresql://postgres@127.0.0.1:5432/postgres")
            print("✓ Connected as postgres superuser!")
            
            # Check if user 'user' exists and create if not
            result = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = 'user'")
            if not result:
                print("Creating user 'user'...")
                await conn.execute("CREATE USER \"user\" WITH PASSWORD 'Mc@042094'")
                print("✓ User 'user' created successfully!")
            else:
                print("✓ User 'user' already exists")
                # Try to update password
                await conn.execute("ALTER USER \"user\" WITH PASSWORD 'Mc@042094'")
                print("✓ Password updated for user 'user'")
            
            # Check if bruno_db exists and create if not
            result = await conn.fetch("SELECT datname FROM pg_database WHERE datname = 'bruno_db'")
            if not result:
                print("Creating bruno_db database...")
                await conn.execute("CREATE DATABASE bruno_db OWNER \"user\"")
                print("✓ bruno_db database created successfully!")
            else:
                print("✓ bruno_db database already exists")
            
            await conn.close()
            
        except Exception as e2:
            print(f"✗ Connection as postgres superuser also failed: {e2}")
            print("You may need to:")
            print("1. Check your PostgreSQL installation")
            print("2. Set up the postgres superuser password")
            print("3. Create the 'user' user manually")

if __name__ == "__main__":
    asyncio.run(test_postgres_connection())

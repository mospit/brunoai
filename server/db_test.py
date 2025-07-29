import asyncio
import asyncpg
import os
from bruno_ai_server.config import settings

async def test_connection():
    print(f"Testing connection to: {settings.db_url}")
    
    # Extract components from DB URL
    db_url = settings.db_url
    print(f"DB URL: {db_url}")
    
    try:
        # Try to connect using asyncpg directly
        conn = await asyncpg.connect(db_url)
        print("✓ Connection successful!")
        
        # Try to run a simple query
        result = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL version: {result}")
        
        await conn.close()
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Try to diagnose the issue
        if "getaddrinfo failed" in str(e):
            print("This suggests a DNS resolution issue with 'localhost'")
            print("Try using 127.0.0.1 instead of localhost")
        elif "password authentication failed" in str(e):
            print("The username/password combination is incorrect")
        elif "database" in str(e).lower() and "does not exist" in str(e).lower():
            print("The database 'bruno_db' does not exist")

if __name__ == "__main__":
    asyncio.run(test_connection())

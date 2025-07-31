#!/usr/bin/env python3
"""
Test table creation with current permissions.
"""

import asyncio
from bruno_ai_server.database import get_async_session
from sqlalchemy import text

async def test_create_table():
    async for session in get_async_session():
        try:
            # Try to create a simple test table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100)
                );
            """))
            await session.commit()
            print("Successfully created test table")
            
            # Clean up
            await session.execute(text("DROP TABLE IF EXISTS test_table;"))
            await session.commit()
            print("Cleaned up test table")
            
        except Exception as e:
            print(f"Error creating table: {e}")
        break

if __name__ == "__main__":
    asyncio.run(test_create_table())

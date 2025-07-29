#!/usr/bin/env python3
"""
Check database status and tables.
"""

import asyncio
from bruno_ai_server.database import get_async_session
from sqlalchemy import text

async def check_tables():
    async for session in get_async_session():
        try:
            result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
            tables = result.fetchall()
            print('Tables in database:')
            for table in tables:
                print(f'  - {table[0]}')
            
            # Check if users table exists and its structure
            try:
                result = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position"))
                columns = result.fetchall()
                if columns:
                    print('\nUsers table structure:')
                    for column in columns:
                        print(f'  - {column[0]}: {column[1]}')
                else:
                    print('\nUsers table does not exist')
            except Exception as e:
                print(f'Error checking users table: {e}')
                
        except Exception as e:
            print(f'Error connecting to database: {e}')
        break

if __name__ == "__main__":
    asyncio.run(check_tables())

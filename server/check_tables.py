import asyncio
from sqlalchemy import text
from bruno_ai_server.database import get_async_session

async def check_tables():
    async for session in get_async_session():
        result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        print("Tables in database:", tables)
        
        if 'users' in tables:
            user_columns = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'"))
            print("Users table columns:")
            for row in user_columns:
                print(f"  {row[0]}: {row[1]}")
        
        if 'households' in tables:
            household_columns = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'households'"))
            print("Households table columns:")
            for row in household_columns:
                print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    asyncio.run(check_tables())

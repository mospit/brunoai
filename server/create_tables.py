import asyncio
from bruno_ai_server.database import create_tables

async def main():
    print("Creating database tables...")
    try:
        await create_tables()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

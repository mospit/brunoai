#!/usr/bin/env python3
"""
Debug script to identify the actual registration error by examining server logs.

This helps understand what's causing the 500 Internal Server Error during registration.
"""

import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

async def test_registration_directly():
    """Test registration by calling the endpoint function directly."""
    print("=" * 60)
    print("DIRECT REGISTRATION TEST - BYPASSING SERVER")
    print("=" * 60)
    
    try:
        from bruno_ai_server.routes.auth import register_user
        from bruno_ai_server.schemas import UserCreate
        from bruno_ai_server.database import get_async_session
        from bruno_ai_server.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from bruno_ai_server.database import Base
        
        print("✅ Successfully imported required modules")
        
        # Create test database
        TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
        
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=True,  # Show SQL queries
        )
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        print("✅ Database tables created")
        
        # Create session
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            print("✅ Database session created")
            
            # Create registration request
            registration_data = UserCreate(
                email="debug-test@example.com",
                name="Debug Test User",
                password="ValidPassword123"
            )
            
            print(f"Testing registration with data: {registration_data.dict()}")
            
            try:
                # Call the registration function directly
                result = await register_user(registration_data, session)
                
                print("✅ SUCCESS: Registration worked when called directly!")
                print(f"Result: {result}")
                
                print("\n🔍 CONCLUSION: The issue is likely in middleware or server setup, not the core registration logic")
                
            except Exception as e:
                print(f"❌ FAILURE: Registration failed with error: {e}")
                print(f"Error type: {type(e).__name__}")
                
                # Print detailed traceback
                import traceback
                print("\nDetailed traceback:")
                traceback.print_exc()
                
                print("\n🔍 CONCLUSION: The issue is in the core registration logic")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Cannot import required modules. Check if all dependencies are available.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

async def test_with_mock_firebase():
    """Test registration with mock Firebase service."""
    print("\n" + "=" * 60)
    print("REGISTRATION TEST WITH MOCK FIREBASE")
    print("=" * 60)
    
    try:
        from bruno_ai_server.routes.auth import register_user
        from bruno_ai_server.schemas import UserCreate
        from bruno_ai_server.database import get_async_session
        from bruno_ai_server.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from bruno_ai_server.database import Base
        from unittest.mock import patch, AsyncMock
        
        # Create test database
        TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
        
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,  # Reduce noise
        )
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # Create session
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Mock Firebase service
            mock_firebase = AsyncMock()
            mock_firebase.create_user.return_value = "mock_firebase_uid_123"
            mock_firebase.is_initialized.return_value = True
            
            # Create registration request
            registration_data = UserCreate(
                email="mock-firebase-test@example.com",
                name="Mock Firebase Test User",
                password="ValidPassword123"
            )
            
            print(f"Testing registration with data: {registration_data.dict()}")
            
            # Patch Firebase service
            with patch('bruno_ai_server.routes.auth.firebase_service', mock_firebase):
                try:
                    result = await register_user(registration_data, session)
                    
                    print("✅ SUCCESS: Registration worked with mock Firebase!")
                    print(f"Result: {result}")
                    
                    # Verify Firebase was called
                    mock_firebase.create_user.assert_called_once()
                    print("✅ Mock Firebase service was called correctly")
                    
                except Exception as e:
                    print(f"❌ FAILURE: Registration failed with mock Firebase: {e}")
                    import traceback
                    traceback.print_exc()
                    
    except Exception as e:
        print(f"❌ Error in mock Firebase test: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests."""
    await test_registration_directly()
    await test_with_mock_firebase()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("If registration worked in direct tests but fails via HTTP:")
    print("- The issue is likely in middleware, server setup, or HTTP handling")
    print("- AuthenticationMiddleware path matching could still be the culprit")
    print()
    print("If registration failed in direct tests:")
    print("- The issue is in the core registration logic (database, Firebase, etc.)")
    print("- Middleware is not the problem")

if __name__ == "__main__":
    asyncio.run(main())

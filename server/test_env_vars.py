#!/usr/bin/env python3
"""
Test script to verify environment variable loading and database connectivity.
"""

import sys
from pathlib import Path

# Add the current directory to the path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

def test_env_loading():
    """Test that environment variables are properly loaded via Pydantic Settings."""
    print("=" * 60)
    print("TESTING ENVIRONMENT VARIABLE LOADING")
    print("=" * 60)
    
    try:
        from bruno_ai_server.config import settings
        print("✅ Successfully imported settings from config")
        
        # Test JWT_SECRET
        print(f"\n🔑 JWT_SECRET:")
        jwt_secret = settings.jwt_secret
        if jwt_secret and jwt_secret.strip():
            print(f"   ✅ JWT_SECRET is loaded and non-empty (length: {len(jwt_secret)})")
            # Don't print the actual secret for security
            print(f"   📝 First 10 chars: {jwt_secret[:10]}...")
        else:
            print("   ❌ JWT_SECRET is empty or not loaded!")
            return False
            
        # Test DB_URL
        print(f"\n🗄️  DB_URL:")
        db_url = settings.db_url
        if db_url and db_url.strip():
            print(f"   ✅ DB_URL is loaded and non-empty")
            # Parse and display connection info (masking password)
            try:
                from sqlalchemy.engine.url import make_url
                parsed_url = make_url(db_url)
                print(f"   📝 Database: {parsed_url.database}")
                print(f"   📝 Host: {parsed_url.host}")
                print(f"   📝 Port: {parsed_url.port}")
                print(f"   📝 Username: {parsed_url.username}")
                print(f"   📝 Password: {'*' * len(str(parsed_url.password)) if parsed_url.password else 'None'}")
            except Exception as e:
                print(f"   ⚠️  Could not parse DB_URL: {e}")
        else:
            print("   ❌ DB_URL is empty or not loaded!")
            return False
            
        # Test other important settings
        print(f"\n⚙️  Other Settings:")
        print(f"   📝 Environment: {settings.environment}")
        print(f"   📝 Debug mode: {settings.debug}")
        print(f"   📝 Host: {settings.host}")
        print(f"   📝 Port: {settings.port}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return False

def test_db_connectivity():
    """Test database connectivity using a simple query."""
    print("\n" + "=" * 60)
    print("TESTING DATABASE CONNECTIVITY")
    print("=" * 60)
    
    try:
        from bruno_ai_server.config import settings
        from sqlalchemy import create_engine, text
        
        print("🔗 Creating database engine...")
        engine = create_engine(settings.db_url)
        
        print("🔗 Testing database connection...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test_value"))
            test_row = result.fetchone()
            print(f"   ✅ Database connection successful! Test query returned: {test_row[0]}")
            
            # Test version query
            result = connection.execute(text("SELECT version()"))
            version_row = result.fetchone()
            print(f"   📝 PostgreSQL version: {version_row[0].split(' ')[0:2]}")
            
            # Test if we can query basic database info
            result = connection.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            print(f"   📝 Connected to database: {db_info[0]} as user: {db_info[1]}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   💡 Make sure PostgreSQL is running and the database exists")
        return False

def test_alembic_connectivity():
    """Test if Alembic can connect to the database."""
    print("\n" + "=" * 60)
    print("TESTING ALEMBIC CONNECTIVITY")
    print("=" * 60)
    
    try:
        from alembic.config import Config
        from alembic import command
        import io
        
        print("🔗 Testing Alembic configuration...")
        
        # Create Alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Capture output
        output = io.StringIO()
        
        # Test current revision
        try:
            command.current(alembic_cfg, verbose=True)
            print("   ✅ Alembic can connect to database")
            
            # Get revision history (just to test connectivity)
            command.history(alembic_cfg, verbose=False)
            print("   ✅ Alembic can read migration history")
            
        except Exception as e:
            print(f"   ⚠️  Alembic connectivity issue: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Alembic test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Environment Variable and Database Connectivity Test")
    print("🎯 Step 5: Check environment variable loading (JWT_SECRET, DB_URL)")
    
    success_count = 0
    total_tests = 3
    
    # Test environment variable loading
    if test_env_loading():
        success_count += 1
    
    # Test database connectivity
    if test_db_connectivity():
        success_count += 1
        
    # Test Alembic connectivity
    if test_alembic_connectivity():
        success_count += 1
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Environment variables are loaded correctly and database is accessible.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

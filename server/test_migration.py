#!/usr/bin/env python
"""
Test script to validate the Alembic migration setup.
This script will check if the migration can be loaded without actual database connection.
"""

import sys
from pathlib import Path

# Add the current directory to the Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Test imports
    from alembic.config import Config
    from bruno_ai_server.models import *  # noqa: F401, F403
    from bruno_ai_server.models.base import Base

    print("✅ All model imports successful")

    # Test that Base has the expected metadata
    tables = list(Base.metadata.tables.keys())
    print(f"✅ Found {len(tables)} tables in metadata:")
    for table in sorted(tables):
        print(f"   - {table}")

    # Test that alembic config can be loaded
    alembic_cfg = Config("alembic.ini")
    print("✅ Alembic configuration loaded successfully")

    # Check that migration file exists
    migration_file = Path("alembic/versions/001_initial_database_schema.py")
    if migration_file.exists():
        print("✅ Initial migration file exists")
    else:
        print("❌ Initial migration file not found")
        sys.exit(1)

    print("\n🎉 All validation checks passed!")
    print("The database schema and migration setup is ready.")
    print("\nTo apply migrations when PostgreSQL is running:")
    print("1. Start PostgreSQL: docker-compose -f ../infra/docker-compose.yml up -d")
    print("2. Run migration: py -m alembic upgrade head")

except Exception as e:
    print(f"❌ Error during validation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

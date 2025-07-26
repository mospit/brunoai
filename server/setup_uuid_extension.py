#!/usr/bin/env python3
"""
Script to set up UUID extension and check database status
"""

from sqlalchemy import create_engine, text
from bruno_ai_server.config import settings

def main():
    engine = create_engine(settings.db_url)
    with engine.connect() as conn:
        try:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            conn.commit()
            print('UUID extension created successfully')
        except Exception as e:
            print(f'Extension creation failed (this may be expected): {e}')
            
        # Check if extension exists
        result = conn.execute(text('SELECT 1 FROM pg_extension WHERE extname = \'uuid-ossp\''))
        if result.scalar():
            print('UUID extension is available')
        else:
            print('UUID extension is not available - continuing without it')
            
        # Check if alembic_version table exists
        result = conn.execute(text("""
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'alembic_version'
        """))
        if result.scalar():
            print('Alembic version table exists')
            version_result = conn.execute(text('SELECT version_num FROM alembic_version'))
            current_version = version_result.scalar()
            print(f'Current migration version: {current_version}')
        else:
            print('Alembic version table does not exist - database not initialized')

if __name__ == "__main__":
    main()

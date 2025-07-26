#!/usr/bin/env python3
"""
Check if pantry tables exist in the database
"""

from sqlalchemy import create_engine, text
from bruno_ai_server.config import settings

def main():
    config = settings
    engine = create_engine(config.db_url)

    with engine.connect() as conn:
        # Check if pantry_items table exists
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%pantry%';
        """))
        
        tables = result.fetchall()
        print('Pantry-related tables:')
        for table in tables:
            print(f'  - {table[0]}')
            
        if not tables:
            print('No pantry tables found. Need to create migration.')
        else:
            # Check pantry_items table structure
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'pantry_items'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            if columns:
                print('\npantry_items table structure:')
                for col in columns:
                    print(f'  - {col[0]}: {col[1]} (nullable: {col[2]})')

if __name__ == "__main__":
    main()

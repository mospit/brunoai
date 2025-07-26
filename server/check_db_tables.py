#!/usr/bin/env python3
"""
Check what tables exist in the database
"""

from sqlalchemy import create_engine, text
from bruno_ai_server.config import settings

def main():
    engine = create_engine(settings.db_url)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = result.fetchall()
        print('Existing tables:')
        for table in tables:
            print(f'  - {table[0]}')
            
        if not tables:
            print('No tables found in the public schema.')

if __name__ == "__main__":
    main()

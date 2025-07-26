#!/usr/bin/env python3
"""
Script to clean database tables and restore from backup
"""
from bruno_ai_server.config import settings
import subprocess
import os
from urllib.parse import urlparse

def clean_and_restore():
    # Parse the DB URL
    db_url = settings.db_url
    parsed = urlparse(db_url)

    # Set environment variables
    env = os.environ.copy()
    env['PGPASSWORD'] = parsed.password

    print('=== Cleaning all tables ===')

    # Get list of all tables
    result = subprocess.run([
        'psql',
        '-h', parsed.hostname,
        '-p', str(parsed.port),
        '-U', parsed.username,
        '-d', parsed.path[1:],
        '-t',  # tuples only
        '-c', "SELECT tablename FROM pg_tables WHERE schemaname='public';"
    ], env=env, capture_output=True, text=True)

    if result.returncode == 0:
        tables = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        print(f'Found tables: {tables}')
        
        # Drop all tables
        if tables:
            drop_tables_sql = 'DROP TABLE IF EXISTS ' + ', '.join(tables) + ' CASCADE;'
            result = subprocess.run([
                'psql',
                '-h', parsed.hostname,
                '-p', str(parsed.port),
                '-U', parsed.username,
                '-d', parsed.path[1:],
                '-c', drop_tables_sql
            ], env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print('✓ All tables dropped')
            else:
                print(f'Error dropping tables: {result.stderr}')
                return False
    else:
        print(f'Error getting table list: {result.stderr}')
        return False

    print('\n=== Restoring from backup ===')
    
    # Restore from backup
    result = subprocess.run([
        'psql',
        '-h', parsed.hostname,
        '-p', str(parsed.port),
        '-U', parsed.username,
        '-d', parsed.path[1:],
        '-f', 'backup_before_migration_20250725_115941.sql'
    ], env=env, capture_output=True, text=True)

    print(f'Restore exit code: {result.returncode}')
    if result.returncode == 0:
        print('✓ Database restored from backup successfully')
        return True
    else:
        print(f'✗ Error restoring database: {result.stderr[:500]}...')
        return False

if __name__ == "__main__":
    if clean_and_restore():
        print('\n✓ Database cleanup and restore completed successfully')
    else:
        print('\n✗ Database cleanup and restore failed')

#!/usr/bin/env python3
"""
Script to restore backup to bruno_db database
"""
from bruno_ai_server.config import settings
import subprocess
import os
from urllib.parse import urlparse

def restore_backup():
    # Parse the DB URL
    db_url = settings.db_url
    parsed = urlparse(db_url)

    env = os.environ.copy()
    env['PGPASSWORD'] = parsed.password

    print(f'=== Testing connection to {parsed.path[1:]} ===')

    # Test connection
    result = subprocess.run([
        'psql',
        '-h', parsed.hostname,
        '-p', str(parsed.port),
        '-U', parsed.username,
        '-d', parsed.path[1:],
        '-c', 'SELECT current_user, current_database();'
    ], env=env, capture_output=True, text=True)

    if result.returncode != 0:
        print(f'✗ Cannot connect: {result.stderr}')
        return False
    
    print('✓ Connected successfully')
    print(f'Connected as: {result.stdout.strip()}')

    print('\n=== Dropping existing tables ===')
    
    # Get list of tables and drop them
    result = subprocess.run([
        'psql',
        '-h', parsed.hostname,
        '-p', str(parsed.port),
        '-U', parsed.username,
        '-d', parsed.path[1:],
        '-t',
        '-c', "SELECT tablename FROM pg_tables WHERE schemaname='public';"
    ], env=env, capture_output=True, text=True)

    if result.returncode == 0:
        tables = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        print(f'Found tables: {tables}')
        
        if tables:
            # Drop all tables
            drop_sql = 'DROP TABLE IF EXISTS ' + ', '.join(tables) + ' CASCADE;'
            result = subprocess.run([
                'psql',
                '-h', parsed.hostname,
                '-p', str(parsed.port),
                '-U', parsed.username,
                '-d', parsed.path[1:],
                '-c', drop_sql
            ], env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print('✓ Tables dropped')
            else:
                print(f'✗ Error dropping tables: {result.stderr}')
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

    if result.returncode == 0:
        print('✓ Backup restored successfully')
        return True
    else:
        print(f'✗ Restore failed: {result.stderr[:500]}...')
        return False

if __name__ == "__main__":
    if restore_backup():
        print('\n✓ Database restore completed successfully')
    else:
        print('\n✗ Database restore failed')

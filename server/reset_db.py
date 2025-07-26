#!/usr/bin/env python3
"""
Script to completely reset the database and restore from backup
"""
from bruno_ai_server.config import settings
import subprocess
import os
from urllib.parse import urlparse

def reset_database():
    # Parse the DB URL
    db_url = settings.db_url
    parsed = urlparse(db_url)

    # Set environment variables
    env = os.environ.copy()
    env['PGPASSWORD'] = parsed.password

    print('=== Dropping and recreating database ===')

    # Drop database
    drop_result = subprocess.run([
        'psql',
        '-h', parsed.hostname,
        '-p', str(parsed.port),
        '-U', parsed.username,
        '-d', 'postgres',
        '-c', f'DROP DATABASE IF EXISTS "{parsed.path[1:]}";'
    ], env=env, capture_output=True, text=True)

    if drop_result.returncode != 0:
        print(f'Drop database error (continuing): {drop_result.stderr}')
    else:
        print('✓ Database dropped')

    # Create database
    result = subprocess.run([
        'psql',
        '-h', parsed.hostname,
        '-p', str(parsed.port),
        '-U', parsed.username,
        '-d', 'postgres',
        '-c', f'CREATE DATABASE "{parsed.path[1:]}";'
    ], env=env, capture_output=True, text=True)

    print(f'Drop/Create exit code: {result.returncode}')
    if result.returncode != 0:
        print(f'Error: {result.stderr}')
        return False
    else:
        print('✓ Database recreated successfully')

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
    if reset_database():
        print('\n✓ Database reset completed successfully')
    else:
        print('\n✗ Database reset failed')

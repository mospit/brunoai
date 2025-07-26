#!/usr/bin/env python3
"""
Temporary script to check database state
"""
from bruno_ai_server.config import settings
import subprocess
import os
from urllib.parse import urlparse

def run_sql_query(query):
    """Run a SQL query against the database"""
    # Parse the DB URL  
    db_url = settings.db_url
    parsed = urlparse(db_url)

    # Set environment variables for psql
    env = os.environ.copy()
    env['PGPASSWORD'] = parsed.password

    result = subprocess.run([
        'psql',
        '-h', parsed.hostname,
        '-p', str(parsed.port),
        '-U', parsed.username, 
        '-d', parsed.path[1:],  # Remove leading /
        '-c', query
    ], env=env, capture_output=True, text=True)

    return result

if __name__ == "__main__":
    # Check if refresh_tokens table exists
    print("=== Checking if refresh_tokens table exists ===")
    result = run_sql_query("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'refresh_tokens');")
    print(f'Exit code: {result.returncode}')
    print('STDOUT:')
    print(result.stdout)
    if result.stderr:
        print('STDERR:')
        print(result.stderr)
    
    print("\n=== Checking current alembic revision in database ===")
    result = run_sql_query("SELECT version_num FROM alembic_version;")
    print(f'Exit code: {result.returncode}')
    print('STDOUT:')
    print(result.stdout)
    if result.stderr:
        print('STDERR:')
        print(result.stderr)
    
    print("\n=== Checking users table schema ===")
    result = run_sql_query("\\d users")
    print(f'Exit code: {result.returncode}')
    print('STDOUT:')
    print(result.stdout)
    if result.stderr:
        print('STDERR:')
        print(result.stderr)
    
    print("\n=== Checking households table schema ===")
    result = run_sql_query("\\d households")
    print(f'Exit code: {result.returncode}')
    print('STDOUT:')
    print(result.stdout)
    if result.stderr:
        print('STDERR:')
        print(result.stderr)

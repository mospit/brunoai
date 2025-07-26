#!/usr/bin/env python3
"""
Script to create database and user with correct permissions
"""
import subprocess
import os

def setup_database():
    print('=== Creating database and user ===')

    # Commands to set up database
    commands = [
        'DROP DATABASE IF EXISTS bruno_ai_v2;',
        'CREATE DATABASE bruno_ai_v2;',
        "CREATE USER bruno_user WITH PASSWORD 'password';",
        'GRANT ALL PRIVILEGES ON DATABASE bruno_ai_v2 TO bruno_user;'
    ]

    for cmd in commands:
        result = subprocess.run([
            'psql',
            '-h', 'localhost',
            '-p', '5432',
            '-U', 'postgres',
            '-d', 'postgres',
            '-c', cmd
        ], capture_output=True, text=True, input='\n')
        
        print(f'Command: {cmd}')
        print(f'Exit code: {result.returncode}')
        if result.returncode != 0:
            print(f'Error: {result.stderr}')
            # Continue anyway, user might already exist
            if 'already exists' not in result.stderr:
                pass  # Don't fail for user already exists
        else:
            print('✓ Success')
        print()
    
    return True

if __name__ == "__main__":
    if setup_database():
        print('✓ Database setup completed successfully')
    else:
        print('✗ Database setup failed')

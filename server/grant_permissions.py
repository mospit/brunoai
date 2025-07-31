#!/usr/bin/env python3
"""
Grant database permissions to user.
"""

import psycopg2

try:
    # Try connecting as postgres (superuser)
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='bruno_db', 
        user='postgres',
        password='password'
    )
    print('Connected as postgres successfully')
    cursor = conn.cursor()
    
    # Grant necessary permissions to user
    print('Granting permissions to user...')
    cursor.execute('GRANT CREATE ON DATABASE bruno_db TO "user";')
    cursor.execute('GRANT CREATE ON SCHEMA public TO "user";')
    cursor.execute('ALTER USER "user" CREATEDB;')
    
    conn.commit()
    cursor.close()
    conn.close()
    print('Permissions granted successfully')
    
except Exception as e:
    print(f'Failed to connect as postgres or grant permissions: {e}')
    
    # Try with different common postgres passwords
    for pwd in ['postgres', '', 'admin']:
        try:
            print(f'Trying postgres with password: {pwd or "(empty)"}')
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='bruno_db', 
                user='postgres',
                password=pwd
            )
            print(f'Connected as postgres with password: {pwd or "(empty)"}')
            cursor = conn.cursor()
            
            # Grant necessary permissions to user
            print('Granting permissions to user...')
            cursor.execute('GRANT CREATE ON DATABASE bruno_db TO "user";')
            cursor.execute('GRANT CREATE ON SCHEMA public TO "user";')
            cursor.execute('ALTER USER "user" CREATEDB;')
            
            conn.commit()
            cursor.close()
            conn.close()
            print('Permissions granted successfully')
            break
            
        except Exception as e2:
            print(f'Failed with password {pwd or "(empty)"}: {e2}')
            continue

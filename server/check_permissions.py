#!/usr/bin/env python3
"""
Check database permissions.
"""

import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='bruno_db',
        user='user',
        password='password'
    )
    cursor = conn.cursor()
    
    # Check user identity
    cursor.execute("SELECT current_user, current_database();")
    user_info = cursor.fetchone()
    print(f'Connected as: {user_info[0]} to database: {user_info[1]}')
    
    # Check user privileges
    cursor.execute("""
        SELECT 
            has_database_privilege('bruno_db', 'CREATE') as can_create_db,
            has_schema_privilege('public', 'CREATE') as can_create_schema,
            has_schema_privilege('public', 'USAGE') as can_use_schema;
    """)
    
    result = cursor.fetchone()
    print(f'Database CREATE privilege: {result[0]}')
    print(f'Schema CREATE privilege: {result[1]}')  
    print(f'Schema USAGE privilege: {result[2]}')
    
    # Check if user is superuser
    cursor.execute("SELECT usesuper FROM pg_user WHERE usename = current_user;")
    is_super = cursor.fetchone()
    print(f'Is superuser: {is_super[0] if is_super else "No"}')
    
    cursor.close()
    conn.close()
        
except Exception as e:
    print(f'Error checking permissions: {e}')

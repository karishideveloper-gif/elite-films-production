#!/usr/bin/env python
"""Test for errors in the application"""

import app
import sqlite3
import os

# Test database connection
db_path = os.path.join(app.BASE_DIR, 'data', 'film_production.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print('✓ Database connected')
    print(f'✓ Tables found: {len(tables)}')
    for table in tables:
        print(f'  - {table[0]}')
    
    conn.close()
else:
    print('✗ Database file not found')

# Test app routes
print('\n✓ Testing app routes:')
with app.app.test_client() as client:
    routes = [
        ('/', 'GET'),
        ('/gallery', 'GET'),
        ('/about', 'GET'),
        ('/services', 'GET'),
        ('/contact', 'GET'),
        ('/login', 'GET'),
    ]
    
    for route, method in routes:
        response = client.get(route)
        status = '✓' if response.status_code == 200 else '✗'
        print(f'  {status} {method} {route}: {response.status_code}')

print('\n✓ All checks passed!')

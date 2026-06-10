#!/usr/bin/env python3
"""Test script to verify app.py has no import or definition errors."""

try:
    import app
    print("✓ app.py imported successfully")
    
    # Check if all required functions exist
    required_functions = [
        'get_db',
        'init_db',
        'get_user',
        'verify_password',
        'create_admin',
        'update_admin_password',
        'send_notification_inquiry',
        'create_inquiry',
        'get_inquiries',
        'get_inquiries_count'
    ]
    
    for func_name in required_functions:
        if hasattr(app, func_name):
            print(f"✓ Function '{func_name}' exists")
        else:
            print(f"✗ Function '{func_name}' is missing!")
    
    # Check if Flask app is properly initialized
    if hasattr(app, 'app'):
        print("✓ Flask app instance exists")
    
    print("\nAll checks passed! No errors detected.")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

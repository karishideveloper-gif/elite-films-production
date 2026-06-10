#!/usr/bin/env python
"""
Admin User Management Script
Easily add, remove, or change admin users for the Film Production app
"""

import sys
import os
from app import app, get_db, create_admin, update_admin_password, USE_POSTGRES

def list_admins():
    """List all admin users"""
    with app.app_context():
        db = get_db()
        if USE_POSTGRES:
            cur = db.cursor()
            cur.execute("SELECT id, username, created_at FROM admin_users ORDER BY created_at")
            admins = cur.fetchall()
            cur.close()
        else:
            admins = db.execute("SELECT id, username, created_at FROM admin_users ORDER BY created_at").fetchall()
        
        if not admins:
            print("❌ No admin users found")
            return
        
        print("\n📋 Current Admin Users:")
        print("-" * 50)
        for admin in admins:
            admin_id, username, created_at = admin
            print(f"  • {username} (ID: {admin_id}, Created: {created_at})")
        print()

def add_admin(username, password):
    """Add a new admin user"""
    with app.app_context():
        try:
            create_admin(username, password)
            print(f"✅ Admin user '{username}' created successfully")
        except Exception as e:
            print(f"❌ Error creating admin: {e}")

def change_password(username, new_password):
    """Change admin password"""
    with app.app_context():
        try:
            update_admin_password(username, new_password)
            print(f"✅ Password for '{username}' changed successfully")
        except Exception as e:
            print(f"❌ Error changing password: {e}")

def delete_admin(username):
    """Delete an admin user"""
    with app.app_context():
        db = get_db()
        try:
            if USE_POSTGRES:
                cur = db.cursor()
                cur.execute("DELETE FROM admin_users WHERE username = %s", (username,))
                if cur.rowcount == 0:
                    print(f"❌ Admin user '{username}' not found")
                    return
                db.commit()
                cur.close()
            else:
                cursor = db.execute("DELETE FROM admin_users WHERE username = ?", (username,))
                if cursor.rowcount == 0:
                    print(f"❌ Admin user '{username}' not found")
                    return
                db.commit()
            
            print(f"✅ Admin user '{username}' deleted successfully")
        except Exception as e:
            print(f"❌ Error deleting admin: {e}")

def main():
    if len(sys.argv) < 2:
        print("""
🎬 Film Production Admin Manager
================================

Usage:
  python manage_admins.py list              # List all admins
  python manage_admins.py add <username>    # Add new admin (prompts for password)
  python manage_admins.py password <username>  # Change admin password
  python manage_admins.py delete <username> # Delete admin user

Examples:
  python manage_admins.py list
  python manage_admins.py add client_admin
  python manage_admins.py password admin
  python manage_admins.py delete old_admin
        """)
        return

    command = sys.argv[1].lower()

    if command == 'list':
        list_admins()

    elif command == 'add':
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_admins.py add <username>")
            return
        username = sys.argv[2]
        password = input(f"Enter password for '{username}': ").strip()
        if not password:
            print("❌ Password cannot be empty")
            return
        confirm = input("Confirm password: ").strip()
        if password != confirm:
            print("❌ Passwords don't match")
            return
        add_admin(username, password)
        list_admins()

    elif command == 'password':
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_admins.py password <username>")
            return
        username = sys.argv[2]
        new_password = input(f"Enter new password for '{username}': ").strip()
        if not new_password:
            print("❌ Password cannot be empty")
            return
        confirm = input("Confirm password: ").strip()
        if new_password != confirm:
            print("❌ Passwords don't match")
            return
        change_password(username, new_password)

    elif command == 'delete':
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_admins.py delete <username>")
            return
        username = sys.argv[2]
        confirm = input(f"⚠️  Are you sure you want to delete '{username}'? (yes/no): ").strip().lower()
        if confirm == 'yes':
            delete_admin(username)
            list_admins()
        else:
            print("❌ Deletion cancelled")

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == '__main__':
    main()

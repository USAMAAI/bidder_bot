#!/usr/bin/env python3
"""
Promote user to admin or create new admin
"""

from src.database import get_all_users, promote_user_to_admin, create_user, ensure_db_exists
import sqlite3

def main():
    ensure_db_exists()
    
    # Get all users
    users = get_all_users()
    print(f"Found {len(users)} users:")
    
    for i, user in enumerate(users):
        admin_status = "👑 ADMIN" if user.get('is_admin') else "👤 USER"
        print(f"{i+1}. {user['username']} - {admin_status}")
    
    # Check if we already have an admin
    admin_users = [u for u in users if u.get('is_admin')]
    if admin_users:
        print(f"\n✅ Found {len(admin_users)} admin user(s):")
        for admin in admin_users:
            print(f"   👑 {admin['username']}")
        return
    
    # No admin users found, let's create one
    print("\n❌ No admin users found. Let's create one...")
    
    # Try to promote first user or create new one
    if users:
        first_user = users[0]
        print(f"Promoting '{first_user['username']}' to admin...")
        
        # First add the is_admin column if it doesn't exist
        try:
            conn = sqlite3.connect("./upwork_jobs.db")
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.commit()
            conn.close()
            print("✅ Added is_admin column")
        except:
            print("ℹ️ is_admin column already exists")
        
        # Now promote the user
        if promote_user_to_admin(first_user['user_id']):
            print(f"✅ {first_user['username']} is now an admin!")
        else:
            print(f"❌ Failed to promote {first_user['username']}")
    else:
        print("Creating new admin user 'admin'...")
        success, result = create_user("admin", "admin@example.com", "adminpass123")
        if success:
            # Make them admin
            promote_user_to_admin(result)
            print("✅ Admin user 'admin' created!")
        else:
            print(f"❌ Failed to create admin user: {result}")

if __name__ == "__main__":
    main() 
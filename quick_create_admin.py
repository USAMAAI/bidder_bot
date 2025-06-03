#!/usr/bin/env python3
"""
Quick Admin User Creation Script
"""

import sys
from src.database import ensure_db_exists, create_admin_user

def create_quick_admin(username, email, password):
    """Create admin user with provided credentials."""
    try:
        ensure_db_exists()
        print("✅ Database initialized")
        
        success, result = create_admin_user(username, email, password)
        
        if success:
            print(f"✅ Admin user '{username}' created successfully!")
            print(f"   User ID: {result}")
            print(f"   Email: {email}")
            print("\n🚀 You can now login to the app with admin privileges!")
            print("   Run: streamlit run app.py")
            return True
        else:
            print(f"❌ Failed to create admin user: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python quick_create_admin.py <username> <email> <password>")
        print("Example: python quick_create_admin.py admin admin@example.com adminpass123")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    if len(username) < 3:
        print("❌ Username must be at least 3 characters long")
        sys.exit(1)
    
    if "@" not in email:
        print("❌ Please provide a valid email address")
        sys.exit(1)
        
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        sys.exit(1)
    
    print(f"🔐 Creating admin user '{username}'...")
    create_quick_admin(username, email, password) 
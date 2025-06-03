#!/usr/bin/env python3
"""
Admin User Creation Script for Upwork AI Jobs Applier

This script allows you to create admin users who have full access to the system.
"""

import sys
import getpass
from src.database import (
    ensure_db_exists, create_admin_user, promote_user_to_admin,
    get_all_users, is_admin_user, authenticate_user
)

def create_new_admin():
    """Create a new admin user."""
    print("🔐 Creating New Admin User")
    print("=" * 40)
    
    # Get admin details
    username = input("Admin Username: ").strip()
    if len(username) < 3:
        print("❌ Username must be at least 3 characters long")
        return False
    
    email = input("Admin Email: ").strip()
    if "@" not in email:
        print("❌ Please enter a valid email address")
        return False
    
    # Get password securely
    password = getpass.getpass("Admin Password (min 8 chars): ")
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        return False
    
    confirm_password = getpass.getpass("Confirm Password: ")
    if password != confirm_password:
        print("❌ Passwords do not match")
        return False
    
    # Create admin user
    print("\n🔄 Creating admin user...")
    success, result = create_admin_user(username, email, password)
    
    if success:
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   User ID: {result}")
        print(f"\n🚀 You can now login to the application with admin privileges!")
        return True
    else:
        print(f"❌ Failed to create admin user: {result}")
        return False

def promote_existing_user():
    """Promote an existing user to admin."""
    print("⬆️  Promoting Existing User to Admin")
    print("=" * 40)
    
    # Get all users
    users = get_all_users()
    if not users:
        print("❌ No users found in the system")
        return False
    
    # Display users
    print("\nExisting Users:")
    for i, user in enumerate(users, 1):
        admin_status = "👑 ADMIN" if user.get('is_admin') else "👤 USER"
        active_status = "✅ Active" if user.get('is_active') else "❌ Inactive"
        print(f"{i:2d}. {user['username']:20s} | {user['email']:30s} | {admin_status} | {active_status}")
    
    # Get selection
    try:
        choice = int(input(f"\nSelect user to promote (1-{len(users)}): "))
        if choice < 1 or choice > len(users):
            print("❌ Invalid selection")
            return False
        
        selected_user = users[choice - 1]
        
        if selected_user.get('is_admin'):
            print(f"❌ {selected_user['username']} is already an admin")
            return False
        
        # Confirm promotion
        confirm = input(f"Promote '{selected_user['username']}' to admin? (y/N): ").lower()
        if confirm != 'y':
            print("❌ Promotion cancelled")
            return False
        
        # Promote user
        success = promote_user_to_admin(selected_user['user_id'])
        if success:
            print(f"✅ {selected_user['username']} has been promoted to admin!")
            return True
        else:
            print(f"❌ Failed to promote {selected_user['username']}")
            return False
            
    except ValueError:
        print("❌ Please enter a valid number")
        return False

def list_admin_users():
    """List all admin users in the system."""
    print("👑 Current Admin Users")
    print("=" * 40)
    
    users = get_all_users()
    admin_users = [user for user in users if user.get('is_admin')]
    
    if not admin_users:
        print("❌ No admin users found in the system")
        print("💡 You should create at least one admin user for system management")
        return
    
    print(f"\nFound {len(admin_users)} admin user(s):")
    for i, user in enumerate(admin_users, 1):
        active_status = "✅ Active" if user.get('is_active') else "❌ Inactive"
        created = user.get('created_at', 'Unknown')[:10] if user.get('created_at') else 'Unknown'
        last_login = user.get('last_login', 'Never')[:10] if user.get('last_login') else 'Never'
        
        print(f"{i:2d}. Username: {user['username']}")
        print(f"    Email: {user['email']}")
        print(f"    Status: {active_status}")
        print(f"    Created: {created}")
        print(f"    Last Login: {last_login}")
        print()

def verify_admin_access():
    """Verify admin access by testing login."""
    print("🔍 Verify Admin Access")
    print("=" * 40)
    
    username = input("Admin Username: ").strip()
    password = getpass.getpass("Admin Password: ")
    
    print("\n🔄 Verifying credentials...")
    success, user_data, message = authenticate_user(username, password)
    
    if success:
        if user_data.get('is_admin'):
            print(f"✅ Admin access verified for {user_data['username']}")
            print(f"   User ID: {user_data['user_id']}")
            print(f"   Email: {user_data['email']}")
            print(f"   Created: {user_data.get('created_at', 'Unknown')[:10]}")
            return True
        else:
            print(f"❌ User {username} exists but is not an admin")
            return False
    else:
        print(f"❌ Authentication failed: {message}")
        return False

def main():
    """Main admin creation interface."""
    print("🤖 Upwork AI Jobs Applier - Admin Management")
    print("=" * 50)
    
    # Initialize database
    try:
        ensure_db_exists()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
    
    while True:
        print("\n🛠️  Admin Management Options:")
        print("1. 🆕 Create New Admin User")
        print("2. ⬆️  Promote Existing User to Admin")
        print("3. 📋 List All Admin Users")
        print("4. 🔍 Verify Admin Access")
        print("5. 🚪 Exit")
        
        try:
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                create_new_admin()
            elif choice == '2':
                promote_existing_user()
            elif choice == '3':
                list_admin_users()
            elif choice == '4':
                verify_admin_access()
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Fix database and create admin user
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime

DB_PATH = "./upwork_jobs.db"

def hash_password(password: str) -> tuple:
    """Hash a password with a random salt."""
    salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return password_hash.hex(), salt

def generate_user_id(username: str) -> str:
    """Generate a unique user ID."""
    timestamp = datetime.now().isoformat()
    unique_string = f"{username}_{timestamp}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

def main():
    """Fix database and create admin user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table not found")
            return
        
        # Check current columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Add is_admin column if it doesn't exist
        if 'is_admin' not in columns:
            print("Adding is_admin column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            conn.commit()
            print("✅ is_admin column added")
        
        # Get existing users
        cursor.execute("SELECT user_id, username, email, is_admin FROM users")
        users = cursor.fetchall()
        print(f"\nFound {len(users)} users:")
        
        for user in users:
            admin_status = "👑 ADMIN" if user[3] else "👤 USER"
            print(f"- {user[1]} ({user[2]}) - {admin_status}")
        
        # Check if we have any admins
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        admin_count = cursor.fetchone()[0]
        
        if admin_count > 0:
            print(f"\n✅ Found {admin_count} admin user(s)")
            return
        
        # Create admin user
        print("\n🔐 Creating admin user 'zaeem'...")
        
        # Check if user already exists
        cursor.execute("SELECT user_id FROM users WHERE username = ? OR email = ?", ("zaeem", "zaeem.codrivity@gmail.com"))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Promote existing user
            print("User 'zaeem' exists, promoting to admin...")
            cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (existing_user[0],))
            conn.commit()
            print("✅ zaeem promoted to admin!")
        else:
            # Create new admin user
            password_hash, salt = hash_password("adminpass123")
            user_id = generate_user_id("zaeem")
            
            cursor.execute("""
            INSERT INTO users (user_id, username, email, password_hash, salt, is_admin)
            VALUES (?, ?, ?, ?, ?, 1)
            """, (user_id, "zaeem", "zaeem.codrivity@gmail.com", password_hash, salt))
            
            conn.commit()
            print(f"✅ Admin user 'zaeem' created successfully!")
            print(f"   User ID: {user_id}")
            print(f"   Username: zaeem")
            print(f"   Email: zaeem.codrivity@gmail.com")
            print(f"   Password: adminpass123")
        
        print("\n🚀 You can now login to the app with admin privileges!")
        print("   Run: streamlit run app.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 
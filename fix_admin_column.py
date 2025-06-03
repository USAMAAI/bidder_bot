#!/usr/bin/env python3
"""
Fix admin column in database
"""

import sqlite3

DB_PATH = "./upwork_jobs.db"

def fix_admin_column():
    """Add is_admin column to users table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check current table structure
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        print("Current columns:", columns)
        
        if 'is_admin' not in columns:
            print("Adding is_admin column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.commit()
            print("✅ is_admin column added successfully!")
        else:
            print("✅ is_admin column already exists")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        print("Updated columns:", columns)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_admin_column() 
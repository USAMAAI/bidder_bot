import sqlite3
import os
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = "./upwork_jobs.db"

def ensure_db_exists():
    """Ensure the database file and directory exist."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(DB_PATH):
        print("Creating new database...")
        create_tables()
    else:
        # Check if user tables exist, create if not
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check for users table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_exists = cursor.fetchone() is not None
        
        # Check for user_sessions table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'")
        sessions_exists = cursor.fetchone() is not None
        
        # Check for prompts table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompts'")
        prompts_exists = cursor.fetchone() is not None
        
        # Check if jobs table has user_id column
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        jobs_has_user_id = 'user_id' in columns
        
        conn.close()
        
        # Create missing tables or columns
        if not users_exists or not sessions_exists or not jobs_has_user_id or not prompts_exists:
            print("Upgrading database schema...")
            create_user_tables()

def create_tables():
    """Create the necessary tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        is_admin BOOLEAN DEFAULT 0,
        profile_data TEXT
    )
    ''')
    
    # Create sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # Create jobs table to match the scraper data structure (now with user_id)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT,
        link TEXT,
        job_type TEXT,
        experience_level TEXT,
        duration TEXT,
        payment_rate TEXT,
        score REAL,
        description TEXT,
        proposal_requirements TEXT,
        client_joined_date TEXT,
        client_location TEXT,
        client_total_spent TEXT,
        client_total_hires INTEGER,
        client_company_profile TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # Create prompts table for admin-managed prompts
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompts (
        prompt_id TEXT PRIMARY KEY,
        prompt_type TEXT NOT NULL,
        prompt_name TEXT NOT NULL,
        prompt_content TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        created_by TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users (user_id),
        UNIQUE(prompt_type)
    )
    ''')
    
    conn.commit()
    conn.close()

def create_user_tables():
    """Create user-related tables for existing database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            profile_data TEXT
        )
        ''')
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Add user_id column to existing jobs table if it doesn't exist
        try:
            # Check if user_id column exists
            cursor.execute("PRAGMA table_info(jobs)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'user_id' not in columns:
                print("Adding user_id column to jobs table...")
                cursor.execute("ALTER TABLE jobs ADD COLUMN user_id TEXT")
                
                # Set a default user_id for existing jobs
                cursor.execute("UPDATE jobs SET user_id = 'default_user' WHERE user_id IS NULL")
                print("Existing jobs assigned to 'default_user'")
        except sqlite3.OperationalError as e:
            # Column might already exist or other issue
            print(f"Note: Jobs table modification: {e}")
        
        # Add is_admin column to existing users table if it doesn't exist
        try:
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'is_admin' not in columns:
                print("Adding is_admin column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
                print("Admin column added to users table")
        except sqlite3.OperationalError as e:
            print(f"Note: Users table modification: {e}")
        
        # Create prompts table for admin-managed prompts
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            prompt_id TEXT PRIMARY KEY,
            prompt_type TEXT NOT NULL,
            prompt_name TEXT NOT NULL,
            prompt_content TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (user_id),
            UNIQUE(prompt_type)
        )
        ''')
        
        conn.commit()
        print("User authentication tables created successfully!")
        
    except Exception as e:
        print(f"Error creating user tables: {e}")
        conn.rollback()
    finally:
        conn.close()

def hash_password(password: str) -> tuple:
    """Hash a password with a random salt."""
    salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return password_hash.hex(), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify a password against its hash and salt."""
    computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return computed_hash.hex() == password_hash

def generate_user_id(username: str) -> str:
    """Generate a unique user ID."""
    timestamp = datetime.now().isoformat()
    unique_string = f"{username}_{timestamp}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

def generate_session_id() -> str:
    """Generate a unique session ID."""
    return secrets.token_urlsafe(32)

def create_user(username: str, email: str, password: str) -> tuple:
    """Create a new user account."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if username or email already exists
        cursor.execute("SELECT username FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone():
            conn.close()
            return False, "Username or email already exists"
        
        # Hash password
        password_hash, salt = hash_password(password)
        
        # Generate user ID
        user_id = generate_user_id(username)
        
        # Insert user
        cursor.execute('''
        INSERT INTO users (user_id, username, email, password_hash, salt)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, email, password_hash, salt))
        
        conn.commit()
        conn.close()
        return True, user_id
        
    except Exception as e:
        conn.close()
        return False, str(e)

def authenticate_user(username: str, password: str) -> tuple:
    """Authenticate a user with username/email and password."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find user by username or email
    cursor.execute('''
    SELECT * FROM users 
    WHERE (username = ? OR email = ?) AND is_active = 1
    ''', (username, username))
    
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return False, None, "Invalid username/email or password"
    
    # Verify password
    if verify_password(password, user['password_hash'], user['salt']):
        # Update last login
        update_last_login(user['user_id'])
        return True, dict(user), "Login successful"
    else:
        return False, None, "Invalid username/email or password"

def create_session(user_id: str, duration_hours: int = 24) -> str:
    """Create a new session for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    session_id = generate_session_id()
    expires_at = datetime.now() + timedelta(hours=duration_hours)
    
    cursor.execute('''
    INSERT INTO user_sessions (session_id, user_id, expires_at)
    VALUES (?, ?, ?)
    ''', (session_id, user_id, expires_at))
    
    conn.commit()
    conn.close()
    return session_id

def validate_session(session_id: str) -> tuple:
    """Validate a session and return user info if valid."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT s.*, u.* FROM user_sessions s
    JOIN users u ON s.user_id = u.user_id
    WHERE s.session_id = ? AND s.is_active = 1 AND s.expires_at > datetime('now')
    ''', (session_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return True, dict(result)
    else:
        return False, None

def invalidate_session(session_id: str) -> bool:
    """Invalidate a session (logout)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE user_sessions SET is_active = 0 
    WHERE session_id = ?
    ''', (session_id,))
    
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def update_last_login(user_id: str):
    """Update the last login timestamp for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE users SET last_login = datetime('now')
    WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def get_user_by_id(user_id: str):
    """Get user information by user ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    return dict(user) if user else None

def cleanup_expired_sessions():
    """Remove expired sessions from the database."""
    try:
        # Ensure tables exist before cleanup
        ensure_db_exists()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if user_sessions table exists before trying to clean it
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'")
        if not cursor.fetchone():
            conn.close()
            return 0
        
        cursor.execute("DELETE FROM user_sessions WHERE expires_at < datetime('now')")
        
        conn.commit()
        deleted_count = cursor.rowcount
        conn.close()
        return deleted_count
    except Exception as e:
        print(f"Error cleaning up expired sessions: {e}")
        return 0

def job_exists(job_id, user_id=None):
    """Check if a job with the given ID already exists in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("SELECT 1 FROM jobs WHERE job_id = ? AND user_id = ?", (job_id, user_id))
    else:
        cursor.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,))
    
    exists = cursor.fetchone() is not None
    
    conn.close()
    return exists

def get_table_columns():
    """Get the list of columns in the jobs table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    conn.close()
    return columns

def save_job(job_data, user_id=None):
    """Save a job to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Extract job_id from link
    job_id = job_data.get('job_id')
    
    # Add user_id to job_data
    if user_id:
        job_data = dict(job_data)
        job_data['user_id'] = user_id
    
    # Check if job already exists for this user
    if user_id and job_exists(job_id, user_id):
        conn.close()
        return False
    elif not user_id and job_exists(job_id):
        conn.close()
        return False
    
    # Get existing table columns
    table_columns = get_table_columns()
    
    # Filter job_data to only include columns that exist in the table
    filtered_job_data = {k: v for k, v in job_data.items() if k in table_columns}
    
    # Prepare columns and values for insertion
    columns = ', '.join(filtered_job_data.keys())
    placeholders = ', '.join(['?' for _ in filtered_job_data])
    values = tuple(filtered_job_data.values())
    
    # Insert the job
    cursor.execute(f"INSERT INTO jobs ({columns}) VALUES ({placeholders})", values)
    
    conn.commit()
    conn.close()
    return True

def save_jobs(jobs_data):
    """Save multiple jobs to the database and return the number of new jobs saved."""
    new_jobs_count = 0
    
    for job_data in jobs_data:
        if save_job(job_data):
            new_jobs_count += 1
    
    return new_jobs_count

def get_all_jobs(user_id=None):
    """Get all jobs from the database for a specific user."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    else:
        # For backward compatibility - get all jobs
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    
    rows = cursor.fetchall()
    
    # Convert rows to dictionaries
    jobs = [dict(row) for row in rows]
    
    conn.close()
    return jobs

def get_job_by_id(job_id, user_id=None):
    """Get a specific job by its ID, optionally filtered by user."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("SELECT * FROM jobs WHERE job_id = ? AND user_id = ?", (job_id, user_id))
    else:
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    
    row = cursor.fetchone()
    
    conn.close()
    return dict(row) if row else None

def update_job(job_id, job_data, user_id=None):
    """Update an existing job in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if job exists
    if user_id and not job_exists(job_id, user_id):
        conn.close()
        return False
    elif not user_id and not job_exists(job_id):
        conn.close()
        return False
    
    # Get existing table columns
    table_columns = get_table_columns()
    
    # Filter job_data to only include columns that exist in the table
    filtered_job_data = {k: v for k, v in job_data.items() if k in table_columns and k not in ['job_id', 'user_id']}
    
    if not filtered_job_data:
        conn.close()
        return False
    
    # Prepare SET clause for UPDATE
    set_clause = ', '.join([f"{k} = ?" for k in filtered_job_data.keys()])
    values = list(filtered_job_data.values())
    
    if user_id:
        values.extend([job_id, user_id])
        cursor.execute(f"UPDATE jobs SET {set_clause} WHERE job_id = ? AND user_id = ?", values)
    else:
        values.append(job_id)
        cursor.execute(f"UPDATE jobs SET {set_clause} WHERE job_id = ?", values)
    
    conn.commit()
    conn.close()
    return True

def delete_job(job_id, user_id=None):
    """Delete a job from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if job exists
    if user_id and not job_exists(job_id, user_id):
        conn.close()
        return False
    elif not user_id and not job_exists(job_id):
        conn.close()
        return False
    
    # Delete the job
    if user_id:
        cursor.execute("DELETE FROM jobs WHERE job_id = ? AND user_id = ?", (job_id, user_id))
    else:
        cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
    
    conn.commit()
    deleted_count = cursor.rowcount
    conn.close()
    
    return deleted_count > 0

def delete_multiple_jobs(job_ids, user_id=None):
    """Delete multiple jobs from the database."""
    if not job_ids:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create placeholders for the IN clause
    placeholders = ', '.join(['?' for _ in job_ids])
    
    # Delete the jobs
    if user_id:
        cursor.execute(f"DELETE FROM jobs WHERE job_id IN ({placeholders}) AND user_id = ?", job_ids + [user_id])
    else:
        cursor.execute(f"DELETE FROM jobs WHERE job_id IN ({placeholders})", job_ids)
    
    conn.commit()
    deleted_count = cursor.rowcount
    conn.close()
    
    return deleted_count

def reset_job_score(job_id, user_id=None):
    """Reset the score of a job to None (for regeneration)."""
    return update_job(job_id, {'score': None}, user_id)

def reset_multiple_job_scores(job_ids, user_id=None):
    """Reset scores for multiple jobs."""
    if not job_ids:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create placeholders for the IN clause
    placeholders = ', '.join(['?' for _ in job_ids])
    
    # Reset scores
    if user_id:
        cursor.execute(f"UPDATE jobs SET score = NULL WHERE job_id IN ({placeholders}) AND user_id = ?", job_ids + [user_id])
    else:
        cursor.execute(f"UPDATE jobs SET score = NULL WHERE job_id IN ({placeholders})", job_ids)
    
    conn.commit()
    updated_count = cursor.rowcount
    conn.close()
    
    return updated_count

def get_jobs_by_criteria(score_min=None, score_max=None, job_type=None, unprocessed_only=False, user_id=None):
    """Get jobs based on specific criteria."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    
    if score_min is not None:
        conditions.append("score >= ?")
        params.append(score_min)
    
    if score_max is not None:
        conditions.append("score <= ?")
        params.append(score_max)
    
    if job_type:
        conditions.append("job_type = ?")
        params.append(job_type)
    
    if unprocessed_only:
        conditions.append("score IS NULL")
    
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    
    query = f"SELECT * FROM jobs {where_clause} ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convert rows to dictionaries
    jobs = [dict(row) for row in rows]
    
    conn.close()
    return jobs

def get_database_stats(user_id=None):
    """Get database statistics for a specific user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    user_filter = "WHERE user_id = ?" if user_id else ""
    params = [user_id] if user_id else []
    
    # Total jobs
    cursor.execute(f"SELECT COUNT(*) FROM jobs {user_filter}", params)
    stats['total_jobs'] = cursor.fetchone()[0]
    
    # Processed jobs (with scores)
    cursor.execute(f"SELECT COUNT(*) FROM jobs {user_filter} {'AND' if user_id else 'WHERE'} score IS NOT NULL", params)
    stats['processed_jobs'] = cursor.fetchone()[0]
    
    # High scoring jobs (score >= 7)
    cursor.execute(f"SELECT COUNT(*) FROM jobs {user_filter} {'AND' if user_id else 'WHERE'} score >= 7", params)
    stats['high_scoring_jobs'] = cursor.fetchone()[0]
    
    # Average score
    cursor.execute(f"SELECT AVG(score) FROM jobs {user_filter} {'AND' if user_id else 'WHERE'} score IS NOT NULL", params)
    avg_score = cursor.fetchone()[0]
    stats['average_score'] = round(avg_score, 2) if avg_score else 0
    
    # Jobs by type
    cursor.execute(f"SELECT job_type, COUNT(*) FROM jobs {user_filter} {'AND' if user_id else 'WHERE'} job_type IS NOT NULL GROUP BY job_type", params)
    stats['jobs_by_type'] = dict(cursor.fetchall())
    
    # Recent activity (jobs added in last 7 days)
    cursor.execute(f"SELECT COUNT(*) FROM jobs {user_filter} {'AND' if user_id else 'WHERE'} created_at >= datetime('now', '-7 days')", params)
    stats['recent_jobs'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def create_admin_user(username: str, email: str, password: str) -> tuple:
    """Create a new admin user account."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if username or email already exists
        cursor.execute("SELECT username FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone():
            conn.close()
            return False, "Username or email already exists"
        
        # Hash password
        password_hash, salt = hash_password(password)
        
        # Generate user ID
        user_id = generate_user_id(username)
        
        # Insert admin user
        cursor.execute('''
        INSERT INTO users (user_id, username, email, password_hash, salt, is_admin)
        VALUES (?, ?, ?, ?, ?, 1)
        ''', (user_id, username, email, password_hash, salt))
        
        conn.commit()
        conn.close()
        return True, user_id
        
    except Exception as e:
        conn.close()
        return False, str(e)

def promote_user_to_admin(user_id: str) -> bool:
    """Promote an existing user to admin."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"Error promoting user to admin: {e}")
        conn.close()
        return False

def demote_admin_user(user_id: str) -> bool:
    """Remove admin privileges from a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET is_admin = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"Error demoting admin user: {e}")
        conn.close()
        return False

def is_admin_user(user_id: str) -> bool:
    """Check if a user has admin privileges."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result and bool(result['is_admin'])

def get_all_users(admin_user_id: str = None) -> list:
    """Get all users (admin only function)."""
    if admin_user_id and not is_admin_user(admin_user_id):
        return []
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
    users = [dict(row) for row in rows]
    conn.close()
    return users

def get_all_jobs_admin(admin_user_id: str = None):
    """Get all jobs from all users (admin only function)."""
    if admin_user_id and not is_admin_user(admin_user_id):
        return []
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT j.*, u.username, u.email 
    FROM jobs j 
    LEFT JOIN users u ON j.user_id = u.user_id 
    ORDER BY j.created_at DESC
    """)
    rows = cursor.fetchall()
    
    jobs = [dict(row) for row in rows]
    conn.close()
    return jobs

def get_system_stats(admin_user_id: str = None) -> dict:
    """Get comprehensive system statistics (admin only)."""
    if admin_user_id and not is_admin_user(admin_user_id):
        return {}
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # User statistics
    cursor.execute("SELECT COUNT(*) FROM users")
    stats['total_users'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    stats['admin_users'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    stats['active_users'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= datetime('now', '-7 days')")
    stats['new_users_week'] = cursor.fetchone()[0]
    
    # Job statistics
    cursor.execute("SELECT COUNT(*) FROM jobs")
    stats['total_jobs'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE score IS NOT NULL")
    stats['processed_jobs'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE score >= 7")
    stats['high_scoring_jobs'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(score) FROM jobs WHERE score IS NOT NULL")
    avg_score = cursor.fetchone()[0]
    stats['average_score'] = round(avg_score, 2) if avg_score else 0
    
    # Session statistics
    cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE is_active = 1")
    stats['active_sessions'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE expires_at < datetime('now')")
    stats['expired_sessions'] = cursor.fetchone()[0]
    
    # Jobs by user
    cursor.execute("""
    SELECT u.username, COUNT(j.job_id) as job_count 
    FROM users u 
    LEFT JOIN jobs j ON u.user_id = j.user_id 
    GROUP BY u.user_id, u.username 
    ORDER BY job_count DESC 
    LIMIT 10
    """)
    stats['top_users_by_jobs'] = dict(cursor.fetchall())
    
    conn.close()
    return stats

def delete_user_admin(user_id: str, admin_user_id: str) -> bool:
    """Delete a user and all their data (admin only)."""
    if not is_admin_user(admin_user_id):
        return False
    
    # Prevent deleting yourself
    if user_id == admin_user_id:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Delete user's jobs
        cursor.execute("DELETE FROM jobs WHERE user_id = ?", (user_id,))
        
        # Delete user's sessions
        cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"Error deleting user: {e}")
        conn.rollback()
        conn.close()
        return False

def toggle_user_status(user_id: str, admin_user_id: str) -> bool:
    """Toggle user active/inactive status (admin only)."""
    if not is_admin_user(admin_user_id):
        return False
    
    # Prevent deactivating yourself
    if user_id == admin_user_id:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE users SET is_active = NOT is_active WHERE user_id = ?", (user_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"Error toggling user status: {e}")
        conn.close()
        return False

# ========================
# PROMPT MANAGEMENT FUNCTIONS
# ========================

def generate_prompt_id(prompt_type: str) -> str:
    """Generate a unique prompt ID."""
    timestamp = datetime.now().isoformat()
    unique_string = f"{prompt_type}_{timestamp}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

def create_or_update_prompt(prompt_type: str, prompt_name: str, prompt_content: str, admin_user_id: str) -> tuple:
    """Create or update a prompt. Only admins can manage prompts."""
    if not is_admin_user(admin_user_id):
        return False, "Only administrators can manage prompts"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if prompt type already exists
        cursor.execute("SELECT prompt_id FROM prompts WHERE prompt_type = ?", (prompt_type,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing prompt
            cursor.execute('''
            UPDATE prompts 
            SET prompt_name = ?, prompt_content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE prompt_type = ?
            ''', (prompt_name, prompt_content, prompt_type))
            action = "updated"
        else:
            # Create new prompt
            prompt_id = generate_prompt_id(prompt_type)
            cursor.execute('''
            INSERT INTO prompts (prompt_id, prompt_type, prompt_name, prompt_content, created_by)
            VALUES (?, ?, ?, ?, ?)
            ''', (prompt_id, prompt_type, prompt_name, prompt_content, admin_user_id))
            action = "created"
        
        conn.commit()
        conn.close()
        return True, f"Prompt {action} successfully"
        
    except Exception as e:
        conn.close()
        return False, str(e)

def get_prompt_by_type(prompt_type: str) -> dict:
    """Get a prompt by its type."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM prompts 
    WHERE prompt_type = ? AND is_active = 1
    ''', (prompt_type,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return dict(result)
    return None

def get_all_prompts(admin_user_id: str = None) -> list:
    """Get all prompts. Only admins can view all prompts."""
    if admin_user_id and not is_admin_user(admin_user_id):
        return []
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT p.*, u.username as created_by_username
    FROM prompts p
    LEFT JOIN users u ON p.created_by = u.user_id
    WHERE p.is_active = 1
    ORDER BY p.prompt_type, p.created_at DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]

def delete_prompt(prompt_type: str, admin_user_id: str) -> tuple:
    """Delete a prompt by type. Only admins can delete prompts."""
    if not is_admin_user(admin_user_id):
        return False, "Only administrators can delete prompts"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM prompts WHERE prompt_type = ?", (prompt_type,))
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True, "Prompt deleted successfully"
        else:
            conn.close()
            return False, "Prompt not found"
    except Exception as e:
        conn.close()
        return False, str(e)

def initialize_default_prompts(admin_user_id: str):
    """Initialize default prompts if they don't exist."""
    if not is_admin_user(admin_user_id):
        return False, "Only administrators can initialize prompts"
    
    # Default cover letter prompt
    default_cover_letter_prompt = """# ROLE

You are an Upwork cover letter specialist, crafting targeted and personalized proposals. 
Create persuasive cover letters that align with job requirements while highlighting the freelancer's skills and experience.

## Relevant Information about Freelancer:
<profile>
{profile}
</profile>

# SOP

1. Address the client's needs directly, focusing on how the freelancer can solve their challenges or meet their goals.
2. Highlight relevant skills and past projects from the freelancer's profile that demonstrate expertise in meeting the job requirements.
3. Show genuine enthusiasm for the job, using a friendly and casual tone.
4. Keep the cover letter under 150 words, ensuring it is concise and easy to read.
5. Use job-related keywords naturally to connect with the client's priorities.
6. Follow the format and style of the example letter, emphasizing the freelancer's ability to deliver value.
7. Avoid using generic words like "hardworking", "dedicated" or "expertise".

# Example Letter:
<letter>
Hi there,  

I'm really excited about the chance to work on AI-driven solutions for OpenAI! With my experience in AI development and automation, I'm confident I can make a real impact.  

Here are a few things I've worked on:  
- Built an AI voice assistant that handled customer queries and improved communication—great for creating voice systems like yours.  
- Designed an AI email automation system to save time by automating responses and admin tasks.  
- Developed an AI outreach tool for lead generation, personalized emails, and prospecting.  

I'd love to chat about how I can help streamline your operations, improve automation, and drive growth for OpenAI!  

Looking forward to it,  
Aymen  
</letter>

# **IMPORTANT**
* **My name is: Aymen**; include it at the end of the letters.
* Follow the example letter format and style.
* ** Take into account the proposal requirements if they are provided.**
* Do not invent any information that is not present in my profile.
* **Use simple, friendly and casual tone throughout the letter**."""

    # Default interview preparation prompt
    default_interview_prompt = """You are a **freelance interview preparation coach**. Your task is to create a tailored call script for a freelancer preparing for an interview with a client. The script should help the freelancer confidently discuss their qualifications and experiences relevant to the job description provided.

## Relevant Information about Freelancer:
<profile>
{profile}
</profile>

# Instructions:
1. Start with a brief introduction the freelancer can use to introduce themselves.
2. Include key points the freelancer should mention regarding their relevant experience and skills related to the job.
3. List 10 potential questions that the client might ask during the interview.
4. Suggest 10 questions the freelancer might ask the client to demonstrate interest and clarify project details.
5. Maintain a friendly and professional tone throughout the script.

# Output:
Return your final output in markdown format."""

    # Create default prompts
    create_or_update_prompt("cover_letter", "Default Cover Letter Template", default_cover_letter_prompt, admin_user_id)
    create_or_update_prompt("interview_prep", "Default Interview Preparation Template", default_interview_prompt, admin_user_id)
    
    return True, "Default prompts initialized successfully"

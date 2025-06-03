# 🔐 Authentication System for Upwork AI Jobs Applier

## Overview

The Upwork AI Jobs Applier now includes a comprehensive user authentication system that allows multiple users to securely manage their job applications independently. Each user has their own isolated data and sessions.

## Features

### 🔑 User Authentication
- **Secure Registration**: Username, email, and password-based registration
- **Login System**: Support for login with username or email
- **Password Security**: Passwords are hashed using PBKDF2 with SHA-256 and random salts
- **Session Management**: Secure session tokens with configurable expiration (1-7 days)
- **Remember Me**: Option to extend session duration for convenience

### 👤 Multi-User Support
- **User Isolation**: Each user's jobs and data are completely isolated
- **Individual Profiles**: Each user can have their own freelancer profile
- **Personal Dashboard**: User-specific metrics and statistics
- **Secure Logout**: Proper session invalidation

### 🛡️ Security Features
- **Password Hashing**: PBKDF2 with 100,000 iterations
- **Random Salts**: Unique salt for each password
- **Session Tokens**: Cryptographically secure random tokens
- **Session Expiration**: Automatic cleanup of expired sessions
- **SQL Injection Protection**: Parameterized queries throughout

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,           -- Unique user identifier
    username TEXT UNIQUE NOT NULL,      -- Username (unique)
    email TEXT UNIQUE NOT NULL,         -- Email address (unique)
    password_hash TEXT NOT NULL,        -- Hashed password
    salt TEXT NOT NULL,                 -- Random salt for password
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,               -- Last login time
    is_active BOOLEAN DEFAULT 1,        -- Account status
    profile_data TEXT                   -- User profile information
);
```

### Sessions Table
```sql
CREATE TABLE user_sessions (
    session_id TEXT PRIMARY KEY,        -- Session token
    user_id TEXT NOT NULL,              -- Associated user
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,      -- Session expiration
    is_active BOOLEAN DEFAULT 1,        -- Session status
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
```

### Updated Jobs Table
```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,              -- NEW: User association
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
);
```

## Getting Started

### 1. First Time Setup
1. **Run the Application**: `streamlit run app.py`
2. **Create Account**: Click on the "Sign Up" tab
3. **Fill Registration Form**:
   - Username (minimum 3 characters)
   - Email address
   - Password (minimum 8 characters)
   - Confirm password
4. **Login**: Use your credentials to access the application

### 2. Login Process
1. **Access Login Page**: Automatically shown for unauthenticated users
2. **Enter Credentials**: Username/email and password
3. **Remember Me**: Check to extend session to 7 days (default: 1 day)
4. **Access Dashboard**: Redirected to your personal dashboard

### 3. User Experience
- **Personal Dashboard**: View your jobs, metrics, and quick actions
- **Data Isolation**: Only see and manage your own jobs
- **Secure Sessions**: Automatic logout on session expiry
- **Account Management**: View account info and manage settings

## API Functions

### Authentication Functions

#### `create_user(username, email, password)`
Creates a new user account with hashed password.
```python
success, user_id = create_user("john_doe", "john@email.com", "password123")
```

#### `authenticate_user(username, password)`
Authenticates user credentials.
```python
success, user_data, message = authenticate_user("john_doe", "password123")
```

#### `create_session(user_id, duration_hours=24)`
Creates a new session for authenticated user.
```python
session_id = create_session(user_id, 168)  # 7 days
```

#### `validate_session(session_id)`
Validates an existing session.
```python
valid, user_data = validate_session(session_id)
```

#### `invalidate_session(session_id)`
Logs out user by invalidating session.
```python
success = invalidate_session(session_id)
```

### User-Aware Database Functions

All existing database functions now accept an optional `user_id` parameter:

```python
# User-specific job operations
jobs = get_all_jobs(user_id)
job = get_job_by_id(job_id, user_id)
success = save_job(job_data, user_id)
success = update_job(job_id, job_data, user_id)
success = delete_job(job_id, user_id)

# User-specific statistics
stats = get_database_stats(user_id)
jobs = get_jobs_by_criteria(user_id=user_id, score_min=7)
```

## Security Considerations

### Password Security
- **Minimum Length**: 8 characters required
- **Hashing Algorithm**: PBKDF2-SHA256 with 100,000 iterations
- **Unique Salts**: Each password has a unique random salt
- **No Plain Text**: Passwords are never stored in plain text

### Session Security
- **Secure Tokens**: Cryptographically secure random session IDs
- **Expiration**: Sessions automatically expire (1-7 days)
- **Cleanup**: Expired sessions are automatically removed
- **Validation**: Session validation on every request

### Data Isolation
- **User Separation**: Complete isolation between user data
- **Query Filtering**: All database queries filtered by user_id
- **Access Control**: Users can only access their own data

## Migration from Non-Authenticated Version

### Existing Data
- Existing jobs will be assigned to a default user ('default_user')
- Database automatically upgrades to include user tables
- No data loss during migration

### Steps for Existing Users
1. **Start Updated App**: Authentication tables are created automatically
2. **Create Account**: Register with the new system
3. **Migrate Data**: Contact administrator to transfer existing jobs (if needed)

## Troubleshooting

### Common Issues

#### "Username or email already exists"
- Try a different username or email
- Check if you already have an account

#### "Session expired"
- Login again with your credentials
- Consider using "Remember Me" for longer sessions

#### "Failed to create account"
- Ensure password meets minimum requirements (8+ characters)
- Check that username is at least 3 characters
- Verify email format is valid

#### "No jobs found"
- This is normal for new accounts
- Add jobs using the "Add Job" page
- Existing jobs are user-specific

### Database Issues
```python
# Clean up expired sessions manually
from src.database import cleanup_expired_sessions
cleanup_expired_sessions()

# Check database tables exist
from src.database import ensure_db_exists
ensure_db_exists()
```

## Development Notes

### Session State Management
```python
# Key session state variables
st.session_state.authenticated    # Boolean: User logged in
st.session_state.user            # Dict: User information
st.session_state.session_id      # String: Session token
```

### User Context
```python
# Get current user ID in any function
def get_current_user_id():
    if st.session_state.authenticated and st.session_state.user:
        return st.session_state.user['user_id']
    return None
```

### Custom Job Processor
The new `UserJobProcessor` class extends the original processor to work with user-specific data:

```python
from src.user_job_processor import UserJobProcessor

processor = UserJobProcessor(
    user_id=user_id,
    profile=profile_text,
    batch_size=3,
    min_score=7
)

result = await processor.process_user_jobs()
```

## Future Enhancements

### Planned Features
- **Password Reset**: Email-based password recovery
- **Profile Management**: Edit username, email, password
- **Account Deletion**: Complete account removal
- **Admin Panel**: User management for administrators
- **OAuth Integration**: Login with Google, GitHub, etc.
- **Team Workspaces**: Shared job management for teams

### API Improvements
- **Rate Limiting**: Prevent abuse of authentication endpoints
- **Audit Logging**: Track user actions and login attempts
- **Enhanced Validation**: More robust input validation
- **Multi-Factor Authentication**: 2FA support

## Support

If you encounter issues with the authentication system:

1. **Check Logs**: Look for error messages in the Streamlit console
2. **Database Issues**: Ensure proper database permissions
3. **Session Problems**: Clear browser cache and cookies
4. **Create Issue**: Report bugs on the project repository

## License

This authentication system is part of the Upwork AI Jobs Applier project and follows the same licensing terms. 
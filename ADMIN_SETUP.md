# 👑 Admin System Setup Guide

## Overview
The Upwork AI Jobs Applier now includes a comprehensive admin system that allows administrators to manage all users, jobs, and system operations.

## Quick Setup

### 1. Create Your First Admin User

**Option A: Quick Creation (Recommended)**
```bash
python fix_and_create_admin.py
```
This script will:
- Fix any database schema issues
- Create an admin user named "zaeem" with email "zaeem.codrivity@gmail.com"
- Set the password to "adminpass123"

**Option B: Interactive Creation**
```bash
python create_admin.py
```
Follow the prompts to create a custom admin user.

**Option C: Command Line Creation**
```bash
python quick_create_admin.py <username> <email> <password>
# Example:
python quick_create_admin.py admin admin@example.com securepass123
```

### 2. Login to the App
```bash
streamlit run app.py
```

Navigate to the login page and use your admin credentials:
- **Username**: zaeem (or your custom username)
- **Password**: adminpass123 (or your custom password)

## Admin Features

### 🏠 Admin Panel Access
Once logged in as an admin, you'll see a crown icon (👑) next to your username and a new navigation option: **"👑 Admin Panel"**

### 📊 System Overview
- **User Statistics**: Total users, active users, admin users, new users in the last 7 days
- **Job Statistics**: Total jobs, processed jobs, high-scoring jobs, average score
- **Session Management**: Active and expired sessions
- **Top Users**: Most active users by job count

### 👥 User Management
- **View All Users**: See complete user list with status indicators
- **Promote/Demote Admins**: Grant or revoke admin privileges
- **Activate/Deactivate Users**: Enable or disable user accounts
- **Delete Users**: Remove users and all their data (irreversible)
- **Session Cleanup**: Remove expired sessions

### 💼 All Jobs Management
- **View All Jobs**: See jobs from all users across the system
- **Filter Options**: Filter by user, score range, job type
- **Comprehensive Data**: User information, job details, scores, links

### 🔧 System Tools
- **Database Operations**: Initialize/upgrade database schema
- **Session Cleanup**: Bulk removal of expired sessions
- **Statistics Recalculation**: Refresh system metrics

### 📈 Analytics Dashboard
- **User Distribution Charts**: Visual breakdown of user types
- **Job Processing Stats**: Processing status visualization
- **Top Users Table**: Most active users ranking

## Admin User Management

### Promote Existing User to Admin
```python
from src.database import promote_user_to_admin
promote_user_to_admin("user_id_here")
```

### Remove Admin Privileges
```python
from src.database import demote_admin_user
demote_admin_user("user_id_here")
```

### Check if User is Admin
```python
from src.database import is_admin_user
if is_admin_user("user_id_here"):
    print("User is an admin")
```

## Security Features

### 🔐 Admin-Only Functions
- All admin functions check user privileges before execution
- Regular users cannot access admin functionality
- Admins cannot delete themselves (safety measure)
- Admins cannot deactivate themselves

### 🛡️ Data Protection
- Complete data isolation between users
- Secure password hashing (PBKDF2-SHA256)
- Session-based authentication
- Automatic expired session cleanup

### 🔍 Audit Trail
- Last login tracking for all users
- User creation timestamps
- Job creation tracking
- Session activity monitoring

## Troubleshooting

### Database Schema Issues
If you encounter database schema errors:
```bash
python fix_and_create_admin.py
```

### Missing Admin Column
```python
import sqlite3
conn = sqlite3.connect("./upwork_jobs.db")
cursor = conn.cursor()
cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
conn.commit()
conn.close()
```

### Check Current Admins
```bash
python -c "from src.database import get_all_users; users = get_all_users(); admins = [u for u in users if u.get('is_admin')]; print(f'Admins: {len(admins)}'); [print(f'- {a[\"username\"]}') for a in admins]"
```

### Reset Admin Status
```python
from src.database import promote_user_to_admin
# Find user ID first, then promote
promote_user_to_admin("your_user_id")
```

## API Reference

### Admin Database Functions

#### `create_admin_user(username, email, password)`
Create a new user with admin privileges.

#### `promote_user_to_admin(user_id)`
Grant admin privileges to an existing user.

#### `demote_admin_user(user_id)`
Remove admin privileges from a user.

#### `is_admin_user(user_id)`
Check if a user has admin privileges.

#### `get_all_users(admin_user_id)`
Get all users (admin only).

#### `get_all_jobs_admin(admin_user_id)`
Get all jobs from all users (admin only).

#### `get_system_stats(admin_user_id)`
Get comprehensive system statistics (admin only).

#### `delete_user_admin(user_id, admin_user_id)`
Delete a user and all their data (admin only).

#### `toggle_user_status(user_id, admin_user_id)`
Toggle user active/inactive status (admin only).

## Best Practices

### 1. Admin Account Security
- Use strong passwords for admin accounts
- Regularly review admin user list
- Remove admin privileges when no longer needed

### 2. User Management
- Monitor new user registrations
- Deactivate instead of deleting for audit purposes
- Regular session cleanup for security

### 3. System Maintenance
- Regularly check system statistics
- Monitor job processing performance
- Clean up expired sessions periodically

### 4. Data Management
- Regular database backups
- Monitor disk usage for job data
- Archive old jobs when necessary

## Default Admin Credentials

**Username**: zaeem  
**Email**: zaeem.codrivity@gmail.com  
**Password**: adminpass123

⚠️ **Important**: Change the default password after first login!

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the database schema in `src/database.py`
3. Check application logs for errors
4. Ensure all dependencies are installed

---

**Happy Administrating!** 👑 
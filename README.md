# 🤖 Upwork AI Jobs Applier

An intelligent Streamlit application that automates job searching and application processes on Upwork using AI-powered matching and personalized cover letter generation.

## ✨ Features

### 🔐 Authentication System
- **Multi-user support** with secure password hashing (PBKDF2-SHA256)
- **Session management** with automatic cleanup
- **Admin panel** for system management
- **User isolation** - each user has their own applications and data

### 🎯 AI-Powered Job Processing
- **Intelligent job scoring** based on your skills and preferences
- **Automated cover letter generation** using AI
- **User-specific applications** saved to individual directories
- **High-score job notifications** (≥7.0) for promising opportunities

### 👨‍💼 Admin Features
- **System Overview** with user statistics and analytics
- **User Management** - create, modify, promote/demote users
- **Job Management** - view all applications across users
- **System Tools** - database maintenance and cleanup
- **Analytics Dashboard** with comprehensive metrics

### 📊 Smart Analytics
- Job processing statistics
- Success rate tracking
- User activity monitoring
- High-score job alerts

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup
1. **Clone the repository**
```bash
git clone https://github.com/YOUR-USERNAME/upwork-ai-jobs-applier.git
cd upwork-ai-jobs-applier
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure the application**
   - Update API keys in your configuration files
   - Modify job search criteria in the settings

4. **Initialize the database**
```bash
python src/database.py
```

5. **Create an admin user** (optional)
```bash
python quick_create_admin.py
```

## 🖥️ Usage

### Starting the Application
```bash
python -m streamlit run app.py
```

Access the application at `http://localhost:8501`

### For Regular Users
1. **Sign Up** - Create your account with email and password
2. **Profile Setup** - Configure your skills, preferences, and job criteria
3. **Process Jobs** - Run the job search and let AI score opportunities
4. **Review Applications** - Check generated cover letters and applications
5. **Apply** - Use the generated content to apply for jobs

### For Admin Users
1. **Access Admin Panel** - Additional tab available after login
2. **Manage Users** - Create, edit, activate/deactivate user accounts
3. **System Overview** - Monitor application performance and usage
4. **Job Analytics** - View success rates and job processing statistics
5. **System Maintenance** - Database cleanup and system tools

## 📁 Project Structure

```
upwork-ai-jobs-applier/
├── app.py                          # Main Streamlit application
├── src/
│   ├── database.py                 # Database management and schema
│   ├── job_processor.py            # Core job processing logic
│   ├── user_job_processor.py       # User-specific job processing
│   ├── manual_job_processor.py     # Manual job processing utilities
│   └── utils.py                    # Helper functions
├── data/
│   ├── users/                      # User-specific data directories
│   ├── applications/               # Generated applications
│   └── high_score_notifications.json # High-score job alerts
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── docs/
│   ├── AUTHENTICATION_README.md    # Authentication system documentation
│   ├── ADMIN_SETUP.md             # Admin setup and usage guide
│   └── APPLICATIONS_PAGE_FIXES.md  # Technical fixes documentation
└── requirements.txt                # Python dependencies
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file with your API keys and configuration:

```env
# Add your API keys here
OPENAI_API_KEY=your_openai_key_here
# Add other configuration variables as needed
```

### Job Search Criteria
Modify the job search parameters in the application settings to match your:
- Skills and expertise
- Desired job categories
- Budget preferences
- Experience level

## 🛡️ Security Features

- **Password Security**: PBKDF2-SHA256 hashing with 100,000 iterations
- **Session Management**: Secure session tokens with automatic expiration
- **User Isolation**: Complete separation of user data and applications
- **Admin Controls**: Granular permissions and system management tools
- **Data Protection**: Sensitive files excluded from version control

## 📊 Database Schema

The application uses SQLite with the following main tables:
- `users` - User accounts and authentication
- `user_sessions` - Active user sessions
- `jobs` - Job listings and processing results
- Admin functions for user and system management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
1. Check the documentation in the `docs/` directory
2. Review the issue tracker for common problems
3. Create a new issue for bugs or feature requests

## 🔄 Version History

- **v1.0.0** - Initial release with basic job processing
- **v2.0.0** - Added multi-user authentication system
- **v2.1.0** - Implemented admin panel and user management
- **v2.2.0** - Added high-score notifications and enhanced analytics

---

**⚠️ Disclaimer**: This tool is for educational purposes. Always review generated content before submitting job applications and ensure compliance with Upwork's terms of service.

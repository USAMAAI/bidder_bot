# 🤖 Upwork AI Jobs Applier - Streamlit Web App

A comprehensive web interface for managing job applications with AI-powered cover letter generation and job scoring.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install streamlit plotly pandas
```

### 2. Set Environment Variables
Make sure your OpenAI API key is set (you can also set it in the app):
```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "your-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Run the Application
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📱 Features

### 📊 Dashboard
- **Overview metrics**: Total jobs, processed jobs, high-scoring jobs, average score
- **Score distribution chart**: Visual representation of job scores
- **Jobs by type chart**: Pie chart showing Fixed vs Hourly jobs
- **Recent jobs list**: Quick view of recently added jobs

### ➕ Add Job
- **Comprehensive form**: Add all job details including:
  - Job title, description, type, payment rate
  - Experience level, duration, URL
  - Client information (location, spending, hires)
  - Proposal requirements
- **Validation**: Ensures required fields are filled
- **Auto-formatting**: Automatically adds $ to payment rates

### 📋 View Jobs
- **Advanced filtering**: Filter by job type, score range, experience level
- **Search functionality**: Search in job titles
- **Detailed view**: Expandable details for each job
- **Score indicators**: Color-coded score display (green=high, yellow=medium, red=low)

### ⚡ Process Jobs
- **Batch processing**: Process multiple jobs simultaneously
- **Configurable settings**: Adjust minimum score threshold and batch size
- **Progress tracking**: Real-time progress bar and status updates
- **Automatic scoring**: AI-powered job scoring based on your profile
- **Application generation**: Creates cover letters and interview prep for high-scoring jobs

### 📄 Applications
- **View generated content**: Browse all generated cover letters and interview prep
- **Organized by date**: Applications grouped by processing date
- **Expandable sections**: Easy-to-read application content
- **Copy-ready**: Content ready to use for job applications

### ⚙️ Settings
- **API key management**: Set or update your OpenAI API key
- **Profile verification**: Check if your profile file exists
- **Database info**: View database statistics
- **File management**: Verify required files are in place

## 📁 File Structure

```
project/
├── app.py                          # Main Streamlit application
├── process_manual_jobs.py          # Job processing logic
├── manual_job_entry.py             # Command-line job entry (backup)
├── quick_add_job.py               # Quick command-line job entry (backup)
├── src/                           # Core application modules
│   ├── database.py               # Database operations
│   ├── utils.py                  # Utility functions
│   ├── nodes.py                  # Job processing nodes
│   └── ...
├── files/
│   └── profile.md                # Your freelancer profile (required)
├── data/
│   └── cover_letter.md           # Generated applications
└── upwork_jobs.db                # SQLite database
```

## 🔧 Configuration

### Required Files

1. **Profile File**: Create `./files/profile.md` with your freelancer profile
2. **Environment**: Set `OPENAI_API_KEY` environment variable
3. **Database**: Will be created automatically on first run

### Optional Configuration

- **Minimum Score**: Adjust in Process Jobs page (default: 7)
- **Batch Size**: Control processing speed (default: 3)
- **API Key**: Can be set in the Settings page

## 🎯 Workflow

1. **Add Jobs**: Use the "Add Job" page to manually add jobs from Upwork
2. **Process Jobs**: Go to "Process Jobs" and click "Process All Jobs"
3. **View Results**: Check the Dashboard for scores and Applications for generated content
4. **Apply**: Copy cover letters from Applications and use them on Upwork

## 📊 Understanding Scores

- **8-10**: Excellent match - High priority
- **7**: Good match - Will generate applications
- **4-6**: Medium match - Review manually
- **1-3**: Poor match - Consider skipping

## 🔍 Tips

- **Add detailed job descriptions** for better scoring accuracy
- **Keep your profile updated** in `./files/profile.md`
- **Use filters** in View Jobs to find specific types of jobs
- **Process jobs in batches** to avoid API rate limits
- **Check Applications regularly** for newly generated content

## 🚨 Troubleshooting

### Common Issues

1. **API Key Error**: Set your OpenAI API key in Settings
2. **Profile Not Found**: Ensure `./files/profile.md` exists
3. **No Jobs Found**: Add some jobs using the Add Job page
4. **Processing Fails**: Check API key and internet connection

### Error Messages

- **"Profile file not found"**: Create `./files/profile.md`
- **"API key not set"**: Configure in Settings page
- **"No unprocessed jobs"**: All jobs already have scores

## 🎨 Customization

The app uses custom CSS for styling. You can modify the appearance by editing the CSS in the `st.markdown()` section of `app.py`.

## 🔄 Updates

The app automatically refreshes data when you:
- Add new jobs
- Process jobs
- Update settings

Manual refresh options are available in the Settings page.

---

**Need help?** Check the command-line tools (`manual_job_entry.py`, `quick_add_job.py`) for backup job entry methods. 
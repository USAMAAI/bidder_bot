# Manual Job Entry System Guide

Since the automated Upwork scraping is currently blocked by anti-bot protection, this manual job entry system allows you to add job details manually to continue using the application workflow.

## 🚀 Quick Start

### Option 1: Quick Entry (Fastest)
For rapid job addition with minimal fields:
```bash
python quick_add_job.py
```

### Option 2: Full Interactive Entry
For complete job details with all fields:
```bash
python manual_job_entry.py --interactive
```

### Option 3: Batch Import from Files
For importing multiple jobs at once:
```bash
# From JSON file
python manual_job_entry.py --import-json jobs.json

# From CSV file  
python manual_job_entry.py --import-csv jobs.csv
```

## 📋 Available Commands

### Interactive Entry
```bash
python manual_job_entry.py --interactive
python manual_job_entry.py -i
```
Provides a step-by-step guided interface to enter all job details.

### View All Jobs
```bash
python manual_job_entry.py --view-jobs
python manual_job_entry.py -v
```
Display all jobs currently stored in the database.

### Import from JSON
```bash
python manual_job_entry.py --import-json example_jobs.json
```
Import jobs from a JSON file. Supports both single job objects and arrays of jobs.

### Import from CSV
```bash
python manual_job_entry.py --import-csv example_jobs.csv
```
Import jobs from a CSV file with headers.

### Create Example Files
```bash
python manual_job_entry.py --create-examples
```
Creates `example_jobs.json` and `example_jobs.csv` template files.

## 📊 Job Fields

### Required Fields
- **Title**: Job title/name
- **Description**: Full job description

### Optional Fields
- **Job Type**: "Fixed" or "Hourly" (defaults to "Fixed")
- **Experience Level**: Entry/Intermediate/Expert
- **Duration**: Project duration (e.g., "1-3 months")
- **Payment Rate**: Rate or budget (e.g., "$15-$25", "$1000")
- **Link**: Job URL
- **Proposal Requirements**: Special client instructions

### Client Information (Optional)
- **Client Location**: Where the client is based
- **Client Joined Date**: When client joined platform
- **Client Total Spent**: Total amount client has spent
- **Client Total Hires**: Number of previous hires
- **Client Company Profile**: Company description

## 📁 File Format Examples

### JSON Format
```json
[
  {
    "title": "AI Agent Developer",
    "description": "We need an experienced AI agent developer...",
    "job_type": "Fixed",
    "experience_level": "Expert",
    "duration": "1-3 months",
    "payment_rate": "$1000-$3000",
    "link": "https://www.upwork.com/jobs/example1",
    "proposal_requirements": "Start with 'AI Expert'",
    "client_location": "United States",
    "client_joined_date": "January 2023",
    "client_total_spent": "$50000",
    "client_total_hires": 25,
    "client_company_profile": "Tech startup focused on automation"
  }
]
```

### CSV Format
Use the headers: `title,description,job_type,experience_level,duration,payment_rate,link,proposal_requirements,client_location,client_joined_date,client_total_spent,client_total_hires,client_company_profile`

## 🔄 Integration with Main Application

Once you've added jobs manually, you can run the main application workflow:

```bash
python main.py
```

The application will:
1. Load your manually entered jobs from the database
2. Score and rank them based on your criteria
3. Generate cover letters and applications
4. Create interview preparation materials

## 💡 Tips for Efficient Job Entry

### 1. **Use Quick Entry for Speed**
When you need to add jobs quickly, use `python quick_add_job.py` - it only asks for essential fields.

### 2. **Batch Import for Multiple Jobs**
If you have many jobs to add:
1. Create a CSV or JSON file
2. Copy the example format
3. Fill in your job data
4. Import with `--import-csv` or `--import-json`

### 3. **Copy-Paste Job Descriptions**
You can copy entire job descriptions from Upwork and paste them directly - the system handles formatting.

### 4. **Payment Rate Formatting**
The system automatically adds "$" if missing:
- Enter: `15-25` → Stored as: `$15-25`
- Enter: `$1000` → Stored as: `$1000`

## 🔍 Finding Jobs to Add

Since scraping is blocked, you can manually browse Upwork and copy job details:

1. **Go to Upwork** and search for relevant jobs
2. **Copy the job details** (title, description, etc.)
3. **Use the manual entry system** to add them
4. **Run the main application** to process them

## 🛠️ Troubleshooting

### "Job already exists" error
Each job gets a unique ID. If you see this error, the job was already added.

### Database not found
The system automatically creates the database on first run.

### Import errors
Check that your JSON/CSV format matches the examples created by `--create-examples`.

### Encoding issues
All files are handled with UTF-8 encoding to support international characters.

## 🔄 Workflow Integration

After adding jobs manually, the rest of the application works normally:

1. **Add jobs manually** (using this system)
2. **Run scoring** (jobs get scored automatically)  
3. **Generate applications** (cover letters created)
4. **Prepare for interviews** (interview prep generated)

This manual system serves as a replacement for the automated scraping while maintaining full functionality of the job application workflow.

## 📞 Support

If you encounter issues:
1. Check that all required Python packages are installed
2. Ensure the database file can be created/accessed
3. Verify JSON/CSV file formats against the examples
4. Use `--view-jobs` to confirm jobs were added correctly 
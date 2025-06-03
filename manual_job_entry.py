#!/usr/bin/env python3
"""
Manual Job Entry System for Upwork AI Jobs Applier

This script provides multiple ways to manually add job information:
1. Interactive command-line interface
2. Import from JSON file
3. Import from CSV file
4. View existing jobs

Usage:
    python manual_job_entry.py --interactive
    python manual_job_entry.py --import-json jobs.json
    python manual_job_entry.py --import-csv jobs.csv
    python manual_job_entry.py --view-jobs
"""

import argparse
import json
import csv
import hashlib
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from src.database import ensure_db_exists, save_job, get_all_jobs
from src.structured_outputs import JobType

def generate_job_id(title: str, company: str = "", link: str = "") -> str:
    """Generate a unique job ID from title, company, and link."""
    unique_string = f"{title}_{company}_{link}_{datetime.now().isoformat()}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

def validate_job_type(job_type: str) -> str:
    """Validate and normalize job type."""
    job_type = job_type.strip().title()
    if job_type not in ["Fixed", "Hourly"]:
        print(f"Warning: Job type '{job_type}' is not standard. Using 'Fixed' as default.")
        return "Fixed"
    return job_type

def validate_payment_rate(payment_rate: str) -> str:
    """Validate and format payment rate."""
    if not payment_rate.strip():
        return ""
    
    # Add $ if not present
    if not payment_rate.startswith('$'):
        payment_rate = '$' + payment_rate
    
    return payment_rate

def interactive_job_entry() -> Dict[str, Any]:
    """Interactive command-line job entry."""
    print("\n" + "="*60)
    print("           MANUAL JOB ENTRY SYSTEM")
    print("="*60)
    print("Enter job details (press Enter to skip optional fields):\n")
    
    job_data = {}
    
    # Required fields
    job_data['title'] = input("📋 Job Title (required): ").strip()
    while not job_data['title']:
        job_data['title'] = input("❗ Job Title is required. Please enter: ").strip()
    
    job_data['description'] = input("📝 Job Description (required): ").strip()
    while not job_data['description']:
        job_data['description'] = input("❗ Job Description is required. Please enter: ").strip()
    
    # Optional fields
    print("\n--- Job Details ---")
    job_type = input("💼 Job Type (Fixed/Hourly) [Fixed]: ").strip() or "Fixed"
    job_data['job_type'] = validate_job_type(job_type)
    
    job_data['experience_level'] = input("🎯 Experience Level (Entry/Intermediate/Expert): ").strip()
    job_data['duration'] = input("⏱️  Duration (e.g., '1-3 months', 'More than 6 months'): ").strip()
    
    payment_rate = input("💰 Payment Rate (e.g., '$15-$25', '$500'): ").strip()
    job_data['payment_rate'] = validate_payment_rate(payment_rate)
    
    job_data['link'] = input("🔗 Job Link/URL: ").strip()
    job_data['proposal_requirements'] = input("📋 Proposal Requirements: ").strip()
    
    # Client Information
    print("\n--- Client Information (Optional) ---")
    client_joined = input("📅 Client Joined Date: ").strip()
    client_location = input("🌍 Client Location: ").strip()
    client_spent = input("💳 Client Total Spent: ").strip()
    client_hires_str = input("👥 Client Total Hires: ").strip()
    client_profile = input("🏢 Client Company Profile: ").strip()
    
    # Process client information
    if client_joined:
        job_data['client_joined_date'] = client_joined
    if client_location:
        job_data['client_location'] = client_location
    if client_spent:
        job_data['client_total_spent'] = validate_payment_rate(client_spent) if client_spent else ""
    if client_hires_str:
        try:
            job_data['client_total_hires'] = int(client_hires_str)
        except ValueError:
            print(f"Warning: Invalid number for client hires: {client_hires_str}")
    if client_profile:
        job_data['client_company_profile'] = client_profile
    
    # Generate job ID
    job_data['job_id'] = generate_job_id(job_data['title'], client_location, job_data.get('link', ''))
    
    return job_data

def import_from_json(file_path: str) -> list:
    """Import jobs from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jobs = []
        if isinstance(data, list):
            jobs = data
        elif isinstance(data, dict):
            jobs = [data]
        
        # Process each job
        processed_jobs = []
        for job in jobs:
            # Ensure required fields
            if not job.get('title') or not job.get('description'):
                print(f"Skipping job without title or description: {job}")
                continue
            
            # Generate job_id if not present
            if not job.get('job_id'):
                job['job_id'] = generate_job_id(
                    job['title'], 
                    job.get('client_location', ''), 
                    job.get('link', '')
                )
            
            # Validate job_type
            if job.get('job_type'):
                job['job_type'] = validate_job_type(job['job_type'])
            
            # Validate payment_rate
            if job.get('payment_rate'):
                job['payment_rate'] = validate_payment_rate(job['payment_rate'])
            
            processed_jobs.append(job)
        
        return processed_jobs
    
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return []

def import_from_csv(file_path: str) -> list:
    """Import jobs from CSV file."""
    try:
        jobs = []
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip empty rows
                if not row.get('title') or not row.get('description'):
                    continue
                
                # Convert string numbers to integers where needed
                if row.get('client_total_hires'):
                    try:
                        row['client_total_hires'] = int(row['client_total_hires'])
                    except ValueError:
                        del row['client_total_hires']
                
                # Generate job_id if not present
                if not row.get('job_id'):
                    row['job_id'] = generate_job_id(
                        row['title'], 
                        row.get('client_location', ''), 
                        row.get('link', '')
                    )
                
                # Validate fields
                if row.get('job_type'):
                    row['job_type'] = validate_job_type(row['job_type'])
                if row.get('payment_rate'):
                    row['payment_rate'] = validate_payment_rate(row['payment_rate'])
                
                jobs.append(row)
        
        return jobs
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def display_job(job: Dict[str, Any], index: int = None):
    """Display a single job in a formatted way."""
    prefix = f"Job #{index}: " if index is not None else "Job: "
    print(f"\n{prefix}{job.get('title', 'No Title')}")
    print("-" * (len(prefix) + len(job.get('title', 'No Title'))))
    
    fields_to_show = [
        ('Description', 'description'),
        ('Job Type', 'job_type'),
        ('Experience Level', 'experience_level'),
        ('Duration', 'duration'),
        ('Payment Rate', 'payment_rate'),
        ('Job Link', 'link'),
        ('Proposal Requirements', 'proposal_requirements'),
        ('Client Location', 'client_location'),
        ('Client Joined', 'client_joined_date'),
        ('Client Total Spent', 'client_total_spent'),
        ('Client Total Hires', 'client_total_hires'),
        ('Client Profile', 'client_company_profile'),
        ('Job ID', 'job_id'),
    ]
    
    for label, key in fields_to_show:
        value = job.get(key)
        if value:
            if key == 'description' and len(str(value)) > 200:
                value = str(value)[:200] + "..."
            print(f"{label}: {value}")

def view_jobs():
    """Display all jobs in the database."""
    jobs = get_all_jobs()
    
    if not jobs:
        print("No jobs found in the database.")
        return
    
    print(f"\n📊 Found {len(jobs)} jobs in the database:")
    print("=" * 60)
    
    for i, job in enumerate(jobs, 1):
        display_job(job, i)
        print()

def create_example_files():
    """Create example JSON and CSV files for reference."""
    
    # Example JSON
    example_json = [
        {
            "title": "AI Agent Developer",
            "description": "We need an experienced AI agent developer to build automated solutions...",
            "job_type": "Fixed",
            "experience_level": "Expert",
            "duration": "1-3 months",
            "payment_rate": "$1000-$3000",
            "link": "https://www.upwork.com/jobs/example1",
            "proposal_requirements": "Start your proposal with 'AI Expert' to show you read this",
            "client_location": "United States",
            "client_joined_date": "January 2023",
            "client_total_spent": "$50000",
            "client_total_hires": 25,
            "client_company_profile": "Tech startup focused on automation"
        }
    ]
    
    with open("example_jobs.json", "w", encoding="utf-8") as f:
        json.dump(example_json, f, indent=2)
    
    # Example CSV
    csv_headers = [
        "title", "description", "job_type", "experience_level", "duration",
        "payment_rate", "link", "proposal_requirements", "client_location",
        "client_joined_date", "client_total_spent", "client_total_hires",
        "client_company_profile"
    ]
    
    with open("example_jobs.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerow(example_json[0])
    
    print("✅ Created example_jobs.json and example_jobs.csv for reference")

def main():
    parser = argparse.ArgumentParser(description="Manual Job Entry System")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--interactive", "-i", action="store_true", help="Interactive job entry")
    group.add_argument("--import-json", metavar="file.json", help="Import jobs from JSON file")
    group.add_argument("--import-csv", metavar="file.csv", help="Import jobs from CSV file")
    group.add_argument("--view-jobs", "-v", action="store_true", help="View all jobs in database")
    group.add_argument("--create-examples", action="store_true", help="Create example JSON and CSV files")
    
    args = parser.parse_args()
    
    # Ensure database exists
    ensure_db_exists()
    
    if args.interactive:
        try:
            job_data = interactive_job_entry()
            
            print("\n" + "="*60)
            print("REVIEW YOUR ENTRY:")
            display_job(job_data)
            
            confirm = input("\n💾 Save this job? (y/N): ").strip().lower()
            if confirm == 'y' or confirm == 'yes':
                if save_job(job_data):
                    print("✅ Job saved successfully!")
                else:
                    print("❌ Failed to save job (may already exist)")
            else:
                print("❌ Job not saved")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
    
    elif args.import_json:
        jobs = import_from_json(args.import_json)
        if jobs:
            saved_count = 0
            for job in jobs:
                if save_job(job):
                    saved_count += 1
                    print(f"✅ Saved: {job['title']}")
                else:
                    print(f"⏭️  Skipped (already exists): {job['title']}")
            print(f"\n📊 Successfully imported {saved_count} out of {len(jobs)} jobs")
        else:
            print("❌ No valid jobs found in JSON file")
    
    elif args.import_csv:
        jobs = import_from_csv(args.import_csv)
        if jobs:
            saved_count = 0
            for job in jobs:
                if save_job(job):
                    saved_count += 1
                    print(f"✅ Saved: {job['title']}")
                else:
                    print(f"⏭️  Skipped (already exists): {job['title']}")
            print(f"\n📊 Successfully imported {saved_count} out of {len(jobs)} jobs")
        else:
            print("❌ No valid jobs found in CSV file")
    
    elif args.view_jobs:
        view_jobs()
    
    elif args.create_examples:
        create_example_files()

if __name__ == "__main__":
    main() 
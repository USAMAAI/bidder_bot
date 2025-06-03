#!/usr/bin/env python3
"""
Quick Job Entry - Simplified version for rapid job addition

Usage: python quick_add_job.py
"""

import hashlib
from datetime import datetime
from src.database import ensure_db_exists, save_job

def quick_add_job():
    """Quick job entry with minimal required fields."""
    print("\n🚀 QUICK JOB ENTRY")
    print("=" * 40)
    print("Enter the essential job details:\n")
    
    # Required fields only
    title = input("📋 Job Title: ").strip()
    if not title:
        print("❌ Job title is required!")
        return
    
    description = input("📝 Job Description: ").strip()
    if not description:
        print("❌ Job description is required!")
        return
    
    # Optional but commonly used fields
    job_type = input("💼 Job Type (Fixed/Hourly) [Fixed]: ").strip() or "Fixed"
    payment_rate = input("💰 Payment Rate: ").strip()
    link = input("🔗 Job URL: ").strip()
    
    # Add $ to payment rate if missing
    if payment_rate and not payment_rate.startswith('$'):
        payment_rate = '$' + payment_rate
    
    # Generate unique job ID
    unique_string = f"{title}_{datetime.now().isoformat()}"
    job_id = hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    # Create job data
    job_data = {
        'job_id': job_id,
        'title': title,
        'description': description,
        'job_type': job_type.title() if job_type.lower() in ['fixed', 'hourly'] else 'Fixed',
        'payment_rate': payment_rate,
        'link': link
    }
    
    # Remove empty fields
    job_data = {k: v for k, v in job_data.items() if v}
    
    print(f"\n📋 Job Summary:")
    print(f"   Title: {title}")
    print(f"   Type: {job_data['job_type']}")
    if payment_rate:
        print(f"   Rate: {payment_rate}")
    if link:
        print(f"   URL: {link}")
    
    confirm = input(f"\n💾 Save this job? (Y/n): ").strip().lower()
    if confirm in ['', 'y', 'yes']:
        if save_job(job_data):
            print(f"✅ Job '{title}' saved successfully!")
            return True
        else:
            print("❌ Failed to save job (may already exist)")
            return False
    else:
        print("❌ Job not saved")
        return False

def main():
    ensure_db_exists()
    
    while True:
        success = quick_add_job()
        
        if success:
            another = input("\n➕ Add another job? (y/N): ").strip().lower()
            if another not in ['y', 'yes']:
                break
        else:
            retry = input("\n🔄 Try again? (y/N): ").strip().lower()
            if retry not in ['y', 'yes']:
                break
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n👋 Goodbye!") 
#!/usr/bin/env python3
"""
Upwork AI Jobs Applier - Streamlit Web Application

A comprehensive web interface for managing job applications with AI-powered
cover letter generation and job scoring.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import asyncio
import hashlib
from datetime import datetime
from typing import List, Dict, Any
import os

# Import existing modules
from src.database import (
    ensure_db_exists, 
    get_all_jobs, 
    get_jobs_by_criteria,
    get_job_by_id,
    save_job,
    update_job,
    delete_job,
    delete_multiple_jobs,
    reset_job_score,
    reset_multiple_job_scores,
    get_database_stats,
    create_user,
    authenticate_user,
    create_session,
    validate_session,
    invalidate_session,
    update_last_login,
    get_user_by_id,
    cleanup_expired_sessions,
    is_admin_user,
    get_all_users,
    get_all_jobs_admin,
    get_system_stats,
    delete_user_admin,
    toggle_user_status,
    promote_user_to_admin,
    demote_admin_user,
    get_prompt_by_type,
    get_all_prompts,
    create_or_update_prompt,
    delete_prompt,
    initialize_default_prompts
)
from src.utils import read_text_file
from src.user_job_processor import UserJobProcessor

# Page configuration
st.set_page_config(
    page_title="Upwork AI Jobs Applier",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .job-card {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: white;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .warning-message {
        color: #ffc107;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables."""
    if 'jobs_data' not in st.session_state:
        st.session_state.jobs_data = None
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None
    if 'api_key_set' not in st.session_state:
        st.session_state.api_key_set = bool(os.getenv('OPENAI_API_KEY'))
    if 'selected_jobs' not in st.session_state:
        st.session_state.selected_jobs = []
    if 'edit_job_id' not in st.session_state:
        st.session_state.edit_job_id = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False

def check_authentication():
    """Check if user is authenticated and session is valid."""
    try:
        # Ensure database is properly initialized
        ensure_db_exists()
        
        if st.session_state.session_id:
            valid, user_data = validate_session(st.session_state.session_id)
            if valid:
                st.session_state.authenticated = True
                st.session_state.user = user_data
                return True
            else:
                # Session expired or invalid
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.session_id = None
        
        return False
    except Exception as e:
        print(f"Authentication check error: {e}")
        # Reset authentication state on error
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.session_id = None
        return False

def login_page():
    """Display login page."""
    st.markdown('<h1 class="main-header">🔐 Welcome to Upwork AI Jobs Applier</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Toggle between login and signup
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                st.subheader("Login to Your Account")
                
                username = st.text_input("Username or Email", placeholder="Enter your username or email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                remember_me = st.checkbox("Remember me for 7 days")
                
                login_button = st.form_submit_button("🔑 Login", type="primary")
                
                if login_button:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        with st.spinner("Logging in..."):
                            success, user_data, message = authenticate_user(username, password)
                            
                            if success:
                                # Create session
                                duration = 168 if remember_me else 24  # 7 days or 1 day
                                session_id = create_session(user_data['user_id'], duration)
                                
                                # Update session state
                                st.session_state.authenticated = True
                                st.session_state.user = user_data
                                st.session_state.session_id = session_id
                                
                                st.success(f"Welcome back, {user_data['username']}!")
                                st.rerun()
                            else:
                                st.error(message)
        
        with tab2:
            with st.form("signup_form"):
                st.subheader("Create New Account")
                
                new_username = st.text_input("Username", placeholder="Choose a username")
                new_email = st.text_input("Email", placeholder="Enter your email address")
                new_password = st.text_input("Password", type="password", placeholder="Choose a strong password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                # Password requirements
                st.caption("Password must be at least 8 characters long")
                
                signup_button = st.form_submit_button("📝 Create Account", type="primary")
                
                if signup_button:
                    # Validation
                    errors = []
                    
                    if not new_username or len(new_username) < 3:
                        errors.append("Username must be at least 3 characters long")
                    
                    if not new_email or "@" not in new_email:
                        errors.append("Please enter a valid email address")
                    
                    if not new_password or len(new_password) < 8:
                        errors.append("Password must be at least 8 characters long")
                    
                    if new_password != confirm_password:
                        errors.append("Passwords do not match")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        with st.spinner("Creating account..."):
                            success, result = create_user(new_username, new_email, new_password)
                            
                            if success:
                                st.success("Account created successfully! Please login with your credentials.")
                                # Clear form
                                st.session_state.show_signup = False
                            else:
                                st.error(f"Failed to create account: {result}")
        
        # App info
        st.divider()
        st.markdown("""
        ### 🤖 About This App
        **Upwork AI Jobs Applier** helps you:
        - 📋 Manage job opportunities from Upwork
        - ⚡ AI-powered job scoring based on your profile
        - ✉️ Generate personalized cover letters
        - 🎤 Prepare for interviews with AI assistance
        
        **Secure & Private**: Your data is encrypted and stored securely.
        """)

def logout():
    """Handle user logout."""
    if st.session_state.session_id:
        invalidate_session(st.session_state.session_id)
    
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.session_id = None
    st.rerun()

def get_current_user_id():
    """Get the current authenticated user's ID."""
    if st.session_state.authenticated and st.session_state.user:
        return st.session_state.user['user_id']
    return None

def load_jobs_data():
    """Load jobs data from database for current user."""
    ensure_db_exists()
    user_id = get_current_user_id()
    jobs = get_all_jobs(user_id)
    if jobs:
        df = pd.DataFrame(jobs)
        # Convert created_at to datetime if present
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
        return df
    return pd.DataFrame()

def generate_job_id(title: str, description: str = "") -> str:
    """Generate a unique job ID."""
    unique_string = f"{title}_{description[:50]}_{datetime.now().isoformat()}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

def show_edit_job_modal(job_id):
    """Show modal for editing job details."""
    user_id = get_current_user_id()
    job = get_job_by_id(job_id, user_id)
    if not job:
        st.error("Job not found!")
        return
    
    with st.form(f"edit_job_{job_id}"):
        st.subheader(f"✏️ Edit Job: {job.get('title', 'Unknown')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Job Title*", value=job.get('title', ''))
            job_type = st.selectbox("Job Type", ["Fixed", "Hourly"], 
                                  index=0 if job.get('job_type') == 'Fixed' else 1)
            payment_rate = st.text_input("Payment Rate", value=job.get('payment_rate', '') or '')
            duration = st.text_input("Duration", value=job.get('duration', '') or '')
            
        with col2:
            experience_levels = ["", "Entry", "Intermediate", "Expert"]
            exp_index = 0
            if job.get('experience_level') in experience_levels:
                exp_index = experience_levels.index(job.get('experience_level'))
            experience_level = st.selectbox("Experience Level", experience_levels, index=exp_index)
            link = st.text_input("Job URL", value=job.get('link', '') or '')
            proposal_requirements = st.text_area("Proposal Requirements", 
                                                value=job.get('proposal_requirements', '') or '')
        
        description = st.text_area("Job Description*", 
                                 value=job.get('description', ''),
                                 height=200)
        
        st.subheader("Client Information")
        col1, col2 = st.columns(2)
        
        with col1:
            client_location = st.text_input("Client Location", value=job.get('client_location', '') or '')
            client_joined_date = st.text_input("Client Joined Date", value=job.get('client_joined_date', '') or '')
            client_total_spent = st.text_input("Client Total Spent", value=job.get('client_total_spent', '') or '')
            
        with col2:
            client_total_hires = st.number_input("Client Total Hires", 
                                               min_value=0, value=job.get('client_total_hires', 0) or 0, step=1)
            client_company_profile = st.text_area("Client Company Profile",
                                                 value=job.get('client_company_profile', '') or '',
                                                 height=100)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("💾 Save Changes", type="primary"):
                # Prepare updated data
                updated_data = {
                    'title': title,
                    'description': description,
                    'job_type': job_type,
                    'experience_level': experience_level or None,
                    'duration': duration or None,
                    'payment_rate': payment_rate or None,
                    'link': link or None,
                    'proposal_requirements': proposal_requirements or None,
                    'client_location': client_location or None,
                    'client_joined_date': client_joined_date or None,
                    'client_total_spent': client_total_spent or None,
                    'client_total_hires': client_total_hires if client_total_hires > 0 else None,
                    'client_company_profile': client_company_profile or None
                }
                
                # Remove None values
                updated_data = {k: v for k, v in updated_data.items() if v is not None}
                
                if update_job(job_id, updated_data, user_id):
                    st.success("✅ Job updated successfully!")
                    st.session_state.edit_job_id = None
                    st.rerun()
                else:
                    st.error("❌ Failed to update job")
        
        with col2:
            if st.form_submit_button("🔄 Reset Score"):
                if reset_job_score(job_id, user_id):
                    st.success("✅ Score reset! Job will be reprocessed.")
                    st.rerun()
                else:
                    st.error("❌ Failed to reset score")
        
        with col3:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.edit_job_id = None
                st.rerun()

async def regenerate_single_job(job_id):
    """Regenerate application for a single job."""
    try:
        user_id = get_current_user_id()
        
        # Reset the job score first
        if not reset_job_score(job_id, user_id):
            return False, "Failed to reset job score"
        
        # Load profile
        profile = read_text_file("./files/profile.md")
        
        # Create processor for single job
        processor = UserJobProcessor(user_id=user_id, profile=profile, batch_size=1, min_score=1)
        
        # Get the specific job
        job = get_job_by_id(job_id, user_id)
        if not job:
            return False, "Job not found"
        
        # Process just this job
        jobs = [job]
        scores = await processor.score_jobs(jobs)
        
        if scores:
            # Update job with new score
            scored_job = dict(job)
            scored_job['score'] = scores[0]['score']
            update_job(job_id, {'score': scores[0]['score']}, user_id)
            
            # Generate application if score is high enough
            if scores[0]['score'] >= processor.min_score:
                applications = await processor.process_jobs_batch([scored_job])
                if applications:
                    processor.save_applications_to_file(applications)
                    return True, f"Job regenerated successfully! Score: {scores[0]['score']}/10"
                else:
                    return True, f"Job scored {scores[0]['score']}/10 but application generation failed"
            else:
                return True, f"Job scored {scores[0]['score']}/10 (below threshold for application generation)"
        else:
            return False, "Failed to score job"
            
    except Exception as e:
        return False, f"Error during regeneration: {str(e)}"

async def run_job_processing(user_id: str, min_score: int, batch_size: int):
    """Run the job processing asynchronously for a specific user."""
    try:
        # Load freelancer profile
        profile = read_text_file("./files/profile.md")
        
        # Create processor
        processor = UserJobProcessor(
            user_id=user_id,
            profile=profile,
            batch_size=batch_size,
            min_score=min_score
        )
        
        # Run processing
        result = await processor.process_user_jobs()
        return result
    except Exception as e:
        return {
            'success': False,
            'message': f"Error during processing: {str(e)}",
            'stats': {'total_jobs': 0, 'scored_jobs': 0, 'high_scoring_jobs': 0, 'applications_generated': 0}
        }

def process_jobs_async(min_score: int, batch_size: int):
    """Process jobs with progress tracking."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("🔄 Starting job processing...")
    progress_bar.progress(10)
    
    try:
        # Check if profile exists
        if not os.path.exists("./files/profile.md"):
            st.error("❌ Profile file not found. Please ensure ./files/profile.md exists.")
            return
        
        status_text.text("📄 Loading profile...")
        progress_bar.progress(20)
        
        # Get current user ID
        user_id = get_current_user_id()
        if not user_id:
            st.error("❌ User not authenticated.")
            return
        
        status_text.text("🔄 Processing jobs...")
        progress_bar.progress(50)
        
        # Run in asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_job_processing(user_id, min_score, batch_size))
        loop.close()
        
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        
        if result['success']:
            st.success("🎉 Job processing completed successfully!")
            
            # Show results
            stats = result['stats']
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Jobs Processed", stats['total_jobs'])
            with col2:
                st.metric("Jobs Scored", stats['scored_jobs'])
            with col3:
                st.metric("High Scoring", stats['high_scoring_jobs'])
            with col4:
                st.metric("Applications Generated", stats['applications_generated'])
        else:
            st.error(f"❌ Processing failed: {result['message']}")
        
        st.session_state.jobs_data = None  # Force refresh
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during processing: {e}")
        progress_bar.empty()
        status_text.empty()

def dashboard_page():
    """Main dashboard page."""
    st.markdown('<h1 class="main-header">🤖 Upwork AI Jobs Applier Dashboard</h1>', unsafe_allow_html=True)
    
    # User welcome message
    if st.session_state.user:
        st.markdown(f"👋 Welcome back, **{st.session_state.user['username']}**!")
    
    # Load data
    df = load_jobs_data()
    
    if df.empty:
        st.warning("No jobs found in database. Add some jobs to get started!")
        return
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    total_jobs = len(df)
    processed_jobs = len(df[df['score'].notna()])
    high_scoring_jobs = len(df[df['score'] >= 7]) if 'score' in df.columns else 0
    avg_score = df['score'].mean() if 'score' in df.columns and not df['score'].isna().all() else 0
    
    with col1:
        st.metric("Total Jobs", total_jobs)
    with col2:
        st.metric("Processed Jobs", processed_jobs)
    with col3:
        st.metric("High Scoring (≥7)", high_scoring_jobs)
    with col4:
        st.metric("Average Score", f"{avg_score:.1f}" if avg_score > 0 else "N/A")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Score Distribution")
        if 'score' in df.columns and not df['score'].isna().all():
            scored_df = df[df['score'].notna()]
            fig = px.histogram(scored_df, x='score', nbins=10, 
                             title="Job Score Distribution",
                             labels={'score': 'Score', 'count': 'Number of Jobs'})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No scored jobs to display")
    
    with col2:
        st.subheader("📈 Jobs by Type")
        if 'job_type' in df.columns:
            job_type_counts = df['job_type'].value_counts()
            fig = px.pie(values=job_type_counts.values, names=job_type_counts.index,
                        title="Distribution by Job Type")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No job type data available")
    
    # Recent jobs
    st.subheader("🕒 Recent Jobs")
    if 'created_at' in df.columns:
        recent_jobs = df.sort_values('created_at', ascending=False).head(5)
    else:
        recent_jobs = df.head(5)
    
    for _, job in recent_jobs.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**{job.get('title', 'No Title')}**")
                st.write(f"Type: {job.get('job_type', 'N/A')} | Payment: {job.get('payment_rate', 'N/A')}")
            with col2:
                score = job.get('score')
                if pd.notna(score):
                    if score >= 7:
                        st.success(f"Score: {score}/10")
                    elif score >= 5:
                        st.warning(f"Score: {score}/10")
                    else:
                        st.error(f"Score: {score}/10")
                else:
                    st.info("Not scored")
            with col3:
                if job.get('link'):
                    st.link_button("View Job", job['link'])
            with col4:
                if st.button("🗑️", key=f"dash_delete_{job['job_id']}", help="Quick Delete"):
                    user_id = get_current_user_id()
                    if delete_job(job['job_id'], user_id):
                        st.success("🗑️ Job deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete")
            st.divider()
    
    # Dashboard cleanup section
    st.divider()
    st.subheader("🧹 Quick Cleanup")
    
    col1, col2, col3, col4 = st.columns(4)
    user_id = get_current_user_id()
    
    with col1:
        # Delete low scoring jobs
        low_score_count = len(df[df['score'] < 4]) if 'score' in df.columns else 0
        if st.button(f"🗑️ Delete Low Scores ({low_score_count})", disabled=low_score_count == 0):
            if low_score_count > 0:
                low_score_ids = df[df['score'] < 4]['job_id'].tolist()
                deleted = delete_multiple_jobs(low_score_ids, user_id)
                st.success(f"🗑️ Deleted {deleted} low-scoring jobs!")
                st.rerun()
    
    with col2:
        # Reset all unprocessed jobs
        unprocessed_count = len(df[df['score'].isna()]) if 'score' in df.columns else len(df)
        if st.button(f"🔄 Reset Unprocessed ({unprocessed_count})", disabled=unprocessed_count == 0):
            if unprocessed_count > 0:
                unprocessed_ids = df[df['score'].isna()]['job_id'].tolist()
                reset_count = reset_multiple_job_scores(unprocessed_ids, user_id)
                st.success(f"🔄 Reset {reset_count} jobs for reprocessing!")
    
    with col3:
        # Delete old jobs (older than 30 days)
        if 'created_at' in df.columns:
            thirty_days_ago = pd.Timestamp.now() - pd.Timedelta(days=30)
            old_jobs = df[df['created_at'] < thirty_days_ago]
            old_count = len(old_jobs)
            if st.button(f"🗓️ Delete Old Jobs ({old_count})", disabled=old_count == 0):
                if old_count > 0:
                    old_job_ids = old_jobs['job_id'].tolist()
                    deleted = delete_multiple_jobs(old_job_ids, user_id)
                    st.success(f"🗓️ Deleted {deleted} old jobs!")
                    st.rerun()
        else:
            st.button("🗓️ Delete Old Jobs (0)", disabled=True)
    
    with col4:
        # Show database stats
        if st.button("📊 Database Stats"):
            stats = get_database_stats(user_id)
            with st.expander("📊 Database Statistics", expanded=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Total Jobs", stats['total_jobs'])
                    st.metric("Processed Jobs", stats['processed_jobs'])
                    st.metric("High Scoring", stats['high_scoring_jobs'])
                with col_b:
                    st.metric("Average Score", stats['average_score'])
                    st.metric("Recent Jobs (7d)", stats['recent_jobs'])
                
                if stats['jobs_by_type']:
                    st.write("**Jobs by Type:**")
                    for job_type, count in stats['jobs_by_type'].items():
                        st.write(f"- {job_type}: {count}")

def add_job_page():
    """Add new job page."""
    st.header("➕ Add New Job")
    
    with st.form("add_job_form"):
        st.subheader("Job Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Job Title*", placeholder="Enter job title")
            job_type = st.selectbox("Job Type", ["Fixed", "Hourly"])
            payment_rate = st.text_input("Payment Rate", placeholder="e.g., $15-25, $1000")
            duration = st.text_input("Duration", placeholder="e.g., 1-3 months")
            
        with col2:
            experience_level = st.selectbox("Experience Level", 
                                          ["", "Entry", "Intermediate", "Expert"])
            link = st.text_input("Job URL", placeholder="https://...")
            proposal_requirements = st.text_area("Proposal Requirements", 
                                                placeholder="Special client instructions...")
        
        description = st.text_area("Job Description*", 
                                 placeholder="Enter the full job description...",
                                 height=200)
        
        st.subheader("Client Information (Optional)")
        col1, col2 = st.columns(2)
        
        with col1:
            client_location = st.text_input("Client Location")
            client_joined_date = st.text_input("Client Joined Date")
            client_total_spent = st.text_input("Client Total Spent")
            
        with col2:
            client_total_hires = st.number_input("Client Total Hires", 
                                               min_value=0, value=0, step=1)
            client_company_profile = st.text_area("Client Company Profile",
                                                 height=100)
        
        submitted = st.form_submit_button("Add Job", type="primary")
        
        if submitted:
            if not title or not description:
                st.error("Title and Description are required!")
            else:
                user_id = get_current_user_id()
                
                # Create job data
                job_data = {
                    'job_id': generate_job_id(title, description),
                    'title': title,
                    'description': description,
                    'job_type': job_type,
                    'experience_level': experience_level or None,
                    'duration': duration or None,
                    'payment_rate': f"${payment_rate}" if payment_rate and not payment_rate.startswith('$') else payment_rate or None,
                    'link': link or None,
                    'proposal_requirements': proposal_requirements or None,
                    'client_location': client_location or None,
                    'client_joined_date': client_joined_date or None,
                    'client_total_spent': f"${client_total_spent}" if client_total_spent and not client_total_spent.startswith('$') else client_total_spent or None,
                    'client_total_hires': client_total_hires if client_total_hires > 0 else None,
                    'client_company_profile': client_company_profile or None
                }
                
                # Remove None values
                job_data = {k: v for k, v in job_data.items() if v is not None}
                
                # Save to database
                if save_job(job_data, user_id):
                    st.success(f"✅ Job '{title}' added successfully!")
                    st.session_state.jobs_data = None  # Force refresh
                    st.rerun()
                else:
                    st.error("❌ Failed to save job (may already exist)")

def view_jobs_page():
    """View and manage jobs page with comprehensive management features."""
    st.header("📋 Manage Jobs")
    
    # Show edit modal if needed
    if st.session_state.edit_job_id:
        show_edit_job_modal(st.session_state.edit_job_id)
        return
    
    df = load_jobs_data()
    user_id = get_current_user_id()
    
    if df.empty:
        st.info("No jobs found. Add some jobs to get started!")
        return
    
    # Bulk operations bar
    st.subheader("🎛️ Bulk Operations")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Track selected jobs
    if 'selected_jobs_temp' not in st.session_state:
        st.session_state.selected_jobs_temp = []
    
    with col1:
        if st.button("☑️ Select All"):
            st.session_state.selected_jobs_temp = df['job_id'].tolist()
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset Scores"):
            if st.session_state.selected_jobs_temp:
                count = reset_multiple_job_scores(st.session_state.selected_jobs_temp, user_id)
                st.success(f"✅ Reset scores for {count} jobs!")
                st.session_state.selected_jobs_temp = []
                st.rerun()
            else:
                st.warning("No jobs selected!")
    
    with col3:
        if st.button("🗑️ Delete Selected", key="manage_jobs_delete_selected"):
            if st.session_state.selected_jobs_temp:
                st.session_state.confirm_delete = True
            else:
                st.warning("No jobs selected!")
    
    with col4:
        if st.button("📊 Process Selected"):
            if st.session_state.selected_jobs_temp:
                # Reset scores for selected jobs and redirect to processing
                reset_multiple_job_scores(st.session_state.selected_jobs_temp, user_id)
                st.success(f"✅ {len(st.session_state.selected_jobs_temp)} jobs queued for processing!")
                st.info("Go to 'Process Jobs' page to run the processing.")
                st.session_state.selected_jobs_temp = []
            else:
                st.warning("No jobs selected!")
    
    with col5:
        if st.button("❌ Clear Selection"):
            st.session_state.selected_jobs_temp = []
            st.rerun()
    
    # Confirm delete dialog
    if st.session_state.get('confirm_delete', False):
        with st.container():
            st.error(f"⚠️ Are you sure you want to delete {len(st.session_state.selected_jobs_temp)} jobs?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete", type="primary"):
                    count = delete_multiple_jobs(st.session_state.selected_jobs_temp, user_id)
                    st.success(f"🗑️ Deleted {count} jobs!")
                    st.session_state.selected_jobs_temp = []
                    st.session_state.confirm_delete = False
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.confirm_delete = False
                    st.rerun()
    
    st.divider()
    
    # Filters
    st.subheader("🔍 Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        job_type_filter = st.selectbox("Job Type", ["All"] + list(df['job_type'].unique()) if 'job_type' in df.columns else ["All"])
    
    with col2:
        score_filter = st.selectbox("Score Range", ["All", "High (≥7)", "Medium (4-6)", "Low (<4)", "Unscored"])
    
    with col3:
        experience_filter = st.selectbox("Experience Level", 
                                       ["All"] + list(df['experience_level'].dropna().unique()) if 'experience_level' in df.columns else ["All"])
    
    with col4:
        search_term = st.text_input("Search in titles")
    
    # Apply filters
    filtered_df = df.copy()
    
    if job_type_filter != "All":
        filtered_df = filtered_df[filtered_df['job_type'] == job_type_filter]
    
    if score_filter != "All":
        if score_filter == "High (≥7)":
            filtered_df = filtered_df[filtered_df['score'] >= 7]
        elif score_filter == "Medium (4-6)":
            filtered_df = filtered_df[(filtered_df['score'] >= 4) & (filtered_df['score'] < 7)]
        elif score_filter == "Low (<4)":
            filtered_df = filtered_df[filtered_df['score'] < 4]
        elif score_filter == "Unscored":
            filtered_df = filtered_df[filtered_df['score'].isna()]
    
    if experience_filter != "All":
        filtered_df = filtered_df[filtered_df['experience_level'] == experience_filter]
    
    if search_term:
        filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
    
    st.write(f"Showing {len(filtered_df)} of {len(df)} jobs")
    
    # Display jobs with management controls
    for i, (_, job) in enumerate(filtered_df.iterrows()):
        with st.container():
            # Selection checkbox
            col_check, col_main, col_score, col_actions = st.columns([0.5, 4, 1, 2])
            
            with col_check:
                selected = st.checkbox("", key=f"select_{job['job_id']}", 
                                     value=job['job_id'] in st.session_state.selected_jobs_temp)
                if selected and job['job_id'] not in st.session_state.selected_jobs_temp:
                    st.session_state.selected_jobs_temp.append(job['job_id'])
                elif not selected and job['job_id'] in st.session_state.selected_jobs_temp:
                    st.session_state.selected_jobs_temp.remove(job['job_id'])
            
            with col_main:
                st.write(f"**{job.get('title', 'No Title')}**")
                description = job.get('description', 'No description')
                if len(description) > 200:
                    description = description[:200] + "..."
                st.write(description)
                
                # Job details
                details = []
                if job.get('job_type'):
                    details.append(f"Type: {job['job_type']}")
                if job.get('payment_rate'):
                    details.append(f"Payment: {job['payment_rate']}")
                if job.get('experience_level'):
                    details.append(f"Level: {job['experience_level']}")
                if job.get('duration'):
                    details.append(f"Duration: {job['duration']}")
                
                if details:
                    st.write(" | ".join(details))
            
            with col_score:
                score = job.get('score')
                if pd.notna(score):
                    if score >= 7:
                        st.success(f"Score: {score}/10")
                    elif score >= 4:
                        st.warning(f"Score: {score}/10")
                    else:
                        st.error(f"Score: {score}/10")
                else:
                    st.info("Not scored")
            
            with col_actions:
                # Action buttons in a more compact layout
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button("✏️", key=f"edit_{job['job_id']}", help="Edit Job"):
                        st.session_state.edit_job_id = job['job_id']
                        st.rerun()
                    
                    if st.button("🔄", key=f"regen_{job['job_id']}", help="Regenerate"):
                        # Show regeneration progress
                        with st.spinner("Regenerating..."):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            success, message = loop.run_until_complete(regenerate_single_job(job['job_id']))
                            loop.close()
                            
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                            st.rerun()
                
                with btn_col2:
                    if st.button("🗑️", key=f"delete_{job['job_id']}", help="Delete Job"):
                        st.session_state[f"confirm_delete_{job['job_id']}"] = True
                        st.rerun()
                    
                    if job.get('link'):
                        st.link_button("🔗", job['link'], help="View Original")
            
            # Individual delete confirmation
            if st.session_state.get(f"confirm_delete_{job['job_id']}", False):
                with st.container():
                    st.error(f"⚠️ Delete '{job.get('title', 'Unknown')}'?")
                    conf_col1, conf_col2 = st.columns(2)
                    with conf_col1:
                        if st.button("✅ Yes", key=f"conf_yes_{job['job_id']}"):
                            if delete_job(job['job_id'], user_id):
                                st.success("🗑️ Job deleted!")
                                st.session_state[f"confirm_delete_{job['job_id']}"] = False
                                st.rerun()
                            else:
                                st.error("Failed to delete job")
                    with conf_col2:
                        if st.button("❌ No", key=f"conf_no_{job['job_id']}"):
                            st.session_state[f"confirm_delete_{job['job_id']}"] = False
                            st.rerun()
            
            # Show more details in expander
            with st.expander("📄 Details"):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    if job.get('client_location'):
                        st.write(f"**Client Location:** {job['client_location']}")
                    if job.get('client_total_spent'):
                        st.write(f"**Client Spent:** {job['client_total_spent']}")
                    if job.get('client_total_hires'):
                        st.write(f"**Client Hires:** {job['client_total_hires']}")
                    if job.get('created_at'):
                        st.write(f"**Added:** {job['created_at']}")
                
                with detail_col2:
                    if job.get('proposal_requirements'):
                        st.write(f"**Requirements:** {job['proposal_requirements']}")
                    if job.get('client_joined_date'):
                        st.write(f"**Client Joined:** {job['client_joined_date']}")
                    if job.get('client_company_profile'):
                        st.write(f"**Company:** {job['client_company_profile']}")
            
            st.divider()
    
    # Show selection summary
    if st.session_state.selected_jobs_temp:
        st.info(f"📌 {len(st.session_state.selected_jobs_temp)} jobs selected")

def process_jobs_page():
    """Process jobs page."""
    st.header("⚡ Process Jobs")
    
    # Check API key
    if not st.session_state.api_key_set:
        st.error("❌ OpenAI API key not set. Please set it in the settings page.")
        return
    
    df = load_jobs_data()
    user_id = get_current_user_id()
    
    if df.empty:
        st.info("No jobs found. Add some jobs first!")
        return
    
    # Get unprocessed jobs
    unprocessed_jobs = df[df['score'].isna()] if 'score' in df.columns else df
    processed_jobs = df[df['score'].notna()] if 'score' in df.columns else pd.DataFrame()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Unprocessed Jobs", len(unprocessed_jobs))
    with col2:
        st.metric("Processed Jobs", len(processed_jobs))
    
    if len(unprocessed_jobs) == 0:
        st.success("✅ All jobs have been processed!")
        return
    
    # Processing settings
    st.subheader("⚙️ Processing Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        min_score = st.slider("Minimum Score for Applications", 1, 10, 7)
    with col2:
        batch_size = st.slider("Batch Size", 1, 5, 3)
    
    # Show unprocessed jobs
    st.subheader("📋 Unprocessed Jobs")
    for _, job in unprocessed_jobs.head(5).iterrows():
        st.write(f"• **{job.get('title', 'No Title')}** ({job.get('job_type', 'N/A')})")
    
    if len(unprocessed_jobs) > 5:
        st.write(f"... and {len(unprocessed_jobs) - 5} more jobs")
    
    # Process button
    if st.button("🚀 Process All Jobs", type="primary"):
        process_jobs_async(min_score, batch_size)

def applications_page():
    """View generated applications page with advanced management features."""
    st.header("📄 Generated Applications")
    
    user_id = get_current_user_id()
    is_admin = is_current_user_admin()
    
    # Show admin notifications for high scores
    if is_admin:
        show_admin_notifications()
    
    # Determine which applications to show
    if is_admin:
        col1, col2 = st.columns(2)
        with col1:
            view_mode = st.selectbox("View Applications", ["My Applications", "All Applications"])
        with col2:
            if view_mode == "All Applications":
                st.info("👑 Admin view: Showing applications from all users")
    else:
        view_mode = "My Applications"
    
    # Check cover letter files
    if view_mode == "My Applications":
        # User-specific file
        cover_letter_file = f"./data/users/{user_id}/cover_letters.md"
        if not os.path.exists(cover_letter_file):
            st.info("No applications generated yet. Process some jobs first!")
            return
    else:
        # Global file for admin
        cover_letter_file = "./data/cover_letter.md"
        if not os.path.exists(cover_letter_file):
            st.info("No applications found in the system.")
            return
    
    try:
        # Parse applications
        applications = parse_applications_file(cover_letter_file)
        
        if not applications:
            st.info("No applications found in the file.")
            return
        
        # Filter applications by user if needed
        if view_mode == "My Applications":
            if is_admin:
                # Admin viewing their own applications - filter by admin's user_id
                applications = [app for app in applications if app.get('user_id') == user_id]
            else:
                # Regular users - should only see their own applications (already from their file)
                # But double-check to ensure data isolation
                applications = [app for app in applications if app.get('user_id') == user_id]
        
        # Header with stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Applications", len(applications))
        with col2:
            unique_dates = len(set(app.get('date', 'Unknown') for app in applications))
            st.metric("Processing Sessions", unique_dates)
        with col3:
            avg_cover_length = sum(len(app.get('cover_letter', '')) for app in applications) // len(applications) if applications else 0
            st.metric("Avg Cover Letter Length", f"{avg_cover_length} chars")
        with col4:
            with_interview_prep = sum(1 for app in applications if app.get('interview_prep'))
            st.metric("With Interview Prep", with_interview_prep)
        
        st.divider()
        
        # Filters and Controls
        st.subheader("🔍 Filters & Controls")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Search
            search_term = st.text_input("🔍 Search in titles", placeholder="Enter job title keywords...")
        
        with col2:
            # Date filter
            dates = sorted(set(app.get('date', 'Unknown') for app in applications), reverse=True)
            selected_date = st.selectbox("📅 Filter by Date", ["All Dates"] + dates)
        
        with col3:
            # User filter (admin only)
            if is_admin and view_mode == "All Applications":
                users = sorted(set(app.get('user_id', 'Unknown') for app in applications))
                selected_user = st.selectbox("👤 Filter by User", ["All Users"] + users)
            else:
                selected_user = "All Users"
        
        with col4:
            # View mode
            display_mode = st.selectbox("👁️ View Mode", ["Cards", "Table", "Detailed"])
        
        # Apply filters
        filtered_apps = applications.copy()
        
        if search_term:
            filtered_apps = [app for app in filtered_apps 
                           if search_term.lower() in app.get('title', '').lower()]
        
        if selected_date != "All Dates":
            filtered_apps = [app for app in filtered_apps 
                           if app.get('date') == selected_date]
        
        if selected_user != "All Users":
            filtered_apps = [app for app in filtered_apps 
                           if app.get('user_id') == selected_user]
        
        st.write(f"Showing {len(filtered_apps)} of {len(applications)} applications")
        
        # Pagination
        items_per_page = st.selectbox("📄 Items per Page", [5, 10, 20, 50], index=1)
        total_pages = (len(filtered_apps) + items_per_page - 1) // items_per_page
        
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.slider("Page", 1, total_pages, 1)
        else:
            page = 1
        
        # Calculate start and end indices
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(filtered_apps))
        page_apps = filtered_apps[start_idx:end_idx]
        
        st.divider()
        
        # Display applications based on view mode
        if display_mode == "Cards":
            display_applications_cards(page_apps, is_admin)
        elif display_mode == "Table":
            display_applications_table(page_apps, is_admin)
        else:  # Detailed
            display_applications_detailed(page_apps, start_idx, is_admin)
        
        # Export options
        st.divider()
        st.subheader("📤 Export Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Copy All Cover Letters", key="apps_export_cover_letters"):
                all_covers = "\n\n" + "="*80 + "\n\n".join([
                    f"JOB: {app.get('title', 'Unknown')}\nUSER: {app.get('user_id', 'Unknown')}\n\n{app.get('cover_letter', '')}"
                    for app in filtered_apps
                ])
                st.code(all_covers, language="text")
        
        with col2:
            if st.button("🎤 Copy All Interview Prep", key="apps_export_interview_prep"):
                all_interviews = "\n\n" + "="*80 + "\n\n".join([
                    f"JOB: {app.get('title', 'Unknown')}\nUSER: {app.get('user_id', 'Unknown')}\n\n{app.get('interview_prep', '')}"
                    for app in filtered_apps if app.get('interview_prep')
                ])
                st.code(all_interviews, language="text")
        
        with col3:
            if st.button("📊 Generate Summary Report", key="apps_export_summary"):
                generate_applications_summary(filtered_apps)
    
    except Exception as e:
        st.error(f"Error reading applications file: {e}")
        with st.expander("🐛 Debug Information"):
            st.text(f"Error: {str(e)}")
            st.text(f"Error type: {type(e)}")

def show_admin_notifications():
    """Show high score notifications for admins."""
    notifications_file = "./data/high_score_notifications.json"
    
    if not os.path.exists(notifications_file):
        return
    
    try:
        import json
        with open(notifications_file, 'r') as f:
            notifications = json.load(f)
        
        if not notifications:
            return
        
        # Show recent notifications (last 10)
        recent_notifications = sorted(notifications, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
        
        if recent_notifications:
            with st.expander("🔔 Recent High Score Notifications", expanded=True):
                st.write("**Recent jobs with scores ≥ 7.0:**")
                
                for notif in recent_notifications:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**{notif.get('job_title', 'Unknown')}**")
                    
                    with col2:
                        st.write(f"👤 {notif.get('username', 'Unknown')}")
                    
                    with col3:
                        score = notif.get('score', 0)
                        if score >= 9:
                            st.success(f"🌟 {score}/10")
                        elif score >= 7:
                            st.warning(f"⭐ {score}/10")
                    
                    with col4:
                        timestamp = notif.get('timestamp', '')
                        if timestamp:
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                st.caption(dt.strftime('%Y-%m-%d %H:%M'))
                            except:
                                st.caption(timestamp[:16])
                
                # Clear notifications button
                if st.button("🗑️ Clear Notifications", key="admin_clear_notifications"):
                    try:
                        os.remove(notifications_file)
                        st.success("Notifications cleared!")
                        st.rerun()
                    except:
                        st.error("Failed to clear notifications")
    
    except Exception as e:
        st.error(f"Error loading notifications: {e}")

def parse_applications_file(file_path):
    """Parse the applications file and return structured data."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by different possible separators
        sections = content.split("====================================================================================================")
        
        if len(sections) <= 1:
            sections = content.split("================================================================================")
        
        applications = []
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            app_data = {}
            
            # Extract metadata from header
            lines = section.split('\n')
            for line in lines[:10]:  # Check first 10 lines for metadata
                if 'DATE:' in line:
                    app_data['date'] = line.replace('DATE:', '').strip()
                elif 'USER:' in line:
                    app_data['user_id'] = line.replace('USER:', '').strip()
                elif 'User ID:' in line:
                    app_data['user_id'] = line.replace('User ID:', '').strip()
            
            # Extract job title
            title = "Unknown Job"
            if "Title:" in section:
                title_lines = [line for line in section.split('\n') if 'Title:' in line]
                if title_lines:
                    title = title_lines[0].replace('# Title:', '').replace('Title:', '').strip()
            app_data['title'] = title
            
            # Split into main parts
            parts = section.split('### ')
            
            for part in parts:
                part = part.strip()
                if part.startswith("Job Description"):
                    app_data['job_description'] = part.replace("Job Description", "").strip()
                elif part.startswith("Cover Letter"):
                    app_data['cover_letter'] = part.replace("Cover Letter", "").strip()
                elif part.startswith("Interview Preparation"):
                    app_data['interview_prep'] = part.replace("Interview Preparation", "").strip()
            
            # Only add if it has essential content
            if app_data.get('cover_letter') or app_data.get('job_description'):
                applications.append(app_data)
        
        return applications
    
    except Exception as e:
        st.error(f"Error parsing applications file: {e}")
        return []

def display_applications_cards(applications, is_admin=False):
    """Display applications in card format."""
    for i, app in enumerate(applications):
        with st.container():
            # Card header
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### 📋 {app.get('title', 'Unknown Job')}")
                if is_admin and app.get('user_id'):
                    st.caption(f"👤 User: {app.get('user_id')}")
                
            with col2:
                if app.get('date') and app.get('date') != 'Unknown':
                    st.caption(f"📅 {app.get('date')}")
                
            with col3:
                cover_length = len(app.get('cover_letter', ''))
                if cover_length > 0:
                    st.caption(f"✉️ {cover_length} chars")
            
            # Quick preview
            cover_preview = app.get('cover_letter', '')[:150]
            if len(cover_preview) < len(app.get('cover_letter', '')):
                cover_preview += "..."
            
            st.write(f"**Preview:** {cover_preview}")
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📋 View Full", key=f"view_{i}"):
                    st.session_state[f"show_full_{i}"] = not st.session_state.get(f"show_full_{i}", False)
            
            with col2:
                if st.button("✉️ Copy Cover", key=f"copy_cover_{i}"):
                    st.code(app.get('cover_letter', ''), language="text")
            
            with col3:
                if app.get('interview_prep') and st.button("🎤 Copy Interview", key=f"copy_interview_{i}"):
                    st.code(app.get('interview_prep', ''), language="text")
            
            with col4:
                if app.get('job_description') and st.button("📄 View Job", key=f"view_job_{i}"):
                    st.session_state[f"show_job_{i}"] = not st.session_state.get(f"show_job_{i}", False)
            
            # Show full content if requested
            if st.session_state.get(f"show_full_{i}", False):
                with st.expander("Full Application", expanded=True):
                    if app.get('cover_letter'):
                        st.markdown("**✉️ Cover Letter:**")
                        st.markdown(app['cover_letter'])
                        st.divider()
                    
                    if app.get('interview_prep'):
                        st.markdown("**🎤 Interview Preparation:**")
                        st.markdown(app['interview_prep'])
            
            # Show job description if requested
            if st.session_state.get(f"show_job_{i}", False):
                with st.expander("Job Description", expanded=True):
                    if app.get('job_description'):
                        clean_desc = app['job_description'].replace('# ', '**').strip()
                        st.markdown(clean_desc)
            
            st.divider()

def display_applications_table(applications, is_admin=False):
    """Display applications in table format."""
    if not applications:
        return
    
    # Prepare table data
    table_data = []
    for i, app in enumerate(applications):
        cover_length = len(app.get('cover_letter', ''))
        has_interview = "✅" if app.get('interview_prep') else "❌"
        
        row_data = {
            "Job Title": app.get('title', 'Unknown')[:40] + ("..." if len(app.get('title', '')) > 40 else ""),
            "Date": app.get('date', 'Unknown'),
            "Cover Letter": f"{cover_length} chars",
            "Interview Prep": has_interview,
            "Actions": f"View #{i+1}"
        }
        
        if is_admin:
            row_data["User"] = app.get('user_id', 'Unknown')[:12]
        
        table_data.append(row_data)
    
    # Display table
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)
    
    # Action buttons below table
    st.write("**Quick Actions:**")
    cols = st.columns(min(5, len(applications)))
    
    for i, app in enumerate(applications[:5]):  # Show first 5
        with cols[i]:
            if st.button(f"View App #{i+1}", key=f"table_view_{i}"):
                with st.expander(f"Application #{i+1}: {app.get('title', 'Unknown')}", expanded=True):
                    if is_admin and app.get('user_id'):
                        st.info(f"👤 User: {app.get('user_id')}")
                    
                    if app.get('cover_letter'):
                        st.markdown("**✉️ Cover Letter:**")
                        st.text(app['cover_letter'])
                        st.divider()
                    
                    if app.get('interview_prep'):
                        st.markdown("**🎤 Interview Preparation:**")
                        st.text(app['interview_prep'])

def display_applications_detailed(applications, start_idx, is_admin=False):
    """Display applications in detailed format."""
    for i, app in enumerate(applications):
        app_number = start_idx + i + 1
        
        st.markdown(f"## 📋 Application #{app_number}: {app.get('title', 'Unknown Job')}")
        
        # Metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**📅 Date:** {app.get('date', 'Unknown')}")
        with col2:
            st.write(f"**✉️ Cover Letter:** {len(app.get('cover_letter', ''))} characters")
        with col3:
            has_prep = "Yes" if app.get('interview_prep') else "No"
            st.write(f"**🎤 Interview Prep:** {has_prep}")
        
        if is_admin and app.get('user_id'):
            st.info(f"👤 **User:** {app.get('user_id')}")
        
        # Tabs for different sections
        tab1, tab2, tab3 = st.tabs(["📄 Job Description", "✉️ Cover Letter", "🎤 Interview Prep"])
        
        with tab1:
            if app.get('job_description'):
                clean_desc = app['job_description'].replace('# ', '**').strip()
                st.markdown(clean_desc)
            else:
                st.info("No job description available")
        
        with tab2:
            if app.get('cover_letter'):
                st.markdown(app['cover_letter'])
                if st.button(f"📋 Copy Cover Letter", key=f"detailed_copy_cover_{i}"):
                    st.code(app['cover_letter'], language="text")
            else:
                st.info("No cover letter available")
        
        with tab3:
            if app.get('interview_prep'):
                st.markdown(app['interview_prep'])
                if st.button(f"📋 Copy Interview Prep", key=f"detailed_copy_interview_{i}"):
                    st.code(app['interview_prep'], language="text")
            else:
                st.info("No interview preparation available")
        
        st.markdown("---")

def generate_applications_summary(applications):
    """Generate a summary report of applications."""
    st.subheader("📊 Applications Summary Report")
    
    # Summary stats
    total_apps = len(applications)
    total_cover_chars = sum(len(app.get('cover_letter', '')) for app in applications)
    apps_with_interview = sum(1 for app in applications if app.get('interview_prep'))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Applications", total_apps)
    with col2:
        st.metric("Total Cover Letter Text", f"{total_cover_chars:,} chars")
    with col3:
        st.metric("With Interview Prep", f"{apps_with_interview}/{total_apps}")
    
    # Applications by date
    if applications:
        dates = [app.get('date', 'Unknown') for app in applications]
        date_counts = pd.Series(dates).value_counts()
        
        st.subheader("Applications by Date")
        fig = px.bar(x=date_counts.index, y=date_counts.values, 
                     labels={'x': 'Date', 'y': 'Number of Applications'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Cover letter length distribution
    if applications:
        lengths = [len(app.get('cover_letter', '')) for app in applications if app.get('cover_letter')]
        if lengths:
            st.subheader("Cover Letter Length Distribution")
            fig = px.histogram(x=lengths, nbins=10,
                             labels={'x': 'Character Count', 'y': 'Number of Applications'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Job titles list
    st.subheader("All Job Titles")
    for i, app in enumerate(applications, 1):
        st.write(f"{i}. {app.get('title', 'Unknown Job')}")

def settings_page():
    """Settings page."""
    st.header("⚙️ Settings")
    
    # User Account Information
    st.subheader("👤 Account Information")
    if st.session_state.user:
        user = st.session_state.user
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Username:** {user.get('username')}")
            st.info(f"**Email:** {user.get('email')}")
            
        with col2:
            if user.get('created_at'):
                st.info(f"**Member since:** {user.get('created_at')[:10]}")
            if user.get('last_login'):
                st.info(f"**Last login:** {user.get('last_login')[:10]}")
    
    st.divider()
    
    # API Key Management
    st.subheader("🔑 API Key Management")
    
    current_key = os.getenv('OPENAI_API_KEY')
    if current_key:
        masked_key = f"{current_key[:8]}...{current_key[-8:]}" if len(current_key) > 16 else "***"
        st.success(f"✅ OpenAI API Key is set: {masked_key}")
    else:
        st.warning("⚠️ OpenAI API Key is not set")
    
    new_api_key = st.text_input("Enter new OpenAI API Key", type="password")
    if st.button("Update API Key"):
        if new_api_key:
            os.environ['OPENAI_API_KEY'] = new_api_key
            st.session_state.api_key_set = True
            st.success("✅ API Key updated successfully!")
            st.rerun()
        else:
            st.error("❌ Please enter a valid API key")
    
    st.divider()
    
    # File Management
    st.subheader("📁 File Management")
    
    # Profile file check
    profile_path = "./files/profile.md"
    if os.path.exists(profile_path):
        st.success("✅ Profile file found")
        with st.expander("View Profile"):
            try:
                profile_content = read_text_file(profile_path)
                st.text(profile_content)
            except Exception as e:
                st.error(f"Error reading profile: {e}")
    else:
        st.warning("⚠️ Profile file not found")
        st.info("Please ensure you have a profile.md file in the ./files/ directory")
    
    st.divider()
    
    # Database info
    st.subheader("🗄️ Your Data")
    user_id = get_current_user_id()
    df = load_jobs_data()
    stats = get_database_stats(user_id)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Your Jobs", stats['total_jobs'])
    with col2:
        st.metric("Processed", stats['processed_jobs'])
    with col3:
        st.metric("High Scoring", stats['high_scoring_jobs'])
    
    if st.button("🔄 Refresh Database Connection", key="settings_refresh_db"):
        ensure_db_exists()
        st.success("Database connection refreshed!")
    
    st.divider()
    
    # Account Actions
    st.subheader("🔧 Account Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Session", key="settings_refresh_session"):
            # Refresh user session
            if check_authentication():
                st.success("Session refreshed successfully!")
            else:
                st.error("Session refresh failed")
    
    with col2:
        if st.button("🚪 Logout", key="settings_logout", type="secondary"):
            logout()

def is_current_user_admin():
    """Check if current user has admin privileges."""
    if not st.session_state.authenticated or not st.session_state.user:
        return False
    return st.session_state.user.get('is_admin', False)

def admin_panel_page():
    """Main admin panel with tabs for different admin functions."""
    if not is_current_user_admin():
        st.error("⛔ Access denied. Admin privileges required.")
        return
    
    st.title("👑 Admin Panel")
    st.markdown("---")
    
    # Admin navigation tabs
    tab_options = [
        "📊 System Overview",
        "👥 User Management", 
        "💼 Jobs Management",
        "📝 Prompt Management",
        "🔧 System Tools",
        "📈 Analytics"
    ]
    
    selected_tab = st.selectbox("Admin Section:", tab_options, key="admin_nav_tabs")
    
    st.markdown("---")
    
    # Route to appropriate admin function
    if selected_tab == "📊 System Overview":
        admin_system_overview()
    elif selected_tab == "👥 User Management":
        admin_user_management()
    elif selected_tab == "💼 Jobs Management":
        admin_jobs_management()
    elif selected_tab == "📝 Prompt Management":
        admin_prompt_management()
    elif selected_tab == "🔧 System Tools":
        admin_system_tools()
    elif selected_tab == "📈 Analytics":
        admin_analytics()

def admin_system_overview():
    """System overview for admins."""
    st.subheader("📊 System Overview")
    
    # Get system statistics
    admin_user_id = get_current_user_id()
    stats = get_system_stats(admin_user_id)
    
    if not stats:
        st.error("Unable to load system statistics")
        return
    
    # Show high score notifications first
    show_admin_notifications()
    
    # System metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total Users", stats['total_users'])
        st.metric("✅ Active Users", stats['active_users'])
    
    with col2:
        st.metric("👑 Admin Users", stats['admin_users'])
        st.metric("🆕 New Users (7d)", stats['new_users_week'])
    
    with col3:
        st.metric("💼 Total Jobs", stats['total_jobs'])
        st.metric("⚡ Processed Jobs", stats['processed_jobs'])
    
    with col4:
        st.metric("🌟 High Scoring Jobs", stats['high_scoring_jobs'])
        st.metric("📊 Average Score", stats['average_score'])
    
    st.divider()
    
    # Session information
    st.subheader("🔐 Session Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🟢 Active Sessions", stats['active_sessions'])
    with col2:
        st.metric("🔴 Expired Sessions", stats['expired_sessions'])
    
    # Recent high score jobs summary
    try:
        notifications_file = "./data/high_score_notifications.json"
        if os.path.exists(notifications_file):
            import json
            with open(notifications_file, 'r') as f:
                notifications = json.load(f)
            
            if notifications:
                # Count notifications by user
                from collections import Counter
                user_counts = Counter(notif.get('username', 'Unknown') for notif in notifications)
                
                st.subheader("🏆 High Score Activity")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("🔔 Total High Score Jobs", len(notifications))
                
                with col2:
                    most_active_user = user_counts.most_common(1)[0] if user_counts else ("None", 0)
                    st.metric("🥇 Most High Scores", f"{most_active_user[0]} ({most_active_user[1]})")
    except:
        pass  # Ignore errors loading notifications
    
    # Top users by jobs
    if stats['top_users_by_jobs']:
        st.subheader("🏆 Most Active Users")
        for username, job_count in list(stats['top_users_by_jobs'].items())[:5]:
            st.write(f"**{username}**: {job_count} jobs")

def admin_user_management():
    """User management interface for admins."""
    st.subheader("👥 User Management")
    
    admin_user_id = get_current_user_id()
    users = get_all_users(admin_user_id)
    
    if not users:
        st.info("No users found in the system")
        return
    
    # User management controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Users", key="admin_users_refresh"):
            st.rerun()
    
    with col2:
        if st.button("🧹 Cleanup Expired Sessions", key="admin_overview_cleanup"):
            cleaned = cleanup_expired_sessions()
            st.success(f"Cleaned {cleaned} expired sessions")
    
    # Users table
    st.divider()
    
    for user in users:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
            
            with col1:
                # User info
                admin_badge = "👑" if user.get('is_admin') else ""
                status_badge = "✅" if user.get('is_active') else "❌"
                st.write(f"**{admin_badge} {user['username']}** {status_badge}")
                st.caption(f"Email: {user['email']} | Created: {user.get('created_at', 'Unknown')[:10]}")
            
            with col2:
                # Job count
                user_jobs = get_all_jobs(user['user_id'])
                st.metric("Jobs", len(user_jobs))
            
            with col3:
                # Last login
                last_login = user.get('last_login', 'Never')
                if last_login and last_login != 'Never':
                    last_login = last_login[:10]
                else:
                    last_login = 'Never'
                st.caption(f"Last login: {last_login}")
            
            with col4:
                # Action buttons
                if user['user_id'] != admin_user_id:  # Can't modify yourself
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    
                    with btn_col1:
                        # Toggle admin status
                        if user.get('is_admin'):
                            if st.button("⬇️", key=f"demote_{user['user_id']}", help="Remove Admin"):
                                if demote_admin_user(user['user_id']):
                                    st.success(f"Removed admin privileges from {user['username']}")
                                    st.rerun()
                        else:
                            if st.button("⬆️", key=f"promote_{user['user_id']}", help="Make Admin"):
                                if promote_user_to_admin(user['user_id']):
                                    st.success(f"Promoted {user['username']} to admin")
                                    st.rerun()
                    
                    with btn_col2:
                        # Toggle active status
                        status_text = "🔓" if user.get('is_active') else "🔒"
                        help_text = "Deactivate" if user.get('is_active') else "Activate"
                        if st.button(status_text, key=f"toggle_{user['user_id']}", help=help_text):
                            if toggle_user_status(user['user_id'], admin_user_id):
                                action = "deactivated" if user.get('is_active') else "activated"
                                st.success(f"User {user['username']} {action}")
                                st.rerun()
                    
                    with btn_col3:
                        # Delete user
                        if st.button("🗑️", key=f"delete_user_{user['user_id']}", help="Delete User"):
                            st.session_state[f"confirm_delete_user_{user['user_id']}"] = True
                            st.rerun()
                    
                    # Delete confirmation
                    if st.session_state.get(f"confirm_delete_user_{user['user_id']}", False):
                        st.error(f"⚠️ Delete user '{user['username']}' and ALL their data?")
                        conf_col1, conf_col2 = st.columns(2)
                        with conf_col1:
                            if st.button("✅ Yes, Delete", key=f"conf_del_user_{user['user_id']}"):
                                if delete_user_admin(user['user_id'], admin_user_id):
                                    st.success(f"Deleted user {user['username']} and all their data")
                                    st.session_state[f"confirm_delete_user_{user['user_id']}"] = False
                                    st.rerun()
                        with conf_col2:
                            if st.button("❌ Cancel", key=f"cancel_del_user_{user['user_id']}"):
                                st.session_state[f"confirm_delete_user_{user['user_id']}"] = False
                                st.rerun()
                else:
                    st.info("You (Admin)")
            
            st.divider()

def admin_jobs_management():
    """Jobs management interface for admins."""
    st.subheader("💼 All Jobs Management")
    
    admin_user_id = get_current_user_id()
    jobs = get_all_jobs_admin(admin_user_id)
    
    if not jobs:
        st.info("No jobs found in the system")
        return
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(jobs)
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        user_filter = st.selectbox("Filter by User", ["All Users"] + list(df['username'].dropna().unique()))
    
    with col2:
        score_filter = st.selectbox("Score Range", ["All", "High (≥7)", "Medium (4-6)", "Low (<4)", "Unscored"])
    
    with col3:
        job_type_filter = st.selectbox("Job Type", ["All"] + list(df['job_type'].dropna().unique()))
    
    with col4:
        limit = st.selectbox("Show", [50, 100, 200, "All"])
    
    # Apply filters
    filtered_df = df.copy()
    
    if user_filter != "All Users":
        filtered_df = filtered_df[filtered_df['username'] == user_filter]
    
    if score_filter != "All":
        if score_filter == "High (≥7)":
            filtered_df = filtered_df[filtered_df['score'] >= 7]
        elif score_filter == "Medium (4-6)":
            filtered_df = filtered_df[(filtered_df['score'] >= 4) & (filtered_df['score'] < 7)]
        elif score_filter == "Low (<4)":
            filtered_df = filtered_df[filtered_df['score'] < 4]
        elif score_filter == "Unscored":
            filtered_df = filtered_df[filtered_df['score'].isna()]
    
    if job_type_filter != "All":
        filtered_df = filtered_df[filtered_df['job_type'] == job_type_filter]
    
    if limit != "All":
        filtered_df = filtered_df.head(limit)
    
    st.write(f"Showing {len(filtered_df)} of {len(df)} jobs")
    
    # Display jobs
    for _, job in filtered_df.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{job.get('title', 'No Title')}**")
                st.caption(f"User: {job.get('username', 'Unknown')} | Type: {job.get('job_type', 'N/A')}")
            
            with col2:
                score = job.get('score')
                if pd.notna(score):
                    if score >= 7:
                        st.success(f"Score: {score}/10")
                    elif score >= 4:
                        st.warning(f"Score: {score}/10")
                    else:
                        st.error(f"Score: {score}/10")
                else:
                    st.info("Not scored")
            
            with col3:
                if job.get('payment_rate'):
                    st.write(f"💰 {job['payment_rate']}")
            
            with col4:
                if job.get('link'):
                    st.link_button("🔗", job['link'], help="View Original")
            
            st.divider()

def admin_system_tools():
    """System tools for admins."""
    st.subheader("🔧 System Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗄️ Database Operations")
        
        if st.button("🔄 Initialize/Upgrade Database", key="admin_tools_init_db"):
            try:
                ensure_db_exists()
                st.success("Database initialized/upgraded successfully!")
            except Exception as e:
                st.error(f"Database operation failed: {e}")
        
        if st.button("🧹 Cleanup Expired Sessions", key="admin_tools_cleanup"):
            cleaned = cleanup_expired_sessions()
            st.success(f"Cleaned {cleaned} expired sessions")
        
        if st.button("📊 Recalculate Statistics", key="admin_tools_recalc_stats"):
            # This could trigger a stats recalculation if needed
            st.success("Statistics recalculated!")
    
    with col2:
        st.subheader("⚠️ Danger Zone")
        
        st.warning("These actions are irreversible!")
        
        if st.button("🗑️ Clear All Expired Sessions", key="admin_tools_clear_all_sessions", type="secondary"):
            cleaned = cleanup_expired_sessions()
            st.success(f"Removed {cleaned} expired sessions")

def admin_analytics():
    """Analytics dashboard for admins."""
    st.subheader("📈 System Analytics")
    
    admin_user_id = get_current_user_id()
    stats = get_system_stats(admin_user_id)
    
    if not stats:
        st.error("Unable to load analytics data")
        return
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("User Distribution")
        user_data = {
            'Admin Users': stats['admin_users'],
            'Regular Users': stats['total_users'] - stats['admin_users'],
            'Inactive Users': stats['total_users'] - stats['active_users']
        }
        
        if any(user_data.values()):
            fig = px.pie(values=list(user_data.values()), names=list(user_data.keys()),
                        title="User Type Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Job Processing Stats")
        job_data = {
            'Processed': stats['processed_jobs'],
            'Unprocessed': stats['total_jobs'] - stats['processed_jobs'],
            'High Scoring': stats['high_scoring_jobs']
        }
        
        if any(job_data.values()):
            fig = px.bar(x=list(job_data.keys()), y=list(job_data.values()),
                        title="Job Processing Status")
            st.plotly_chart(fig, use_container_width=True)
    
    # Top users table
    if stats['top_users_by_jobs']:
        st.subheader("🏆 Most Active Users")
        top_users_df = pd.DataFrame(list(stats['top_users_by_jobs'].items()), 
                                   columns=['Username', 'Job Count'])
        st.dataframe(top_users_df, use_container_width=True)

def admin_prompt_management():
    """Prompt management for admins."""
    st.subheader("📝 Prompt Management")
    
    admin_user_id = get_current_user_id()
    
    # Initialize default prompts if none exist
    if st.button("🔄 Initialize Default Prompts", key="init_default_prompts"):
        success, message = initialize_default_prompts(admin_user_id)
        if success:
            st.success(message)
        else:
            st.error(message)
        st.rerun()
    
    # Get all existing prompts
    prompts = get_all_prompts(admin_user_id)
    
    # Display current prompts
    if prompts:
        st.subheader("📋 Current Prompts")
        
        for prompt in prompts:
            with st.expander(f"{prompt['prompt_name']} ({prompt['prompt_type']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.text_area(
                        "Preview:", 
                        value=prompt['prompt_content'][:300] + "..." if len(prompt['prompt_content']) > 300 else prompt['prompt_content'],
                        height=100,
                        disabled=True,
                        key=f"preview_{prompt['prompt_type']}"
                    )
                    st.caption(f"Created: {prompt['created_at']} | Updated: {prompt['updated_at']}")
                    if prompt.get('created_by_username'):
                        st.caption(f"By: {prompt['created_by_username']}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{prompt['prompt_type']}"):
                        st.session_state[f"editing_{prompt['prompt_type']}"] = True
                        st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"delete_{prompt['prompt_type']}", type="secondary"):
                        success, message = delete_prompt(prompt['prompt_type'], admin_user_id)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                        st.rerun()
    
    st.divider()
    
    # Add/Edit prompt form
    st.subheader("➕ Add/Edit Prompt")
    
    # Check if we're editing an existing prompt
    editing_prompt = None
    for prompt in prompts:
        if st.session_state.get(f"editing_{prompt['prompt_type']}", False):
            editing_prompt = prompt
            break
    
    with st.form("prompt_form"):
        if editing_prompt:
            st.info(f"Editing: {editing_prompt['prompt_name']}")
            prompt_type = st.selectbox(
                "Prompt Type:",
                ["cover_letter", "interview_prep"],
                index=0 if editing_prompt['prompt_type'] == 'cover_letter' else 1,
                disabled=True  # Don't allow changing type when editing
            )
            prompt_name = st.text_input(
                "Prompt Name:",
                value=editing_prompt['prompt_name']
            )
            prompt_content = st.text_area(
                "Prompt Content:",
                value=editing_prompt['prompt_content'],
                height=400,
                help="Use {profile} as a placeholder for the freelancer profile information."
            )
        else:
            prompt_type = st.selectbox(
                "Prompt Type:",
                ["cover_letter", "interview_prep"],
                help="Select the type of prompt you want to create/update"
            )
            prompt_name = st.text_input(
                "Prompt Name:",
                placeholder="e.g., Professional Cover Letter Template"
            )
            prompt_content = st.text_area(
                "Prompt Content:",
                height=400,
                placeholder="Enter your prompt template here...",
                help="Use {profile} as a placeholder for the freelancer profile information."
            )
        
        # Form buttons
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            submit_button = st.form_submit_button(
                "💾 Save Prompt" if not editing_prompt else "💾 Update Prompt",
                type="primary"
            )
        
        with col2:
            if editing_prompt and st.form_submit_button("❌ Cancel Edit"):
                for key in list(st.session_state.keys()):
                    if key.startswith("editing_"):
                        del st.session_state[key]
                st.rerun()
        
        with col3:
            if st.form_submit_button("📖 Help"):
                st.session_state.show_prompt_help = True
    
    # Handle form submission
    if submit_button and prompt_name and prompt_content:
        success, message = create_or_update_prompt(
            prompt_type, 
            prompt_name, 
            prompt_content, 
            admin_user_id
        )
        
        if success:
            st.success(message)
            # Clear editing state
            for key in list(st.session_state.keys()):
                if key.startswith("editing_"):
                    del st.session_state[key]
            st.rerun()
        else:
            st.error(message)
    
    # Show help if requested
    if st.session_state.get('show_prompt_help', False):
        with st.expander("📖 Prompt Help & Examples", expanded=True):
            st.markdown("""
            ### How to Create Effective Prompts
            
            **Available Placeholders:**
            - `{profile}` - Will be replaced with the freelancer's profile information
            
            **Cover Letter Prompt Tips:**
            - Include clear instructions for tone and style
            - Specify word count limits
            - Provide example format or structure
            - Include any specific requirements (like name inclusion)
            
            **Interview Preparation Prompt Tips:**
            - Ask for structured output (introduction, key points, questions)
            - Specify number of questions to generate
            - Include both client questions and questions to ask the client
            - Request professional tone guidelines
            
            **Example Cover Letter Prompt Structure:**
            ```
            You are a professional cover letter writer. Create a personalized cover letter.
            
            Freelancer Profile:
            {profile}
            
            Instructions:
            1. Keep it under 150 words
            2. Use friendly, professional tone
            3. Include specific examples from the profile
            4. Address the job requirements directly
            ```
            """)
            
            if st.button("❌ Close Help"):
                st.session_state.show_prompt_help = False
                st.rerun()

def main():
    """Main application."""
    init_session_state()
    
    # Initialize database first
    try:
        ensure_db_exists()
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        st.stop()
    
    # Clean up expired sessions (with error handling)
    try:
        cleanup_expired_sessions()
    except Exception as e:
        print(f"Session cleanup error: {e}")
    
    # Check authentication
    if not check_authentication():
        login_page()
        return
    
    # Sidebar navigation for authenticated users
    with st.sidebar:
        st.title("🤖 Jobs Applier")
        
        # User info
        if st.session_state.user:
            user_display = st.session_state.user['username']
            if is_current_user_admin():
                user_display += " 👑"
            st.markdown(f"👤 **{user_display}**")
            if st.button("🚪 Logout", key="sidebar_logout"):
                logout()
        
        # Navigation options
        nav_options = [
            "📊 Dashboard",
            "➕ Add Job", 
            "🛠️ Manage Jobs",
            "⚡ Process Jobs",
            "📄 Applications",
            "⚙️ Settings"
        ]
        
        # Add admin panel for admin users
        if is_current_user_admin():
            nav_options.append("👑 Admin Panel")
        
        page = st.selectbox("Navigate to:", nav_options)
        
        st.divider()
        
        # Quick stats
        df = load_jobs_data()
        if not df.empty:
            st.metric("Total Jobs", len(df))
            processed = len(df[df['score'].notna()]) if 'score' in df.columns else 0
            st.metric("Processed", processed)
            
            if 'score' in df.columns and not df['score'].isna().all():
                avg_score = df['score'].mean()
                st.metric("Avg Score", f"{avg_score:.1f}")
        
        # Quick actions in sidebar
        st.divider()
        st.write("**Quick Actions**")
        
        if not df.empty:
            user_id = get_current_user_id()
            # Quick cleanup buttons
            unprocessed = len(df[df['score'].isna()]) if 'score' in df.columns else 0
            if unprocessed > 0:
                if st.button(f"⚡ Process {unprocessed} Jobs", key="sidebar_process_jobs"):
                    st.session_state.selected_page = "⚡ Process Jobs"
                    st.rerun()
            
            low_scores = len(df[df['score'] < 4]) if 'score' in df.columns else 0
            if low_scores > 0:
                if st.button(f"🗑️ Clean {low_scores} Low Scores", key="sidebar_clean_low_scores"):
                    # Quick delete low scores
                    low_score_ids = df[df['score'] < 4]['job_id'].tolist()
                    deleted = delete_multiple_jobs(low_score_ids, user_id)
                    st.success(f"Deleted {deleted} jobs!")
                    st.rerun()
    
    # Handle page selection
    if 'selected_page' in st.session_state:
        page = st.session_state.selected_page
        del st.session_state.selected_page
    
    # Main content
    if page == "📊 Dashboard":
        dashboard_page()
    elif page == "➕ Add Job":
        add_job_page()
    elif page == "🛠️ Manage Jobs":
        view_jobs_page()
    elif page == "⚡ Process Jobs":
        process_jobs_page()
    elif page == "📄 Applications":
        applications_page()
    elif page == "⚙️ Settings":
        settings_page()
    elif page == "👑 Admin Panel":
        admin_panel_page()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
User-aware Job Processor for the Upwork AI Jobs Applier

This module extends the ManualJobProcessor to work with user-specific data
and handle multi-user scenarios.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_jobs_by_criteria, update_job, get_user_by_id
from process_manual_jobs import ManualJobProcessor
import openai


class UserJobProcessor(ManualJobProcessor):
    """User-aware job processor that extends ManualJobProcessor."""
    
    def __init__(self, user_id: str, profile: str, batch_size: int = 3, min_score: int = 7):
        """
        Initialize the UserJobProcessor.
        
        Args:
            user_id: The ID of the user whose jobs to process
            profile: The freelancer profile text
            batch_size: Number of jobs to process in each batch
            min_score: Minimum score threshold for generating applications
        """
        super().__init__(profile, batch_size, min_score)
        self.user_id = user_id
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.high_score_notifications = []  # Store notifications for high scores
    
    def load_unprocessed_jobs(self) -> List[Dict[str, Any]]:
        """Load unprocessed jobs for the specific user from the database."""
        try:
            # Get jobs that haven't been scored yet for this user
            jobs = get_jobs_by_criteria(
                unprocessed_only=True,
                user_id=self.user_id
            )
            
            print(f"Loaded {len(jobs)} unprocessed jobs for user {self.user_id}")
            return jobs
            
        except Exception as e:
            print(f"Error loading unprocessed jobs: {e}")
            return []
    
    async def score_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score jobs using AI."""
        scored_jobs = []
        
        for job in jobs:
            try:
                # Create prompt for scoring
                prompt = f"""
                Rate this job opportunity from 1-10 based on how well it matches the freelancer profile.
                
                Freelancer Profile:
                {self.profile}
                
                Job Details:
                Title: {job.get('title', 'N/A')}
                Type: {job.get('job_type', 'N/A')}
                Experience Level: {job.get('experience_level', 'N/A')}
                Payment: {job.get('payment_rate', 'N/A')}
                Description: {job.get('description', 'N/A')[:500]}...
                
                Provide only a numeric score from 1-10. Consider:
                - Skill match
                - Payment rate
                - Experience level requirements
                - Project complexity
                - Long-term potential
                """
                
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10
                )
                
                score_text = response.choices[0].message.content.strip()
                try:
                    score = float(score_text)
                    score = max(1, min(10, score))  # Clamp between 1-10
                except ValueError:
                    score = 5.0  # Default score if parsing fails
                
                job_with_score = dict(job)
                job_with_score['score'] = score
                scored_jobs.append(job_with_score)
                
                # Check for high score notification
                if score >= 7.0:
                    user_info = get_user_by_id(self.user_id)
                    username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
                    self.high_score_notifications.append({
                        'user_id': self.user_id,
                        'username': username,
                        'job_title': job.get('title', 'Unknown'),
                        'score': score,
                        'timestamp': datetime.now().isoformat()
                    })
                
                print(f"Scored job '{job.get('title', 'Unknown')}': {score}/10")
                
            except Exception as e:
                print(f"Error scoring job {job.get('title', 'Unknown')}: {e}")
                job_with_score = dict(job)
                job_with_score['score'] = 5.0
                scored_jobs.append(job_with_score)
        
        return scored_jobs
    
    def save_job_score(self, job: Dict[str, Any]) -> bool:
        """Save job score to database."""
        return update_job(job['job_id'], {'score': job['score']}, self.user_id)
    
    async def process_jobs_batch(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of jobs to generate applications."""
        applications = []
        
        for job in jobs:
            try:
                # Generate cover letter
                cover_letter_prompt = f"""
                Write a personalized cover letter for this job application.
                
                Freelancer Profile:
                {self.profile}
                
                Job Details:
                Title: {job.get('title', 'N/A')}
                Description: {job.get('description', 'N/A')}
                Requirements: {job.get('proposal_requirements', 'N/A')}
                
                Write a professional, engaging cover letter that highlights relevant experience and addresses the job requirements. Keep it concise (2-3 paragraphs).
                """
                
                cover_response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": cover_letter_prompt}],
                    max_tokens=500
                )
                
                cover_letter = cover_response.choices[0].message.content.strip()
                
                # Generate interview preparation
                interview_prompt = f"""
                Prepare potential interview questions and answers for this job.
                
                Job Title: {job.get('title', 'N/A')}
                Job Description: {job.get('description', 'N/A')[:300]}...
                
                Provide 3-5 likely interview questions with suggested answers based on the freelancer profile.
                """
                
                interview_response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model="gpt-3.5-turbo", 
                    messages=[{"role": "user", "content": interview_prompt}],
                    max_tokens=600
                )
                
                interview_prep = interview_response.choices[0].message.content.strip()
                
                applications.append({
                    'user_id': self.user_id,
                    'job_id': job['job_id'],
                    'title': job.get('title', 'Unknown'),
                    'score': job.get('score', 0),
                    'cover_letter': cover_letter,
                    'interview_prep': interview_prep,
                    'job_description': job.get('description', ''),
                    'created_at': datetime.now().isoformat()
                })
                
                print(f"Generated application for '{job.get('title', 'Unknown')}'")
                
            except Exception as e:
                print(f"Error generating application for {job.get('title', 'Unknown')}: {e}")
        
        return applications
    
    def save_applications_to_file(self, applications: List[Dict[str, Any]]):
        """Save applications to user-specific file."""
        if not applications:
            return
        
        # Create user-specific data directory
        user_data_dir = f"./data/users/{self.user_id}"
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Save to user-specific file
        user_file = f"{user_data_dir}/cover_letters.md"
        
        with open(user_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n{'='*100}\n")
            f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"USER: {self.user_id}\n")
            f.write(f"BATCH: {len(applications)} applications\n")
            f.write(f"{'='*100}\n\n")
            
            for app in applications:
                f.write(f"# Title: {app['title']}\n")
                f.write(f"Score: {app['score']}/10\n")
                f.write(f"Job ID: {app['job_id']}\n\n")
                
                f.write(f"### Job Description\n")
                f.write(f"{app['job_description']}\n\n")
                
                f.write(f"### Cover Letter\n")
                f.write(f"{app['cover_letter']}\n\n")
                
                f.write(f"### Interview Preparation\n")
                f.write(f"{app['interview_prep']}\n\n")
                
                f.write(f"{'/'*100}\n\n")
        
        # Also save to global file for admin access
        global_file = "./data/cover_letter.md"
        os.makedirs("./data", exist_ok=True)
        
        with open(global_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n{'='*100}\n")
            f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"USER: {self.user_id}\n")
            f.write(f"BATCH: {len(applications)} applications\n")
            f.write(f"{'='*100}\n\n")
            
            for app in applications:
                f.write(f"# Title: {app['title']}\n")
                f.write(f"Score: {app['score']}/10\n")
                f.write(f"Job ID: {app['job_id']}\n")
                f.write(f"User ID: {app['user_id']}\n\n")
                
                f.write(f"### Job Description\n")
                f.write(f"{app['job_description']}\n\n")
                
                f.write(f"### Cover Letter\n")
                f.write(f"{app['cover_letter']}\n\n")
                
                f.write(f"### Interview Preparation\n")
                f.write(f"{app['interview_prep']}\n\n")
                
                f.write(f"{'/'*100}\n\n")
        
        print(f"Applications saved to both user file ({user_file}) and global file ({global_file})")
    
    def save_high_score_notifications(self):
        """Save high score notifications to file."""
        if not self.high_score_notifications:
            return
        
        notifications_file = "./data/high_score_notifications.json"
        os.makedirs("./data", exist_ok=True)
        
        import json
        
        # Load existing notifications
        existing_notifications = []
        if os.path.exists(notifications_file):
            try:
                with open(notifications_file, 'r') as f:
                    existing_notifications = json.load(f)
            except:
                existing_notifications = []
        
        # Add new notifications
        existing_notifications.extend(self.high_score_notifications)
        
        # Save updated notifications
        with open(notifications_file, 'w') as f:
            json.dump(existing_notifications, f, indent=2)
        
        print(f"Saved {len(self.high_score_notifications)} high score notifications")
    
    async def process_user_jobs(self) -> Dict[str, Any]:
        """Main method to process all unprocessed jobs for the user."""
        try:
            # Load unprocessed jobs
            unprocessed_jobs = self.load_unprocessed_jobs()
            
            if not unprocessed_jobs:
                return {
                    'success': True,
                    'message': 'No unprocessed jobs found',
                    'stats': {'total_jobs': 0, 'scored_jobs': 0, 'high_scoring_jobs': 0, 'applications_generated': 0}
                }
            
            total_jobs = len(unprocessed_jobs)
            scored_jobs = 0
            high_scoring_jobs = 0
            applications_generated = 0
            
            # Process jobs in batches
            for i in range(0, len(unprocessed_jobs), self.batch_size):
                batch = unprocessed_jobs[i:i + self.batch_size]
                
                # Score jobs
                scored_batch = await self.score_jobs(batch)
                
                # Save scores to database
                for job in scored_batch:
                    if self.save_job_score(job):
                        scored_jobs += 1
                        if job['score'] >= 7.0:
                            high_scoring_jobs += 1
                
                # Generate applications for high-scoring jobs
                high_scoring_batch = [job for job in scored_batch if job['score'] >= self.min_score]
                
                if high_scoring_batch:
                    applications = await self.process_jobs_batch(high_scoring_batch)
                    if applications:
                        self.save_applications_to_file(applications)
                        applications_generated += len(applications)
            
            # Save high score notifications
            self.save_high_score_notifications()
            
            return {
                'success': True,
                'message': f'Successfully processed {scored_jobs} jobs',
                'stats': {
                    'total_jobs': total_jobs,
                    'scored_jobs': scored_jobs,
                    'high_scoring_jobs': high_scoring_jobs,
                    'applications_generated': applications_generated
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error processing jobs: {str(e)}',
                'stats': {'total_jobs': 0, 'scored_jobs': 0, 'high_scoring_jobs': 0, 'applications_generated': 0}
            }


async def main():
    """Test function for the UserJobProcessor."""
    # This is mainly for testing - in the Streamlit app, this will be called differently
    pass


if __name__ == "__main__":
    asyncio.run(main()) 
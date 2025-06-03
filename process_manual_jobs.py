#!/usr/bin/env python3
"""
Process Manual Jobs - Runs the application workflow on manually added jobs

This script processes jobs that were added manually to the database,
bypassing the scraping step and directly running scoring, application
generation, and interview preparation.

Usage: python process_manual_jobs.py
"""

import asyncio
from datetime import datetime
from colorama import Fore, Style
from dotenv import load_dotenv

from src.utils import read_text_file, format_scraped_job_for_scoring, convert_jobs_matched_to_string_list, COVER_LETTERS_FILE
from src.structured_outputs import JobScores, JobApplication
from src.database import ensure_db_exists, get_all_jobs, save_jobs
from src.nodes import CreateJobApplicationNodes
from src.prompts import SCORE_JOBS_PROMPT
from src.utils import ainvoke_llm

# Load environment variables from a .env file
load_dotenv()

class ManualJobProcessor:
    """Processes manually added jobs through the application workflow."""
    
    def __init__(self, profile, batch_size=3, min_score=7):
        """
        Initialize the manual job processor.
        
        Args:
            profile: User profile information for job applications
            batch_size: Number of jobs to process in parallel
            min_score: Minimum score threshold for processing jobs
        """
        self.profile = profile
        self.batch_size = batch_size
        self.min_score = min_score
        self.job_application_nodes = CreateJobApplicationNodes(profile)
        ensure_db_exists()

    def get_unprocessed_jobs(self):
        """Get all jobs from database that haven't been scored yet."""
        all_jobs = get_all_jobs()
        print(f"Found {len(all_jobs)} total jobs in database")
        
        # Filter for jobs without scores or with None scores
        unprocessed_jobs = [job for job in all_jobs if job.get('score') is None]
        print(f"Found {len(unprocessed_jobs)} unprocessed jobs")
        
        return unprocessed_jobs

    async def score_jobs(self, jobs):
        """Score a list of jobs using the LLM."""
        print(Fore.YELLOW + f"----- Scoring {len(jobs)} jobs -----\n" + Style.RESET_ALL)
        
        if not jobs:
            return []

        # Format jobs for scoring
        jobs_list = format_scraped_job_for_scoring(jobs)
        score_jobs_prompt = SCORE_JOBS_PROMPT.format(profile=self.profile)
        
        results = await ainvoke_llm(
            system_prompt=score_jobs_prompt,
            user_message=f"Evaluate these Jobs:\n\n{jobs_list}",
            model="openai/gpt-4o-mini",
            response_format=JobScores
        )
        
        job_scores = results.model_dump()
        return job_scores["scores"]

    def add_scores_to_jobs(self, jobs, scores):
        """Add scores to job objects."""
        scored_jobs = []
        for job, score_data in zip(jobs, scores):
            job_copy = dict(job)
            job_copy['score'] = score_data['score']
            scored_jobs.append(job_copy)
        return scored_jobs

    def filter_high_scoring_jobs(self, jobs):
        """Filter jobs based on minimum score threshold."""
        high_scoring = [job for job in jobs if job.get('score', 0) >= self.min_score]
        print(f"Found {len(high_scoring)} jobs with score >= {self.min_score}")
        return high_scoring

    async def generate_application_for_job(self, job_description):
        """Generate application content for a single job."""
        try:
            print(f"Debug - Starting application generation...")
            print(f"Debug - Job description length: {len(job_description)}")
            
            # Create application state
            app_state = {"job_description": job_description}
            print(f"Debug - Created app_state with keys: {list(app_state.keys())}")
            
            # Gather relevant info from profile
            print(f"Debug - Gathering relevant info from profile...")
            gathered_state = await self.job_application_nodes.gather_relevant_infos_from_profile(app_state)
            
            # Preserve the job_description in the state
            app_state.update(gathered_state)
            print(f"Debug - After gather_relevant_infos, app_state keys: {list(app_state.keys())}")
            
            # Generate cover letter and interview prep in parallel
            print(f"Debug - Generating cover letter and interview prep...")
            cover_letter_task = self.job_application_nodes.generate_cover_letter(app_state)
            interview_prep_task = self.job_application_nodes.generate_interview_preparation(app_state)
            
            cover_letter_state, interview_prep_state = await asyncio.gather(
                cover_letter_task, 
                interview_prep_task
            )
            
            print(f"Debug - Cover letter state keys: {list(cover_letter_state.keys())}")
            print(f"Debug - Interview prep state keys: {list(interview_prep_state.keys())}")
            
            # Combine results
            final_state = {
                **app_state,
                "cover_letter": cover_letter_state["cover_letter"],
                "interview_prep": interview_prep_state["interview_prep"]
            }
            
            # Finalize application
            print(f"Debug - Finalizing application...")
            final_state = self.job_application_nodes.finalize_job_application(final_state)
            print(f"Debug - Final state keys: {list(final_state.keys())}")
            
            return final_state["applications"][0]  # finalize returns a list, get the first item
        
        except Exception as e:
            print(f"Error generating application: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None

    async def process_jobs_batch(self, jobs_batch):
        """Process a batch of jobs in parallel."""
        print(f"Processing batch of {len(jobs_batch)} jobs...")
        
        # Convert jobs to description strings for the application generator
        job_descriptions = []
        for job in jobs_batch:
            # More robust job description formatting
            job_desc = f"Title: {job.get('title', 'N/A')}\n"
            
            # Handle description field properly
            description = job.get('description', 'N/A')
            if description and description != 'N/A':
                job_desc += f"Description: {description}\n"
            
            # Add other fields if available
            if job.get('payment_rate'):
                job_desc += f"Payment: {job.get('payment_rate')}\n"
            if job.get('job_type'):
                job_desc += f"Type: {job.get('job_type')}\n"
            if job.get('experience_level'):
                job_desc += f"Experience: {job.get('experience_level')}\n"
            if job.get('duration'):
                job_desc += f"Duration: {job.get('duration')}\n"
            if job.get('proposal_requirements'):
                job_desc += f"Requirements: {job.get('proposal_requirements')}\n"
            if job.get('link'):
                job_desc += f"Link: {job.get('link')}\n"
                
            job_descriptions.append(job_desc)
            
            # Debug: Print the formatted job description
            print(f"Debug - Formatted job description for '{job.get('title', 'Unknown')}':")
            print(f"Length: {len(job_desc)} characters")
            print(f"Preview: {job_desc[:200]}...")
        
        # Generate applications in parallel
        applications = await asyncio.gather(
            *[self.generate_application_for_job(desc) for desc in job_descriptions],
            return_exceptions=True
        )
        
        # Filter out exceptions and None results
        valid_applications = []
        for i, app in enumerate(applications):
            if isinstance(app, Exception):
                print(f"Error generating application {i+1}: {app}")
            elif app is not None:
                valid_applications.append(app)
            else:
                print(f"Application {i+1} returned None")
        
        return valid_applications

    def save_applications_to_file(self, applications):
        """Save generated applications to the cover letters file."""
        if not applications:
            return
            
        print(Fore.YELLOW + f"----- Saving {len(applications)} Job Applications -----\n" + Style.RESET_ALL)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(COVER_LETTERS_FILE, "a", encoding="utf-8") as file:
            file.write("\n" + "=" * 80 + "\n")
            file.write(f"MANUAL JOBS PROCESSING - DATE: {timestamp}\n")
            file.write("=" * 80 + "\n\n")
            
            for i, application in enumerate(applications, 1):
                file.write(f"APPLICATION #{i}\n")
                file.write("-" * 40 + "\n\n")
                
                file.write("### Job Description\n")
                file.write(application.job_description + "\n\n")
                
                file.write("### Cover Letter\n")
                file.write(application.cover_letter + "\n\n")
                
                file.write("### Interview Preparation\n")
                file.write(application.interview_preparation + "\n\n")
                file.write("-" * 80 + "\n\n")

    async def run(self):
        """Run the complete manual job processing workflow."""
        print(Fore.BLUE + "----- Processing Manually Added Jobs -----\n" + Style.RESET_ALL)
        
        # Step 1: Get unprocessed jobs from database
        jobs = self.get_unprocessed_jobs()
        
        if not jobs:
            print(Fore.RED + "No unprocessed jobs found in database." + Style.RESET_ALL)
            print("Add jobs using: python quick_add_job.py or python manual_job_entry.py --interactive")
            return
        
        # Step 2: Score all jobs
        scores = await self.score_jobs(jobs)
        
        # Step 3: Add scores to jobs and save back to database
        scored_jobs = self.add_scores_to_jobs(jobs, scores)
        save_jobs(scored_jobs)  # Update database with scores
        
        # Display scores
        print(Fore.CYAN + "----- Job Scores -----" + Style.RESET_ALL)
        for job in scored_jobs:
            title = job.get('title', 'No Title')[:50]
            score = job.get('score', 0)
            print(f"  {title:<50} Score: {score}/10")
        
        # Step 4: Filter high-scoring jobs
        high_scoring_jobs = self.filter_high_scoring_jobs(scored_jobs)
        
        if not high_scoring_jobs:
            print(Fore.RED + f"No jobs scored >= {self.min_score}. Try lowering the threshold." + Style.RESET_ALL)
            return
        
        # Step 5: Process jobs in batches
        all_applications = []
        
        for i in range(0, len(high_scoring_jobs), self.batch_size):
            batch = high_scoring_jobs[i:i + self.batch_size]
            print(f"\nProcessing batch {i//self.batch_size + 1} ({len(batch)} jobs)...")
            
            applications = await self.process_jobs_batch(batch)
            all_applications.extend(applications)
        
        # Step 6: Save applications to file
        self.save_applications_to_file(all_applications)
        
        # Summary
        print(Fore.GREEN + "\n----- Processing Complete! -----" + Style.RESET_ALL)
        print(f"✅ Processed: {len(jobs)} jobs")
        print(f"✅ High scoring (>= {self.min_score}): {len(high_scoring_jobs)} jobs") 
        print(f"✅ Applications generated: {len(all_applications)}")
        print(f"✅ Applications saved to: {COVER_LETTERS_FILE}")

async def main():
    """Main function to run manual job processing."""
    try:
        # Load freelancer profile
        profile = read_text_file("./files/profile.md")
        
        # Create processor with customizable parameters
        processor = ManualJobProcessor(
            profile=profile,
            batch_size=3,      # Process 3 jobs at a time
            min_score=7        # Only process jobs with score >= 7
        )
        
        # Run the processing workflow
        await processor.run()
        
    except FileNotFoundError as e:
        print(Fore.RED + f"Error: {e}" + Style.RESET_ALL)
        print("Make sure you have a profile.md file in the ./files/ directory")
    except Exception as e:
        print(Fore.RED + f"Error: {e}" + Style.RESET_ALL)

if __name__ == "__main__":
    asyncio.run(main()) 
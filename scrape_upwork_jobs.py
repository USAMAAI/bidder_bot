import asyncio
from src.scraper import UpworkJobScraper
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

if __name__ == "__main__":
    search_query = "AI agent developer"
    number_of_jobs = 10
    
    print(f"Searching for: {search_query}")
    print(f"Number of jobs to scrape: {number_of_jobs}")
    
    scraper = UpworkJobScraper()
    result = asyncio.run(scraper.scrape_upwork_data(search_query, number_of_jobs))
    print(f"Result: {result}")
    print(f"Found {len(result)} jobs")
    
    # Save results to file for manual inspection
    if result:
        with open("scraped_jobs.txt", "w", encoding="utf-8") as f:
            for i, job in enumerate(result):
                f.write(f"Job {i+1}:\n")
                for key, value in job.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n" + "="*50 + "\n\n")
        print("Jobs saved to scraped_jobs.txt")
    else:
        print("No jobs found. This could be due to:")
        print("1. Network connectivity issues")
        print("2. Upwork blocking automated requests")
        print("3. Changes in Upwork's page structure")
        print("4. Search query returning no results")

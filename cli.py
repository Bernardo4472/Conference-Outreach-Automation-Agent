#!/usr/bin/env python3
"""
Conference Outreach Automation Agent (MVP) - CLI Interface

This script provides a command-line interface for the Conference Outreach Automation Agent.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from src.main import main as run_main

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("conference_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Conference Outreach Automation Agent"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["conferenceindex", "10times", "eventbrite"],
        help="List of conference sources to scrape"
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=["AI", "Tech", "Artificial Intelligence", "Machine Learning"],
        help="Keywords to filter conferences"
    )
    parser.add_argument(
        "--location",
        default="Europe",
        help="Location to filter conferences"
    )
    parser.add_argument(
        "--start-date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Start date for conference search (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="End date for conference search (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--max-conferences",
        type=int,
        default=10,
        help="Maximum number of conferences to process"
    )
    parser.add_argument(
        "--output",
        default="conference_outreach_results.csv",
        help="Output file path"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run the setup wizard to create a .env file"
    )
    
    args = parser.parse_args()
    
    if args.setup:
        setup_wizard()
    else:
        try:
            run_main()
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}", exc_info=True)
            sys.exit(1)


def setup_wizard():
    """Run the setup wizard to create a .env file."""
    print("Conference Outreach Automation Agent - Setup Wizard")
    print("=================================================")
    print("This wizard will help you set up the necessary configuration for the agent.")
    print("Press Enter to use the default values shown in brackets.\n")
    
    # Check if .env file already exists
    env_path = Path(".env")
    if env_path.exists():
        overwrite = input("A .env file already exists. Overwrite? (y/n) [n]: ").strip().lower()
        if overwrite != "y":
            print("Setup cancelled.")
            return
    
    # Get OpenAI API key
    openai_api_key = input("Enter your OpenAI API key: ").strip()
    while not openai_api_key:
        print("Error: OpenAI API key is required.")
        openai_api_key = input("Enter your OpenAI API key: ").strip()
    
    # Get scraping settings
    scrape_delay_min = input("Enter minimum delay between requests in seconds [2]: ").strip()
    scrape_delay_min = scrape_delay_min or "2"
    
    scrape_delay_max = input("Enter maximum delay between requests in seconds [5]: ").strip()
    scrape_delay_max = scrape_delay_max or "5"
    
    # Get company information
    company_name = input("Enter your company name [WhyAI]: ").strip()
    company_name = company_name or "WhyAI"
    
    company_description = input("Enter a brief description of your company: ").strip()
    if not company_description:
        company_description = "WhyAI is a leading AI solutions provider specializing in natural language processing and computer vision applications for enterprise clients."
    
    # Get speaker information
    speaker_name = input("Enter the speaker's name: ").strip()
    speaker_title = input("Enter the speaker's title: ").strip()
    speaker_bio = input("Enter a brief bio for the speaker: ").strip()
    
    # Create .env file
    with open(".env", "w") as f:
        f.write(f"# OpenAI API Key\n")
        f.write(f"OPENAI_API_KEY={openai_api_key}\n\n")
        
        f.write(f"# Scraping settings\n")
        f.write(f"SCRAPE_DELAY_MIN={scrape_delay_min}\n")
        f.write(f"SCRAPE_DELAY_MAX={scrape_delay_max}\n\n")
        
        f.write(f"# Email settings\n")
        f.write(f"COMPANY_NAME={company_name}\n")
        f.write(f'COMPANY_DESCRIPTION="{company_description}"\n')
        f.write(f"SPEAKER_NAME={speaker_name}\n")
        f.write(f"SPEAKER_TITLE={speaker_title}\n")
        f.write(f'SPEAKER_BIO="{speaker_bio}"\n')
    
    print("\nSetup complete! Configuration saved to .env file.")
    print("You can now run the agent with: python cli.py")


if __name__ == "__main__":
    main()

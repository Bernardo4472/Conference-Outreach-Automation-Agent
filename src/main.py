#!/usr/bin/env python3
"""
Conference Outreach Automation Agent (MVP)

This script automates the process of finding and contacting event organizers
for relevant tech conferences in Europe.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.scrapers.conference_scraper import ConferenceScraper
from src.scrapers.contact_extractor import ContactExtractor
from src.email_generation.email_generator import EmailGenerator
from src.utils.data_exporter import export_to_csv

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


def parse_arguments():
    """Parse command line arguments."""
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
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()
    
    try:
        # Step 1: Scrape conferences
        logger.info("Starting conference scraping...")
        conference_scraper = ConferenceScraper(
            sources=args.sources,
            keywords=args.keywords,
            location=args.location,
            start_date=args.start_date,
            end_date=args.end_date,
            max_conferences=args.max_conferences,
            headless=args.headless
        )
        conferences = conference_scraper.scrape()
        logger.info(f"Found {len(conferences)} relevant conferences")
        
        # Step 2: Extract contact information
        logger.info("Extracting contact information...")
        contact_extractor = ContactExtractor(headless=args.headless)
        conferences_with_contacts = contact_extractor.extract_contacts(conferences)
        
        # Step 3: Generate outreach emails
        logger.info("Generating outreach emails...")
        email_generator = EmailGenerator()
        conferences_with_emails = email_generator.generate_emails(conferences_with_contacts)
        
        # Step 4: Export results
        logger.info(f"Exporting results to {args.output}...")
        export_to_csv(conferences_with_emails, args.output)
        
        logger.info("Process completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

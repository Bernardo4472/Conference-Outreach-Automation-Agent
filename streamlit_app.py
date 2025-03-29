#!/usr/bin/env python3
"""
Conference Outreach Automation Agent (MVP) - Streamlit Interface

This script provides a web interface for the Conference Outreach Automation Agent using Streamlit.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

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


def create_env_file(openai_api_key, company_name, company_description, speaker_name, speaker_title, speaker_bio):
    """Create a .env file with the provided settings."""
    with open(".env", "w") as f:
        f.write(f"# OpenAI API Key\n")
        f.write(f"OPENAI_API_KEY={openai_api_key}\n\n")
        
        f.write(f"# Scraping settings\n")
        f.write(f"SCRAPE_DELAY_MIN=2\n")
        f.write(f"SCRAPE_DELAY_MAX=5\n\n")
        
        f.write(f"# Email settings\n")
        f.write(f"COMPANY_NAME={company_name}\n")
        f.write(f'COMPANY_DESCRIPTION="{company_description}"\n')
        f.write(f"SPEAKER_NAME={speaker_name}\n")
        f.write(f"SPEAKER_TITLE={speaker_title}\n")
        f.write(f'SPEAKER_BIO="{speaker_bio}"\n')
    
    # Reload environment variables
    load_dotenv(override=True)


def run_conference_scraper(sources, keywords, location, start_date, end_date, max_conferences, headless):
    """Run the conference scraper and return the results."""
    try:
        # Step 1: Scrape conferences
        st.info("Starting conference scraping...")
        progress_bar = st.progress(0)
        
        conference_scraper = ConferenceScraper(
            sources=sources,
            keywords=keywords,
            location=location,
            start_date=start_date,
            end_date=end_date,
            max_conferences=max_conferences,
            headless=headless
        )
        conferences = conference_scraper.scrape()
        
        st.success(f"Found {len(conferences)} relevant conferences")
        progress_bar.progress(25)
        
        # Step 2: Extract contact information
        st.info("Extracting contact information...")
        contact_extractor = ContactExtractor(headless=headless)
        conferences_with_contacts = contact_extractor.extract_contacts(conferences)
        
        # Count conferences with contacts
        conferences_with_contacts_count = sum(1 for conf in conferences_with_contacts if conf.has_contacts())
        st.success(f"Found contacts for {conferences_with_contacts_count} out of {len(conferences)} conferences")
        progress_bar.progress(50)
        
        # Step 3: Generate outreach emails
        st.info("Generating outreach emails...")
        email_generator = EmailGenerator()
        conferences_with_emails = email_generator.generate_emails(conferences_with_contacts)
        
        # Count conferences with emails
        conferences_with_emails_count = sum(1 for conf in conferences_with_emails if conf.has_outreach_email())
        st.success(f"Generated emails for {conferences_with_emails_count} conferences")
        progress_bar.progress(75)
        
        # Step 4: Export results
        output_file = "conference_outreach_results.csv"
        st.info(f"Exporting results to {output_file}...")
        export_to_csv(conferences_with_emails, output_file)
        
        st.success("Process completed successfully!")
        progress_bar.progress(100)
        
        # Display results
        display_results(conferences_with_emails, output_file)
        
        return conferences_with_emails
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return []


def display_results(conferences, output_file):
    """Display the results in the Streamlit interface."""
    if not conferences:
        st.warning("No conferences found.")
        return
    
    # Create a DataFrame for display
    data = []
    for conference in conferences:
        for contact in conference.contacts:
            data.append({
                "Conference": conference.title,
                "Date": conference.start_date.strftime("%Y-%m-%d"),
                "Location": conference.location,
                "Organizer": contact.name,
                "Role": contact.role or "",
                "Email": contact.email,
                "Has Email": bool(conference.outreach_email)
            })
    
    if not data:
        st.warning("No contacts found for the conferences.")
        return
    
    df = pd.DataFrame(data)
    
    # Display summary
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Conferences", len(conferences))
    col2.metric("Contacts", len(data))
    col3.metric("With Emails", sum(1 for conf in conferences if conf.has_outreach_email()))
    
    # Display table
    st.subheader("Results")
    st.dataframe(df)
    
    # Provide download link
    with open(output_file, "rb") as file:
        st.download_button(
            label="Download CSV",
            data=file,
            file_name=output_file,
            mime="text/csv"
        )
    
    # Display sample email
    st.subheader("Sample Email")
    for conference in conferences:
        if conference.has_outreach_email():
            st.text_area("Generated Email", conference.outreach_email, height=300)
            break


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Conference Outreach Automation Agent",
        page_icon="📅",
        layout="wide"
    )
    
    st.title("Conference Outreach Automation Agent")
    st.markdown("""
    This tool automates the process of finding and contacting event organizers for relevant tech conferences.
    """)
    
    # Check if .env file exists
    env_path = Path(".env")
    if not env_path.exists():
        st.warning("No configuration file found. Please set up your configuration first.")
        setup_tab = True
    else:
        setup_tab = False
    
    # Create tabs
    if setup_tab:
        tab1, tab2 = st.tabs(["Setup", "Run"])
    else:
        tab1, tab2 = st.tabs(["Run", "Setup"])
    
    # Setup tab
    with tab1 if setup_tab else tab2:
        st.header("Configuration Setup")
        
        with st.form("setup_form"):
            st.subheader("OpenAI API Key")
            openai_api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
            
            st.subheader("Company Information")
            company_name = st.text_input("Company Name", value=os.getenv("COMPANY_NAME", "WhyAI"))
            company_description = st.text_area("Company Description", value=os.getenv("COMPANY_DESCRIPTION", "WhyAI is a leading AI solutions provider specializing in natural language processing and computer vision applications for enterprise clients."))
            
            st.subheader("Speaker Information")
            speaker_name = st.text_input("Speaker Name", value=os.getenv("SPEAKER_NAME", ""))
            speaker_title = st.text_input("Speaker Title", value=os.getenv("SPEAKER_TITLE", ""))
            speaker_bio = st.text_area("Speaker Bio", value=os.getenv("SPEAKER_BIO", ""))
            
            submit_button = st.form_submit_button("Save Configuration")
        
        if submit_button:
            if not openai_api_key:
                st.error("OpenAI API Key is required.")
            else:
                create_env_file(
                    openai_api_key,
                    company_name,
                    company_description,
                    speaker_name,
                    speaker_title,
                    speaker_bio
                )
                st.success("Configuration saved successfully!")
    
    # Run tab
    with tab2 if setup_tab else tab1:
        st.header("Run Conference Scraper")
        
        with st.form("run_form"):
            # Sources
            st.subheader("Conference Sources")
            sources = st.multiselect(
                "Select sources to scrape",
                ["conferenceindex", "10times", "eventbrite"],
                default=["conferenceindex", "10times", "eventbrite"]
            )
            
            # Keywords
            st.subheader("Keywords")
            keywords_input = st.text_input(
                "Enter keywords (comma-separated)",
                value="AI, Tech, Artificial Intelligence, Machine Learning"
            )
            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
            
            # Location
            location = st.text_input("Location", value="Europe")
            
            # Date range
            st.subheader("Date Range")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now().date()
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=(datetime.now() + timedelta(days=365)).date()
                )
            
            # Other settings
            st.subheader("Additional Settings")
            max_conferences = st.number_input("Maximum Conferences", min_value=1, max_value=100, value=10)
            headless = st.checkbox("Run in Headless Mode", value=True)
            
            run_button = st.form_submit_button("Run Scraper")
        
        if run_button:
            if not sources:
                st.error("Please select at least one source.")
            elif not keywords:
                st.error("Please enter at least one keyword.")
            elif not location:
                st.error("Please enter a location.")
            elif start_date > end_date:
                st.error("Start date cannot be after end date.")
            else:
                run_conference_scraper(
                    sources=sources,
                    keywords=keywords,
                    location=location,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    max_conferences=max_conferences,
                    headless=headless
                )


if __name__ == "__main__":
    main()

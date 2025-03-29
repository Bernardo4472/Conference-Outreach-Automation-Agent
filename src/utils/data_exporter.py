"""
Data exporter utilities for the Conference Outreach Automation Agent.
"""

import csv
import logging
from pathlib import Path
from typing import List

import pandas as pd

from src.utils.models import Conference

logger = logging.getLogger(__name__)


def export_to_csv(conferences: List[Conference], output_path: str) -> None:
    """
    Export conference data to a CSV file.
    
    Args:
        conferences: List of Conference objects
        output_path: Path to the output CSV file
    """
    # Create output directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for export
    data = []
    for conference in conferences:
        for contact in conference.contacts:
            data.append({
                "conference_name": conference.title,
                "date": conference.start_date.strftime("%Y-%m-%d"),
                "end_date": conference.end_date.strftime("%Y-%m-%d") if conference.end_date else "",
                "location": conference.location,
                "website_url": str(conference.website_url),
                "organizer_name": contact.name,
                "organizer_role": contact.role or "",
                "email": contact.email,
                "phone": contact.phone or "",
                "linkedin": contact.linkedin or "",
                "generated_email_message": conference.outreach_email or ""
            })
    
    # If no contacts were found, still include the conference in the output
    for conference in conferences:
        if not conference.has_contacts():
            data.append({
                "conference_name": conference.title,
                "date": conference.start_date.strftime("%Y-%m-%d"),
                "end_date": conference.end_date.strftime("%Y-%m-%d") if conference.end_date else "",
                "location": conference.location,
                "website_url": str(conference.website_url),
                "organizer_name": "",
                "organizer_role": "",
                "email": "",
                "phone": "",
                "linkedin": "",
                "generated_email_message": ""
            })
    
    # Export to CSV
    if data:
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(data)} records to {output_path}")
    else:
        # Create an empty CSV with headers
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "conference_name", "date", "end_date", "location", "website_url",
                "organizer_name", "organizer_role", "email", "phone", "linkedin",
                "generated_email_message"
            ])
        logger.warning(f"No data to export. Created empty CSV file at {output_path}")

"""
Conference scraper module.

This module handles scraping conference information from various sources.
"""

import logging
import os
import random
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup
import pandas as pd

from src.utils.models import Conference

logger = logging.getLogger(__name__)


class ConferenceScraper:
    """Scraper for finding relevant conferences."""
    
    def __init__(
        self,
        sources: List[str],
        keywords: List[str],
        location: str,
        start_date: str,
        end_date: Optional[str] = None,
        max_conferences: int = 10,
        headless: bool = True
    ):
        """
        Initialize the conference scraper.
        
        Args:
            sources: List of sources to scrape (e.g., "conferenceindex", "10times")
            keywords: List of keywords to filter conferences
            location: Location to filter conferences
            start_date: Start date for conference search (YYYY-MM-DD)
            end_date: End date for conference search (YYYY-MM-DD)
            max_conferences: Maximum number of conferences to process
            headless: Whether to run the browser in headless mode
        """
        self.sources = sources
        self.keywords = keywords
        self.location = location
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        self.max_conferences = max_conferences
        self.headless = headless
        
        # Load delay settings from environment variables or use defaults
        self.delay_min = float(os.getenv("SCRAPE_DELAY_MIN", "2"))
        self.delay_max = float(os.getenv("SCRAPE_DELAY_MAX", "5"))
        
        # Source-specific scraping methods
        self.source_scrapers = {
            "conferenceindex": self._scrape_conferenceindex,
            "10times": self._scrape_10times,
            "eventbrite": self._scrape_eventbrite,
        }
    
    def scrape(self) -> List[Conference]:
        """
        Scrape conferences from all specified sources.
        
        Returns:
            List of Conference objects
        """
        all_conferences = []
        
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            try:
                for source in self.sources:
                    if source in self.source_scrapers:
                        logger.info(f"Scraping conferences from {source}...")
                        
                        try:
                            page = context.new_page()
                            conferences = self.source_scrapers[source](page)
                            all_conferences.extend(conferences)
                            logger.info(f"Found {len(conferences)} conferences from {source}")
                            
                            # Apply max conferences limit
                            if len(all_conferences) >= self.max_conferences:
                                all_conferences = all_conferences[:self.max_conferences]
                                break
                                
                        except Exception as e:
                            logger.error(f"Error scraping {source}: {str(e)}", exc_info=True)
                        finally:
                            page.close()
                    else:
                        logger.warning(f"Unsupported source: {source}")
            finally:
                context.close()
                browser.close()
        
        return all_conferences
    
    def _random_delay(self) -> None:
        """Add a random delay between requests to avoid being blocked."""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
    
    def _is_relevant_conference(self, title: str, description: str = "") -> bool:
        """
        Check if a conference is relevant based on keywords.
        
        Args:
            title: Conference title
            description: Conference description
        
        Returns:
            True if the conference is relevant, False otherwise
        """
        text = (title + " " + description).lower()
        return any(keyword.lower() in text for keyword in self.keywords)
    
    def _is_in_date_range(self, date: datetime) -> bool:
        """
        Check if a date is within the specified range.
        
        Args:
            date: Date to check
        
        Returns:
            True if the date is within range, False otherwise
        """
        if date < self.start_date:
            return False
        
        if self.end_date and date > self.end_date:
            return False
        
        return True
    
    def _is_in_location(self, location: str) -> bool:
        """
        Check if a location matches the specified location.
        
        Args:
            location: Location to check
        
        Returns:
            True if the location matches, False otherwise
        """
        return self.location.lower() in location.lower()
    
    def _scrape_conferenceindex(self, page: Page) -> List[Conference]:
        """
        Scrape conferences from conferenceindex.org.
        
        Args:
            page: Playwright page object
        
        Returns:
            List of Conference objects
        """
        conferences = []
        
        # Navigate to the search page
        base_url = "https://conferenceindex.org"
        search_url = f"{base_url}/conferences/europe?keywords={'+'.join(self.keywords)}"
        
        page.goto(search_url)
        page.wait_for_load_state("networkidle")
        
        # Extract conference listings
        html_content = page.content()
        soup = BeautifulSoup(html_content, "lxml")
        
        conference_elements = soup.select(".conference-item")
        
        for element in conference_elements:
            try:
                title_element = element.select_one(".conference-title a")
                title = title_element.text.strip() if title_element else "Unknown Conference"
                
                # Extract date
                date_element = element.select_one(".conference-dates")
                date_text = date_element.text.strip() if date_element else ""
                
                # Parse date (format: "15 Jul 2025 - 17 Jul 2025")
                start_date = None
                end_date = None
                
                if date_text:
                    date_parts = date_text.split(" - ")
                    try:
                        start_date = datetime.strptime(date_parts[0], "%d %b %Y")
                        if len(date_parts) > 1:
                            end_date = datetime.strptime(date_parts[1], "%d %b %Y")
                    except ValueError:
                        logger.warning(f"Could not parse date: {date_text}")
                        continue
                
                if not start_date or not self._is_in_date_range(start_date):
                    continue
                
                # Extract location
                location_element = element.select_one(".conference-location")
                location = location_element.text.strip() if location_element else "Unknown Location"
                
                if not self._is_in_location(location):
                    continue
                
                # Extract website URL
                website_url = urljoin(base_url, title_element["href"]) if title_element else None
                
                if not website_url:
                    continue
                
                # Extract description
                description_element = element.select_one(".conference-description")
                description = description_element.text.strip() if description_element else ""
                
                # Check if conference is relevant
                if not self._is_relevant_conference(title, description):
                    continue
                
                # Create Conference object
                conference = Conference(
                    title=title,
                    start_date=start_date,
                    end_date=end_date,
                    location=location,
                    website_url=website_url,
                    description=description
                )
                
                conferences.append(conference)
                
                # Visit conference page to get the official website
                page.goto(website_url)
                page.wait_for_load_state("networkidle")
                
                html_content = page.content()
                soup = BeautifulSoup(html_content, "lxml")
                
                official_website_element = soup.select_one("a[href*='http']:not([href*='conferenceindex.org'])")
                if official_website_element:
                    official_website = official_website_element["href"]
                    conference.website_url = official_website
                
                self._random_delay()
                
            except Exception as e:
                logger.error(f"Error processing conference: {str(e)}")
        
        return conferences
    
    def _scrape_10times(self, page: Page) -> List[Conference]:
        """
        Scrape conferences from 10times.com.
        
        Args:
            page: Playwright page object
        
        Returns:
            List of Conference objects
        """
        conferences = []
        
        # Navigate to the search page
        base_url = "https://10times.com"
        search_url = f"{base_url}/events?kw={'+'.join(self.keywords)}&ci=europe"
        
        page.goto(search_url)
        page.wait_for_load_state("networkidle")
        
        # Extract conference listings
        html_content = page.content()
        soup = BeautifulSoup(html_content, "lxml")
        
        conference_elements = soup.select(".event-list-item")
        
        for element in conference_elements:
            try:
                title_element = element.select_one(".event-name a")
                title = title_element.text.strip() if title_element else "Unknown Conference"
                
                # Extract date
                date_element = element.select_one(".event-dates")
                date_text = date_element.text.strip() if date_element else ""
                
                # Parse date (format varies)
                start_date = None
                end_date = None
                
                if date_text:
                    # Try different date formats
                    date_formats = [
                        "%d %b %Y",  # 15 Jul 2025
                        "%d-%d %b %Y",  # 15-17 Jul 2025
                        "%d %b - %d %b %Y",  # 15 Jul - 17 Jul 2025
                    ]
                    
                    for date_format in date_formats:
                        try:
                            if "-" in date_text and " - " not in date_text:
                                # Format: 15-17 Jul 2025
                                parts = date_text.split("-")
                                day_start = parts[0].strip()
                                rest = parts[1].strip()
                                
                                start_date = datetime.strptime(f"{day_start} {rest}", "%d %b %Y")
                                end_date = datetime.strptime(f"{parts[1].strip()}", "%d %b %Y")
                                break
                            elif " - " in date_text:
                                # Format: 15 Jul - 17 Jul 2025
                                parts = date_text.split(" - ")
                                start_date = datetime.strptime(parts[0], "%d %b")
                                end_date = datetime.strptime(parts[1], "%d %b %Y")
                                
                                # Set the year for start_date
                                start_date = start_date.replace(year=end_date.year)
                                break
                            else:
                                # Format: 15 Jul 2025
                                start_date = datetime.strptime(date_text, date_format)
                                break
                        except ValueError:
                            continue
                
                if not start_date or not self._is_in_date_range(start_date):
                    continue
                
                # Extract location
                location_element = element.select_one(".event-location")
                location = location_element.text.strip() if location_element else "Unknown Location"
                
                if not self._is_in_location(location):
                    continue
                
                # Extract website URL
                website_url = urljoin(base_url, title_element["href"]) if title_element else None
                
                if not website_url:
                    continue
                
                # Extract description
                description_element = element.select_one(".event-description")
                description = description_element.text.strip() if description_element else ""
                
                # Check if conference is relevant
                if not self._is_relevant_conference(title, description):
                    continue
                
                # Create Conference object
                conference = Conference(
                    title=title,
                    start_date=start_date,
                    end_date=end_date,
                    location=location,
                    website_url=website_url,
                    description=description
                )
                
                conferences.append(conference)
                
                # Visit conference page to get the official website
                page.goto(website_url)
                page.wait_for_load_state("networkidle")
                
                html_content = page.content()
                soup = BeautifulSoup(html_content, "lxml")
                
                official_website_element = soup.select_one("a.website-link")
                if official_website_element:
                    official_website = official_website_element["href"]
                    conference.website_url = official_website
                
                self._random_delay()
                
            except Exception as e:
                logger.error(f"Error processing conference: {str(e)}")
        
        return conferences
    
    def _scrape_eventbrite(self, page: Page) -> List[Conference]:
        """
        Scrape conferences from eventbrite.com.
        
        Args:
            page: Playwright page object
        
        Returns:
            List of Conference objects
        """
        conferences = []
        
        # Navigate to the search page
        base_url = "https://www.eventbrite.com"
        search_url = f"{base_url}/d/europe/conferences/?q={'+'.join(self.keywords)}"
        
        page.goto(search_url)
        page.wait_for_load_state("networkidle")
        
        # Extract conference listings
        html_content = page.content()
        soup = BeautifulSoup(html_content, "lxml")
        
        conference_elements = soup.select(".search-event-card-wrapper")
        
        for element in conference_elements:
            try:
                title_element = element.select_one(".event-card__title")
                title = title_element.text.strip() if title_element else "Unknown Conference"
                
                # Extract date
                date_element = element.select_one(".event-card__date")
                date_text = date_element.text.strip() if date_element else ""
                
                # Parse date (format varies)
                start_date = None
                end_date = None
                
                if date_text:
                    # Try to extract date using regex
                    date_match = re.search(r'(\w{3} \d{1,2})(?: - (\w{3} \d{1,2}))?, (\d{4})', date_text)
                    if date_match:
                        start_date_str = f"{date_match.group(1)}, {date_match.group(3)}"
                        try:
                            start_date = datetime.strptime(start_date_str, "%b %d, %Y")
                            
                            if date_match.group(2):
                                end_date_str = f"{date_match.group(2)}, {date_match.group(3)}"
                                end_date = datetime.strptime(end_date_str, "%b %d, %Y")
                        except ValueError:
                            logger.warning(f"Could not parse date: {date_text}")
                            continue
                
                if not start_date or not self._is_in_date_range(start_date):
                    continue
                
                # Extract location
                location_element = element.select_one(".event-card__location")
                location = location_element.text.strip() if location_element else "Unknown Location"
                
                if not self._is_in_location(location):
                    continue
                
                # Extract website URL
                link_element = element.select_one("a.event-card-link")
                website_url = urljoin(base_url, link_element["href"]) if link_element else None
                
                if not website_url:
                    continue
                
                # Extract description (not available in the card, need to visit the page)
                description = ""
                
                # Check if conference is relevant
                if not self._is_relevant_conference(title, description):
                    continue
                
                # Create Conference object
                conference = Conference(
                    title=title,
                    start_date=start_date,
                    end_date=end_date,
                    location=location,
                    website_url=website_url,
                    description=description
                )
                
                conferences.append(conference)
                
                # Visit conference page to get more details
                page.goto(website_url)
                page.wait_for_load_state("networkidle")
                
                html_content = page.content()
                soup = BeautifulSoup(html_content, "lxml")
                
                # Extract description
                description_element = soup.select_one(".event-details__description")
                if description_element:
                    description = description_element.text.strip()
                    conference.description = description
                
                # Extract official website if available
                official_website_element = soup.select_one("a[href*='http']:not([href*='eventbrite.com'])")
                if official_website_element:
                    official_website = official_website_element["href"]
                    conference.website_url = official_website
                
                self._random_delay()
                
            except Exception as e:
                logger.error(f"Error processing conference: {str(e)}")
        
        return conferences

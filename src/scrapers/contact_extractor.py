"""
Contact extractor module.

This module handles extracting contact information from conference websites.
"""

import logging
import os
import random
import re
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup

from src.utils.models import Conference, Contact

logger = logging.getLogger(__name__)


class ContactExtractor:
    """Extractor for finding contact information on conference websites."""
    
    # Common contact page paths
    CONTACT_PATHS = [
        "/contact", "/contacts", "/contact-us", "/about", "/about-us",
        "/team", "/organizers", "/committee", "/staff", "/speakers"
    ]
    
    # Organizer role keywords
    ORGANIZER_ROLES = [
        "organizer", "organiser", "coordinator", "manager", "director",
        "chair", "lead", "head", "event manager", "event director",
        "conference chair", "program chair", "committee chair"
    ]
    
    # Email regex pattern
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    def __init__(self, headless: bool = True):
        """
        Initialize the contact extractor.
        
        Args:
            headless: Whether to run the browser in headless mode
        """
        self.headless = headless
        
        # Load delay settings from environment variables or use defaults
        self.delay_min = float(os.getenv("SCRAPE_DELAY_MIN", "2"))
        self.delay_max = float(os.getenv("SCRAPE_DELAY_MAX", "5"))
    
    def extract_contacts(self, conferences: List[Conference]) -> List[Conference]:
        """
        Extract contact information from conference websites.
        
        Args:
            conferences: List of Conference objects
        
        Returns:
            List of Conference objects with contact information
        """
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            try:
                page = context.new_page()
                
                for i, conference in enumerate(conferences):
                    logger.info(f"Extracting contacts for conference {i+1}/{len(conferences)}: {conference.title}")
                    
                    try:
                        self._extract_contacts_for_conference(page, conference)
                        
                        if conference.has_contacts():
                            logger.info(f"Found {len(conference.contacts)} contacts for {conference.title}")
                        else:
                            logger.warning(f"No contacts found for {conference.title}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting contacts for {conference.title}: {str(e)}", exc_info=True)
                    
                    self._random_delay()
            finally:
                page.close()
                context.close()
                browser.close()
        
        return conferences
    
    def _random_delay(self) -> None:
        """Add a random delay between requests to avoid being blocked."""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
    
    def _extract_contacts_for_conference(self, page: Page, conference: Conference) -> None:
        """
        Extract contact information for a specific conference.
        
        Args:
            page: Playwright page object
            conference: Conference object
        """
        website_url = str(conference.website_url)
        
        # Visit the main page first
        try:
            page.goto(website_url, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # Extract contacts from the main page
            self._extract_contacts_from_page(page, conference)
            
            # If no contacts found, try contact pages
            if not conference.has_contacts():
                self._visit_contact_pages(page, conference)
        except Exception as e:
            logger.error(f"Error visiting {website_url}: {str(e)}")
    
    def _visit_contact_pages(self, page: Page, conference: Conference) -> None:
        """
        Visit potential contact pages and extract contact information.
        
        Args:
            page: Playwright page object
            conference: Conference object
        """
        website_url = str(conference.website_url)
        parsed_url = urlparse(website_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Find links that might lead to contact pages
        html_content = page.content()
        soup = BeautifulSoup(html_content, "lxml")
        
        # Collect potential contact page links
        contact_links = []
        
        # Look for links with contact-related text
        for link in soup.find_all("a", href=True):
            href = link["href"]
            link_text = link.text.strip().lower()
            
            # Skip empty links, anchors, or external links
            if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            
            # Check if the link text contains contact-related keywords
            contact_keywords = ["contact", "about", "team", "organizer", "committee", "staff", "speaker"]
            if any(keyword in link_text for keyword in contact_keywords):
                # Resolve relative URLs
                if not href.startswith(("http://", "https://")):
                    href = urljoin(base_url, href)
                
                # Only include links from the same domain
                if urlparse(href).netloc == parsed_url.netloc:
                    contact_links.append(href)
        
        # Add common contact paths if not already included
        for path in self.CONTACT_PATHS:
            contact_url = urljoin(base_url, path)
            if contact_url not in contact_links:
                contact_links.append(contact_url)
        
        # Visit each potential contact page
        visited_urls = set()
        
        for link in contact_links:
            if link in visited_urls:
                continue
            
            visited_urls.add(link)
            
            try:
                logger.info(f"Visiting potential contact page: {link}")
                page.goto(link, timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # Extract contacts from the page
                self._extract_contacts_from_page(page, conference)
                
                # If we found contacts, we can stop
                if conference.has_contacts():
                    break
                
                self._random_delay()
                
            except Exception as e:
                logger.error(f"Error visiting {link}: {str(e)}")
    
    def _extract_contacts_from_page(self, page: Page, conference: Conference) -> None:
        """
        Extract contact information from the current page.
        
        Args:
            page: Playwright page object
            conference: Conference object
        """
        html_content = page.content()
        soup = BeautifulSoup(html_content, "lxml")
        
        # Extract emails from the page
        emails = self._extract_emails(soup)
        
        # Extract structured contact information
        self._extract_structured_contacts(soup, conference, emails)
        
        # If no structured contacts found, use emails as fallback
        if not conference.has_contacts() and emails:
            for email in emails:
                # Try to extract a name from the email
                name_part = email.split('@')[0]
                name = ' '.join(word.capitalize() for word in re.findall(r'[a-zA-Z]+', name_part))
                
                if not name:
                    name = "Unknown"
                
                contact = Contact(
                    name=name,
                    email=email,
                    role="Contact"
                )
                
                conference.contacts.append(contact)
    
    def _extract_emails(self, soup: BeautifulSoup) -> Set[str]:
        """
        Extract email addresses from the page.
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Set of email addresses
        """
        emails = set()
        
        # Extract emails from text
        page_text = soup.get_text()
        email_matches = re.findall(self.EMAIL_PATTERN, page_text)
        emails.update(email_matches)
        
        # Extract emails from mailto links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("mailto:"):
                email = href[7:].split('?')[0]  # Remove mailto: prefix and any parameters
                if re.match(self.EMAIL_PATTERN, email):
                    emails.add(email)
        
        return emails
    
    def _extract_structured_contacts(self, soup: BeautifulSoup, conference: Conference, emails: Set[str]) -> None:
        """
        Extract structured contact information from the page.
        
        Args:
            soup: BeautifulSoup object
            conference: Conference object
            emails: Set of email addresses
        """
        # Look for common contact information patterns
        
        # Method 1: Look for team/staff/committee sections
        team_sections = soup.find_all(["section", "div"], class_=lambda c: c and any(keyword in c.lower() for keyword in ["team", "staff", "committee", "organizer", "speaker"]))
        
        for section in team_sections:
            # Look for person cards/items within the section
            person_elements = section.find_all(["div", "li"], class_=lambda c: c and any(keyword in c.lower() for keyword in ["person", "member", "card", "item", "profile"]))
            
            if not person_elements:
                # If no specific person elements found, try to find any divs that might contain person info
                person_elements = section.find_all(["div", "li"])
            
            for person in person_elements:
                name_element = person.find(["h2", "h3", "h4", "h5", "strong", "b", "span", "div"], class_=lambda c: c and "name" in c.lower() if c else False)
                
                if not name_element:
                    name_element = person.find(["h2", "h3", "h4", "h5"])
                
                if name_element:
                    name = name_element.text.strip()
                    
                    # Skip if name is too short or looks like a heading
                    if len(name) < 3 or name.lower() in ["name", "team", "staff", "committee", "organizers", "speakers"]:
                        continue
                    
                    # Extract role
                    role_element = person.find(["p", "span", "div"], class_=lambda c: c and any(keyword in c.lower() for keyword in ["role", "position", "title", "job"]) if c else False)
                    role = role_element.text.strip() if role_element else None
                    
                    # If no specific role element found, look for text that might be a role
                    if not role:
                        for element in person.find_all(["p", "span", "div"]):
                            text = element.text.strip()
                            if text and text != name and len(text) < 50:
                                role = text
                                break
                    
                    # Check if the role is related to event organization
                    is_organizer = False
                    if role:
                        is_organizer = any(keyword in role.lower() for keyword in self.ORGANIZER_ROLES)
                    
                    # Extract email
                    email = None
                    email_element = person.find("a", href=lambda h: h and h.startswith("mailto:"))
                    
                    if email_element:
                        email = email_element["href"][7:].split('?')[0]  # Remove mailto: prefix and any parameters
                    else:
                        # Look for email in text
                        person_text = person.get_text()
                        email_matches = re.findall(self.EMAIL_PATTERN, person_text)
                        if email_matches:
                            email = email_matches[0]
                        else:
                            # Try to match with extracted emails
                            name_parts = name.lower().split()
                            for extracted_email in emails:
                                email_prefix = extracted_email.split('@')[0].lower()
                                if any(part in email_prefix for part in name_parts):
                                    email = extracted_email
                                    break
                    
                    # Extract phone
                    phone = None
                    phone_element = person.find("a", href=lambda h: h and h.startswith("tel:"))
                    
                    if phone_element:
                        phone = phone_element["href"][4:]  # Remove tel: prefix
                    else:
                        # Look for phone in text
                        phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?(?:\d{1,4}[-.\s]?){1,3}\d{1,4}'
                        phone_matches = re.findall(phone_pattern, person.get_text())
                        if phone_matches:
                            phone = phone_matches[0]
                    
                    # Extract LinkedIn
                    linkedin = None
                    linkedin_element = person.find("a", href=lambda h: h and "linkedin.com" in h)
                    
                    if linkedin_element:
                        linkedin = linkedin_element["href"]
                    
                    # Only add contact if we have an email or it's clearly an organizer
                    if email or is_organizer:
                        contact = Contact(
                            name=name,
                            role=role,
                            email=email or "",
                            phone=phone,
                            linkedin=linkedin
                        )
                        
                        # Check if this contact is already added
                        if not any(c.email == contact.email for c in conference.contacts if c.email):
                            conference.contacts.append(contact)
        
        # Method 2: Look for contact information in structured data
        contact_sections = soup.find_all(["section", "div"], class_=lambda c: c and "contact" in c.lower() if c else False)
        
        for section in contact_sections:
            # Look for email
            email_element = section.find("a", href=lambda h: h and h.startswith("mailto:"))
            
            if email_element:
                email = email_element["href"][7:].split('?')[0]  # Remove mailto: prefix and any parameters
                
                # Try to extract a name
                name_element = section.find(["h2", "h3", "h4", "h5", "strong", "b"])
                name = name_element.text.strip() if name_element else "Contact"
                
                # Create contact
                contact = Contact(
                    name=name,
                    email=email,
                    role="Contact"
                )
                
                # Check if this contact is already added
                if not any(c.email == contact.email for c in conference.contacts if c.email):
                    conference.contacts.append(contact)

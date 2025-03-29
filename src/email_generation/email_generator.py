"""
Email generator module.

This module handles generating personalized outreach emails for conference organizers.
"""

import logging
import os
from typing import Dict, List, Optional

import openai

from src.utils.models import Conference, Contact

logger = logging.getLogger(__name__)


class EmailGenerator:
    """Generator for personalized outreach emails."""
    
    def __init__(self):
        """Initialize the email generator."""
        # Load OpenAI API key from environment variables
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai.api_key:
            logger.warning("OpenAI API key not found. Email generation will be disabled.")
        
        # Load company and speaker information from environment variables
        self.company_name = os.getenv("COMPANY_NAME", "WhyAI")
        self.company_description = os.getenv("COMPANY_DESCRIPTION", "")
        self.speaker_name = os.getenv("SPEAKER_NAME", "")
        self.speaker_title = os.getenv("SPEAKER_TITLE", "")
        self.speaker_bio = os.getenv("SPEAKER_BIO", "")
    
    def generate_emails(self, conferences: List[Conference]) -> List[Conference]:
        """
        Generate personalized outreach emails for conference organizers.
        
        Args:
            conferences: List of Conference objects with contact information
        
        Returns:
            List of Conference objects with outreach emails
        """
        if not openai.api_key:
            logger.error("OpenAI API key not found. Skipping email generation.")
            return conferences
        
        for conference in conferences:
            if conference.has_contacts():
                try:
                    # Get the first contact (primary organizer)
                    primary_contact = conference.contacts[0]
                    
                    # Generate email
                    email = self._generate_email(conference, primary_contact)
                    
                    # Set the outreach email
                    conference.outreach_email = email
                    
                    logger.info(f"Generated email for {conference.title}")
                    
                except Exception as e:
                    logger.error(f"Error generating email for {conference.title}: {str(e)}", exc_info=True)
        
        return conferences
    
    def _generate_email(self, conference: Conference, contact: Contact) -> str:
        """
        Generate a personalized outreach email for a conference organizer.
        
        Args:
            conference: Conference object
            contact: Contact object
        
        Returns:
            Generated email text
        """
        # Prepare the prompt for the OpenAI API
        prompt = self._create_prompt(conference, contact)
        
        try:
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",  # Use GPT-4 for high-quality emails
                messages=[
                    {"role": "system", "content": "You are an expert at writing personalized, professional outreach emails for business development."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract the generated email
            email = response.choices[0].message.content.strip()
            
            return email
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            
            # Fallback to a template-based email
            return self._create_template_email(conference, contact)
    
    def _create_prompt(self, conference: Conference, contact: Contact) -> str:
        """
        Create a prompt for the OpenAI API.
        
        Args:
            conference: Conference object
            contact: Contact object
        
        Returns:
            Prompt text
        """
        prompt = f"""
        Write a personalized outreach email to a conference organizer with the following details:

        Conference: {conference.title}
        Date: {conference.start_date.strftime("%Y-%m-%d")}
        Location: {conference.location}
        Organizer: {contact.name}
        Organizer Role: {contact.role or "Event Organizer"}

        Company Information:
        Company Name: {self.company_name}
        Company Description: {self.company_description}

        Speaker Information:
        Speaker Name: {self.speaker_name}
        Speaker Title: {self.speaker_title}
        Speaker Bio: {self.speaker_bio}

        The email should:
        1. Be professional and personalized to the specific conference and organizer
        2. Express interest in speaking or participating at the conference
        3. Briefly highlight the company's expertise and the value we can bring to the conference
        4. Suggest a follow-up call or meeting
        5. Thank the organizer for their consideration
        6. Include a professional signature

        The tone should be friendly but professional, and the email should be concise (around 250-300 words).
        Do not use generic phrases like "I hope this email finds you well" or "I am writing to inquire about".
        Make it sound human and personalized, not like a mass email.
        """
        
        return prompt
    
    def _create_template_email(self, conference: Conference, contact: Contact) -> str:
        """
        Create a template-based email as a fallback.
        
        Args:
            conference: Conference object
            contact: Contact object
        
        Returns:
            Email text
        """
        conference_date = conference.start_date.strftime("%B %Y")
        
        email = f"""
Subject: Speaking Opportunity at {conference.title}

Dear {contact.name},

I noticed that you're organizing {conference.title} in {conference.location} this {conference_date}, and I'm reaching out to explore the possibility of contributing as a speaker.

At {self.company_name}, we specialize in {self.company_description} I believe our expertise would be valuable to your audience, particularly on topics related to the latest advancements in AI technology and its practical applications.

{self.speaker_name}, our {self.speaker_title}, has extensive experience presenting at similar events and consistently receives positive feedback for delivering engaging, informative sessions that balance technical insights with practical takeaways.

Would you be open to a brief call next week to discuss potential speaking opportunities or other ways we might contribute to your event? I'd be happy to share more details about our proposed topics and presentation format.

Thank you for considering this request. I look forward to the possibility of collaborating with you on making {conference.title} a success.

Best regards,

{self.speaker_name}
{self.speaker_title}
{self.company_name}
        """
        
        return email.strip()

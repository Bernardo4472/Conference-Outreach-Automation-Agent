"""
Tests for the data models.
"""

import unittest
from datetime import datetime

from src.utils.models import Conference, Contact


class TestContact(unittest.TestCase):
    """Tests for the Contact model."""
    
    def test_contact_creation(self):
        """Test creating a Contact object."""
        contact = Contact(
            name="John Doe",
            role="Event Manager",
            email="john.doe@example.com",
            phone="+1234567890",
            linkedin="https://linkedin.com/in/johndoe"
        )
        
        self.assertEqual(contact.name, "John Doe")
        self.assertEqual(contact.role, "Event Manager")
        self.assertEqual(contact.email, "john.doe@example.com")
        self.assertEqual(contact.phone, "+1234567890")
        self.assertEqual(contact.linkedin, "https://linkedin.com/in/johndoe")
    
    def test_contact_string_representation(self):
        """Test the string representation of a Contact object."""
        contact = Contact(
            name="John Doe",
            role="Event Manager",
            email="john.doe@example.com"
        )
        
        self.assertEqual(str(contact), "John Doe (Event Manager) - john.doe@example.com")
    
    def test_contact_with_missing_role(self):
        """Test creating a Contact object with a missing role."""
        contact = Contact(
            name="John Doe",
            email="john.doe@example.com"
        )
        
        self.assertEqual(str(contact), "John Doe (Unknown role) - john.doe@example.com")


class TestConference(unittest.TestCase):
    """Tests for the Conference model."""
    
    def test_conference_creation(self):
        """Test creating a Conference object."""
        conference = Conference(
            title="AI Tech Summit 2025",
            start_date=datetime(2025, 5, 15),
            end_date=datetime(2025, 5, 17),
            location="Berlin, Germany",
            website_url="https://aitechsummit.com",
            description="A conference about AI technology."
        )
        
        self.assertEqual(conference.title, "AI Tech Summit 2025")
        self.assertEqual(conference.start_date, datetime(2025, 5, 15))
        self.assertEqual(conference.end_date, datetime(2025, 5, 17))
        self.assertEqual(conference.location, "Berlin, Germany")
        self.assertEqual(str(conference.website_url), "https://aitechsummit.com")
        self.assertEqual(conference.description, "A conference about AI technology.")
        self.assertEqual(conference.contacts, [])
        self.assertIsNone(conference.outreach_email)
    
    def test_conference_string_representation(self):
        """Test the string representation of a Conference object."""
        conference = Conference(
            title="AI Tech Summit 2025",
            start_date=datetime(2025, 5, 15),
            end_date=datetime(2025, 5, 17),
            location="Berlin, Germany",
            website_url="https://aitechsummit.com"
        )
        
        self.assertEqual(str(conference), "AI Tech Summit 2025 (2025-05-15 to 2025-05-17) - Berlin, Germany")
    
    def test_conference_string_representation_without_end_date(self):
        """Test the string representation of a Conference object without an end date."""
        conference = Conference(
            title="AI Tech Summit 2025",
            start_date=datetime(2025, 5, 15),
            location="Berlin, Germany",
            website_url="https://aitechsummit.com"
        )
        
        self.assertEqual(str(conference), "AI Tech Summit 2025 (2025-05-15) - Berlin, Germany")
    
    def test_conference_has_contacts(self):
        """Test the has_contacts method."""
        conference = Conference(
            title="AI Tech Summit 2025",
            start_date=datetime(2025, 5, 15),
            location="Berlin, Germany",
            website_url="https://aitechsummit.com"
        )
        
        self.assertFalse(conference.has_contacts())
        
        contact = Contact(
            name="John Doe",
            email="john.doe@example.com"
        )
        
        conference.contacts.append(contact)
        
        self.assertTrue(conference.has_contacts())
    
    def test_conference_has_outreach_email(self):
        """Test the has_outreach_email method."""
        conference = Conference(
            title="AI Tech Summit 2025",
            start_date=datetime(2025, 5, 15),
            location="Berlin, Germany",
            website_url="https://aitechsummit.com"
        )
        
        self.assertFalse(conference.has_outreach_email())
        
        conference.outreach_email = "Dear John, ..."
        
        self.assertTrue(conference.has_outreach_email())


if __name__ == "__main__":
    unittest.main()

"""
Data models for the Conference Outreach Automation Agent.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Contact(BaseModel):
    """Contact information for a conference organizer."""
    
    name: str
    role: Optional[str] = None
    email: str
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of a contact."""
        return f"{self.name} ({self.role or 'Unknown role'}) - {self.email}"


class Conference(BaseModel):
    """Conference information."""
    
    title: str
    start_date: datetime
    end_date: Optional[datetime] = None
    location: str
    website_url: HttpUrl
    description: Optional[str] = None
    contacts: List[Contact] = Field(default_factory=list)
    outreach_email: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of a conference."""
        date_str = self.start_date.strftime("%Y-%m-%d")
        if self.end_date:
            date_str += f" to {self.end_date.strftime('%Y-%m-%d')}"
        
        return f"{self.title} ({date_str}) - {self.location}"
    
    def has_contacts(self) -> bool:
        """Check if the conference has any contacts."""
        return len(self.contacts) > 0
    
    def has_outreach_email(self) -> bool:
        """Check if the conference has an outreach email."""
        return self.outreach_email is not None

# app/schemas/weekly_newsletter.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class WeeklyNewsletterBase(BaseModel):
    """Base schema for weekly newsletter"""
    title: str
    key_highlight: str
    content: str
    weeklynewsletter_topic_id: int

class WeeklyNewsletterCreate(WeeklyNewsletterBase):
    """Schema for creating a newsletter"""
    pass

class WeeklyNewsletterUpdate(BaseModel):
    """Schema for updating a newsletter"""
    title: Optional[str] = None
    key_highlight: Optional[str] = None
    content: Optional[str] = None
    weeklynewsletter_topic_id: Optional[int] = None

class WeeklyNewsletter(WeeklyNewsletterBase):
    """Schema for retrieving a newsletter"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
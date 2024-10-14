#/app/schemas/newsletter.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .topic import Topic

class NewsletterBase(BaseModel):
    title: str
    content: str
    topic_id: int
    subscription_ids: Optional[str] = None
    email_content: Optional[str] = None

class NewsletterCreate(NewsletterBase):
    pass

class NewsletterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    topic_id: Optional[int] = None
    subscription_ids: Optional[str] = None
    email_content: Optional[str] = None

class Newsletter(NewsletterBase):
    id: int
    created_at: datetime
    topic: Topic

    class Config:
        from_attributes = True
# app/schemas/newsletter.py
from pydantic import BaseModel
from datetime import datetime
from .topic import Topic

class NewsletterBase(BaseModel):
    title: str
    content: str
    topic_id: int

class NewsletterCreate(NewsletterBase):
    pass

class Newsletter(NewsletterBase):
    id: int
    created_at: datetime
    topic: Topic

    class Config:
        from_attributes = True
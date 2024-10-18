from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class WeeklyNewsletterBase(BaseModel):
    title: str
    key_highlight: str
    content: str
    weeklynewsletter_topic_id: int

class WeeklyNewsletterCreate(WeeklyNewsletterBase):
    pass

class WeeklyNewsletterUpdate(BaseModel):
    title: Optional[str] = None
    key_highlight: Optional[str] = None
    content: Optional[str] = None
    weeklynewsletter_topic_id: Optional[int] = None

class WeeklyNewsletter(WeeklyNewsletterBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
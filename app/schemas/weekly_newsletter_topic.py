from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class WeeklyNewsletterTopicBase(BaseModel):
    name: str
    is_active: str = 'Y'

class WeeklyNewsletterTopicCreate(WeeklyNewsletterTopicBase):
    pass

class WeeklyNewsletterTopicUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class WeeklyNewsletterTopic(WeeklyNewsletterTopicBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
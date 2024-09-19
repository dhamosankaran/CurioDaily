# app/schemas/topic.py
from pydantic import BaseModel

class TopicBase(BaseModel):
    name: str
    is_active: str = 'Y'

class TopicCreate(TopicBase):
    pass

class Topic(TopicBase):
    id: int

    class Config:
        orm_mode = True
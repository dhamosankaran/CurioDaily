# app/schemas/topic.py
from pydantic import BaseModel

class TopicBase(BaseModel):
    name: str

class TopicCreate(TopicBase):
    pass

class Topic(TopicBase):
    id: int

    class Config:
        from_attributes = True
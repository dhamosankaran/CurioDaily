# app/schemas/subscription.py
from pydantic import BaseModel, EmailStr
from typing import List
from .topic import Topic

class SubscriptionBase(BaseModel):
    email: EmailStr
    is_active: bool = True

class SubscriptionCreate(SubscriptionBase):
    topic_ids: List[int]

class Subscription(SubscriptionBase):
    id: int
    topics: List[Topic]

    class Config:
        from_attributes = True

class SubscriptionUpdate(BaseModel):
    is_active: bool

class SubscriptionInDB(Subscription):
    pass
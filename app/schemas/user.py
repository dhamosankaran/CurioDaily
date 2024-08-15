# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import List

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class NewsletterSubscription(BaseModel):
    email: EmailStr
    topics: List[str]
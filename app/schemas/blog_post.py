# app/schemas/blog_post.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class BlogPostBase(BaseModel):
    """Base schema for blog posts"""
    title: str
    content: str
    image_url: str
    social_summary: str
    original_idea: str

class BlogPostCreate(BlogPostBase):
    """Schema for creating blog posts"""
    pass

class BlogPostUpdate(BaseModel):
    """Schema for updating blog posts"""
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    social_summary: Optional[str] = None
    original_idea: Optional[str] = None

class BlogPostLikeBase(BaseModel):
    """Base schema for blog post likes"""
    post_id: int
    user_email: EmailStr

class BlogPostLikeCreate(BlogPostLikeBase):
    """Schema for creating blog post likes"""
    pass

class BlogPostLike(BlogPostLikeBase):
    """Schema for complete blog post like representation"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BlogPostLikeDetail(BaseModel):
    """Schema for detailed like information"""
    user_email: str
    created_at: datetime

    class Config:
        from_attributes = True

class BlogPost(BlogPostBase):
    """Schema for complete blog post representation"""
    id: int
    created_at: datetime
    view_count: int = 0
    like_count: int = 0
    recent_likes: Optional[List[BlogPostLikeDetail]] = []

    class Config:
        from_attributes = True
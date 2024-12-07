# app/models/blog_post.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class BlogPost(Base):
    """Model for blog posts"""
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    image_url = Column(String(512), nullable=False)
    social_summary = Column(String(280), nullable=False)
    original_idea = Column(Text, nullable=False)
    view_count = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )
    # Add relationship to likes
    likes = relationship("BlogPostLike", back_populates="post", cascade="all, delete-orphan")

class BlogPostLike(Base):
    """Model for blog post likes"""
    __tablename__ = "blog_post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    user_email = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship with blog post
    post = relationship("BlogPost", back_populates="likes")

    __table_args__ = (UniqueConstraint('post_id', 'user_email', name='blog_post_likes_unique'),)

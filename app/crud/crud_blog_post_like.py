# app/crud/crud_blog_post_like.py
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
from app.models.blog_post import BlogPostLike
from app.schemas.blog_post_like import BlogPostLikeCreate

logger = logging.getLogger(__name__)

def create_blog_post_like(
    db: Session,
    like: BlogPostLikeCreate
) -> Optional[BlogPostLike]:
    """Create a new blog post like"""
    try:
        # Check if like already exists
        existing_like = db.query(BlogPostLike).filter(
            BlogPostLike.post_id == like.post_id,
            BlogPostLike.user_email == like.user_email
        ).first()
        
        if existing_like:
            return None
            
        db_like = BlogPostLike(
            post_id=like.post_id,
            user_email=like.user_email
        )
        db.add(db_like)
        db.commit()
        db.refresh(db_like)
        return db_like
    except Exception as e:
        logger.error(f"Error creating blog post like: {str(e)}")
        db.rollback()
        return None

def get_blog_post_likes(
    db: Session,
    post_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[BlogPostLike]:
    """Get all likes for a blog post"""
    return db.query(BlogPostLike)\
             .filter(BlogPostLike.post_id == post_id)\
             .offset(skip)\
             .limit(limit)\
             .all()

def get_blog_post_like_count(db: Session, post_id: int) -> int:
    """Get the total number of likes for a blog post"""
    return db.query(BlogPostLike)\
             .filter(BlogPostLike.post_id == post_id)\
             .count()

def delete_blog_post_like(
    db: Session,
    post_id: int,
    user_email: str
) -> bool:
    """Delete a blog post like"""
    try:
        like = db.query(BlogPostLike).filter(
            BlogPostLike.post_id == post_id,
            BlogPostLike.user_email == user_email
        ).first()
        
        if like:
            db.delete(like)
            db.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting blog post like: {str(e)}")
        db.rollback()
        return False
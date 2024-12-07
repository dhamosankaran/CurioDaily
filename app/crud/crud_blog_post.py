# app/crud/crud_blog_post.py

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.blog_post import BlogPost, BlogPostLike
import logging

logger = logging.getLogger(__name__)

def get_blog_posts(db: Session, skip: int = 0, limit: int = 10) -> List[BlogPost]:
    """Get a list of blog posts with pagination and like counts"""
    posts = db.query(BlogPost)\
             .order_by(desc(BlogPost.created_at))\
             .offset(skip)\
             .limit(limit)\
             .all()
    
    # Add like count to each post
    for post in posts:
        post.like_count = db.query(BlogPostLike).filter(BlogPostLike.post_id == post.id).count()
    
    return posts

def get_blog_post(db: Session, blog_post_id: int):
    """Get a single blog post with like count and recent likes"""
    try:
        post = db.query(BlogPost).filter(BlogPost.id == blog_post_id).first()
        if post:
            # Get likes count
            post.like_count = get_post_likes_count(db, blog_post_id)
            
            # Get recent likes (e.g., last 5)
            recent_likes = db.query(BlogPostLike)\
                            .filter(BlogPostLike.post_id == blog_post_id)\
                            .order_by(BlogPostLike.created_at.desc())\
                            .limit(5)\
                            .all()
            
            post.recent_likes = [
                {
                    "user_email": like.user_email,
                    "created_at": like.created_at
                } for like in recent_likes
            ]
            
            # Increment view count
            post.view_count += 1
            db.commit()
            
        return post
    except Exception as e:
        logger.error(f"Error fetching blog post {blog_post_id}: {str(e)}")
        return None

def like_blog_post(db: Session, post_id: int, user_email: str) -> Optional[BlogPostLike]:
    """Add a like to a blog post"""
    try:
        # Check if user already liked the post
        existing_like = db.query(BlogPostLike).filter(
            BlogPostLike.post_id == post_id,
            BlogPostLike.user_email == user_email
        ).first()
        
        if existing_like:
            return None
        
        new_like = BlogPostLike(post_id=post_id, user_email=user_email)
        db.add(new_like)
        db.commit()
        db.refresh(new_like)
        return new_like
    except Exception as e:
        logger.error(f"Error liking blog post {post_id}: {str(e)}")
        db.rollback()
        return None

def unlike_blog_post(db: Session, post_id: int, user_email: str) -> bool:
    """Remove a like from a blog post"""
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
        logger.error(f"Error unliking blog post {post_id}: {str(e)}")
        db.rollback()
        return False

def get_post_like_status(db: Session, post_id: int, user_email: str) -> bool:
    """Check if a user has liked a post"""
    return db.query(BlogPostLike).filter(
        BlogPostLike.post_id == post_id,
        BlogPostLike.user_email == user_email
    ).first() is not None

def get_post_likes_count(db: Session, post_id: int) -> int:
    """
    Get the total number of likes for a specific blog post
    
    Args:
        db: Database session
        post_id: ID of the blog post
    
    Returns:
        int: Total number of likes for the post
    """
    try:
        return db.query(BlogPostLike).filter(BlogPostLike.post_id == post_id).count()
    except Exception as e:
        logger.error(f"Error getting likes count for post {post_id}: {str(e)}")
        raise

def get_post_likes_details(db: Session, post_id: int) -> List[dict]:
    """
    Get detailed information about likes for a specific blog post
    
    Args:
        db: Database session
        post_id: ID of the blog post
    
    Returns:
        List[dict]: List of like details including user email and timestamp
    """
    try:
        likes = db.query(BlogPostLike)\
                  .filter(BlogPostLike.post_id == post_id)\
                  .order_by(BlogPostLike.created_at.desc())\
                  .all()
        return [
            {
                "user_email": like.user_email,
                "created_at": like.created_at
            } for like in likes
        ]
    except Exception as e:
        logger.error(f"Error getting likes details for post {post_id}: {str(e)}")
        return []
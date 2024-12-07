# app/api/endpoints/blog_post_likes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.api import deps
from app.schemas.blog_post_like import BlogPostLikeCreate, BlogPostLike
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=BlogPostLike)
def create_blog_post_like(
    like: BlogPostLikeCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Toggle like on a blog post.
    """
    try:
        result = crud.create_like(db=db, like=like)
        if result:
            return result
        return {"status": "unliked"}
    except Exception as e:
        logger.error(f"Error creating like: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/post/{post_id}", response_model=List[schemas.BlogPostLike])
def read_post_likes(
    post_id: int,
    db: Session = Depends(deps.get_db)
):
    """Get all likes for a specific post"""
    try:
        likes = crud.get_likes_by_post(db=db, post_id=post_id)
        return likes
    except Exception as e:
        logger.error(f"Error fetching likes: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/post/{post_id}/count")
def read_post_like_count(
    post_id: int,
    db: Session = Depends(deps.get_db)
):
    """Get the number of likes for a post"""
    try:
        count = crud.get_like_count(db=db, post_id=post_id)
        return {"count": count}
    except Exception as e:
        logger.error(f"Error fetching like count: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/check/{post_id}/{user_email}")
def check_user_like(
    post_id: int,
    user_email: str,
    db: Session = Depends(deps.get_db)
):
    """Check if a user has liked a specific post"""
    try:
        like = crud.get_like_by_user_and_post(
            db=db, 
            post_id=post_id, 
            user_email=user_email
        )
        return {"has_liked": like is not None}
    except Exception as e:
        logger.error(f"Error checking like status: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
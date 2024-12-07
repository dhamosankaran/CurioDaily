# app/api/endpoints/blog_posts.py

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import crud, schemas
from app.api import deps
from app.core.config import settings
import markdown2
from app.crud import crud_blog_post as crud
from app.models.blog_post import BlogPostLike



logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/api/blog")
async def get_blog_posts_api(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(deps.get_db)
):
    skip = (page - 1) * limit
    posts = crud.get_blog_posts(db, skip=skip, limit=limit)
    return {
        "posts": posts,
        "page": page,
        "limit": limit
    }


@router.get("/", response_class=HTMLResponse)
async def render_blog_index(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(deps.get_db)
):
    skip = (page - 1) * limit
    posts = crud.get_blog_posts(db, skip=skip, limit=limit)
    
    return templates.TemplateResponse(
        "blogindex.html",
        {
            "request": request,
            "base_url": settings.BASE_URL,
            "posts": posts
        }
    )

def process_content(content: str) -> str:
    # Convert markdown to HTML with extras
    html_content = markdown2.markdown(content, extras=[
        'fenced-code-blocks',
        'header-ids',
        'tables',
        'break-on-newline',
        'cuddled-lists'
    ])
    return html_content

@router.get("/{post_id}", response_class=HTMLResponse)
async def read_blog_post(
    request: Request,
    post_id: int,
    db: Session = Depends(deps.get_db)
):
    try:
        post = crud.get_blog_post(db=db, blog_post_id=post_id)
        if post:
            # Process the content before sending to template
            post.content = process_content(post.content)
        
        return templates.TemplateResponse(
            "blog_post.html",
            {
                "request": request,
                "base_url": settings.BASE_URL,
                "post": post
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving blog post {post_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{post_id}/like")
async def like_post(
    post_id: int = Path(..., title="The ID of the post to like"),
    user_email: str = Query(..., title="Email of the user liking the post"),
    db: Session = Depends(deps.get_db)
):
    """Add a like to a blog post"""
    like = crud.like_blog_post(db=db, post_id=post_id, user_email=user_email)
    if like is None:
        raise HTTPException(status_code=400, detail="Post already liked or not found")
    return {"status": "success", "message": "Post liked successfully"}

@router.delete("/{post_id}/like")
async def unlike_post(
    post_id: int = Path(..., title="The ID of the post to unlike"),
    user_email: str = Query(..., title="Email of the user unliking the post"),
    db: Session = Depends(deps.get_db)
):
    """Remove a like from a blog post"""
    success = crud.unlike_blog_post(db=db, post_id=post_id, user_email=user_email)
    if not success:
        raise HTTPException(status_code=404, detail="Like not found")
    return {"status": "success", "message": "Post unliked successfully"}

@router.get("/{post_id}/like-status")
async def get_like_status(
    post_id: int = Path(..., title="The ID of the post to check"),
    user_email: str = Query(..., title="Email of the user"),
    db: Session = Depends(deps.get_db)
):
    """Check if a user has liked a post"""
    is_liked = crud.get_post_like_status(db=db, post_id=post_id, user_email=user_email)
    return {"is_liked": is_liked}


@router.get("/{post_id}/likes/count")
async def get_post_likes_count(
    post_id: int = Path(..., title="The ID of the post to get likes count"),
    db: Session = Depends(deps.get_db)
):
    """
    Get the total number of likes for a blog post
    """
    try:
        count = crud.get_post_likes_count(db=db, post_id=post_id)
        return {"post_id": post_id, "likes_count": count}
    except Exception as e:
        logger.error(f"Error getting likes count: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting likes count")

@router.get("/{post_id}/likes/details")
async def get_post_likes_details(
    post_id: int = Path(..., title="The ID of the post to get likes details"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(deps.get_db)
):
    """
    Get detailed information about likes for a blog post with pagination
    """
    try:
        # First verify if the post exists
        post = crud.get_blog_post(db=db, blog_post_id=post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Blog post not found")
            
        likes = db.query(BlogPostLike)\
                 .filter(BlogPostLike.post_id == post_id)\
                 .order_by(BlogPostLike.created_at.desc())\
                 .offset(skip)\
                 .limit(limit)\
                 .all()
                 
        total_likes = crud.get_post_likes_count(db=db, post_id=post_id)
        
        return {
            "post_id": post_id,
            "total_likes": total_likes,
            "likes": [
                {
                    "user_email": like.user_email,
                    "created_at": like.created_at.isoformat()
                } for like in likes
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total_likes
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting likes details: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting likes details")
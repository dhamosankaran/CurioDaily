# app/api/endpoints/weekly_newsletter.py

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
from app import crud, schemas
from app.api import deps
from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/personal-diary", response_class=HTMLResponse)
async def render_diary_index(
    topic_id: int = 1,
    db: Session = Depends(deps.get_db)
):
    """Render the complete diary index page for a specific topic"""
    try:
        latest_entry = crud.get_latest_weekly_newsletter(db, topic_id=topic_id)
        recent_entries = crud.get_recent_weekly_newsletters(
            db, 
            topic_id=topic_id, 
            limit=4
        )[1:4] if latest_entry else []

        env = Environment(
            loader=FileSystemLoader("app/templates"),
            autoescape=True
        )
        template = env.get_template("diaryindex.html")

        html_content = template.render(
            latest_entry=latest_entry,
            recent_entries=recent_entries,
            base_url=settings.BASE_URL,
            topic_id=topic_id
        )

        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error rendering diary index: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while rendering diary index"
        )

@router.get("/personal-diary/latest", response_model=schemas.WeeklyNewsletter)
async def get_latest_diary_entry(
    topic_id: int = 1,
    db: Session = Depends(deps.get_db)
):
    """Get the latest diary entry for a specific topic"""
    try:
        latest_entry = crud.get_latest_weekly_newsletter(db, topic_id=topic_id)
        if not latest_entry:
            raise HTTPException(
                status_code=404,
                detail="No diary entries available"
            )
        return latest_entry
    except Exception as e:
        logger.error(f"Error fetching latest diary entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/personal-diary/recent", response_model=List[schemas.WeeklyNewsletter])
async def get_recent_diary_entries(
    topic_id: int = 1,
    db: Session = Depends(deps.get_db)
):
    """Get recent diary entries for a specific topic"""
    try:
        entries = crud.get_recent_weekly_newsletters(db, topic_id=topic_id, limit=4)
        if not entries:
            return []
        return entries[1:4]  # Exclude the latest entry
    except Exception as e:
        logger.error(f"Error fetching recent diary entries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching recent entries"
        )

@router.get("/", response_model=List[schemas.WeeklyNewsletter])
def read_weekly_newsletters(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    newsletters = crud.get_weekly_newsletters(db, skip=skip, limit=limit)
    return newsletters
    
@router.post("/", response_model=schemas.WeeklyNewsletter)
def create_weekly_newsletter(newsletter: schemas.WeeklyNewsletterCreate, db: Session = Depends(deps.get_db)):
    return crud.create_weekly_newsletter(db=db, newsletter=newsletter)

@router.get("/{newsletter_id}", response_model=schemas.WeeklyNewsletter)
def read_weekly_newsletter(newsletter_id: int, db: Session = Depends(deps.get_db)):
    db_newsletter = crud.get_weekly_newsletter(db, newsletter_id=newsletter_id)
    if db_newsletter is None:
        raise HTTPException(status_code=404, detail="Weekly Newsletter not found")
    return db_newsletter

@router.put("/{newsletter_id}", response_model=schemas.WeeklyNewsletter)
def update_weekly_newsletter(newsletter_id: int, newsletter: schemas.WeeklyNewsletterUpdate, db: Session = Depends(deps.get_db)):
    db_newsletter = crud.update_weekly_newsletter(db, newsletter_id=newsletter_id, newsletter=newsletter)
    if db_newsletter is None:
        raise HTTPException(status_code=404, detail="Weekly Newsletter not found")
    return db_newsletter

@router.get("/topic/{topic_id}/render", response_class=HTMLResponse)
def render_weekly_newsletter_by_topic(
    topic_id: int,
    db: Session = Depends(deps.get_db)
):
    newsletters = crud.get_weekly_newsletters_by_topic(db, topic_id=topic_id, limit=1)
    if not newsletters:
        raise HTTPException(status_code=404, detail="No newsletters found for this topic")
    
    latest_newsletter = newsletters[0]
    return HTMLResponse(content=latest_newsletter.content, status_code=200)

@router.delete("/{newsletter_id}", response_model=bool)
def delete_weekly_newsletter(newsletter_id: int, db: Session = Depends(deps.get_db)):
    success = crud.delete_weekly_newsletter(db, newsletter_id=newsletter_id)
    if not success:
        raise HTTPException(status_code=404, detail="Weekly Newsletter not found")
    return success
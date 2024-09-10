# app/api/endpoints/newsletters.py

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.api import deps

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=schemas.Newsletter)
def create_newsletter(newsletter: schemas.NewsletterCreate, db: Session = Depends(deps.get_db)):
    logger.info(f"Creating new newsletter with title: {newsletter.title}")
    try:
        return crud.create_newsletter(db=db, newsletter=newsletter)
    except Exception as e:
        logger.error(f"Error creating newsletter: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/recent", response_model=List[schemas.Newsletter])
def read_recent_newsletters(
    days: int = Query(7, ge=1, le=30),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(deps.get_db)
):
    logger.info(f"Fetching recent newsletters for the last {days} days, skip: {skip}, limit: {limit}")
    try:
        newsletters = crud.get_recent_newsletters(db, days=days, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(newsletters)} newsletters")
        return newsletters
    except Exception as e:
        logger.error(f"Error fetching recent newsletters: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/topic/{topic_id}", response_model=List[schemas.Newsletter])
def read_newsletters_by_topic(
    topic_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(deps.get_db)
):
    logger.info(f"Fetching newsletters for topic_id: {topic_id}, skip: {skip}, limit: {limit}")
    try:
        newsletters = crud.get_newsletters_by_topic(db, topic_id=topic_id, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(newsletters)} newsletters for topic_id: {topic_id}")
        if not newsletters:
            raise HTTPException(status_code=404, detail="No newsletters found for this topic")
        return newsletters
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching newsletters for topic_id {topic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# New endpoint to get a specific newsletter by ID
@router.get("/{newsletter_id}", response_model=schemas.Newsletter)
def read_newsletter(newsletter_id: int, db: Session = Depends(deps.get_db)):
    logger.info(f"Fetching newsletter with id: {newsletter_id}")
    try:
        newsletter = crud.get_newsletter(db, newsletter_id=newsletter_id)
        if newsletter is None:
            logger.warning(f"Newsletter with id {newsletter_id} not found")
            raise HTTPException(status_code=404, detail="Newsletter not found")
        return newsletter
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching newsletter with id {newsletter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
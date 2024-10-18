from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.api import deps

router = APIRouter()


@router.get("/active", response_model=List[schemas.WeeklyNewsletterTopic])
def read_active_weekly_newsletter_topics(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    topics = crud.get_active_weekly_newsletter_topics(db, skip=skip, limit=limit)
    return topics

@router.post("/", response_model=schemas.WeeklyNewsletterTopic)
def create_weekly_newsletter_topic(topic: schemas.WeeklyNewsletterTopicCreate, db: Session = Depends(deps.get_db)):
    return crud.create_weekly_newsletter_topic(db=db, topic=topic)



@router.get("/{topic_id}", response_model=schemas.WeeklyNewsletterTopic)
def read_weekly_newsletter_topic(topic_id: int, db: Session = Depends(deps.get_db)):
    db_topic = crud.get_weekly_newsletter_topic(db, topic_id=topic_id)
    if db_topic is None:
        raise HTTPException(status_code=404, detail="Weekly Newsletter Topic not found")
    return db_topic

@router.get("/", response_model=List[schemas.WeeklyNewsletterTopic])
def read_weekly_newsletter_topics(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    topics = crud.get_weekly_newsletter_topics(db, skip=skip, limit=limit)
    return topics

@router.put("/{topic_id}", response_model=schemas.WeeklyNewsletterTopic)
def update_weekly_newsletter_topic(topic_id: int, topic: schemas.WeeklyNewsletterTopicUpdate, db: Session = Depends(deps.get_db)):
    db_topic = crud.update_weekly_newsletter_topic(db, topic_id=topic_id, topic=topic)
    if db_topic is None:
        raise HTTPException(status_code=404, detail="Weekly Newsletter Topic not found")
    return db_topic

@router.delete("/{topic_id}", response_model=bool)
def delete_weekly_newsletter_topic(topic_id: int, db: Session = Depends(deps.get_db)):
    success = crud.delete_weekly_newsletter_topic(db, topic_id=topic_id)
    if not success:
        raise HTTPException(status_code=404, detail="Weekly Newsletter Topic not found")
    return success
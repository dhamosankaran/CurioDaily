# app/api/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@router.post("/subscribe", response_model=schemas.User)
def subscribe_to_newsletter(subscription: schemas.NewsletterSubscription, db: Session = Depends(deps.get_db)):
    user = crud.get_user_by_email(db, email=subscription.email)
    if not user:
        user = crud.create_user(db, schemas.UserCreate(email=subscription.email, password="temporary"))
    
    # Convert topic names to IDs
    topic_ids = []
    for topic_name in subscription.topics:
        topic = crud.get_topic_by_name(db, name=topic_name)
        if not topic:
            topic = crud.create_topic(db, schemas.TopicCreate(name=topic_name))
        topic_ids.append(topic.id)
    
    return crud.subscribe_user_to_topics(db=db, user_id=user.id, topic_ids=topic_ids)

@router.get("/me/topics", response_model=List[schemas.Topic])
def read_user_topics(current_user: models.User = Depends(deps.get_current_user), db: Session = Depends(deps.get_db)):
    return current_user.topics
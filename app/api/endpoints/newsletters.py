# app/api/endpoints/newsletters.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.api import deps

router = APIRouter()

@router.post("/", response_model=schemas.Newsletter)
def create_newsletter(newsletter: schemas.NewsletterCreate, db: Session = Depends(deps.get_db)):
    return crud.create_newsletter(db=db, newsletter=newsletter)

@router.get("/recent", response_model=List[schemas.Newsletter])
def read_recent_newsletters(days: int = 7, skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    newsletters = crud.get_recent_newsletters(db, days=days, skip=skip, limit=limit)
    return newsletters

@router.get("/topic/{topic_id}", response_model=List[schemas.Newsletter])
def read_newsletters_by_topic(topic_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    newsletters = crud.get_newsletters_by_topic(db, topic_id=topic_id, skip=skip, limit=limit)
    return newsletters
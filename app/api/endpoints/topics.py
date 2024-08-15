# app/api/endpoints/topics.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.api import deps

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=schemas.Topic)
def create_topic(topic: schemas.TopicCreate, db: Session = Depends(deps.get_db)):
    logger.info(f"Received request to create topic: {topic.name}")
    return crud.create_topic(db=db, topic=topic)

@router.get("/", response_model=List[schemas.Topic])
def read_topics(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    logger.info(f"Fetching topics with skip={skip} and limit={limit}")
    topics = crud.get_topics(db, skip=skip, limit=limit)
    return topics

@router.get("/{topic_id}", response_model=schemas.Topic)
def read_topic(topic_id: int, db: Session = Depends(deps.get_db)):
    logger.info(f"Fetching topic with ID: {topic_id}")
    db_topic = crud.get_topic(db, topic_id=topic_id)
    if db_topic is None:
        logger.warning(f"Topic with ID {topic_id} not found")
        raise HTTPException(status_code=404, detail="Topic not found")
    return db_topic


@router.get("/list/all", response_model=List[schemas.Topic])
def list_all_topics(db: Session = Depends(deps.get_db)):
    logger.info("Received request to list all topics")
    topics = crud.list_all_topics(db)
    if not topics:
        logger.warning("No topics found")
        return []
    logger.info(f"Returning {len(topics)} topics")
    return topics
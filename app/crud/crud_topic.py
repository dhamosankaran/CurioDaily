# app/crud/crud_topic.py

import logging
from sqlalchemy.orm import Session
from app import models, schemas

logger = logging.getLogger(__name__)

def create_topic(db: Session, topic: schemas.TopicCreate):
    logger.info(f"Creating new topic: {topic.name}")
    db_topic = models.Topic(name=topic.name, is_active=topic.is_active)
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    logger.info(f"Topic created successfully. ID: {db_topic.id}")
    return db_topic

def get_topics(db: Session, skip: int = 0, limit: int = 100):
    logger.info(f"Fetching active topics with skip={skip} and limit={limit}")
    topics = db.query(models.Topic).filter(models.Topic.is_active == 'Y').offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(topics)} active topics")
    return topics

def get_topic(db: Session, topic_id: int):
    logger.info(f"Fetching active topic with ID: {topic_id}")
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id, models.Topic.is_active == 'Y').first()
    if topic:
        logger.info(f"Active topic found: {topic.name}")
    else:
        logger.warning(f"Active topic with ID {topic_id} not found")
    return topic

def list_all_topics(db: Session):
    logger.info("Listing all active topics")
    topics = db.query(models.Topic).filter(models.Topic.is_active == 'Y').all()
    for topic in topics:
        logger.info(f"Topic ID: {topic.id}, Name: {topic.name}")
    return topics

def seed_initial_topics(db: Session):
    logger.info("Checking if initial topics need to be seeded")
    if db.query(models.Topic).count() == 0:
        logger.info("No topics found. Seeding initial topics.")
        initial_topics = ["AI", "Tech", "Business", "Science"]
        for topic_name in initial_topics:
            db_topic = models.Topic(name=topic_name, is_active='Y')
            db.add(db_topic)
        db.commit()
        logger.info(f"Seeded {len(initial_topics)} initial topics")
    else:
        logger.info("Topics already exist. No need to seed.")
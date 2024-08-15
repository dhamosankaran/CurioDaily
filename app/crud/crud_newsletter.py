# app/crud/crud_newsletter.py
from sqlalchemy.orm import Session
from app import models, schemas
from datetime import datetime, timedelta

def create_newsletter(db: Session, newsletter: schemas.NewsletterCreate):
    db_newsletter = models.Newsletter(**newsletter.dict())
    db.add(db_newsletter)
    db.commit()
    db.refresh(db_newsletter)
    return db_newsletter

def get_recent_newsletters(db: Session, days: int = 7, skip: int = 0, limit: int = 100):
    recent_date = datetime.utcnow() - timedelta(days=days)
    return db.query(models.Newsletter).filter(models.Newsletter.created_at >= recent_date).offset(skip).limit(limit).all()

def get_newsletters_by_topic(db: Session, topic_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Newsletter).filter(models.Newsletter.topic_id == topic_id).offset(skip).limit(limit).all()

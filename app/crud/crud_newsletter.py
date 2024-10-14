#app/crud/crud_newsletter.py
from sqlalchemy.orm import Session
from app import models, schemas
from datetime import datetime, timedelta
from typing import List, Optional

def create_newsletter(db: Session, newsletter: schemas.NewsletterCreate) -> models.Newsletter:
    db_newsletter = models.Newsletter(**newsletter.dict())
    db.add(db_newsletter)
    db.commit()
    db.refresh(db_newsletter)
    return db_newsletter

def get_newsletter(db: Session, newsletter_id: int) -> Optional[models.Newsletter]:
    return db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()

def get_recent_newsletters(db: Session, days: int = 7, skip: int = 0, limit: int = 100) -> List[models.Newsletter]:
    recent_date = datetime.utcnow() - timedelta(days=days)
    return db.query(models.Newsletter)\
             .filter(models.Newsletter.created_at >= recent_date)\
             .order_by(models.Newsletter.created_at.desc())\
             .offset(skip)\
             .limit(limit)\
             .all()

def get_newsletters_by_topic(db: Session, topic_id: int, skip: int = 0, limit: int = 100) -> List[models.Newsletter]:
    return db.query(models.Newsletter)\
             .filter(models.Newsletter.topic_id == topic_id)\
             .order_by(models.Newsletter.created_at.desc())\
             .offset(skip)\
             .limit(limit)\
             .all()

def update_newsletter(db: Session, newsletter_id: int, newsletter_update: schemas.NewsletterUpdate) -> Optional[models.Newsletter]:
    db_newsletter = get_newsletter(db, newsletter_id)
    if db_newsletter:
        update_data = newsletter_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_newsletter, key, value)
        db.commit()
        db.refresh(db_newsletter)
    return db_newsletter

def delete_newsletter(db: Session, newsletter_id: int) -> bool:
    db_newsletter = get_newsletter(db, newsletter_id)
    if db_newsletter:
        db.delete(db_newsletter)
        db.commit()
        return True
    return False
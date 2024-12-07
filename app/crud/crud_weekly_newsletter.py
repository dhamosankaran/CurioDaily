# app/crud/crud_weekly_newsletter.py

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import WeeklyNewsletter
from app.schemas.weekly_newsletter import WeeklyNewsletterCreate, WeeklyNewsletterUpdate

def create_weekly_newsletter(db: Session, newsletter: WeeklyNewsletterCreate) -> WeeklyNewsletter:
    """Create a new weekly newsletter entry"""
    db_newsletter = WeeklyNewsletter(**newsletter.dict())
    db.add(db_newsletter)
    db.commit()
    db.refresh(db_newsletter)
    return db_newsletter

def get_weekly_newsletter(db: Session, newsletter_id: int) -> Optional[WeeklyNewsletter]:
    """Get a specific newsletter by ID"""
    return db.query(WeeklyNewsletter).filter(WeeklyNewsletter.id == newsletter_id).first()

def get_weekly_newsletters(db: Session, skip: int = 0, limit: int = 100) -> List[WeeklyNewsletter]:
    """Get a list of newsletters with pagination"""
    return db.query(WeeklyNewsletter)\
             .order_by(desc(WeeklyNewsletter.created_at))\
             .offset(skip)\
             .limit(limit)\
             .all()

def get_weekly_newsletters_by_topic(
    db: Session, 
    topic_id: int, 
    skip: int = 0, 
    limit: int = 10
) -> List[WeeklyNewsletter]:
    """Get newsletters filtered by topic_id"""
    return db.query(WeeklyNewsletter)\
             .filter(WeeklyNewsletter.weeklynewsletter_topic_id == topic_id)\
             .order_by(desc(WeeklyNewsletter.created_at))\
             .offset(skip)\
             .limit(limit)\
             .all()

def get_latest_weekly_newsletter(db: Session, topic_id: int = 1) -> Optional[WeeklyNewsletter]:
    """
    Retrieve the latest weekly newsletter for a specific topic.
    
    Args:
        db (Session): Database session
        topic_id (int): Topic ID to filter by, defaults to 1
        
    Returns:
        Optional[WeeklyNewsletter]: Latest newsletter entry or None if no entries exist
    """
    return db.query(WeeklyNewsletter)\
             .filter(WeeklyNewsletter.weeklynewsletter_topic_id == topic_id)\
             .order_by(desc(WeeklyNewsletter.created_at))\
             .first()

def get_recent_weekly_newsletters(
    db: Session, 
    topic_id: int = 1,
    limit: int = 4
) -> List[WeeklyNewsletter]:
    """
    Retrieve recent weekly newsletters for a specific topic.
    
    Args:
        db (Session): Database session
        topic_id (int): Topic ID to filter by, defaults to 1
        limit (int): Maximum number of entries to retrieve
        
    Returns:
        List[WeeklyNewsletter]: List of recent newsletter entries
    """
    return db.query(WeeklyNewsletter)\
             .filter(WeeklyNewsletter.weeklynewsletter_topic_id == topic_id)\
             .order_by(desc(WeeklyNewsletter.created_at))\
             .limit(limit)\
             .all()

def update_weekly_newsletter(
    db: Session, 
    newsletter_id: int, 
    newsletter: WeeklyNewsletterUpdate
) -> Optional[WeeklyNewsletter]:
    """Update an existing newsletter"""
    db_newsletter = get_weekly_newsletter(db, newsletter_id)
    if db_newsletter:
        update_data = newsletter.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_newsletter, key, value)
        db.commit()
        db.refresh(db_newsletter)
    return db_newsletter

def delete_weekly_newsletter(db: Session, newsletter_id: int) -> bool:
    """Delete a newsletter"""
    db_newsletter = get_weekly_newsletter(db, newsletter_id)
    if db_newsletter:
        db.delete(db_newsletter)
        db.commit()
        return True
    return False
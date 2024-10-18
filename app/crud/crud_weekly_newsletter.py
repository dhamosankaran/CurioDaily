from sqlalchemy.orm import Session
from app.models.weekly_newsletter import WeeklyNewsletter
from app.schemas.weekly_newsletter import WeeklyNewsletterCreate, WeeklyNewsletterUpdate

def create_weekly_newsletter(db: Session, newsletter: WeeklyNewsletterCreate):
    db_newsletter = WeeklyNewsletter(**newsletter.dict())
    db.add(db_newsletter)
    db.commit()
    db.refresh(db_newsletter)
    return db_newsletter

def get_weekly_newsletter(db: Session, newsletter_id: int):
    return db.query(WeeklyNewsletter).filter(WeeklyNewsletter.id == newsletter_id).first()

def get_weekly_newsletters_by_topic(db: Session, topic_id: int, skip: int = 0, limit: int = 10):
    return db.query(WeeklyNewsletter).filter(
        WeeklyNewsletter.weeklynewsletter_topic_id == topic_id
    ).order_by(WeeklyNewsletter.created_at.desc()).offset(skip).limit(limit).all()

def get_weekly_newsletter(db: Session, skip: int = 0, limit: int = 100):
    return db.query(WeeklyNewsletter).offset(skip).limit(limit).all()

def get_weekly_newsletters(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.WeeklyNewsletter).offset(skip).limit(limit).all()

def update_weekly_newsletter(db: Session, newsletter_id: int, newsletter: WeeklyNewsletterUpdate):
    db_newsletter = get_weekly_newsletter(db, newsletter_id)
    if db_newsletter:
        update_data = newsletter.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_newsletter, key, value)
        db.commit()
        db.refresh(db_newsletter)
    return db_newsletter

def delete_weekly_newsletter(db: Session, newsletter_id: int):
    db_newsletter = get_weekly_newsletter(db, newsletter_id)
    if db_newsletter:
        db.delete(db_newsletter)
        db.commit()
        return True
    return False
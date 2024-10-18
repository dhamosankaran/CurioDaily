from sqlalchemy.orm import Session
from app.models.weekly_newsletter_topic import WeeklyNewsletterTopic
from app.schemas.weekly_newsletter_topic import WeeklyNewsletterTopicCreate, WeeklyNewsletterTopicUpdate

def create_weekly_newsletter_topic(db: Session, topic: WeeklyNewsletterTopicCreate):
    db_topic = WeeklyNewsletterTopic(**topic.dict())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

def get_active_weekly_newsletter_topics(db: Session, skip: int = 0, limit: int = 100):
    return db.query(WeeklyNewsletterTopic).filter(WeeklyNewsletterTopic.is_active == 'Y').offset(skip).limit(limit).all()

def get_weekly_newsletter_topic(db: Session, topic_id: int):
    return db.query(WeeklyNewsletterTopic).filter(WeeklyNewsletterTopic.id == topic_id).first()

def get_weekly_newsletter_topics(db: Session, skip: int = 0, limit: int = 100):
    return db.query(WeeklyNewsletterTopic).offset(skip).limit(limit).all()

def update_weekly_newsletter_topic(db: Session, topic_id: int, topic: WeeklyNewsletterTopicUpdate):
    db_topic = get_weekly_newsletter_topic(db, topic_id)
    if db_topic:
        update_data = topic.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_topic, key, value)
        db.commit()
        db.refresh(db_topic)
    return db_topic

def delete_weekly_newsletter_topic(db: Session, topic_id: int):
    db_topic = get_weekly_newsletter_topic(db, topic_id)
    if db_topic:
        db.delete(db_topic)
        db.commit()
        return True
    return False
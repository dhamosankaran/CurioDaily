# app/crud/crud_subscription.py

import logging
from sqlalchemy.orm import Session
from app import models, schemas

logger = logging.getLogger(__name__)

def create_subscription(db: Session, subscription: schemas.SubscriptionCreate):
    logger.info(f"Creating new subscription for email: {subscription.email}")
    
    db_subscription = models.Subscription(email=subscription.email, is_active=subscription.is_active)
    logger.debug(f"Subscription object created: {db_subscription}")

    associated_topics = []
    for topic_id in subscription.topic_ids:
        logger.debug(f"Attempting to associate topic ID: {topic_id}")
        topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        if topic:
            db_subscription.topics.append(topic)
            associated_topics.append(topic_id)
            logger.info(f"Topic ID {topic_id} associated with subscription")
        else:
            logger.warning(f"Topic ID {topic_id} not found in database. Skipping this topic.")

    if not associated_topics:
        logger.warning("No valid topics were associated with this subscription.")

    try:
        db.add(db_subscription)
        logger.debug("Subscription added to session")
        db.commit()
        logger.info("Database commit successful")
        db.refresh(db_subscription)
        logger.debug("Subscription refreshed from database")
    except Exception as e:
        logger.error(f"Error occurred while saving subscription: {str(e)}", exc_info=True)
        db.rollback()
        raise

    logger.info(f"Subscription created successfully. ID: {db_subscription.id}, Associated Topics: {associated_topics}")
    return db_subscription

def get_subscription_by_email(db: Session, email: str):
    logger.info(f"Attempting to retrieve subscription for email: {email}")
    subscription = db.query(models.Subscription).filter(models.Subscription.email == email).first()
    if subscription:
        logger.info(f"Subscription found for email: {email}")
    else:
        logger.info(f"No subscription found for email: {email}")
    return subscription

def update_subscription_status(db: Session, email: str, is_active: bool):
    logger.info(f"Updating subscription status for email: {email}")
    db_subscription = get_subscription_by_email(db, email)
    if db_subscription:
        db_subscription.is_active = is_active
        db.commit()
        db.refresh(db_subscription)
        logger.info(f"Subscription status updated for email: {email}. New status: {'Active' if is_active else 'Inactive'}")
        return db_subscription
    else:
        logger.warning(f"No subscription found for email: {email}. Status update failed.")
        return None


# Add this new function to crud/crud_subscription.py

def update_subscription_status(db: Session, subscription_id: int, is_active: bool):
    logger.info(f"Updating subscription status for ID: {subscription_id}")
    db_subscription = db.query(models.Subscription).filter(models.Subscription.id == subscription_id).first()
    if db_subscription:
        db_subscription.is_active = is_active
        db.commit()
        db.refresh(db_subscription)
        logger.info(f"Subscription status updated for ID: {subscription_id}. New status: {'Active' if is_active else 'Inactive'}")
        return db_subscription
    else:
        logger.warning(f"No subscription found for ID: {subscription_id}. Status update failed.")
        return None
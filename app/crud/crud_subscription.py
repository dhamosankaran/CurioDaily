# app/crud/crud_subscription.py

import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete as sa_delete  # Import delete function from SQLAlchemy
from app import models, schemas

logger = logging.getLogger(__name__)

def create_subscription(db: Session, subscription: schemas.SubscriptionCreate):
    logger.info(f"Creating or updating subscription for email: {subscription.email}")
    
    try:
        # Try to get existing subscription
        db_subscription = db.query(models.Subscription).filter(models.Subscription.email == subscription.email).first()
        
        if db_subscription:
            logger.info(f"Existing subscription found for email: {subscription.email}")
            db_subscription.is_active = True
            db_subscription.name = subscription.name
        else:
            logger.info(f"Creating new subscription for email: {subscription.email}")
            db_subscription = models.Subscription(name=subscription.name, email=subscription.email, is_active=True)
            db.add(db_subscription)
        
        db.flush()  # This will assign an ID to db_subscription if it's new
        
        logger.debug(f"Subscription object: {db_subscription}")

        # Clear existing topic associations
        db.query(models.subscription_topic).filter(models.subscription_topic.c.subscription_id == db_subscription.id).delete()

        # Add new topic associations
        for topic_id in subscription.topic_ids:
            db.execute(
                models.subscription_topic.insert().values(
                    subscription_id=db_subscription.id,
                    topic_id=topic_id
                )
            )

        db.commit()
        logger.info(f"Subscription created/updated successfully. ID: {db_subscription.id}")
        return db_subscription

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError occurred: {str(e)}")
        raise ValueError("Email already exists")
    except Exception as e:
        db.rollback()
        logger.error(f"Error occurred while saving subscription: {str(e)}", exc_info=True)
        raise


def get_subscription_by_email(db: Session, email: str):
    logger.info(f"Attempting to retrieve subscription for email: {email}")
    subscription = db.query(models.Subscription).filter(models.Subscription.email == email).first()
    if subscription:
        logger.info(f"Subscription found for email: {email}")
    else:
        logger.info(f"No subscription found for email: {email}")
    return subscription


def update_subscription_status(db: Session, subscription_id: int, is_active: bool):
    """
    Update the subscription status and remove associated topic relationships if deactivating.

    Args:
        db (Session): The database session.
        subscription_id (int): The ID of the subscription to update.
        is_active (bool): The new status of the subscription.

    Returns:
        models.Subscription: The updated subscription object, or None if not found.
    """
    logger.info(f"Updating subscription status for ID: {subscription_id}")
    try:
        db_subscription = db.query(models.Subscription).filter(models.Subscription.id == subscription_id).first()
        
        if db_subscription:
            db_subscription.is_active = is_active
            logger.info(f"Setting is_active to {is_active} for subscription ID: {subscription_id}")
            
            if not is_active:
                # Remove all associated topics from subscription_topic table when deactivating the subscription
                delete_stmt = sa_delete(models.subscription_topic).where(
                    models.subscription_topic.c.subscription_id == subscription_id
                )
                db.execute(delete_stmt)
                logger.info(f"Removed topic associations for subscription ID: {subscription_id}")
            
            db.commit()
            db.refresh(db_subscription)
            logger.info(f"Subscription status updated for ID: {subscription_id}. New status: {'Active' if is_active else 'Inactive'}")
            return db_subscription
        else:
            logger.warning(f"No subscription found for ID: {subscription_id}. Status update failed.")
            return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating subscription status for ID {subscription_id}: {str(e)}", exc_info=True)
        return None
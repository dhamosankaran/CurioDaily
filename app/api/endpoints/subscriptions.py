# app/api/endpoints/subscriptions.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.api import deps

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=schemas.Subscription)
def create_subscription(subscription: schemas.SubscriptionCreate, db: Session = Depends(deps.get_db)):
    logger.info(f"Received request to create subscription for email: {subscription.email}")
    db_subscription = crud.get_subscription_by_email(db, email=subscription.email)
    if db_subscription:
        logger.warning(f"Subscription already exists for email: {subscription.email}")
        raise HTTPException(status_code=400, detail="Email already subscribed")
    return crud.create_subscription(db=db, subscription=subscription)

@router.get("/{email}", response_model=schemas.Subscription)
def read_subscription(email: str, db: Session = Depends(deps.get_db)):
    logger.info(f"Fetching subscription for email: {email}")
    db_subscription = crud.get_subscription_by_email(db, email=email)
    if db_subscription is None:
        logger.warning(f"No subscription found for email: {email}")
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription
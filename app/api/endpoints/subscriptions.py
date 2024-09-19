# app/api/endpoints/subscriptions.py

import logging
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import crud, schemas
from app.api import deps
from fastapi import Path

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

@router.api_route("/{subscription_id}/unsubscribe", methods=["GET", "PUT"], response_model=schemas.Subscription)
def unsubscribe(subscription_id: int, request: Request, db: Session = Depends(deps.get_db)):
    db_subscription = crud.update_subscription_status(db, subscription_id=subscription_id, is_active=False)
    if db_subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # If it's a GET request, redirect to the main page with the success parameter
    if request.method == "GET":
        base_url = str(request.base_url)
        return RedirectResponse(url=f"{base_url}?unsubscribe=success")
    
    return db_subscription

  

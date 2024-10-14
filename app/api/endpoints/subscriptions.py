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
    logger.info(f"Received request to create or update subscription for email: {subscription.email}")
    try:
        return crud.create_subscription(db=db, subscription=subscription)
    except ValueError as e:
        logger.warning(f"Subscription creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during subscription creation: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/{email}", response_model=schemas.Subscription)
def read_subscription(email: str, db: Session = Depends(deps.get_db)):
    logger.info(f"Fetching subscription for email: {email}")
    db_subscription = crud.get_subscription_by_email(db, email=email)
    if db_subscription is None:
        logger.warning(f"No subscription found for email: {email}")
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription

@router.api_route("/{subscription_id}/unsubscribe", methods=["GET", "PUT"])
async def unsubscribe(
    request: Request,
    subscription_id: int = Path(...),
    db: Session = Depends(deps.get_db)
):
    """
    Unsubscribe a user by setting their subscription to inactive and removing topic associations.
    
    Args:
        request (Request): The incoming request object.
        subscription_id (int): The ID of the subscription to be updated.
        db (Session): The database session.
    
    Returns:
        A redirect response for GET requests or a JSON response for PUT requests.
    """
    logger.info(f"Unsubscribe request received for subscription ID: {subscription_id}")
    
    updated_subscription = crud.update_subscription_status(db, subscription_id=subscription_id, is_active=False)
    
    if not updated_subscription:
        logger.warning(f"Unsubscription failed for ID: {subscription_id}")
        raise HTTPException(status_code=404, detail="Subscription not found or unsubscription failed")
    
    if request.method == "GET":
        base_url = str(request.base_url)
        return RedirectResponse(url=f"{base_url}?unsubscribe=success")
    
    return {"message": "Successfully unsubscribed", "subscription": updated_subscription}
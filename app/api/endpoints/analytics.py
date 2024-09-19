# app/api/endpoints/analytics.py


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.analytics import PageViewCreate, EventCreate
from app.crud import crud_analytics
from app.api import deps

router = APIRouter()

@router.post("/track-pageview")
def track_pageview(pageview: PageViewCreate, db: Session = Depends(deps.get_db)):
    return crud_analytics.create_pageview(db, pageview)

@router.post("/track-event")
def track_event(event: EventCreate, db: Session = Depends(deps.get_db)):
    return crud_analytics.create_event(db, event)

# Add this new test endpoint
@router.get("/test")
def test_analytics():
    return {"message": "Analytics endpoint is working"}
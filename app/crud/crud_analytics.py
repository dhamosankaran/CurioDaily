from sqlalchemy.orm import Session
from app.models.analytics import PageView, Event
from app.schemas.analytics import PageViewCreate, EventCreate

def create_pageview(db: Session, pageview: PageViewCreate):
    db_pageview = PageView(**pageview.dict())
    db.add(db_pageview)
    db.commit()
    db.refresh(db_pageview)
    return db_pageview

def create_event(db: Session, event: EventCreate):
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


    
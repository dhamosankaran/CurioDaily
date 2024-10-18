from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app import crud, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.WeeklyNewsletter])
def read_weekly_newsletters(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    newsletters = crud.get_weekly_newsletters(db, skip=skip, limit=limit)
    return newsletters
    
    
@router.post("/", response_model=schemas.WeeklyNewsletter)
def create_weekly_newsletter(newsletter: schemas.WeeklyNewsletterCreate, db: Session = Depends(deps.get_db)):
    return crud.create_weekly_newsletter(db=db, newsletter=newsletter)

@router.get("/{weeklynewsletter_topic_id}", response_model=schemas.WeeklyNewsletter)
def read_weekly_newsletter(newsletter_id: int, db: Session = Depends(deps.get_db)):
    db_newsletter = crud.get_weekly_newsletter(db, newsletter_id=newsletter_id)
    if db_newsletter is None:
        raise HTTPException(status_code=404, detail="Weekly Newsletter not found")
    return db_newsletter

@router.get("/", response_model=List[schemas.WeeklyNewsletter])
def read_weekly_newsletter(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    newsletters = crud.get_weekly_newsletter(db, skip=skip, limit=limit)
    return newsletters

@router.put("/{newsletter_id}", response_model=schemas.WeeklyNewsletter)
def update_weekly_newsletter(newsletter_id: int, newsletter: schemas.WeeklyNewsletterUpdate, db: Session = Depends(deps.get_db)):
    db_newsletter = crud.update_weekly_newsletter(db, newsletter_id=newsletter_id, newsletter=newsletter)
    if db_newsletter is None:
        raise HTTPException(status_code=404, detail="Weekly Newsletter not found")
    return db_newsletter


@router.get("/topic/{topic_id}/render", response_class=HTMLResponse)
def render_weekly_newsletter_by_topic(
    topic_id: int,
    db: Session = Depends(deps.get_db)
):
    newsletters = crud.get_weekly_newsletters_by_topic(db, topic_id=topic_id, limit=1)
    if not newsletters:
        raise HTTPException(status_code=404, detail="No newsletters found for this topic")
    
    latest_newsletter = newsletters[0]
    return HTMLResponse(content=latest_newsletter.content, status_code=200)


@router.delete("/{newsletter_id}", response_model=bool)
def delete_weekly_newsletter(newsletter_id: int, db: Session = Depends(deps.get_db)):
    success = crud.delete_weekly_newsletter(db, newsletter_id=newsletter_id)
    if not success:
        raise HTTPException(status_code=404, detail="Weekly Newsletter not found")
    return success
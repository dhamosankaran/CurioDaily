from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import crud, schemas
from app.api import deps

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/{topic_name}")
async def get_weekly_update(request: Request, topic_name: str, db: Session = Depends(deps.get_db)):
    topic = crud.get_topic_by_name(db, topic_name)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    this_week_update = crud.get_latest_newsletter(db, topic.id)
    recent_updates = crud.get_recent_newsletters(db, topic.id, limit=3)
    
    return templates.TemplateResponse("weekly_update.html", {
        "request": request,
        "topic": topic,
        "this_week_update": this_week_update,
        "recent_updates": recent_updates
    })
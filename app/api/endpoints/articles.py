# app/api/endpoints/articles.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.api import deps

router = APIRouter()

@router.post("/", response_model=schemas.Article)
def create_article(article: schemas.ArticleCreate, db: Session = Depends(deps.get_db)):
    return crud.create_article(db=db, article=article)

@router.get("/", response_model=List[schemas.Article])
def read_articles(skip: int = 0, limit: int = 10, db: Session = Depends(deps.get_db)):
    return crud.get_articles(db, skip=skip, limit=limit)

@router.get("/topic/{topic_id}", response_model=List[schemas.Article])
def read_articles_by_topic(topic_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(deps.get_db)):
    return crud.get_articles_by_topic(db, topic_id=topic_id, skip=skip, limit=limit)
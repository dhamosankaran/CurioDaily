# app/crud/crud_article.py
from sqlalchemy.orm import Session
from app.models.article import Article
from app.schemas.article import ArticleCreate

def create_article(db: Session, article: ArticleCreate):
    db_article = Article(**article.dict())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

def get_article(db: Session, article_id: int):
    return db.query(Article).filter(Article.id == article_id).first()

def get_articles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Article).offset(skip).limit(limit).all()

def get_articles_by_topic(db: Session, topic_id: int, skip: int = 0, limit: int = 100):
    return db.query(Article).filter(Article.topic_id == topic_id).offset(skip).limit(limit).all()
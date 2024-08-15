# app/schemas/article.py
from pydantic import BaseModel
from datetime import datetime

class ArticleBase(BaseModel):
    title: str
    content: str
    topic_id: int

class ArticleCreate(ArticleBase):
    pass

class Article(ArticleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
# app/models/article.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    topic_id = Column(Integer, ForeignKey('topics.id'))
    topic = relationship("Topic", back_populates="articles")
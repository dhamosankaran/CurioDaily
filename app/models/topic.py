# app/models/topic.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    newsletters = relationship("Newsletter", back_populates="topic")
    subscriptions = relationship("Subscription", secondary="subscription_topic", back_populates="topics")
    subscribers = relationship("User", secondary="user_topic", back_populates="topics")
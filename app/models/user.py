# app/models/user.py
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

user_topic = Table('user_topic', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('topic_id', Integer, ForeignKey('topics.id'))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), onupdate=func.now())
    topics = relationship("Topic", secondary=user_topic, back_populates="subscribers")
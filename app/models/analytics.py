from sqlalchemy import Column, Integer, String, DateTime
from app.db.base_class import Base
from datetime import datetime

class PageView(Base):
    __tablename__ = "pageviews"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    title = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True)
    action = Column(String)
    label = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
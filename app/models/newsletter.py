# app/models/newsletter.py



from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Newsletter(Base):
    __tablename__ = "newsletters"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    topic_id = Column(Integer, ForeignKey("topics.id"))
    subscription_ids = Column(Text)
    email_content = Column(Text)
    
    topic = relationship("Topic", back_populates="newsletters")

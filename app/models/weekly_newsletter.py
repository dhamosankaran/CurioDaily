# app/models/weekly_newsletter.py

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class WeeklyNewsletter(Base):
    __tablename__ = "weekly_newsletter"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, index=True)
    key_highlight = Column(Text)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    weeklynewsletter_topic_id = Column(Integer, ForeignKey("weekly_newsletter_topics.id"))

    # Relationship
    topic = relationship("WeeklyNewsletterTopic", back_populates="newsletters")
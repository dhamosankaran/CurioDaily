from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class WeeklyNewsletter(Base):
    __tablename__ = "weekly_newsletter"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    key_highlight = Column(String)
    content = Column(String)
    created_at = Column(DateTime(timezone=True), server_default='now()')
    weeklynewsletter_topic_id = Column(Integer, ForeignKey("weekly_newsletter_topics.id"))

    topic = relationship("WeeklyNewsletterTopic", back_populates="newsletters")
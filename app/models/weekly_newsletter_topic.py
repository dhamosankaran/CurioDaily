from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class WeeklyNewsletterTopic(Base):
    __tablename__ = "weekly_newsletter_topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default='CURRENT_TIMESTAMP')
    updated_at = Column(DateTime(timezone=True), server_default='CURRENT_TIMESTAMP', onupdate='CURRENT_TIMESTAMP')
    is_active = Column(String(1), nullable=False, default='Y')
    

    __table_args__ = (
        CheckConstraint(is_active.in_(['Y', 'N']), name='weekly_newsletter_topics_is_active_check'),
    )

    newsletters = relationship("WeeklyNewsletter", back_populates="topic")
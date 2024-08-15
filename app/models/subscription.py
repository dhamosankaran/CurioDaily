# app/models/subscription.py
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

subscription_topic = Table('subscription_topic', Base.metadata,
    Column('subscription_id', Integer, ForeignKey('subscriptions.id')),
    Column('topic_id', Integer, ForeignKey('topics.id'))
)

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    topics = relationship("Topic", secondary=subscription_topic, back_populates="subscriptions")

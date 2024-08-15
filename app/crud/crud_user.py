# app/crud/crud_user.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def subscribe_user_to_topics(db: Session, user_id: int, topic_ids: list[int]):
    user = db.query(User).filter(User.id == user_id).first()
    topics = db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
    user.topics.extend(topics)
    db.commit()
    db.refresh(user)
    return user
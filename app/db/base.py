from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


from app.db.base_class import Base
from app.models.topic import Topic
from app.models.subscription import Subscription
from app.models.newsletter import Newsletter
from app.models.user import User


from app.core.config import settings

engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
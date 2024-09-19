from pydantic import BaseModel
from datetime import datetime

class PageViewBase(BaseModel):
    url: str
    title: str

class PageViewCreate(PageViewBase):
    pass

class PageView(PageViewBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class EventBase(BaseModel):
    category: str
    action: str
    label: str

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
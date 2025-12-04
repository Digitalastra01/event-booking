from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: datetime
    location: str
    capacity: int

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    title: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None
    capacity: Optional[int] = None

class EventInDBBase(EventBase):
    id: uuid.UUID
    organizer_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class Event(EventInDBBase):
    pass

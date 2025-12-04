from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid
from app.models.booking import BookingStatus

class BookingBase(BaseModel):
    event_id: uuid.UUID

class BookingCreate(BookingBase):
    tickets_count: int = 1
    user_name: Optional[str] = None
    user_email: Optional[EmailStr] = None

class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None
    tickets_count: Optional[int] = None
    guest_name: Optional[str] = None
    guest_email: Optional[EmailStr] = None

class BookingInDBBase(BookingBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: BookingStatus
    tickets_count: int
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class Booking(BookingInDBBase):
    pass

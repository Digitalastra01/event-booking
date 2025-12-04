from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingUpdate
import uuid

class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    async def create_with_user(
        self, db: AsyncSession, *, obj_in: BookingCreate, user_id: uuid.UUID
    ) -> Booking:
        obj_in_data = obj_in.model_dump()
        if "user_name" in obj_in_data:
            obj_in_data["guest_name"] = obj_in_data.pop("user_name")
        if "user_email" in obj_in_data:
            obj_in_data["guest_email"] = obj_in_data.pop("user_email")
        db_obj = Booking(**obj_in_data, user_id=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi_by_user(
        self, db: AsyncSession, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        result = await db.execute(
            select(Booking)
            .filter(Booking.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

booking = CRUDBooking(Booking)

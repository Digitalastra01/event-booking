from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate
import uuid

class CRUDEvent(CRUDBase[Event, EventCreate, EventUpdate]):
    async def create_with_organizer(
        self, db: AsyncSession, *, obj_in: EventCreate, organizer_id: uuid.UUID
    ) -> Event:
        obj_in_data = obj_in.model_dump()
        db_obj = Event(**obj_in_data, organizer_id=organizer_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi_by_organizer(
        self, db: AsyncSession, *, organizer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Event]:
        result = await db.execute(
            select(Event)
            .filter(Event.organizer_id == organizer_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def decrease_capacity(
        self, db: AsyncSession, *, event_id: uuid.UUID, tickets: int
    ) -> Event:
        event = await self.get(db, id=event_id)
        if not event:
            return None
        event.capacity -= tickets
        db.add(event)
        await db.commit()
        # await db.refresh(event) # Avoid refresh to prevent MissingGreenlet
        return event

event = CRUDEvent(Event)

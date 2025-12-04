from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Request

from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api import deps
from app.crud import event as crud_event
from app.schemas.event import Event, EventCreate, EventUpdate
from app.models.user import User
from app.utils.logger import get_logger
from app.core.ratelimit import limiter

router = APIRouter()

logger = get_logger(__name__)

@router.get("/all", response_model=List[Event])
@limiter.limit("10/minute")
async def read_all_events(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Retrieve all events without pagination.
    """
    logger.info("Fetching all events")
    events = await crud_event.get_all(db)
    logger.info("Fetched %d events", len(events))
    return events

@router.post("/", response_model=Event)
async def create_event(
    *,
    db: AsyncSession = Depends(deps.get_db),
    event_in: EventCreate,
    current_user: User = Depends(deps.get_current_active_organizer),
) -> Any:
    """
    Create new event.
    """
    logger.info("Organizer %s creating event '%s'", current_user.id, event_in.title)
    event = await crud_event.create_with_organizer(
        db=db, obj_in=event_in, organizer_id=current_user.id
    )
    logger.info("Event '%s' created with id %s", event.title, event.id)
    return event

@router.get("/{id}", response_model=Event)
async def read_event(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: uuid.UUID,
) -> Any:
    """
    Get event by ID.
    """
    event = await crud_event.get(db=db, id=id)
    if not event:
        logger.warning("Event %s not found", id)
        raise HTTPException(status_code=404, detail="Event not found")
    logger.info("Event %s retrieved", id)
    return event

@router.put("/{id}", response_model=Event)
async def update_event(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: uuid.UUID,
    event_in: EventUpdate,
    current_user: User = Depends(deps.get_current_active_organizer),
) -> Any:
    """
    Update an event.
    """
    logger.info("Organizer %s updating event %s", current_user.id, id)
    event = await crud_event.get(db=db, id=id)
    if not event:
        logger.warning("Event %s not found for update", id)
        raise HTTPException(status_code=404, detail="Event not found")
    if event.organizer_id != current_user.id:
        logger.warning(
            "Organizer %s lacks permission to update event %s",
            current_user.id,
            id,
        )
        raise HTTPException(status_code=403, detail="Not enough permissions")
    event = await crud_event.update(db=db, db_obj=event, obj_in=event_in)
    logger.info("Event %s updated", id)
    return event

@router.delete("/{id}", response_model=Event)
async def delete_event(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_organizer),
) -> Any:
    """
    Delete an event.
    """
    logger.info("Organizer %s deleting event %s", current_user.id, id)
    event = await crud_event.get(db=db, id=id)
    if not event:
        logger.warning("Event %s not found for deletion", id)
        raise HTTPException(status_code=404, detail="Event not found")
    if event.organizer_id != current_user.id:
        logger.warning(
            "Organizer %s lacks permission to delete event %s",
            current_user.id,
            id,
        )
        raise HTTPException(status_code=403, detail="Not enough permissions")
    event = await crud_event.remove(db=db, id=id)
    logger.info("Event %s deleted", id)
    return event

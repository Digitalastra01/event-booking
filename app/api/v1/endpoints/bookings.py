from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
import uuid

from app.api import deps
from app.crud import booking as crud_booking
from app.crud import event as crud_event
from app.schemas.booking import Booking, BookingCreate, BookingUpdate
from app.models.user import User, UserRole
from app.services.booking_notifications import queue_booking_confirmation
from app.utils.logger import get_logger

router = APIRouter()

logger = get_logger(__name__)

@router.get("/", response_model=List[Booking])
async def read_bookings(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve bookings for current user.
    """
    if current_user.role != UserRole.USER:
        logger.warning("User %s with role %s attempted to list bookings", current_user.id, current_user.role)
        raise HTTPException(status_code=403, detail="Only users can view their bookings")
    logger.info("Listing bookings for user %s", current_user.id)
    bookings = await crud_booking.get_multi_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    logger.info("Fetched %d bookings for user %s", len(bookings), current_user.id)
    return bookings

@router.post("/", response_model=Booking)
async def create_booking(
    *,
    db: AsyncSession = Depends(deps.get_db),
    booking_in: BookingCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new booking.
    """
    if current_user.role != UserRole.USER:
        logger.warning("User %s with role %s attempted to create booking", current_user.id, current_user.role)
        raise HTTPException(status_code=403, detail="Only users can book events")

    event = await crud_event.get(db=db, id=booking_in.event_id)
    if not event:
        logger.warning("Event %s not found for booking", booking_in.event_id)
        raise HTTPException(status_code=404, detail="Event not found")
    if event.capacity < booking_in.tickets_count:
        logger.warning(
            "Insufficient capacity for event %s: requested %d, available %d",
            booking_in.event_id,
            booking_in.tickets_count,
            event.capacity,
        )
        raise HTTPException(status_code=400, detail="Not enough tickets available")

    logger.info(
        "Creating booking for user %s on event %s with %d tickets",
        current_user.id,
        booking_in.event_id,
        booking_in.tickets_count,
    )
    # Extract data before commit (which expires objects)
    event_title = event.title
    event_date = event.date
    event_location = event.location
    event_description = event.description
    user_email = booking_in.user_email or current_user.email
    # Use provided user_name (guest name) or fallback to account name
    user_name = booking_in.user_name or current_user.name or 'User'
    tickets_count = booking_in.tickets_count

    booking = await crud_booking.create_with_user(
        db=db, obj_in=booking_in, user_id=current_user.id
    )
    logger.info("Booking %s created for user %s", booking.id, current_user.id)

    # Save data before commit (which expires objects)
    booking_id = booking.id
    booking_user_id = booking.user_id
    booking_event_id = booking.event_id
    booking_status = booking.status
    booking_tickets_count = booking.tickets_count
    booking_guest_name = booking.guest_name
    booking_guest_email = booking.guest_email
    booking_created_at = booking.created_at

    # Decrease event capacity
    await db.execute(
        update(crud_event.model)
        .where(crud_event.model.id == event.id)
        .values(capacity=crud_event.model.capacity - tickets_count)
    )
    await db.commit()

    # Send confirmation email via service
    queue_booking_confirmation(
        booking_id=booking_id,
        user_email=user_email,
        user_name=user_name,
        event_title=event_title,
        event_date=event_date,
        event_location=event_location,
        event_description=event_description,
        tickets_count=tickets_count,
    )

    return {
        "id": booking_id,
        "user_id": booking_user_id,
        "event_id": booking_event_id,
        "status": booking_status,
        "tickets_count": booking_tickets_count,
        "guest_name": booking_guest_name,
        "guest_email": booking_guest_email,
        "created_at": booking_created_at
    }

@router.put("/{id}", response_model=Booking)
async def update_booking(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: uuid.UUID,
    booking_in: BookingUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a booking.
    """
    if current_user.role != UserRole.USER:
        logger.warning("User %s with role %s attempted to update booking", current_user.id, current_user.role)
        raise HTTPException(status_code=403, detail="Only users can update bookings")
    booking = await crud_booking.get(db=db, id=id)
    if not booking:
        logger.warning("Booking %s not found for update", id)
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id:
        logger.warning(
            "User %s attempted to update booking %s owned by %s",
            current_user.id,
            id,
            booking.user_id,
        )
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_data = booking_in.model_dump(exclude_unset=True)

    if "tickets_count" in update_data:
        new_tickets_count = update_data["tickets_count"]
        if new_tickets_count is None or new_tickets_count <= 0:
            logger.warning("Invalid tickets count %s for booking %s", new_tickets_count, id)
            raise HTTPException(status_code=400, detail="Tickets count must be greater than zero")

        ticket_diff = new_tickets_count - booking.tickets_count
        if ticket_diff != 0:
            event = await crud_event.get(db=db, id=booking.event_id)
            if not event:
                logger.error("Event %s not found while updating booking %s", booking.event_id, id)
                raise HTTPException(status_code=500, detail="Related event not found")
            if ticket_diff > 0 and event.capacity < ticket_diff:
                logger.warning(
                    "Insufficient capacity for event %s: requested change %d, available %d",
                    booking.event_id,
                    ticket_diff,
                    event.capacity,
                )
                raise HTTPException(status_code=400, detail="Not enough tickets available")
            await db.execute(
                update(crud_event.model)
                .where(crud_event.model.id == booking.event_id)
                .values(capacity=crud_event.model.capacity - ticket_diff)
            )

    booking = await crud_booking.update(db=db, db_obj=booking, obj_in=booking_in)
    logger.info("Booking %s updated by user %s", id, current_user.id)
    return booking

@router.delete("/{id}", response_model=Booking)
async def cancel_booking(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Cancel a booking.
    """
    if current_user.role != UserRole.USER:
        logger.warning("User %s with role %s attempted to cancel booking", current_user.id, current_user.role)
        raise HTTPException(status_code=403, detail="Only users can cancel bookings")
    booking = await crud_booking.get(db=db, id=id)
    if not booking:
        logger.warning("Booking %s not found for cancellation", id)
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id:
        logger.warning(
            "User %s attempted to cancel booking %s owned by %s",
            current_user.id,
            id,
            booking.user_id,
        )
        raise HTTPException(status_code=403, detail="Not enough permissions")
    booking = await crud_booking.remove(db=db, id=id)
    logger.info("Booking %s cancelled by user %s", id, current_user.id)
    return booking

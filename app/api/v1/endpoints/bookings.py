from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
import uuid

from app.api import deps
from app.crud import booking as crud_booking
from app.crud import event as crud_event
from app.schemas.booking import Booking, BookingCreate, BookingUpdate
from app.models.user import User, UserRole
from app.models.booking import Booking as BookingModel
from app.core.email import send_email
from app.worker import send_email_task

router = APIRouter()

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
    bookings = await crud_booking.get_multi_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
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
        raise HTTPException(status_code=403, detail="Only users can book events")

    event = await crud_event.get(db=db, id=booking_in.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.capacity < booking_in.tickets_count:
        raise HTTPException(status_code=400, detail="Not enough tickets available")
    
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

    # Send confirmation email
    email_subject = f"Booking Confirmation: {event_title} (Updated)"
    email_content = f"""
    <html>
        <body>
            <h1>Booking Confirmation</h1>
            <p>Hi {user_name},</p>
            <p>You have successfully booked the event: <strong>{event_title}</strong>.</p>
            <p><strong>Email:</strong> {user_email}</p>
            <p><strong>Tickets:</strong> {tickets_count}</p>
            <p><strong>Date:</strong> {event_date}</p>
            <p><strong>Location:</strong> {event_location}</p>
            <p><strong>Description:</strong> {event_description}</p>
            <p>Thank you for using our service!</p>
        </body>
    </html>
    """
    # We run this in the background using Celery
    try:
        print(f"DEBUG EMAIL CONTENT:\n{email_content}")
        send_email_task.delay(
            email_to=[user_email],
            subject=email_subject,
            html_content=email_content
        )
        print(f"INFO: Email confirmation queued for {user_email} for event '{event_title}'")
    except Exception as e:
        print(f"Failed to queue email: {e}")

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
    booking = await crud_booking.get(db=db, id=id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    booking = await crud_booking.update(db=db, db_obj=booking, obj_in=booking_in)
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
    booking = await crud_booking.get(db=db, id=id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    booking = await crud_booking.remove(db=db, id=id)
    return booking

import uuid
from typing import Optional

from app.worker import send_email_task
from app.utils.logger import get_logger

logger = get_logger(__name__)


def queue_booking_confirmation(
    *,
    booking_id: uuid.UUID,
    user_email: str,
    user_name: str,
    event_title: str,
    event_date,
    event_location: str,
    event_description: Optional[str],
    tickets_count: int,
) -> None:
    """Compose and enqueue booking confirmation email."""
    email_subject = f"Booking Confirmation: {event_title}"
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
            <p><strong>Description:</strong> {event_description or 'N/A'}</p>
            <p>Thank you for using our service!</p>
        </body>
    </html>
    """

    try:
        logger.debug("Email content for booking %s: %s", booking_id, email_content)
        send_email_task.delay(
            email_to=[user_email],
            subject=email_subject,
            html_content=email_content,
        )
        logger.info(
            "Email confirmation queued for booking %s to %s for event '%s'",
            booking_id,
            user_email,
            event_title,
        )
    except Exception as exc:  # pragma: no cover - logging path
        logger.exception(
            "Failed to queue email for booking %s: %s",
            booking_id,
            exc,
        )

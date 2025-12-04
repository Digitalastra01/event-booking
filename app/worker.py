from app.core.celery_app import celery_app
from app.core.email import send_email
from asgiref.sync import async_to_sync

@celery_app.task(acks_late=True)
def send_email_task(email_to: list[str], subject: str, html_content: str) -> str:
    async_to_sync(send_email)(email_to, subject, html_content)
    return "Email sent"

from celery import Celery
from app.core.config import settings

celery_app = Celery("worker", broker=settings.REDIS_URL, include=["app.worker"])


celery_app.conf.update(task_track_started=True)

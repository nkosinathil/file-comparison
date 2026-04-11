"""
Celery application bootstrap.

This keeps worker startup functional in environments that run
`celery -A app.celery worker`.
"""

from celery import Celery

from .config import settings

celery = Celery(
    "aurex",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
app = celery

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

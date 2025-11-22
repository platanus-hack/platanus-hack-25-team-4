"""
Celery Configuration - Background task queue for async processing.

Tasks are executed asynchronously by workers, allowing the API to respond
quickly while processing happens in the background.
"""

from celery import Celery

from ..core import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "circles-etl", broker=settings._celery_broker, backend=settings._celery_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    worker_prefetch_multiplier=1,
)


# Task decorators will be defined in separate files
# Example structure:
# @celery_app.task(name="process_resume")
# def process_resume(job_id: str, file_path: str):
#     # Process resume asynchronously
#     pass

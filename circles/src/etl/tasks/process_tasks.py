"""
Celery Tasks - Background job processing for data ingestion.

Defines async tasks for processing each data type with adapter pipeline.
"""

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..adapters.base import DataType
from ..adapters.registry import get_registry
from ..core import get_settings
from .celery_app import celery_app


# Database session setup
async def get_db_session() -> AsyncSession:
    """Create async database session."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_delete=False)
    return async_session()


@celery_app.task(name="process_resume")
def process_resume_task(job_id: str, file_path: str, user_id: int) -> Dict[str, Any]:
    """Process resume file asynchronously."""
    return {
        "job_id": job_id,
        "status": "processing",
        "data_type": "resume",
        "message": f"Processing resume from {file_path}",
    }


@celery_app.task(name="process_photo")
def process_photo_task(job_id: str, file_path: str, user_id: int) -> Dict[str, Any]:
    """Process photo file asynchronously."""
    return {
        "job_id": job_id,
        "status": "processing",
        "data_type": "photo",
        "message": f"Processing photo from {file_path}",
    }


@celery_app.task(name="process_voice_note")
def process_voice_note_task(
    job_id: str, file_path: str, user_id: int
) -> Dict[str, Any]:
    """Process voice note asynchronously."""
    return {
        "job_id": job_id,
        "status": "processing",
        "data_type": "voice_note",
        "message": f"Processing voice note from {file_path}",
    }


@celery_app.task(name="process_chat_transcript")
def process_chat_transcript_task(
    job_id: str, transcript_data: Dict[str, Any], user_id: int
) -> Dict[str, Any]:
    """Process chat transcript asynchronously."""
    return {
        "job_id": job_id,
        "status": "processing",
        "data_type": "chat_transcript",
        "message": "Processing chat transcript",
    }


@celery_app.task(name="process_calendar")
def process_calendar_task(job_id: str, file_path: str, user_id: int) -> Dict[str, Any]:
    """Process calendar file asynchronously."""
    return {
        "job_id": job_id,
        "status": "processing",
        "data_type": "calendar",
        "message": f"Processing calendar from {file_path}",
    }


@celery_app.task(name="process_email")
def process_email_task(
    job_id: str, email_data: Dict[str, Any], user_id: int
) -> Dict[str, Any]:
    """Process email data asynchronously."""
    return {
        "job_id": job_id,
        "status": "processing",
        "data_type": "email",
        "message": "Processing email data",
    }


@celery_app.task(name="process_social_post")
def process_social_post_task(
    job_id: str, post_data: Dict[str, Any], user_id: int
) -> Dict[str, Any]:
    """Process social media post asynchronously."""
    return {
        "job_id": job_id,
        "status": "processing",
        "data_type": "social_post",
        "message": "Processing social media post",
    }


@celery_app.task(name="process_blog_post")
def process_blog_post_task(
    job_id: str, blog_data: Dict[str, Any], user_id: int
) -> Dict[str, Any]:
    """Process blog post asynchronously."""
    return {
        "job_id": job_id,
        "status": "processing",
        "data_type": "blog_post",
        "message": "Processing blog post",
    }


@celery_app.task(name="process_screenshot")
def process_screenshot_task(
    job_id: str, file_path: str, user_id: int
) -> Dict[str, Any]:
    """Process screenshot asynchronously."""
    return {
        "job_id": job_id,
        "status": "processing",
        "data_type": "screenshot",
        "message": f"Processing screenshot from {file_path}",
    }


@celery_app.task(name="process_shared_image")
def process_shared_image_task(
    job_id: str, file_path: str, user_id: int
) -> Dict[str, Any]:
    """Process shared image asynchronously."""
    return {
        "job_id": job_id,
        "status": "processing",
        "data_type": "shared_image",
        "message": f"Processing shared image from {file_path}",
    }


# Generic processing task that routes to appropriate adapter
@celery_app.task(bind=True, name="generic_process_data")
def generic_process_data(
    self,
    job_id: str,
    data_type: str,
    input_data: Any,
    user_id: int,
    source_id: int,
) -> Dict[str, Any]:
    """
    Generic task for processing any data type using appropriate adapter.

    Routes to the correct adapter based on data_type.
    """
    try:
        # Get registry and retrieve adapter
        registry = get_registry()

        # Map string to DataType enum
        data_type_map = {
            "resume": DataType.RESUME,
            "photo": DataType.PHOTO,
            "voice_note": DataType.VOICE_NOTE,
            "chat_transcript": DataType.CHAT_TRANSCRIPT,
            "calendar": DataType.CALENDAR,
            "email": DataType.EMAIL,
            "social_post": DataType.SOCIAL_POST,
            "blog_post": DataType.BLOG_POST,
            "screenshot": DataType.SCREENSHOT,
            "shared_image": DataType.SHARED_IMAGE,
        }

        enum_type = data_type_map.get(data_type)
        if not enum_type:
            return {
                "job_id": job_id,
                "status": "failed",
                "error": f"Unknown data type: {data_type}",
            }

        adapter_result = registry.get_adapter(enum_type)
        if adapter_result.is_error:
            return {
                "job_id": job_id,
                "status": "failed",
                "error": f"No adapter for {data_type}",
            }

        # TODO: Implement full async pipeline execution
        # This would require:
        # - Using adapter_result.value to get the adapter
        # - Creating AdapterContext with user_id, source_id, data_type, trace_id
        # - Running adapter.execute() with proper database session management

        return {
            "job_id": job_id,
            "status": "queued",
            "data_type": data_type,
            "message": f"Task queued for {data_type} processing",
        }

    except Exception as e:
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
        }

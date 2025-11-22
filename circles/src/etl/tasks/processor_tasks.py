"""
Celery Task Execution - Full adapter pipeline integration.

Executes the 4-phase ETL pipeline asynchronously for all data types.
Integrates with database persistence and error tracking.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..adapters.base import AdapterContext, DataType
from ..core import ProcessingError, get_settings
from .celery_app import celery_app

logger = logging.getLogger(__name__)

# Database engine (singleton pattern)
_engine = None
_async_session_factory = None


async def init_db_engine():
    """Initialize database engine and session factory."""
    global _engine, _async_session_factory
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
        )
        _async_session_factory = sessionmaker(
            _engine, class_=AsyncSession, expire_on_delete=False
        )
    return _async_session_factory


async def get_db_session():
    """Get database session."""
    factory = await init_db_engine()
    async with factory() as session:
        yield session


async def execute_adapter_pipeline(
    adapter_class,
    input_data: Any,
    user_id: int,
    source_id: int,
    job_id: str,
    data_type: str,
) -> Dict[str, Any]:
    """
    Execute complete adapter pipeline for a data type.

    Args:
        adapter_class: The adapter class to use
        input_data: Input data (file path or dict)
        user_id: User ID
        source_id: Source ID
        job_id: Job ID for tracking
        data_type: Data type string

    Returns:
        Result dictionary with success/error info
    """
    session = None
    try:
        # Initialize database
        factory = await init_db_engine()

        # Create adapter instance
        adapter = adapter_class()

        # Create adapter context
        context = AdapterContext(
            user_id=user_id,
            source_id=source_id,
            data_type=DataType[data_type.upper().replace("-", "_")],
            trace_id=job_id,
        )

        # Execute pipeline with database session
        async with factory() as session:
            result = await adapter.execute(input_data, context, session)

            if result.is_error:
                error = result.error_value
                logger.error(
                    f"Pipeline failed for {data_type} job {job_id}: {error.message}"
                )
                return {
                    "job_id": job_id,
                    "status": "failed",
                    "data_type": data_type,
                    "error": error.message,
                    "error_type": error.error_type,
                }

            # Success - result.value contains the persisted model instance
            data = result.value
            logger.info(f"Pipeline completed successfully for {data_type} job {job_id}")

            return {
                "job_id": job_id,
                "status": "completed",
                "data_type": data_type,
                "model_id": getattr(data, "id", None),
                "message": f"Successfully processed {data_type}",
            }

    except ProcessingError as e:
        logger.error(f"Processing error for job {job_id}: {e.message}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": data_type,
            "error": e.message,
            "error_type": e.error_type,
        }

    except Exception as e:
        logger.exception(f"Unexpected error processing job {job_id}: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": data_type,
            "error": str(e),
            "error_type": "system_error",
        }

    finally:
        if session:
            await session.close()


def _run_async_pipeline(
    adapter_class, input_data, user_id, source_id, job_id, data_type
):
    """
    Synchronous wrapper to run async pipeline in Celery.

    Celery is synchronous, so we use this to bridge to async code.
    """
    return asyncio.run(
        execute_adapter_pipeline(
            adapter_class, input_data, user_id, source_id, job_id, data_type
        )
    )


# Task definitions for each data type
@celery_app.task(name="process_resume", bind=True)
def process_resume_task(
    self, job_id: str, file_path: str, user_id: int, source_id: int
):
    """Process resume file asynchronously."""
    from ..adapters import ResumeAdapter

    try:
        return _run_async_pipeline(
            ResumeAdapter,
            Path(file_path),
            user_id,
            source_id,
            job_id,
            "resume",
        )
    except Exception as e:
        logger.error(f"Resume processing task failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": "resume",
            "error": str(e),
        }


@celery_app.task(name="process_photo", bind=True)
def process_photo_task(self, job_id: str, file_path: str, user_id: int, source_id: int):
    """Process photo file with Claude Vision asynchronously."""
    from ..adapters import PhotoAdapter

    try:
        return _run_async_pipeline(
            PhotoAdapter,
            Path(file_path),
            user_id,
            source_id,
            job_id,
            "photo",
        )
    except Exception as e:
        logger.error(f"Photo processing task failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": "photo",
            "error": str(e),
        }


@celery_app.task(name="process_voice_note", bind=True)
def process_voice_note_task(
    self, job_id: str, file_path: str, user_id: int, source_id: int
):
    """Process voice note with Whisper asynchronously."""
    from ..adapters import VoiceNoteAdapter

    try:
        return _run_async_pipeline(
            VoiceNoteAdapter,
            Path(file_path),
            user_id,
            source_id,
            job_id,
            "voice_note",
        )
    except Exception as e:
        logger.error(f"Voice note processing task failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": "voice_note",
            "error": str(e),
        }


@celery_app.task(name="process_calendar", bind=True)
def process_calendar_task(
    self, job_id: str, file_path: str, user_id: int, source_id: int
):
    """Process calendar file asynchronously."""
    from ..adapters import CalendarAdapter

    try:
        return _run_async_pipeline(
            CalendarAdapter,
            Path(file_path),
            user_id,
            source_id,
            job_id,
            "calendar",
        )
    except Exception as e:
        logger.error(f"Calendar processing task failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": "calendar",
            "error": str(e),
        }


@celery_app.task(name="process_screenshot", bind=True)
def process_screenshot_task(
    self, job_id: str, file_path: str, user_id: int, source_id: int
):
    """Process screenshot file asynchronously."""
    from ..adapters import ScreenshotAdapter

    try:
        return _run_async_pipeline(
            ScreenshotAdapter,
            Path(file_path),
            user_id,
            source_id,
            job_id,
            "screenshot",
        )
    except Exception as e:
        logger.error(f"Screenshot processing task failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": "screenshot",
            "error": str(e),
        }


@celery_app.task(name="process_shared_image", bind=True)
def process_shared_image_task(
    self, job_id: str, file_path: str, user_id: int, source_id: int
):
    """Process shared image file asynchronously."""
    from ..adapters import SharedImageAdapter

    try:
        return _run_async_pipeline(
            SharedImageAdapter,
            Path(file_path),
            user_id,
            source_id,
            job_id,
            "shared_image",
        )
    except Exception as e:
        logger.error(f"Shared image processing task failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": "shared_image",
            "error": str(e),
        }


@celery_app.task(name="process_chat_transcript", bind=True)
def process_chat_transcript_task(
    self, job_id: str, transcript_data: Dict[str, Any], user_id: int, source_id: int
):
    """Process chat transcript asynchronously."""
    from ..adapters import ChatTranscriptAdapter

    try:
        return _run_async_pipeline(
            ChatTranscriptAdapter,
            transcript_data,
            user_id,
            source_id,
            job_id,
            "chat_transcript",
        )
    except Exception as e:
        logger.error(f"Chat transcript processing task failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": "chat_transcript",
            "error": str(e),
        }


@celery_app.task(name="process_email", bind=True)
def process_email_task(
    self, job_id: str, email_data: Dict[str, Any], user_id: int, source_id: int
):
    """Process email data asynchronously."""
    from ..adapters import EmailAdapter

    try:
        return _run_async_pipeline(
            EmailAdapter,
            email_data,
            user_id,
            source_id,
            job_id,
            "email",
        )
    except Exception as e:
        logger.error(f"Email processing task failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": "email",
            "error": str(e),
        }


@celery_app.task(name="process_social_post", bind=True)
def process_social_post_task(
    self, job_id: str, post_data: Dict[str, Any], user_id: int, source_id: int
):
    """Process social media post asynchronously."""
    from ..adapters import SocialPostAdapter

    try:
        return _run_async_pipeline(
            SocialPostAdapter,
            post_data,
            user_id,
            source_id,
            job_id,
            "social_post",
        )
    except Exception as e:
        logger.error(f"Social post processing task failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": "social_post",
            "error": str(e),
        }


@celery_app.task(name="process_blog_post", bind=True)
def process_blog_post_task(
    self, job_id: str, blog_data: Dict[str, Any], user_id: int, source_id: int
):
    """Process blog post asynchronously."""
    from ..adapters import BlogPostAdapter

    try:
        return _run_async_pipeline(
            BlogPostAdapter,
            blog_data,
            user_id,
            source_id,
            job_id,
            "blog_post",
        )
    except Exception as e:
        logger.error(f"Blog post processing task failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "data_type": "blog_post",
            "error": str(e),
        }

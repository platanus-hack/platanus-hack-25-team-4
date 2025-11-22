"""
Upload API Routes - FastAPI endpoints for file and data uploads.

Provides endpoints for uploading all 10 data types with async processing.
"""

import logging
import secrets
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Body, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from ...core import SecureFileValidator, get_settings
from ...tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/upload", tags=["uploads"])


class UploadStatus(str, Enum):
    """Upload job status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """Response for upload request."""

    job_id: str
    status: UploadStatus
    data_type: str
    message: str
    timestamp: datetime


class JobStatusResponse(BaseModel):
    """Response for job status query."""

    job_id: str
    status: UploadStatus
    data_type: str
    progress: Optional[int] = None
    error: Optional[str] = None


# In-memory job tracking (MVP - replace with database for production)
_job_store: dict = {}


def _create_job(job_id: str, data_type: str, status: UploadStatus) -> None:
    """Store job metadata."""
    _job_store[job_id] = {
        "data_type": data_type,
        "status": status,
        "error": None,
        "progress": 0,
    }


def _get_job(job_id: str) -> Optional[dict]:
    """Retrieve job metadata."""
    return _job_store.get(job_id)


def _update_job(
    job_id: str,
    status: Optional[UploadStatus] = None,
    progress: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    """Update job metadata."""
    if job_id in _job_store:
        if status:
            _job_store[job_id]["status"] = status
        if progress is not None:
            _job_store[job_id]["progress"] = progress
        if error:
            _job_store[job_id]["error"] = error


async def _validate_and_save_file(
    file: UploadFile,
    file_type: str,
    job_id: str,
    subdirectory: str,
) -> Path:
    """Common validation and save logic for file uploads."""
    settings = get_settings()
    content = await file.read()

    # Validate file
    validation = await SecureFileValidator.validate_file(
        filename=file.filename or f"{file_type}_file",
        content=content,
        file_type=file_type,
    )

    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=validation.error
        )

    # Save file temporarily
    upload_dir = settings.upload_dir_path / subdirectory
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = (
        f"{job_id}_{SecureFileValidator.sanitize_filename(file.filename or file_type)}"
    )
    file_path = upload_dir / safe_filename

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path


def _queue_celery_task(
    task_name: str, job_id: str, user_id: str, source_id: int = 1, **kwargs
) -> None:
    """
    Queue a Celery task for processing.

    Args:
        task_name: Name of the Celery task
        job_id: Job ID for tracking
        user_id: Authenticated user ID from JWT token
        source_id: Source ID (default: 1 for MVP)
        **kwargs: Additional arguments to pass to the task
    """
    try:
        celery_app.send_task(
            task_name,
            kwargs={
                "job_id": job_id,
                "user_id": user_id,
                "source_id": source_id,
                **kwargs,
            },
        )
        logger.info(f"Queued task {task_name} with job_id {job_id} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to queue task {task_name}: {e}")
        raise


@router.post(
    "/resume", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_resume(
    file: Annotated[UploadFile, File(description="Resume file (PDF, DOCX, TXT)")],
    user_id: str,
) -> UploadResponse:
    """Upload a resume file for processing."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "resume", UploadStatus.PENDING)

    try:
        file_path = await _validate_and_save_file(file, "resume", job_id, "resumes")

        # Queue Celery task for background processing
        _queue_celery_task(
            "process_resume",
            job_id,
            user_id=user_id,
            file_path=str(file_path),
        )
        _update_job(job_id, UploadStatus.PROCESSING)

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PROCESSING,
            data_type="resume",
            message=f"Resume '{file.filename}' queued for processing",
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        _update_job(job_id, UploadStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed",
        )


@router.post(
    "/photo", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_photo(
    file: Annotated[
        UploadFile, File(description="Photo file (JPG, PNG, GIF, WebP, HEIC)")
    ],
    user_id: str,
) -> UploadResponse:
    """Upload a photo for VLM analysis."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "photo", UploadStatus.PENDING)

    try:
        file_path = await _validate_and_save_file(file, "image", job_id, "photos")

        # Queue Celery task for Claude Vision analysis
        _queue_celery_task(
            "process_photo",
            job_id,
            user_id=user_id,
            file_path=str(file_path),
        )
        _update_job(job_id, UploadStatus.PROCESSING)

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PROCESSING,
            data_type="photo",
            message=f"Photo '{file.filename}' queued for vision analysis",
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Photo upload failed: {e}")
        _update_job(job_id, UploadStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed",
        )


@router.post(
    "/voice-note", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_voice_note(
    file: Annotated[
        UploadFile, File(description="Audio file (MP3, WAV, OGG, WebM, M4A)")
    ],
    user_id: str,
) -> UploadResponse:
    """Upload a voice note for transcription."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "voice_note", UploadStatus.PENDING)

    try:
        file_path = await _validate_and_save_file(file, "audio", job_id, "voice_notes")

        # Queue Celery task for Whisper transcription
        _queue_celery_task(
            "process_voice_note",
            job_id,
            user_id=user_id,
            file_path=str(file_path),
        )
        _update_job(job_id, UploadStatus.PROCESSING)

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PROCESSING,
            data_type="voice_note",
            message=f"Voice note '{file.filename}' queued for transcription",
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice note upload failed: {e}")
        _update_job(job_id, UploadStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed",
        )


@router.post(
    "/calendar", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_calendar(
    file: Annotated[UploadFile, File(description="Calendar file (ICS)")],
    user_id: str,
) -> UploadResponse:
    """Upload a calendar file in ICS format."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "calendar", UploadStatus.PENDING)

    try:
        file_path = await _validate_and_save_file(file, "calendar", job_id, "calendars")

        # Queue Celery task for calendar parsing
        _queue_celery_task(
            "process_calendar",
            job_id,
            user_id=user_id,
            file_path=str(file_path),
        )
        _update_job(job_id, UploadStatus.PROCESSING)

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PROCESSING,
            data_type="calendar",
            message=f"Calendar file '{file.filename}' queued for processing",
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Calendar upload failed: {e}")
        _update_job(job_id, UploadStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed",
        )


@router.post(
    "/screenshot", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_screenshot(
    file: Annotated[UploadFile, File(description="Screenshot file (PNG, JPG)")],
    user_id: str,
) -> UploadResponse:
    """Upload a screenshot for vision analysis."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "screenshot", UploadStatus.PENDING)

    try:
        file_path = await _validate_and_save_file(file, "image", job_id, "screenshots")

        # Queue Celery task for vision analysis
        _queue_celery_task(
            "process_screenshot",
            job_id,
            user_id=user_id,
            file_path=str(file_path),
        )
        _update_job(job_id, UploadStatus.PROCESSING)

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PROCESSING,
            data_type="screenshot",
            message=f"Screenshot '{file.filename}' queued for analysis",
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Screenshot upload failed: {e}")
        _update_job(job_id, UploadStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed",
        )


@router.post(
    "/shared-image", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_shared_image(
    file: Annotated[UploadFile, File(description="Shared image file (PNG, JPG)")],
    user_id: str,
) -> UploadResponse:
    """Upload a shared image."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "shared_image", UploadStatus.PENDING)

    try:
        file_path = await _validate_and_save_file(
            file, "image", job_id, "shared_images"
        )

        # Queue Celery task for processing
        _queue_celery_task(
            "process_shared_image",
            job_id,
            user_id=user_id,
            file_path=str(file_path),
        )
        _update_job(job_id, UploadStatus.PROCESSING)

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PROCESSING,
            data_type="shared_image",
            message=f"Image '{file.filename}' queued for processing",
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Shared image upload failed: {e}")
        _update_job(job_id, UploadStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed",
        )


@router.post(
    "/chat-transcript",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_chat_transcript(
    data: Annotated[Dict[str, Any], Body(description="Chat transcript JSON data")],
    user_id: str,
) -> UploadResponse:
    """Upload chat transcript data (JSON)."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "chat_transcript", UploadStatus.PENDING)

    try:
        # Validate data
        if not data or "messages" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chat transcript must include 'messages' field",
            )

        # Queue Celery task for processing
        _queue_celery_task(
            "process_chat_transcript",
            job_id,
            user_id=user_id,
            transcript_data=data,
        )
        _update_job(job_id, UploadStatus.PROCESSING)

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PROCESSING,
            data_type="chat_transcript",
            message="Chat transcript queued for processing",
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat transcript upload failed: {e}")
        _update_job(job_id, UploadStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed",
        )


@router.post(
    "/email", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_email(
    data: Annotated[Dict[str, Any], Body(description="Email JSON data")],
    user_id: str,
) -> UploadResponse:
    """Upload email data (JSON)."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "email", UploadStatus.PENDING)

    try:
        # Validate data
        if not data or "threads" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email data must include 'threads' field",
            )

        # Queue Celery task for processing
        _queue_celery_task(
            "process_email",
            job_id,
            user_id=user_id,
            email_data=data,
        )
        _update_job(job_id, UploadStatus.PROCESSING)

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PROCESSING,
            data_type="email",
            message="Email data queued for processing",
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email upload failed: {e}")
        _update_job(job_id, UploadStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed",
        )


@router.post(
    "/social-post", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_social_post(
    data: Annotated[Dict[str, Any], Body(description="Social post JSON data")],
    user_id: str,
) -> UploadResponse:
    """Upload social media post data (JSON)."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "social_post", UploadStatus.PENDING)

    try:
        # Validate data
        if not data or "platform" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Social post must include 'platform' field",
            )

        # Queue Celery task for processing
        _queue_celery_task(
            "process_social_post", job_id, user_id=user_id, post_data=data
        )
        _update_job(job_id, UploadStatus.PROCESSING)

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PROCESSING,
            data_type="social_post",
            message="Social post queued for processing",
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        _update_job(job_id, UploadStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {e}",
        )


@router.post(
    "/blog-post", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_blog_post(
    data: Annotated[
        Dict[str, Any], Body(description="Blog post JSON data (markdown + metadata)")
    ],
    user_id: str,
) -> UploadResponse:
    """Upload blog post data (Markdown + metadata)."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "blog_post", UploadStatus.PENDING)

    try:
        # Validate data
        if not data or "markdown" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Blog post must include 'markdown' field",
            )

        # Queue Celery task for processing
        _queue_celery_task("process_blog_post", job_id, user_id=user_id, blog_data=data)
        _update_job(job_id, UploadStatus.PROCESSING)

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PROCESSING,
            data_type="blog_post",
            message="Blog post queued for processing",
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        _update_job(job_id, UploadStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {e}",
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_upload_status(job_id: str) -> JobStatusResponse:
    """Check processing status of an upload job."""
    job = _get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    response = JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        data_type=job["data_type"],
        progress=job.get("progress"),
    )

    if job.get("error"):
        response.error = job["error"]

    return response

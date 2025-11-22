"""
Upload API Routes - FastAPI endpoints for file and data uploads.

Provides endpoints for uploading all 10 data types with async processing.
"""

import secrets
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from ...core import SecureFileValidator, get_settings

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


@router.post(
    "/resume", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_resume(
    file: Annotated[UploadFile, File(description="Resume file (PDF, DOCX, TXT)")],
) -> UploadResponse:
    """Upload a resume file for processing."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "resume", UploadStatus.PENDING)

    try:
        await _validate_and_save_file(file, "resume", job_id, "resumes")
        # TODO: Queue Celery task for processing

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PENDING,
            data_type="resume",
            message=f"Resume '{file.filename}' queued for processing",
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
    "/photo", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_photo(
    file: Annotated[
        UploadFile, File(description="Photo file (JPG, PNG, GIF, WebP, HEIC)")
    ],
) -> UploadResponse:
    """Upload a photo for VLM analysis."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "photo", UploadStatus.PENDING)

    try:
        await _validate_and_save_file(file, "image", job_id, "photos")
        # TODO: Queue Celery task for processing

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PENDING,
            data_type="photo",
            message=f"Photo '{file.filename}' queued for vision analysis",
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
    "/voice-note", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_voice_note(
    file: Annotated[
        UploadFile, File(description="Audio file (MP3, WAV, OGG, WebM, M4A)")
    ],
) -> UploadResponse:
    """Upload a voice note for transcription."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "voice_note", UploadStatus.PENDING)

    try:
        await _validate_and_save_file(file, "audio", job_id, "voice_notes")
        # TODO: Queue Celery task for processing

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PENDING,
            data_type="voice_note",
            message=f"Voice note '{file.filename}' queued for transcription",
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
    "/calendar", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_calendar(
    file: Annotated[UploadFile, File(description="Calendar file (ICS)")],
) -> UploadResponse:
    """Upload a calendar file in ICS format."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "calendar", UploadStatus.PENDING)

    try:
        await _validate_and_save_file(file, "calendar", job_id, "calendars")
        # TODO: Queue Celery task for processing

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PENDING,
            data_type="calendar",
            message=f"Calendar file '{file.filename}' queued for processing",
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
    "/screenshot", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_screenshot(
    file: Annotated[UploadFile, File(description="Screenshot file (PNG, JPG)")],
) -> UploadResponse:
    """Upload a screenshot for vision analysis."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "screenshot", UploadStatus.PENDING)

    try:
        await _validate_and_save_file(file, "image", job_id, "screenshots")
        # TODO: Queue Celery task for processing

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PENDING,
            data_type="screenshot",
            message=f"Screenshot '{file.filename}' queued for analysis",
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
    "/shared-image", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_shared_image(
    file: Annotated[UploadFile, File(description="Shared image file (PNG, JPG)")],
) -> UploadResponse:
    """Upload a shared image."""
    job_id = secrets.token_urlsafe(16)
    _create_job(job_id, "shared_image", UploadStatus.PENDING)

    try:
        await _validate_and_save_file(file, "image", job_id, "shared_images")
        # TODO: Queue Celery task for processing

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PENDING,
            data_type="shared_image",
            message=f"Image '{file.filename}' queued for processing",
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
    "/chat-transcript",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_chat_transcript(
    data: Dict[str, Any],
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

        # TODO: Queue Celery task for processing

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PENDING,
            data_type="chat_transcript",
            message="Chat transcript queued for processing",
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
    "/email", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_email(data: Dict[str, Any]) -> UploadResponse:
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

        # TODO: Queue Celery task for processing

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PENDING,
            data_type="email",
            message="Email data queued for processing",
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
    "/social-post", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_social_post(data: Dict[str, Any]) -> UploadResponse:
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

        # TODO: Queue Celery task for processing

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PENDING,
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
async def upload_blog_post(data: Dict[str, Any]) -> UploadResponse:
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

        # TODO: Queue Celery task for processing

        return UploadResponse(
            job_id=job_id,
            status=UploadStatus.PENDING,
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

"""
Consolidation API Routes - FastAPI endpoints for profile consolidation.

Provides endpoints for triggering and monitoring user profile consolidation
from all available data sources.
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...core import get_settings
from ...tasks.celery_app import celery_app
from ...tasks.consolidation_tasks import consolidate_user_profile_task
from ..auth import get_current_user, validate_user_id_ownership

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/consolidation", tags=["consolidation"])


class ConsolidationStatus(str, Enum):
    """Consolidation job status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConsolidationRequest(BaseModel):
    """Request to consolidate a user profile."""

    user_id: str
    llm_provider: Optional[str] = "anthropic"  # 'anthropic' or 'openai'

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "user_id": "user_123",
                "llm_provider": "anthropic",
            }
        }


class ConsolidationResponse(BaseModel):
    """Response for consolidation request."""

    task_id: str
    user_id: str
    status: ConsolidationStatus
    llm_provider: str
    message: str
    timestamp: datetime


class ConsolidationStatusResponse(BaseModel):
    """Response for consolidation status query."""

    task_id: str
    user_id: str
    status: ConsolidationStatus
    llm_provider: str
    progress: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    timestamp: datetime


@router.post(
    "/consolidate",
    response_model=ConsolidationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger profile consolidation",
    description="Trigger consolidation of all available user data into a comprehensive profile.",
)
async def trigger_consolidation(
    request: ConsolidationRequest,
    current_user: str = Depends(get_current_user),
) -> ConsolidationResponse:
    """
    Trigger profile consolidation for a user.

    Aggregates all available user data (resume, photos, voice notes, etc.)
    and uses an LLM to synthesize a comprehensive UserProfile.

    The consolidation runs asynchronously in the background.
    Use the /status/{task_id} endpoint to monitor progress.

    Args:
        request: Consolidation request with user_id and llm_provider

    Returns:
        ConsolidationResponse with task_id for tracking

    Raises:
        HTTPException: If user_id is invalid or request fails
    """
    try:
        # Validate user ownership
        validate_user_id_ownership(request.user_id, current_user)

        if not request.user_id or not request.user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required",
            )

        if request.llm_provider not in ["anthropic", "openai"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="llm_provider must be 'anthropic' or 'openai'",
            )

        # Queue Celery task for consolidation
        task = consolidate_user_profile_task.apply_async(
            args=[request.user_id, request.llm_provider],
            task_id=f"consolidate_{request.user_id}_{int(datetime(UTC).timestamp())}",
        )

        logger.info(
            f"Queued consolidation task {task.id} for user {request.user_id} with provider {request.llm_provider}"
        )

        return ConsolidationResponse(
            task_id=task.id,
            user_id=request.user_id,
            status=ConsolidationStatus.PENDING,
            llm_provider=request.llm_provider,
            message=f"Consolidation started for user {request.user_id}",
            timestamp=datetime(UTC),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering consolidation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start consolidation",
        )


@router.get(
    "/status/{task_id}",
    response_model=ConsolidationStatusResponse,
    summary="Get consolidation status",
    description="Get the current status of a consolidation task.",
)
async def get_consolidation_status(
    task_id: str,
    current_user: str = Depends(get_current_user),
) -> ConsolidationStatusResponse:
    """
    Get the status of a consolidation task.

    Args:
        task_id: The task ID returned from /consolidate endpoint

    Returns:
        ConsolidationStatusResponse with current status

    Raises:
        HTTPException: If task_id is not found
    """
    try:
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)

        # Determine status
        if task_result.state == "PENDING":
            status_str = ConsolidationStatus.PENDING
            progress = "Waiting to start"
        elif task_result.state == "STARTED":
            status_str = ConsolidationStatus.PROCESSING
            progress = "Running consolidation pipeline"
        elif task_result.state == "SUCCESS":
            status_str = ConsolidationStatus.COMPLETED
            progress = "Consolidation completed"
        elif task_result.state == "FAILURE":
            status_str = ConsolidationStatus.FAILED
            progress = f"Failed: {task_result.info}"
        elif task_result.state == "RETRY":
            status_str = ConsolidationStatus.PROCESSING
            progress = "Retrying due to error"
        else:
            status_str = ConsolidationStatus.PROCESSING
            progress = f"Status: {task_result.state}"

        # Extract result data if available
        result_data = None
        error_msg = None

        if task_result.state == "SUCCESS" and isinstance(task_result.result, dict):
            result_data = task_result.result
            if result_data.get("status") != "success":
                error_msg = result_data.get("error") or result_data.get("message")
        elif task_result.state == "FAILURE":
            error_msg = str(task_result.info)

        # Parse user_id from task_id (format: consolidate_user_id_timestamp)
        task_parts = task_id.split("_")
        user_id = "_".join(task_parts[1:-1]) if len(task_parts) > 2 else "unknown"

        return ConsolidationStatusResponse(
            task_id=task_id,
            user_id=user_id,
            status=status_str,
            llm_provider="unknown",  # Would need to store in task metadata
            progress=progress,
            error=error_msg,
            result=result_data,
            timestamp=datetime(UTC),
        )

    except Exception as e:
        logger.error(f"Error getting consolidation status for task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task status",
        )


@router.post(
    "/consolidate-sync",
    response_model=Dict[str, Any],
    summary="Consolidate profile synchronously",
    description="Consolidate profile synchronously (blocking). For small datasets or testing only.",
)
async def consolidate_sync(
    request: ConsolidationRequest,
    current_user: str = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Synchronously consolidate a user profile.

    WARNING: This endpoint blocks until consolidation completes.
    Use the async /consolidate endpoint for production.

    Only use this for testing or small datasets.

    Args:
        request: Consolidation request with user_id and llm_provider

    Returns:
        Consolidated profile or error details

    Raises:
        HTTPException: If consolidation fails
    """
    try:
        # Validate user ownership
        validate_user_id_ownership(request.user_id, current_user)

        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from ...consolidation.orchestrator import ProfileConsolidationOrchestrator

        if not request.user_id or not request.user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required",
            )

        if request.llm_provider not in ["anthropic", "openai"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="llm_provider must be 'anthropic' or 'openai'",
            )

        async def _consolidate_async():
            settings = get_settings()
            engine = create_async_engine(
                settings.database_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
            )
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_delete=False
            )

            async with async_session() as session:
                orchestrator = (
                    ProfileConsolidationOrchestrator.create_with_llm_provider(
                        session, llm_provider_name=request.llm_provider
                    )
                )
                result = await orchestrator.consolidate_user_profile(request.user_id)

                if result.is_ok:
                    profile = result.value
                    return {
                        "status": "success",
                        "user_id": request.user_id,
                        "profile_id": profile.id,
                        "message": f"Profile consolidated successfully for user {request.user_id}",
                    }
                else:
                    error = result.error_value
                    return {
                        "status": "failed",
                        "user_id": request.user_id,
                        "error": str(error),
                        "message": f"Profile consolidation failed for user {request.user_id}",
                    }

        # Run consolidation
        result = await _consolidate_async()

        if result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Consolidation failed"),
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in synchronous consolidation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consolidation failed: {str(e)}",
        )


@router.get(
    "/info",
    response_model=Dict[str, Any],
    summary="Get consolidation API info",
    description="Get information about the consolidation API.",
)
async def consolidation_info() -> Dict[str, Any]:
    """
    Get consolidation API information.

    Returns:
        Information about consolidation endpoints and providers
    """
    return {
        "endpoints": {
            "consolidate_async": "POST /api/v1/consolidation/consolidate",
            "consolidate_sync": "POST /api/v1/consolidation/consolidate-sync",
            "status": "GET /api/v1/consolidation/status/{task_id}",
            "info": "GET /api/v1/consolidation/info",
        },
        "llm_providers": ["anthropic", "openai"],
        "description": "Consolidates all available user data into a comprehensive profile using injected LLM",
        "documentation": {
            "async_flow": [
                "POST /consolidate with user_id and llm_provider",
                "Receive task_id in response",
                "Poll GET /status/{task_id} to monitor progress",
            ],
            "sync_flow": [
                "POST /consolidate-sync with user_id and llm_provider",
                "Wait for response (blocks until complete)",
                "Receive consolidated profile directly",
            ],
        },
    }

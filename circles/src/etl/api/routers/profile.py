"""
Profile management API routes.

This module provides endpoints for managing user profiles, including
creating and updating bio and interests.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session

# Create router
router = APIRouter(
    prefix="/api/v1/profile",
    tags=["profile"],
)


# ============================================================================
# Request/Response Models
# ============================================================================


class Interest(BaseModel):
    """User interest with title and description."""

    title: str
    description: str


class UpdateProfileRequest(BaseModel):
    """Request model for updating user bio and interests."""

    user_id: str = Field(..., description="Unique user identifier")
    bio: Optional[str] = Field(None, description="User bio/description")
    interests: Optional[List[Interest]] = Field(
        None, description="List of user interests with title and description"
    )


class ProfileResponse(BaseModel):
    """Response model for profile operations."""

    user_id: str
    bio: Optional[str] = None
    interests: Optional[List[Dict[str, str]]] = None
    profile_completed: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    message: str


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/update-bio-interests",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update user bio and interests",
    description="Creates or updates the bio and interests for a given user. "
    "If the user profile doesn't exist, it will be created.",
)
async def update_bio_interests(
    request: UpdateProfileRequest,
    session: AsyncSession = Depends(get_async_session),
) -> ProfileResponse:
    """
    Create or update user bio and interests in User.profile JSON field.

    Args:
        request: UpdateProfileRequest containing user_id, bio, and interests
        session: Database session (injected by FastAPI)

    Returns:
        ProfileResponse with updated profile data

    Raises:
        HTTPException: If validation fails or database error occurs
    """
    try:
        # Get the user
        query = text('SELECT id, profile, "createdAt", "updatedAt" FROM "User" WHERE id = :user_id')
        result = await session.execute(query, {"user_id": request.user_id})
        user_row = result.fetchone()

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {request.user_id}",
            )

        # Parse existing profile or create new one
        current_profile = user_row[1] or {}

        # Update bio and interests
        if request.bio is not None:
            current_profile["bio"] = request.bio
        if request.interests is not None:
            current_profile["interests"] = [i.dict() for i in request.interests]

        # Check if profile is completed
        profile_completed = bool(current_profile.get("bio") and current_profile.get("interests"))
        current_profile["profile_completed"] = profile_completed

        # Update the user's profile field
        import json

        update_query = text(
            'UPDATE "User" SET profile = :profile, "updatedAt" = NOW() WHERE id = :user_id'
        )
        await session.execute(
            update_query, {"profile": json.dumps(current_profile), "user_id": request.user_id}
        )
        await session.commit()

        return ProfileResponse(
            user_id=request.user_id,
            bio=current_profile.get("bio"),
            interests=current_profile.get("interests"),
            profile_completed=profile_completed,
            created_at=user_row[2],
            updated_at=datetime.now(UTC),
            message="Profile updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}",
        ) from e


@router.get(
    "/{user_id}",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile bio and interests",
    description="Retrieves the bio and interests for a given user.",
)
async def get_profile(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> ProfileResponse:
    """
    Get user profile bio and interests from User.profile JSON field.

    Args:
        user_id: Unique user identifier
        session: Database session (injected by FastAPI)

    Returns:
        ProfileResponse with profile data

    Raises:
        HTTPException: If user not found or database error occurs
    """
    try:
        query = text('SELECT id, profile, "createdAt", "updatedAt" FROM "User" WHERE id = :user_id')
        result = await session.execute(query, {"user_id": user_id})
        user_row = result.fetchone()

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        profile_data = user_row[1] or {}

        return ProfileResponse(
            user_id=user_id,
            bio=profile_data.get("bio"),
            interests=profile_data.get("interests"),
            profile_completed=profile_data.get("profile_completed", False),
            created_at=user_row[2],
            updated_at=user_row[3],
            message="Profile retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}",
        ) from e

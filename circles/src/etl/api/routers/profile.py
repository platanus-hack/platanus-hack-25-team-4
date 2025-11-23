"""
Profile management API routes.

This module provides endpoints for managing user profiles, including
creating and updating bio and interests.
"""

from datetime import UTC, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlmodel import select

from src.database import get_session
from src.profile_schema import Interest, UserProfile

# Create router
router = APIRouter(
    prefix="/api/v1/profile",
    tags=["profile"],
)


# ============================================================================
# Request/Response Models
# ============================================================================


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
    interests: Optional[List[Interest]] = None
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
    session: Session = Depends(get_session),
) -> ProfileResponse:
    """
    Create or update user bio and interests.

    Args:
        request: UpdateProfileRequest containing user_id, bio, and interests
        session: Database session (injected by FastAPI)

    Returns:
        ProfileResponse with updated profile data

    Raises:
        HTTPException: If validation fails or database error occurs
    """
    try:
        # Check if profile exists
        statement = select(UserProfile).where(UserProfile.user_id == request.user_id)
        result = session.execute(statement)
        profile = result.scalar_one_or_none()

        if profile:
            # Update existing profile
            if request.bio is not None:
                profile.bio = request.bio
            if request.interests is not None:
                profile.interests = request.interests
            profile.updated_at = datetime.now(UTC)

            # Check if profile is completed (has bio and at least one interest)
            if profile.bio and profile.interests:
                profile.profile_completed = True

            session.add(profile)
            session.commit()
            session.refresh(profile)

            return ProfileResponse(
                user_id=profile.user_id,
                bio=profile.bio,
                interests=profile.interests,
                profile_completed=profile.profile_completed,
                created_at=profile.created_at,
                updated_at=profile.updated_at,
                message="Profile updated successfully",
            )
        else:
            # Create new profile
            new_profile = UserProfile(
                user_id=request.user_id,
                bio=request.bio,
                interests=request.interests,
                profile_completed=bool(request.bio and request.interests),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            session.add(new_profile)
            session.commit()
            session.refresh(new_profile)

            return ProfileResponse(
                user_id=new_profile.user_id,
                bio=new_profile.bio,
                interests=new_profile.interests,
                profile_completed=new_profile.profile_completed,
                created_at=new_profile.created_at,
                updated_at=new_profile.updated_at,
                message="Profile created successfully",
            )

    except Exception as e:
        session.rollback()
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
    session: Session = Depends(get_session),
) -> ProfileResponse:
    """
    Get user profile bio and interests.

    Args:
        user_id: Unique user identifier
        session: Database session (injected by FastAPI)

    Returns:
        ProfileResponse with profile data

    Raises:
        HTTPException: If user not found or database error occurs
    """
    try:
        statement = select(UserProfile).where(UserProfile.user_id == user_id)
        result = session.execute(statement)
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile not found for user_id: {user_id}",
            )

        return ProfileResponse(
            user_id=profile.user_id,
            bio=profile.bio,
            interests=profile.interests,
            profile_completed=profile.profile_completed,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            message="Profile retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}",
        ) from e

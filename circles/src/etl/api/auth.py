"""
API Authentication and Authorization module.

Provides JWT-based authentication for consolidation API endpoints.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core import get_settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


def create_access_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT access token for API authentication.

    Args:
        user_id: User ID to encode in token
        expires_delta: Token expiration time (default: 24 hours)

    Returns:
        Encoded JWT token
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    expire = datetime.now(UTC) + expires_delta
    to_encode = {"sub": user_id, "exp": expire}

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def verify_token(token: str) -> str:
    """
    Verify JWT token and extract user_id.

    Args:
        token: JWT token to verify

    Returns:
        User ID from token

    Raises:
        ValueError: If token is invalid or expired
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("No user_id in token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Dependency for FastAPI route protection.

    Verifies JWT token and returns authenticated user_id.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        Authenticated user_id

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = verify_token(credentials.credentials)
        logger.debug(f"Successfully authenticated user: {user_id}")
        return user_id
    except ValueError as e:
        logger.warning(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_user_id_ownership(
    requested_user_id: str,
    authenticated_user_id: str,
) -> bool:
    """
    Validate that authenticated user has access to requested user_id.

    Args:
        requested_user_id: User ID from request
        authenticated_user_id: User ID from authentication token

    Returns:
        True if user has access, False otherwise

    Raises:
        HTTPException: If access is denied
    """
    # Allow admin token (future feature) or self-access
    if authenticated_user_id == requested_user_id:
        return True

    # Could extend this with admin check or delegation
    # For now, only allow self-access
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to consolidate this user's profile",
    )

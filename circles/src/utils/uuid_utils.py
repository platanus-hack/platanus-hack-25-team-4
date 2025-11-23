"""UUID utilities for user ID generation and validation."""

from uuid import UUID, uuid4


def generate_user_id() -> str:
    """Generate a new user ID (UUID v4 as string).

    Returns:
        A UUID v4 string suitable for use as a user ID
    """
    return str(uuid4())


def validate_user_id(user_id: str) -> bool:
    """Validate that user_id is a valid UUID string.

    Args:
        user_id: The user ID to validate

    Returns:
        True if user_id is a valid UUID, False otherwise
    """
    if not isinstance(user_id, str):
        return False
    try:
        UUID(user_id)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def create_test_user_id(index: int = 0) -> str:
    """Create a deterministic test user ID based on an index.

    Useful for test fixtures where you need consistent, reproducible UUIDs.
    For example: index=1 -> "00000000-0000-0000-0000-000000000001"

    Args:
        index: An integer to base the UUID on (0-255 for visible results)

    Returns:
        A UUID string based on the index
    """
    return f"00000000-0000-0000-0000-{index:012d}"

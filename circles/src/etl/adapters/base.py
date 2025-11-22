"""Base types and exceptions for ETL adapters.

This module defines common types, exceptions, and utilities used across
all adapter implementations in the ETL pipeline.
"""

from pathlib import Path
from typing import TypeAlias

# Type aliases for common adapter inputs
FilePath: TypeAlias = Path | str
FileContent: TypeAlias = bytes | str


class AdapterError(Exception):
    """Base exception for all adapter-related errors."""

    pass


class ModelLoadError(AdapterError):
    """Raised when a model fails to load."""

    pass


class InferenceError(AdapterError):
    """Raised when inference fails."""

    pass


class ConversionError(AdapterError):
    """Raised when file conversion fails."""

    pass


class UnsupportedFormatError(ConversionError):
    """Raised when a file format is not supported."""

    pass


class InvalidInputError(AdapterError):
    """Raised when input validation fails."""

    pass


def ensure_path(file_path: FilePath) -> Path:
    """Convert a file path to a Path object and validate it exists.

    Args:
        file_path: Path-like object or string representing a file path.

    Returns:
        Path object for the file.

    Raises:
        InvalidInputError: If the path doesn't exist or is not a file.
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path

    if not path.exists():
        raise InvalidInputError(f"File does not exist: {path}")

    if not path.is_file():
        raise InvalidInputError(f"Path is not a file: {path}")

    return path

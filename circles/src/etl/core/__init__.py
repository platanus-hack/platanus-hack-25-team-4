"""
Core ETL infrastructure - Result monad, exceptions, security, configuration.
"""

from .result import Result, ProcessingError
from .exceptions import (
    ETLException,
    ValidationError,
    FileValidationError,
    SecurityError,
    ProcessingError as ProcessingErrorClass,
    ExternalAPIError,
    TimeoutError,
    PersistenceError,
    DatabaseError,
    IntegrityError,
    ConfigurationError,
    APIKeyMissingError,
    ResourceError,
    FileNotFoundError,
    StorageError,
)
from .security import SecureFileValidator, ValidationResult
from .config import Settings, get_settings, set_settings

__all__ = [
    "Result",
    "ProcessingError",
    "ETLException",
    "ValidationError",
    "FileValidationError",
    "SecurityError",
    "ProcessingErrorClass",
    "ExternalAPIError",
    "TimeoutError",
    "PersistenceError",
    "DatabaseError",
    "IntegrityError",
    "ConfigurationError",
    "APIKeyMissingError",
    "ResourceError",
    "FileNotFoundError",
    "StorageError",
    "SecureFileValidator",
    "ValidationResult",
    "Settings",
    "get_settings",
    "set_settings",
]

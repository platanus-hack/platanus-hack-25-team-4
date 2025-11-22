"""
ETL Exception Hierarchy - Structured error handling.

All exceptions in the ETL system inherit from a common base class
to allow for consistent error handling across the system.
"""

from typing import Any, Dict, Optional


class ETLException(Exception):
    """Base exception for all ETL operations."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


# Validation Errors


class ValidationError(ETLException):
    """Raised when input data fails validation."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.field = field
        super().__init__(message, error_code="VALIDATION_ERROR", details=details or {})


class FileValidationError(ValidationError):
    """Raised when file validation fails (type, size, format)."""

    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.filename = filename
        self.reason = reason
        super().__init__(message, details=details or {})


class SecurityError(ValidationError):
    """Raised when security validation fails (path traversal, XXE, zip bomb)."""

    def __init__(
        self,
        message: str,
        security_issue: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.security_issue = security_issue
        super().__init__(message, details=details or {})


# Processing Errors


class ProcessingError(ETLException):
    """Raised when data processing fails."""

    def __init__(
        self,
        message: str,
        processor: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.processor = processor
        super().__init__(message, error_code="PROCESSING_ERROR", details=details or {})


class ExternalAPIError(ProcessingError):
    """Raised when external API call fails (VLM, Whisper, embedding)."""

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        status_code: Optional[int] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.service = service
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(
            message, error_code="EXTERNAL_API_ERROR", details=details or {}
        )


class TimeoutError(ProcessingError):
    """Raised when processing exceeds time limit."""

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, details=details or {})


# Persistence Errors


class PersistenceError(ETLException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.operation = operation
        super().__init__(message, error_code="PERSISTENCE_ERROR", details=details or {})


class DatabaseError(PersistenceError):
    """Raised when database connection or query fails."""

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.query = query
        super().__init__(message, operation="database", details=details or {})


class IntegrityError(PersistenceError):
    """Raised when database integrity constraints are violated."""

    def __init__(
        self,
        message: str,
        constraint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.constraint = constraint
        super().__init__(message, operation="integrity_check", details=details or {})


# Configuration Errors


class ConfigurationError(ETLException):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.config_key = config_key
        super().__init__(message, error_code="CONFIG_ERROR", details=details or {})


class APIKeyMissingError(ConfigurationError):
    """Raised when required API key is not configured."""

    def __init__(self, service: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"API key missing for {service}. Set {service.upper()}_API_KEY environment variable.",
            config_key=f"{service.upper()}_API_KEY",
            details=details or {},
        )


# Resource Errors


class ResourceError(ETLException):
    """Raised when resource (file, network, etc.) is unavailable."""

    def __init__(
        self,
        message: str,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.resource = resource
        super().__init__(message, error_code="RESOURCE_ERROR", details=details or {})


class FileNotFoundError(ResourceError):
    """Raised when expected file is not found."""

    def __init__(self, filepath: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"File not found: {filepath}", resource=filepath, details=details or {}
        )


class StorageError(ResourceError):
    """Raised when storage operations fail (disk full, permissions, etc.)."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, resource="storage", details=details or {})

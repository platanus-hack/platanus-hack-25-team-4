"""
Base Adapter - Abstract base class for all data type adapters.

Implements the Template Method pattern with a 4-phase pipeline:
1. VALIDATE - Check input data validity
2. PROCESS - Transform using processors
3. PERSIST - Store in database
4. CLEANUP - Remove temporary resources

All concrete adapters must implement these 4 methods.
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, Optional, Protocol, TypeVar, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from ..core import ProcessingError, Result

# Type variables for input/output
InputT = TypeVar("InputT")  # Input data type (Path, dict, etc.)
OutputT = TypeVar("OutputT")  # Output database model


# Exception classes for adapters
class AdapterError(Exception):
    """Base exception class for all adapter errors."""

    pass


class InvalidInputError(AdapterError):
    """Raised when input data is invalid or malformed."""

    pass


class ConversionError(AdapterError):
    """Raised when conversion/transformation fails."""

    pass


class UnsupportedFormatError(ConversionError):
    """Raised when file format is not supported."""

    pass


class ModelLoadError(AdapterError):
    """Raised when ML model fails to load."""

    pass


class InferenceError(AdapterError):
    """Raised when ML inference fails."""

    pass


# Type aliases for file handling
FilePath = str | Path
FileContent = str | bytes


def ensure_path(file_path: FilePath) -> Path:
    """
    Convert a file path (str or Path) to a Path object.

    Args:
        file_path: A string path or Path object

    Returns:
        Path object
    """
    if isinstance(file_path, str):
        return Path(file_path)
    return file_path


class DataType(str, Enum):
    """Supported data types in the ETL system."""

    RESUME = "resume"
    CHAT_TRANSCRIPT = "chat_transcript"
    EMAIL = "email"
    CALENDAR = "calendar"
    SOCIAL_POST = "social_post"
    BLOG_POST = "blog_post"
    PHOTO = "photo"
    SHARED_IMAGE = "shared_image"
    SCREENSHOT = "screenshot"
    VOICE_NOTE = "voice_note"


@runtime_checkable
class ProcessorResult(Protocol):
    """
    Protocol for processor output - what processors must return.

    Processors transform raw input into structured data ready for persistence.
    """

    content: Dict[str, Any]  # Main processed content
    metadata: Dict[str, Any]  # Extracted metadata
    embeddings: Optional[Dict[str, Any]]  # Optional embeddings (vector representations)


class AdapterContext:
    """
    Context passed through the adapter pipeline.

    Carries important information needed across all 4 phases.
    """

    def __init__(
        self,
        user_id: int,
        source_id: int,
        data_type: DataType,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        input_path: Optional[Path] = None,
        session: Optional[Any] = None,
    ):
        self.user_id = user_id
        self.source_id = source_id
        self.data_type = data_type
        self.metadata = metadata or {}
        self.trace_id = trace_id or f"{data_type}-{user_id}-{source_id}"
        self.input_path = input_path
        self.session = session

    def __repr__(self) -> str:
        return f"AdapterContext(user_id={self.user_id}, data_type={self.data_type}, trace_id={self.trace_id})"


class BaseAdapter(ABC, Generic[InputT, OutputT]):
    """
    Abstract base adapter for all data type processors.

    Implements Template Method pattern enforcing a consistent 4-phase pipeline:
    1. Validate - Verify input is correct format, not malicious
    2. Process - Transform using appropriate processor (markitdown, VLM, etc.)
    3. Persist - Save processed data to database
    4. Cleanup - Remove temporary files/resources

    Subclasses must implement: validate, process, persist
    Subclasses may override: cleanup, get_processor, get_repository

    Type parameters:
        InputT: Type of input data (Path for files, dict for JSON, etc.)
        OutputT: Type of output database model
    """

    @property
    @abstractmethod
    def data_type(self) -> DataType:
        """Return the DataType this adapter handles."""
        pass

    @property
    @abstractmethod
    def processor_class(self) -> type:
        """Return the processor class to use."""
        pass

    @property
    @abstractmethod
    def repository_class(self) -> type:
        """Return the repository class to use."""
        pass

    @abstractmethod
    async def validate_input(
        self, input_data: InputT, context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """
        Phase 1: Validate input data before processing.

        Checks:
        - File exists and has correct format/extension
        - File size is within limits
        - File is not malicious (path traversal, zip bomb, XXE)
        - Data has required fields

        Args:
            input_data: Raw input data to validate
            context: Adapter context with user_id, trace_id, etc.

        Returns:
            Result.ok(None) if valid
            Result.error(ProcessingError) if invalid
        """
        pass

    @abstractmethod
    async def process(
        self, input_data: InputT, context: AdapterContext
    ) -> Result[ProcessorResult, ProcessingError]:
        """
        Phase 2: Main processing logic - extract and transform data.

        Uses the appropriate processor (ResumeProcessor, PhotoProcessor, etc.)
        to convert raw input into structured ProcessorResult.

        Handles:
        - File reading/parsing
        - API calls (VLM, Whisper, etc.)
        - NLP operations
        - Data extraction
        - Embedding generation

        Args:
            input_data: Validated input data
            context: Adapter context

        Returns:
            Result.ok(ProcessorResult) on success
            Result.error(ProcessingError) on failure
        """
        pass

    @abstractmethod
    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[OutputT, ProcessingError]:
        """
        Phase 3: Store processed data in database.

        Uses the appropriate repository to save data to database:
        - Create database models
        - Insert into PostgreSQL
        - Handle transactions
        - Return created models

        Args:
            processor_result: Output from processor
            context: Adapter context
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Result.ok(OutputT) with stored database model
            Result.error(ProcessingError) on failure
        """
        pass

    async def cleanup(self, input_data: InputT, context: AdapterContext) -> None:
        """
        Phase 4: Cleanup temporary resources.

        Default implementation removes file if input is a Path.
        Override if additional cleanup needed (temporary directories, API cleanup, etc.).

        Args:
            input_data: Original input data
            context: Adapter context
        """
        if isinstance(input_data, Path):
            try:
                input_data.unlink(missing_ok=True)
            except Exception:
                pass  # Cleanup failures are non-fatal

    async def execute(
        self, input_data: InputT, context: AdapterContext, session: AsyncSession
    ) -> Result[OutputT, ProcessingError]:
        """
        Execute the complete 4-phase pipeline (Template Method).

        This is the main entry point for all adapters. It orchestrates the pipeline
        and ensures proper error handling and cleanup.

        Pipeline:
        1. Validate input
        2. Process data
        3. Persist to database
        4. Cleanup resources

        If any phase fails, remaining phases are skipped and cleanup is performed.

        Args:
            input_data: Raw input data
            context: Adapter context
            session: Database session

        Returns:
            Result.ok(OutputT) on complete success
            Result.error(ProcessingError) if any phase fails
        """
        # Phase 1: Validate
        validation_result = await self.validate_input(input_data, context)
        if validation_result.is_error:
            await self.cleanup(input_data, context)
            return Result.error(validation_result.error_value)

        # Phase 2: Process
        process_result = await self.process(input_data, context)
        if process_result.is_error:
            await self.cleanup(input_data, context)
            return Result.error(process_result.error_value)

        # Phase 3: Persist
        persist_result = await self.persist(process_result.value, context, session)
        if persist_result.is_error:
            await self.cleanup(input_data, context)
            return Result.error(persist_result.error_value)

        # Phase 4: Cleanup
        await self.cleanup(input_data, context)

        return Result.ok(persist_result.value)

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(data_type={self.data_type})"

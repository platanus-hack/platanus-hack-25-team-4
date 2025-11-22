"""
Resume Adapter - Handles resume file uploads and processing.

Implements the 4-phase pipeline:
1. Validate - Check file is valid PDF/DOCX/TXT
2. Process - Extract text and structure with markitdown + NLP
3. Persist - Save to database
4. Cleanup - Remove temporary files
"""

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ..core import ProcessingError, Result, SecureFileValidator
from ..models import ResumeData
from ..processors.resume_processor import ResumeProcessor
from .base import AdapterContext, BaseAdapter, DataType, ProcessorResult


class ResumeAdapter(BaseAdapter[Path, ResumeData]):
    """Resume file adapter."""

    @property
    def data_type(self) -> DataType:
        return DataType.RESUME

    @property
    def processor_class(self) -> type:
        return ResumeProcessor

    @property
    def repository_class(self) -> type:
        return None  # Using direct model operations for MVP

    async def validate_input(
        self, input_data: Path, context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """
        Phase 1: Validate resume file.

        Checks:
        - File exists
        - File extension is .pdf, .docx, or .txt
        - File size is reasonable
        - File is not malicious
        """
        if not input_data.exists():
            error = ProcessingError(
                f"Resume file not found: {input_data}", error_type="file_not_found"
            )
            return Result.error(error)

        # Read content for validation
        try:
            with open(input_data, "rb") as f:
                content = f.read()
        except Exception as e:
            error = ProcessingError(
                f"Failed to read file: {e}", error_type="file_read_error"
            )
            return Result.error(error)

        # Validate using SecureFileValidator
        validation_result = await SecureFileValidator.validate_file(
            filename=input_data.name, content=content, file_type="resume"
        )

        if not validation_result.is_valid:
            error = ProcessingError(
                validation_result.error or "File validation failed",
                error_type="validation_error",
            )
            return Result.error(error)

        return Result.ok(None)

    async def process(
        self, input_data: Path, context: AdapterContext
    ) -> Result[ProcessorResult, ProcessingError]:
        """
        Phase 2: Process resume file.

        Extracts text and structure using ResumeProcessor.
        """
        try:
            processor = ResumeProcessor()
            result = await processor.process(input_data)

            # Convert SimpleProcessorResult to ProcessorResult protocol
            return Result.ok(result)

        except Exception as e:
            error = ProcessingError(
                f"Resume processing failed: {e}", error_type="processing_error"
            )
            return Result.error(error)

    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[ResumeData, ProcessingError]:
        """
        Phase 3: Persist resume to database.

        Creates ResumeData record with processed content.
        """
        try:
            # Create model
            resume = ResumeData(
                user_id=context.user_id,
                source_id=context.source_id,
                full_text=processor_result.content.get("full_text", ""),
                structured_data=processor_result.content.get("structured", {}),
            )

            # Add to session
            session.add(resume)
            await session.flush()  # Get the ID without committing

            return Result.ok(resume)

        except Exception as e:
            error = ProcessingError(
                f"Database persistence failed: {e}", error_type="persistence_error"
            )
            return Result.error(error)

    async def cleanup(self, input_data: Path, context: AdapterContext) -> None:
        """Phase 4: Cleanup temporary files."""
        await super().cleanup(input_data, context)

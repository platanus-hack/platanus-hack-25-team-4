"""
Photo Adapter - Handles image file uploads and processing with VLM analysis.

Implements the 4-phase pipeline:
1. Validate - Check file is valid image (JPEG, PNG, GIF, WebP, HEIC)
2. Process - Analyze with Claude Vision API for captions and analysis
3. Persist - Save to database
4. Cleanup - Remove temporary files
"""

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ..core import ProcessingError, Result, SecureFileValidator
from ..models import Photo
from ..processors.photo_processor import PhotoProcessor
from .base import AdapterContext, BaseAdapter, DataType, ProcessorResult


class PhotoAdapter(BaseAdapter[Path, Photo]):
    """Photo file adapter with VLM analysis."""

    @property
    def data_type(self) -> DataType:
        return DataType.PHOTO

    @property
    def processor_class(self) -> type:
        return PhotoProcessor

    @property
    def repository_class(self) -> type:
        return None  # Using direct model operations for MVP

    async def validate_input(
        self, input_data: Path, context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """
        Phase 1: Validate image file.

        Checks:
        - File exists
        - File extension is .jpg, .png, .gif, .webp, or .heic
        - File size is reasonable (max 25MB)
        - File is not malicious
        """
        if not input_data.exists():
            error = ProcessingError(
                f"Image file not found: {input_data}", error_type="file_not_found"
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
            filename=input_data.name, content=content, file_type="image"
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
        Phase 2: Process image file with Claude Vision.

        Extracts visual captions and detailed analysis.
        """
        try:
            processor = PhotoProcessor()
            result = await processor.process(input_data)

            # Convert SimpleProcessorResult to ProcessorResult protocol
            return Result.ok(result)

        except Exception as e:
            error = ProcessingError(
                f"Image processing failed: {e}", error_type="processing_error"
            )
            return Result.error(error)

    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[Photo, ProcessingError]:
        """
        Phase 3: Persist photo analysis to database.

        Creates Photo record with vision analysis results.
        """
        try:
            # Extract caption and analysis
            content = processor_result.content
            caption = content.get("caption", "")
            analysis = content.get("analysis", {})
            metadata = processor_result.metadata or {}
            exif_data = metadata.get("exif_data", {})

            # Create model
            photo = Photo(
                user_id=context.user_id,
                source_id=context.source_id,
                file_reference={
                    "filename": content.get("image_file", ""),
                    "size": metadata.get("file_size", 0),
                    "type": metadata.get("file_type", ""),
                },
                vlm_caption=caption,
                vlm_analysis=analysis,
                exif_data=exif_data,
            )

            # Add to session
            session.add(photo)
            await session.flush()  # Get the ID without committing

            return Result.ok(photo)

        except Exception as e:
            error = ProcessingError(
                f"Database persistence failed: {e}", error_type="persistence_error"
            )
            return Result.error(error)

    async def cleanup(self, input_data: Path, context: AdapterContext) -> None:
        """Phase 4: Cleanup temporary files."""
        await super().cleanup(input_data, context)

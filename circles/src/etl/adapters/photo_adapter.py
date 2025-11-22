"""
Photo Adapter - Handles image file uploads and processing with VLM analysis.

Implements the 4-phase pipeline:
1. Validate - Check file is valid image (JPEG, PNG, GIF, WebP, HEIC)
2. Process - Analyze with Claude Vision API for captions and analysis
3. Persist - Save to database
4. Cleanup - Remove temporary files

Supports both single image and batch processing with parallel VLM calls.
"""

from pathlib import Path
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from ..core import ProcessingError, Result, SecureFileValidator
from ..models import Photo
from ..processors.photo_processor import PhotoProcessor
from ..repositories import PhotoRepository
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
        return PhotoRepository

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

        Creates Photo record with vision analysis results using repository.
        """
        try:
            repository = PhotoRepository()
            photo = await repository.create_from_processor_result(
                user_id=context.user_id,
                source_id=context.source_id,
                processor_result=processor_result,
                session=session,
            )
            return Result.ok(photo)

        except Exception as e:
            error = ProcessingError(
                f"Database persistence failed: {e}", error_type="persistence_error"
            )
            return Result.error(error)

    async def cleanup(self, input_data: Path, context: AdapterContext) -> None:
        """Phase 4: Cleanup temporary files."""
        await super().cleanup(input_data, context)

    async def validate_batch(
        self, file_paths: List[Path], context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """
        Validate multiple image files.

        Args:
            file_paths: List of image file paths
            context: Adapter context

        Returns:
            Result indicating all files are valid
        """
        try:
            for file_path in file_paths:
                validation_result = await self.validate_input(file_path, context)
                if validation_result.is_error:
                    return validation_result
            return Result.ok(None)

        except Exception as e:
            error = ProcessingError(
                f"Batch validation failed: {e}", error_type="validation_error"
            )
            return Result.error(error)

    async def process_batch(
        self, file_paths: List[Path], context: AdapterContext
    ) -> Result[List[ProcessorResult], ProcessingError]:
        """
        Process multiple images in parallel.

        Args:
            file_paths: List of image file paths
            context: Adapter context

        Returns:
            Result with list of processor results
        """
        try:
            processor = PhotoProcessor(max_concurrent=30)
            # Enable image optimization for batch
            results = await processor.process_batch(file_paths, optimize_images=True)
            return Result.ok(results)

        except Exception as e:
            error = ProcessingError(
                f"Batch processing failed: {e}", error_type="processing_error"
            )
            return Result.error(error)

    async def persist_batch(
        self,
        processor_results: List[ProcessorResult],
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[List[Photo], ProcessingError]:
        """
        Persist multiple processed photos efficiently.

        Uses batch insert for better database performance.

        Args:
            processor_results: List of processor results
            context: Adapter context
            session: Database session

        Returns:
            Result with list of created photo records
        """
        try:
            repository = PhotoRepository()
            photos = await repository.create_batch_from_processor_results(
                user_id=context.user_id,
                source_id=context.source_id,
                processor_results=processor_results,
                session=session,
            )
            return Result.ok(photos)

        except Exception as e:
            error = ProcessingError(
                f"Batch persistence failed: {e}", error_type="persistence_error"
            )
            return Result.error(error)

    async def execute_batch(
        self,
        file_paths: List[Path],
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[List[Photo], ProcessingError]:
        """
        Execute full 4-phase pipeline for batch of images.

        Optimized for parallel processing with minimal database overhead.

        Args:
            file_paths: List of image file paths
            context: Adapter context
            session: Database session

        Returns:
            Result with list of persisted photo records
        """
        # Phase 1: Validate all files
        validation_result = await self.validate_batch(file_paths, context)
        if validation_result.is_error:
            return validation_result

        # Phase 2: Process all files in parallel
        processing_result = await self.process_batch(file_paths, context)
        if processing_result.is_error:
            return Result.error(processing_result.error_value)

        # Phase 3: Persist all results
        persist_result = await self.persist_batch(
            processing_result.value, context, session
        )
        if persist_result.is_error:
            return persist_result

        # Phase 4: Cleanup (handled separately per file)
        for file_path in file_paths:
            await self.cleanup(file_path, context)

        return Result.ok(persist_result.value)

"""
Voice Note Adapter - Handles audio file uploads and processing with Whisper transcription.

Implements the 4-phase pipeline:
1. Validate - Check file is valid audio (MP3, WAV, OGG, WebM, M4A)
2. Process - Transcribe with OpenAI Whisper API
3. Persist - Save to database
4. Cleanup - Remove temporary files
"""

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ..core import ProcessingError, Result, SecureFileValidator
from ..models import VoiceNote
from ..processors.voice_note_processor import VoiceNoteProcessor
from .base import AdapterContext, BaseAdapter, DataType, ProcessorResult


class VoiceNoteAdapter(BaseAdapter[Path, VoiceNote]):
    """Voice note file adapter with Whisper transcription."""

    @property
    def data_type(self) -> DataType:
        return DataType.VOICE_NOTE

    @property
    def processor_class(self) -> type:
        return VoiceNoteProcessor

    @property
    def repository_class(self) -> type:
        return None  # Using direct model operations for MVP

    async def validate_input(
        self, input_data: Path, context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """
        Phase 1: Validate audio file.

        Checks:
        - File exists
        - File extension is .mp3, .wav, .ogg, .webm, or .m4a
        - File size is reasonable (max 50MB)
        - File is not malicious
        """
        if not input_data.exists():
            error = ProcessingError(
                f"Audio file not found: {input_data}", error_type="file_not_found"
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
            filename=input_data.name, content=content, file_type="audio"
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
        Phase 2: Process audio file with Whisper.

        Transcribes audio and extracts metadata.
        """
        try:
            processor = VoiceNoteProcessor()
            result = await processor.process(input_data)

            # Convert SimpleProcessorResult to ProcessorResult protocol
            return Result.ok(result)

        except Exception as e:
            error = ProcessingError(
                f"Audio transcription failed: {e}", error_type="processing_error"
            )
            return Result.error(error)

    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[VoiceNote, ProcessingError]:
        """
        Phase 3: Persist voice note to database.

        Creates VoiceNote record with transcription and analysis.
        """
        try:
            # Extract transcription and analysis
            content = processor_result.content
            transcription = content.get("transcription", "")
            language = content.get("language", "unknown")
            topics = content.get("topics", [])
            sentiment = content.get("sentiment", {"sentiment": "neutral", "score": 0.5})
            metadata = processor_result.metadata or {}

            # Create model
            voice_note = VoiceNote(
                user_id=context.user_id,
                source_id=context.source_id,
                audio_file={
                    "filename": "audio_file",
                    "size": metadata.get("file_size", 0),
                    "type": metadata.get("file_type", ""),
                },
                transcription=transcription,
                transcription_confidence=metadata.get("confidence", 0.0),
                language=language,
                extracted_topics=topics,
                sentiment=sentiment,
            )

            # Add to session
            session.add(voice_note)
            await session.flush()  # Get the ID without committing

            return Result.ok(voice_note)

        except Exception as e:
            error = ProcessingError(
                f"Database persistence failed: {e}", error_type="persistence_error"
            )
            return Result.error(error)

    async def cleanup(self, input_data: Path, context: AdapterContext) -> None:
        """Phase 4: Cleanup temporary files."""
        await super().cleanup(input_data, context)

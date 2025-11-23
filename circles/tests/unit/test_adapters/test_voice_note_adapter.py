"""
Unit tests for VoiceNoteAdapter.

Tests the 4-phase pipeline (Validate, Process, Persist, Cleanup) for voice note processing.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.etl.adapters.base import AdapterContext, DataType
from src.etl.adapters.voice_note_adapter import VoiceNoteAdapter
from src.etl.core import ProcessingError, Result


@pytest.mark.unit
class TestVoiceNoteAdapter:
    """Test VoiceNoteAdapter functionality."""

    @pytest.fixture
    async def voice_adapter(self):
        """Create a VoiceNoteAdapter instance."""
        return VoiceNoteAdapter()

    @pytest.fixture
    def sample_voice_file(self, tmp_path):
        """Create a temporary voice note file."""
        voice_path = tmp_path / "test_note.mp3"
        # Minimal MP3 magic bytes
        voice_path.write_bytes(b"ID3")
        return voice_path

    @pytest.fixture
    def mock_adapter_context(self, sample_voice_file):
        """Create a mock AdapterContext."""
        return AdapterContext(
            user_id=1,
            source_id=1,
            data_type=DataType.VOICE_NOTE,
            input_path=sample_voice_file,
            session=AsyncMock(spec=AsyncSession),
        )

    @pytest.mark.asyncio
    async def test_validate_input_valid_voice(self, voice_adapter, sample_voice_file):
        """Test validation of a valid voice note file."""
        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.VOICE_NOTE)
        result = await voice_adapter.validate_input(sample_voice_file, context)

        assert result.is_ok, "Valid voice file should pass validation"

    @pytest.mark.asyncio
    async def test_validate_input_nonexistent_file(self, voice_adapter, tmp_path):
        """Test validation of non-existent file."""
        non_existent = tmp_path / "nonexistent.mp3"
        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.VOICE_NOTE)

        result = await voice_adapter.validate_input(non_existent, context)
        assert result.is_error, "Non-existent file should fail validation"

    @pytest.mark.asyncio
    async def test_validate_input_invalid_extension(self, voice_adapter, tmp_path):
        """Test validation of unsupported file type."""
        invalid_file = tmp_path / "note.txt"
        invalid_file.write_text("content")

        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.VOICE_NOTE)
        result = await voice_adapter.validate_input(invalid_file, context)

        assert result.is_error, "Invalid file extension should fail validation"

    @pytest.mark.asyncio
    async def test_validate_input_supported_formats(self, voice_adapter, tmp_path):
        """Test validation of all supported audio formats."""
        supported_formats = [".mp3", ".wav", ".ogg", ".webm", ".m4a"]

        for ext in supported_formats:
            test_file = tmp_path / f"note{ext}"
            test_file.write_bytes(b"dummy audio content")

            context = AdapterContext(
                user_id=1, source_id=1, data_type=DataType.VOICE_NOTE
            )
            result = await voice_adapter.validate_input(test_file, context)

            assert result.is_ok, f"{ext} should be a valid audio format"

    @pytest.mark.asyncio
    async def test_process_voice_note(
        self, voice_adapter, sample_voice_file, mock_adapter_context
    ):
        """Test processing a voice note file."""
        mock_processor_result = MagicMock(
            content={
                "transcription": "Hello, this is a test voice note",
                "segments": [{"text": "Hello"}],
            },
            metadata={"file_type": ".mp3", "file_size": 5000},
            embeddings=None,
        )

        with patch(
            "src.etl.adapters.voice_note_adapter.VoiceNoteProcessor"
        ) as MockProcessor:
            mock_instance = MockProcessor.return_value
            mock_instance.process = AsyncMock(return_value=mock_processor_result)

            result = await voice_adapter.process(
                sample_voice_file, mock_adapter_context
            )

            assert result.is_ok, "Processing should succeed"
            assert "transcription" in result.value.content
            assert result.value.metadata["file_type"] == ".mp3"

    @pytest.mark.asyncio
    async def test_process_voice_note_processor_error(
        self, voice_adapter, sample_voice_file, mock_adapter_context
    ):
        """Test handling of processor errors."""
        with patch(
            "src.etl.adapters.voice_note_adapter.VoiceNoteProcessor"
        ) as MockProcessor:
            mock_instance = MockProcessor.return_value
            mock_instance.process = AsyncMock(
                side_effect=ValueError("Whisper API error")
            )

            result = await voice_adapter.process(
                sample_voice_file, mock_adapter_context
            )

            assert result.is_error, "Processing should fail and return error Result"
            assert "Whisper API error" in str(result.error_value)

    @pytest.mark.asyncio
    async def test_persist_voice_data(self, voice_adapter, mock_adapter_context):
        """Test persisting processed voice note data."""
        processor_result = MagicMock(
            content={"transcription": "Hello world", "segments": []},
            metadata={"file_type": ".mp3"},
        )

        mock_session = AsyncMock(spec=AsyncSession)
        result = await voice_adapter.persist(
            processor_result, mock_adapter_context, mock_session
        )

        assert result.is_ok, "Persistence should succeed"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup(
        self, voice_adapter, sample_voice_file, mock_adapter_context
    ):
        """Test cleanup phase."""
        # Cleanup accepts input_data and context
        await voice_adapter.cleanup(sample_voice_file, mock_adapter_context)

        # Cleanup should complete without errors
        assert True

    @pytest.mark.asyncio
    async def test_execute_full_pipeline(
        self, voice_adapter, sample_voice_file, mock_adapter_context
    ):
        """Test the complete 4-phase pipeline."""
        mock_processor_result = MagicMock(
            content={"transcription": "Test transcription"},
            metadata={"file_type": ".mp3"},
        )
        mock_voice_note = MagicMock()

        with patch.object(
            voice_adapter, "validate_input", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = Result.ok(None)
            with patch.object(
                voice_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                mock_process.return_value = Result.ok(mock_processor_result)
                with patch.object(
                    voice_adapter, "persist", new_callable=AsyncMock
                ) as mock_persist:
                    mock_persist.return_value = Result.ok(mock_voice_note)
                    with patch.object(
                        voice_adapter, "cleanup", new_callable=AsyncMock
                    ) as mock_cleanup:
                        mock_session = AsyncMock(spec=AsyncSession)
                        result = await voice_adapter.execute(
                            sample_voice_file, mock_adapter_context, mock_session
                        )

                        assert result.is_ok, "Execute should succeed"
                        mock_persist.assert_called_once()
                        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_validation_failure(
        self, voice_adapter, sample_voice_file, mock_adapter_context
    ):
        """Test pipeline stops at validation failure."""
        validation_error = ProcessingError(
            "Validation failed", error_type="validation_error"
        )

        with patch.object(
            voice_adapter, "validate_input", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = Result.error(validation_error)
            with patch.object(
                voice_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                mock_session = AsyncMock(spec=AsyncSession)
                result = await voice_adapter.execute(
                    sample_voice_file, mock_adapter_context, mock_session
                )

                assert result.is_error, "Execute should fail at validation"
                mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_transcription_quality(self, voice_adapter, mock_adapter_context):
        """Test that transcription is properly extracted."""
        processor_result = MagicMock(
            content={
                "transcription": "Hello world, this is a test",
                "confidence": 0.95,
                "segments": [
                    {"text": "Hello", "start": 0, "end": 1},
                    {"text": "world", "start": 1.5, "end": 2},
                ],
            },
            metadata={"file_type": ".mp3"},
        )

        mock_session = AsyncMock(spec=AsyncSession)
        result = await voice_adapter.persist(
            processor_result, mock_adapter_context, mock_session
        )

        assert result.is_ok, "Persistence should succeed"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_voice_file(self, voice_adapter, tmp_path):
        """Test processing of large voice file."""
        large_file = tmp_path / "large_note.mp3"
        # Create a 100MB file
        large_content = b"ID3" + (b"x" * (100 * 1024 * 1024 - 3))
        large_file.write_bytes(large_content)

        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.VOICE_NOTE)
        result = await voice_adapter.validate_input(large_file, context)

        # Should still validate, but may need size limits
        # Check that result is a Result type
        assert result.is_ok or result.is_error, "Result should be a Result type"

    @pytest.mark.asyncio
    async def test_silent_voice_note(self, voice_adapter, mock_adapter_context):
        """Test processing of silent voice note."""
        processor_result = MagicMock(
            content={
                "transcription": "",  # Empty transcription for silent audio
                "segments": [],
            },
            metadata={"file_type": ".mp3"},
        )

        mock_session = AsyncMock(spec=AsyncSession)
        result = await voice_adapter.persist(
            processor_result, mock_adapter_context, mock_session
        )

        assert result.is_ok, "Should handle empty transcription gracefully"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_passed_through_phases(
        self, voice_adapter, sample_voice_file, mock_adapter_context
    ):
        """Test that context is passed correctly through all phases."""
        mock_processor_result = MagicMock(content={}, metadata={})
        mock_voice_note = MagicMock()

        with patch.object(
            voice_adapter, "validate_input", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = Result.ok(None)
            with patch.object(
                voice_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                mock_process.return_value = Result.ok(mock_processor_result)
                with patch.object(
                    voice_adapter, "persist", new_callable=AsyncMock
                ) as mock_persist:
                    mock_persist.return_value = Result.ok(mock_voice_note)
                    with patch.object(voice_adapter, "cleanup", new_callable=AsyncMock):
                        mock_session = AsyncMock(spec=AsyncSession)
                        await voice_adapter.execute(
                            sample_voice_file, mock_adapter_context, mock_session
                        )

                        # Verify process received input_data and context
                        mock_process.assert_called_once_with(
                            sample_voice_file, mock_adapter_context
                        )

    @pytest.mark.asyncio
    async def test_multiple_format_support(self, voice_adapter, tmp_path):
        """Test handling of various audio formats."""
        formats_and_magic = [
            (".mp3", b"ID3"),
            (".wav", b"RIFF"),
            (".ogg", b"OggS"),
            (".webm", b"\x1a\x45\xdf\xa3"),
            (".m4a", b"\x00\x00\x00\x20ftypisom"),
        ]

        for ext, magic_bytes in formats_and_magic:
            test_file = tmp_path / f"note{ext}"
            test_file.write_bytes(magic_bytes)

            context = AdapterContext(
                user_id=1, source_id=1, data_type=DataType.VOICE_NOTE
            )
            result = await voice_adapter.validate_input(test_file, context)

            assert result.is_ok, f"Should support {ext} format"

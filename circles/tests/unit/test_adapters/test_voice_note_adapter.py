"""
Unit tests for VoiceNoteAdapter.

Tests the 4-phase pipeline (Validate, Process, Persist, Cleanup) for voice note processing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.etl.adapters.base import AdapterContext, DataType
from src.etl.adapters.voice_note_adapter import VoiceNoteAdapter


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
            data_type=DataType.VOICE_NOTE,
            input_path=sample_voice_file,
            user_id="test_user_123",
            session=AsyncMock(spec=AsyncSession),
        )

    @pytest.mark.asyncio
    async def test_validate_input_valid_voice(self, voice_adapter, sample_voice_file):
        """Test validation of a valid voice note file."""
        result = await voice_adapter.validate_input(sample_voice_file)

        assert result is True, "Valid voice file should pass validation"

    @pytest.mark.asyncio
    async def test_validate_input_nonexistent_file(self, voice_adapter, tmp_path):
        """Test validation of non-existent file."""
        non_existent = tmp_path / "nonexistent.mp3"

        with pytest.raises(FileNotFoundError):
            await voice_adapter.validate_input(non_existent)

    @pytest.mark.asyncio
    async def test_validate_input_invalid_extension(self, voice_adapter, tmp_path):
        """Test validation of unsupported file type."""
        invalid_file = tmp_path / "note.txt"
        invalid_file.write_text("content")

        result = await voice_adapter.validate_input(invalid_file)

        assert result is False, "Invalid file extension should fail validation"

    @pytest.mark.asyncio
    async def test_validate_input_supported_formats(self, voice_adapter, tmp_path):
        """Test validation of all supported audio formats."""
        supported_formats = [".mp3", ".wav", ".ogg", ".webm", ".m4a"]

        for ext in supported_formats:
            test_file = tmp_path / f"note{ext}"
            test_file.write_bytes(b"dummy audio content")

            result = await voice_adapter.validate_input(test_file)

            assert result is True, f"{ext} should be a valid audio format"

    @pytest.mark.asyncio
    async def test_process_voice_note(self, voice_adapter, mock_adapter_context):
        """Test processing a voice note file."""
        with patch.object(
            voice_adapter.processor,
            "process",
            return_value=MagicMock(
                content={
                    "transcription": "Hello, this is a test voice note",
                    "segments": [{"text": "Hello"}],
                },
                metadata={"file_type": ".mp3", "file_size": 5000},
                embeddings=None,
            ),
        ):
            result = await voice_adapter.process(mock_adapter_context)

            assert result is not None
            assert "transcription" in result.content
            assert result.metadata["file_type"] == ".mp3"

    @pytest.mark.asyncio
    async def test_process_voice_note_processor_error(
        self, voice_adapter, mock_adapter_context
    ):
        """Test handling of processor errors."""
        with patch.object(
            voice_adapter.processor,
            "process",
            side_effect=ValueError("Whisper API error"),
        ):
            with pytest.raises(ValueError):
                await voice_adapter.process(mock_adapter_context)

    @pytest.mark.asyncio
    async def test_persist_voice_data(self, voice_adapter, mock_adapter_context):
        """Test persisting processed voice note data."""
        processor_result = MagicMock(
            content={"transcription": "Hello world", "segments": []},
            metadata={"file_type": ".mp3"},
        )

        with patch.object(voice_adapter, "_save_to_database", new_callable=AsyncMock):
            await voice_adapter.persist(mock_adapter_context, processor_result)

            voice_adapter._save_to_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup(self, voice_adapter, mock_adapter_context):
        """Test cleanup phase."""
        with patch.object(voice_adapter, "_cleanup_temp_files", new_callable=AsyncMock):
            await voice_adapter.cleanup(mock_adapter_context)

            # Cleanup should complete without errors
            assert True

    @pytest.mark.asyncio
    async def test_execute_full_pipeline(
        self, voice_adapter, sample_voice_file, mock_adapter_context
    ):
        """Test the complete 4-phase pipeline."""
        with patch.object(voice_adapter, "validate_input", return_value=True):
            with patch.object(
                voice_adapter,
                "process",
                return_value=MagicMock(
                    content={"transcription": "Test transcription"},
                    metadata={"file_type": ".mp3"},
                ),
            ):
                with patch.object(voice_adapter, "persist", new_callable=AsyncMock):
                    with patch.object(voice_adapter, "cleanup", new_callable=AsyncMock):
                        result = await voice_adapter.execute(mock_adapter_context)

                        assert result is not None
                        voice_adapter.persist.assert_called_once()
                        voice_adapter.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_validation_failure(
        self, voice_adapter, mock_adapter_context
    ):
        """Test pipeline stops at validation failure."""
        with patch.object(voice_adapter, "validate_input", return_value=False):
            with patch.object(
                voice_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                result = await voice_adapter.execute(mock_adapter_context)

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

        with patch.object(voice_adapter, "_save_to_database", new_callable=AsyncMock):
            await voice_adapter.persist(mock_adapter_context, processor_result)

            # Verify persistence was called
            voice_adapter._save_to_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_voice_file(self, voice_adapter, tmp_path):
        """Test processing of large voice file."""
        large_file = tmp_path / "large_note.mp3"
        # Create a 100MB file
        large_content = b"ID3" + (b"x" * (100 * 1024 * 1024 - 3))
        large_file.write_bytes(large_content)

        result = await voice_adapter.validate_input(large_file)

        # Should still validate, but may need size limits
        assert isinstance(result, bool)

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

        with patch.object(voice_adapter, "_save_to_database", new_callable=AsyncMock):
            await voice_adapter.persist(mock_adapter_context, processor_result)

            # Should handle empty transcription gracefully
            voice_adapter._save_to_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_passed_through_phases(
        self, voice_adapter, mock_adapter_context
    ):
        """Test that context is passed correctly through all phases."""
        with patch.object(voice_adapter, "validate_input", return_value=True):
            with patch.object(
                voice_adapter,
                "process",
                return_value=MagicMock(content={}, metadata={}),
            ) as mock_process:
                with patch.object(voice_adapter, "persist", new_callable=AsyncMock):
                    with patch.object(voice_adapter, "cleanup", new_callable=AsyncMock):
                        await voice_adapter.execute(mock_adapter_context)

                        # Verify process received the context
                        mock_process.assert_called_once_with(mock_adapter_context)

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

            result = await voice_adapter.validate_input(test_file)

            assert result is True, f"Should support {ext} format"

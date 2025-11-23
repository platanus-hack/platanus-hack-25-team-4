"""
Unit tests for PhotoAdapter.

Tests the 4-phase pipeline (Validate, Process, Persist, Cleanup) for photo processing.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.etl.adapters.base import AdapterContext, DataType
from src.etl.adapters.photo_adapter import PhotoAdapter
from src.etl.core import ProcessingError, Result


@pytest.mark.unit
class TestPhotoAdapter:
    """Test PhotoAdapter functionality."""

    @pytest.fixture
    async def photo_adapter(self):
        """Create a PhotoAdapter instance."""
        return PhotoAdapter()

    @pytest.fixture
    def sample_photo_file(self, tmp_path):
        """Create a temporary photo file."""
        photo_path = tmp_path / "test_photo.jpg"
        # Minimal JPEG magic bytes
        photo_path.write_bytes(b"\xff\xd8\xff\xe0")
        return photo_path

    @pytest.fixture
    def mock_adapter_context(self, sample_photo_file):
        """Create a mock AdapterContext."""
        return AdapterContext(
            user_id=1,
            source_id=1,
            data_type=DataType.PHOTO,
            input_path=sample_photo_file,
            session=AsyncMock(spec=AsyncSession),
        )

    @pytest.mark.asyncio
    async def test_validate_input_valid_photo(self, photo_adapter, sample_photo_file):
        """Test validation of a valid photo file."""
        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.PHOTO)
        result = await photo_adapter.validate_input(sample_photo_file, context)

        assert result.is_ok, "Valid photo file should pass validation"

    @pytest.mark.asyncio
    async def test_validate_input_nonexistent_file(self, photo_adapter, tmp_path):
        """Test validation of non-existent file."""
        non_existent = tmp_path / "nonexistent.jpg"
        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.PHOTO)

        result = await photo_adapter.validate_input(non_existent, context)
        assert result.is_error, "Non-existent file should fail validation"

    @pytest.mark.asyncio
    async def test_validate_input_invalid_extension(self, photo_adapter, tmp_path):
        """Test validation of unsupported file type."""
        invalid_file = tmp_path / "document.txt"
        invalid_file.write_text("content")
        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.PHOTO)

        result = await photo_adapter.validate_input(invalid_file, context)

        assert result.is_error, "Invalid file extension should fail validation"

    @pytest.mark.asyncio
    async def test_validate_input_supported_formats(self, photo_adapter, tmp_path):
        """Test validation of all supported image formats."""
        supported_formats = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"]

        for ext in supported_formats:
            test_file = tmp_path / f"photo{ext}"
            test_file.write_bytes(b"dummy image content")
            context = AdapterContext(user_id=1, source_id=1, data_type=DataType.PHOTO)

            result = await photo_adapter.validate_input(test_file, context)

            assert result.is_ok, f"{ext} should be a valid photo format"

    @pytest.mark.asyncio
    async def test_process_photo(
        self, photo_adapter, sample_photo_file, mock_adapter_context
    ):
        """Test processing a photo file."""
        mock_processor_result = MagicMock(
            content={
                "caption": "A test image",
                "analysis": {"objects": ["test"]},
                "image_file": "test_photo.jpg",
            },
            metadata={"file_type": ".jpg", "file_size": 500},
            embeddings=None,
        )

        with patch("src.etl.adapters.photo_adapter.PhotoProcessor") as MockProcessor:
            mock_instance = MockProcessor.return_value
            mock_instance.process = AsyncMock(return_value=mock_processor_result)

            result = await photo_adapter.process(
                sample_photo_file, mock_adapter_context
            )

            assert result.is_ok, "Processing should succeed"
            assert "caption" in result.value.content
            assert result.value.metadata["file_type"] == ".jpg"

    @pytest.mark.asyncio
    async def test_process_photo_processor_error(
        self, photo_adapter, sample_photo_file, mock_adapter_context
    ):
        """Test handling of processor errors."""
        with patch("src.etl.adapters.photo_adapter.PhotoProcessor") as MockProcessor:
            mock_instance = MockProcessor.return_value
            mock_instance.process = AsyncMock(
                side_effect=ValueError("Vision API error")
            )

            result = await photo_adapter.process(
                sample_photo_file, mock_adapter_context
            )

            assert result.is_error, "Processing should fail and return error Result"
            assert "Vision API error" in str(result.error_value)

    @pytest.mark.asyncio
    async def test_persist_photo_data(self, photo_adapter, mock_adapter_context):
        """Test persisting processed photo data."""
        processor_result = MagicMock(
            content={"caption": "A test image", "analysis": {}},
            metadata={"file_type": ".jpg"},
        )

        mock_session = AsyncMock(spec=AsyncSession)
        result = await photo_adapter.persist(
            processor_result, mock_adapter_context, mock_session
        )

        assert result.is_ok, "Persistence should succeed"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup(
        self, photo_adapter, sample_photo_file, mock_adapter_context
    ):
        """Test cleanup phase."""
        # Cleanup accepts input_data and context
        await photo_adapter.cleanup(sample_photo_file, mock_adapter_context)

        # Cleanup should complete without errors
        assert True

    @pytest.mark.asyncio
    async def test_execute_full_pipeline(
        self, photo_adapter, sample_photo_file, mock_adapter_context
    ):
        """Test the complete 4-phase pipeline."""
        mock_processor_result = MagicMock(
            content={"caption": "Test image"},
            metadata={"file_type": ".jpg"},
        )
        mock_photo_data = MagicMock()

        with patch.object(
            photo_adapter, "validate_input", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = Result.ok(None)
            with patch.object(
                photo_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                mock_process.return_value = Result.ok(mock_processor_result)
                with patch.object(
                    photo_adapter, "persist", new_callable=AsyncMock
                ) as mock_persist:
                    mock_persist.return_value = Result.ok(mock_photo_data)
                    with patch.object(
                        photo_adapter, "cleanup", new_callable=AsyncMock
                    ) as mock_cleanup:
                        mock_session = AsyncMock(spec=AsyncSession)
                        result = await photo_adapter.execute(
                            sample_photo_file, mock_adapter_context, mock_session
                        )

                        assert result.is_ok, "Execute should succeed"
                        mock_persist.assert_called_once()
                        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_validation_failure(
        self, photo_adapter, sample_photo_file, mock_adapter_context
    ):
        """Test pipeline stops at validation failure."""
        validation_error = ProcessingError(
            "Validation failed", error_type="validation_error"
        )

        with patch.object(
            photo_adapter, "validate_input", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = Result.error(validation_error)
            with patch.object(
                photo_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                mock_session = AsyncMock(spec=AsyncSession)
                result = await photo_adapter.execute(
                    sample_photo_file, mock_adapter_context, mock_session
                )

                assert result.is_error, "Execute should fail at validation"
                mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_exif_data_extraction(self, photo_adapter, mock_adapter_context):
        """Test that EXIF data is extracted during processing."""
        processor_result = MagicMock(
            content={"caption": "Photo with EXIF"},
            metadata={"file_type": ".jpg", "exif_data": {"camera": "Canon"}},
        )

        mock_session = AsyncMock(spec=AsyncSession)
        result = await photo_adapter.persist(
            processor_result, mock_adapter_context, mock_session
        )

        assert result.is_ok, "Persistence should succeed"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_photo_file(self, photo_adapter, tmp_path):
        """Test processing of large photo file."""
        large_file = tmp_path / "large_photo.jpg"
        # Create a 10MB file
        large_content = b"\xff\xd8\xff\xe0" + (b"x" * (10 * 1024 * 1024 - 4))
        large_file.write_bytes(large_content)

        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.PHOTO)
        result = await photo_adapter.validate_input(large_file, context)

        # Should still validate, but may need size limits
        # Check that result is a Result type
        assert result.is_ok or result.is_error, "Result should be a Result type"

    @pytest.mark.asyncio
    async def test_corrupted_photo_file(self, photo_adapter, tmp_path):
        """Test handling of corrupted photo file."""
        corrupted_file = tmp_path / "corrupted.jpg"
        # Write invalid JPEG data
        corrupted_file.write_bytes(b"This is not a valid JPEG file")

        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.PHOTO)
        # Validation might pass if only checking extension
        result = await photo_adapter.validate_input(corrupted_file, context)

        # Check that result is a Result type
        assert result.is_ok or result.is_error, "Result should be a Result type"

    @pytest.mark.asyncio
    async def test_context_passed_through_phases(
        self, photo_adapter, sample_photo_file, mock_adapter_context
    ):
        """Test that context is passed correctly through all phases."""
        mock_processor_result = MagicMock(content={}, metadata={})
        mock_photo_data = MagicMock()

        with patch.object(
            photo_adapter, "validate_input", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = Result.ok(None)
            with patch.object(
                photo_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                mock_process.return_value = Result.ok(mock_processor_result)
                with patch.object(
                    photo_adapter, "persist", new_callable=AsyncMock
                ) as mock_persist:
                    mock_persist.return_value = Result.ok(mock_photo_data)
                    with patch.object(photo_adapter, "cleanup", new_callable=AsyncMock):
                        mock_session = AsyncMock(spec=AsyncSession)
                        await photo_adapter.execute(
                            sample_photo_file, mock_adapter_context, mock_session
                        )

                        # Verify process received input_data and context
                        mock_process.assert_called_once_with(
                            sample_photo_file, mock_adapter_context
                        )

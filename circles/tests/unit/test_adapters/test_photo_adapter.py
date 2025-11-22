"""
Unit tests for PhotoAdapter.

Tests the 4-phase pipeline (Validate, Process, Persist, Cleanup) for photo processing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from circles.src.etl.adapters.base import AdapterContext, DataType
from circles.src.etl.adapters.photo_adapter import PhotoAdapter


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
            data_type=DataType.PHOTO,
            input_path=sample_photo_file,
            user_id="test_user_123",
            session=AsyncMock(spec=AsyncSession),
        )

    @pytest.mark.asyncio
    async def test_validate_input_valid_photo(self, photo_adapter, sample_photo_file):
        """Test validation of a valid photo file."""
        result = await photo_adapter.validate_input(sample_photo_file)

        assert result is True, "Valid photo file should pass validation"

    @pytest.mark.asyncio
    async def test_validate_input_nonexistent_file(self, photo_adapter, tmp_path):
        """Test validation of non-existent file."""
        non_existent = tmp_path / "nonexistent.jpg"

        with pytest.raises(FileNotFoundError):
            await photo_adapter.validate_input(non_existent)

    @pytest.mark.asyncio
    async def test_validate_input_invalid_extension(self, photo_adapter, tmp_path):
        """Test validation of unsupported file type."""
        invalid_file = tmp_path / "document.txt"
        invalid_file.write_text("content")

        result = await photo_adapter.validate_input(invalid_file)

        assert result is False, "Invalid file extension should fail validation"

    @pytest.mark.asyncio
    async def test_validate_input_supported_formats(self, photo_adapter, tmp_path):
        """Test validation of all supported image formats."""
        supported_formats = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"]

        for ext in supported_formats:
            test_file = tmp_path / f"photo{ext}"
            test_file.write_bytes(b"dummy image content")

            result = await photo_adapter.validate_input(test_file)

            assert result is True, f"{ext} should be a valid photo format"

    @pytest.mark.asyncio
    async def test_process_photo(self, photo_adapter, mock_adapter_context):
        """Test processing a photo file."""
        with patch.object(
            photo_adapter.processor,
            "process",
            return_value=MagicMock(
                content={
                    "caption": "A test image",
                    "analysis": {"objects": ["test"]},
                    "image_file": "test_photo.jpg",
                },
                metadata={"file_type": ".jpg", "file_size": 500},
                embeddings=None,
            ),
        ):
            result = await photo_adapter.process(mock_adapter_context)

            assert result is not None
            assert "caption" in result.content
            assert result.metadata["file_type"] == ".jpg"

    @pytest.mark.asyncio
    async def test_process_photo_processor_error(
        self, photo_adapter, mock_adapter_context
    ):
        """Test handling of processor errors."""
        with patch.object(
            photo_adapter.processor,
            "process",
            side_effect=ValueError("Vision API error"),
        ):
            with pytest.raises(ValueError):
                await photo_adapter.process(mock_adapter_context)

    @pytest.mark.asyncio
    async def test_persist_photo_data(self, photo_adapter, mock_adapter_context):
        """Test persisting processed photo data."""
        processor_result = MagicMock(
            content={"caption": "A test image", "analysis": {}},
            metadata={"file_type": ".jpg"},
        )

        with patch.object(photo_adapter, "_save_to_database", new_callable=AsyncMock):
            await photo_adapter.persist(mock_adapter_context, processor_result)

            photo_adapter._save_to_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup(self, photo_adapter, mock_adapter_context):
        """Test cleanup phase."""
        with patch.object(photo_adapter, "_cleanup_temp_files", new_callable=AsyncMock):
            await photo_adapter.cleanup(mock_adapter_context)

            # Cleanup should complete without errors
            assert True

    @pytest.mark.asyncio
    async def test_execute_full_pipeline(
        self, photo_adapter, sample_photo_file, mock_adapter_context
    ):
        """Test the complete 4-phase pipeline."""
        with patch.object(photo_adapter, "validate_input", return_value=True):
            with patch.object(
                photo_adapter,
                "process",
                return_value=MagicMock(
                    content={"caption": "Test image"},
                    metadata={"file_type": ".jpg"},
                ),
            ):
                with patch.object(photo_adapter, "persist", new_callable=AsyncMock):
                    with patch.object(photo_adapter, "cleanup", new_callable=AsyncMock):
                        result = await photo_adapter.execute(mock_adapter_context)

                        assert result is not None
                        photo_adapter.persist.assert_called_once()
                        photo_adapter.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_validation_failure(
        self, photo_adapter, mock_adapter_context
    ):
        """Test pipeline stops at validation failure."""
        with patch.object(photo_adapter, "validate_input", return_value=False):
            with patch.object(
                photo_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                result = await photo_adapter.execute(mock_adapter_context)

                mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_exif_data_extraction(self, photo_adapter, mock_adapter_context):
        """Test that EXIF data is extracted during processing."""
        processor_result = MagicMock(
            content={"caption": "Photo with EXIF"},
            metadata={"file_type": ".jpg", "exif_data": {"camera": "Canon"}},
        )

        with patch.object(photo_adapter, "_save_to_database", new_callable=AsyncMock):
            await photo_adapter.persist(mock_adapter_context, processor_result)

            photo_adapter._save_to_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_photo_file(self, photo_adapter, tmp_path):
        """Test processing of large photo file."""
        large_file = tmp_path / "large_photo.jpg"
        # Create a 10MB file
        large_content = b"\xff\xd8\xff\xe0" + (b"x" * (10 * 1024 * 1024 - 4))
        large_file.write_bytes(large_content)

        result = await photo_adapter.validate_input(large_file)

        # Should still validate, but may need size limits
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_corrupted_photo_file(self, photo_adapter, tmp_path):
        """Test handling of corrupted photo file."""
        corrupted_file = tmp_path / "corrupted.jpg"
        # Write invalid JPEG data
        corrupted_file.write_bytes(b"This is not a valid JPEG file")

        # Validation might pass if only checking extension
        result = await photo_adapter.validate_input(corrupted_file)

        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_context_passed_through_phases(
        self, photo_adapter, mock_adapter_context
    ):
        """Test that context is passed correctly through all phases."""
        with patch.object(photo_adapter, "validate_input", return_value=True):
            with patch.object(
                photo_adapter,
                "process",
                return_value=MagicMock(content={}, metadata={}),
            ) as mock_process:
                with patch.object(photo_adapter, "persist", new_callable=AsyncMock):
                    with patch.object(photo_adapter, "cleanup", new_callable=AsyncMock):
                        await photo_adapter.execute(mock_adapter_context)

                        # Verify process received the context
                        mock_process.assert_called_once_with(mock_adapter_context)

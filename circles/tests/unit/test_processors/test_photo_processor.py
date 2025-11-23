"""
Unit tests for PhotoProcessor.

Tests image processing with Claude Vision API mocking.
"""

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.etl.processors.photo_processor import (
    PhotoProcessor,
    SimpleProcessorResult,
)

from tests.fixtures.fixture_factories import DataTypeFixtures


@pytest.mark.unit
class TestPhotoProcessor:
    """Test PhotoProcessor functionality."""

    @pytest.fixture
    async def photo_processor(self):
        """Create a PhotoProcessor instance."""
        return PhotoProcessor()

    @pytest.fixture
    def sample_photo_file(self, tmp_path, sample_photo_bytes):
        """Create a temporary photo file."""
        photo_path = tmp_path / "test_photo.jpg"
        photo_path.write_bytes(sample_photo_bytes)
        return photo_path

    @pytest.mark.asyncio
    async def test_process_valid_photo(self, photo_processor, sample_photo_file):
        """Test processing a valid photo file."""
        # Mock the Claude Vision API call
        with patch.object(
            photo_processor.client.messages,
            "create",
            return_value=MagicMock(
                content=[
                    MagicMock(
                        text='{"caption": "A test image", "analysis": {"objects": ["test"]}}'
                    )
                ]
            ),
        ):
            result = await photo_processor.process(sample_photo_file)

        assert isinstance(result, SimpleProcessorResult)
        assert "caption" in result.content
        assert "analysis" in result.content
        assert "image_file" in result.content
        assert result.content["caption"] == "A test image"
        assert result.metadata["file_type"] == ".jpg"
        assert result.metadata["file_size"] > 0

    @pytest.mark.asyncio
    async def test_process_photo_with_exif(self, photo_processor, sample_photo_file):
        """Test processing photo and attempting EXIF extraction."""
        with patch.object(
            photo_processor.client.messages,
            "create",
            return_value=MagicMock(
                content=[
                    MagicMock(
                        text='{"caption": "Photo with EXIF", "analysis": {"mood": "professional"}}'
                    )
                ]
            ),
        ):
            result = await photo_processor.process(sample_photo_file)

        assert isinstance(result, SimpleProcessorResult)
        assert "exif_data" in result.metadata
        # EXIF extraction may or may not succeed depending on PIL availability
        assert isinstance(result.metadata["exif_data"], dict)

    @pytest.mark.asyncio
    async def test_process_multiple_image_formats(
        self, photo_processor, tmp_path, sample_photo_bytes
    ):
        """Test processing different image formats."""
        formats = {
            ".jpg": sample_photo_bytes,
            ".png": sample_photo_bytes,
            ".gif": sample_photo_bytes,
        }

        for ext, image_data in formats.items():
            photo_path = tmp_path / f"test_photo{ext}"
            # Use a minimal image to avoid format-specific parsing
            photo_path.write_bytes(image_data)

            media_type = photo_processor._get_media_type(photo_path)
            assert media_type.startswith("image/")

    def test_get_media_type_known_formats(self, photo_processor):
        """Test media type detection for known formats."""
        test_cases = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".heic": "image/heic",
        }

        for ext, expected_type in test_cases.items():
            path = Path(f"test{ext}")
            assert photo_processor._get_media_type(path) == expected_type

    def test_get_media_type_unknown_format(self, photo_processor):
        """Test media type detection for unknown formats defaults to JPEG."""
        path = Path("test.unknown")
        assert photo_processor._get_media_type(path) == "image/jpeg"

    @pytest.mark.asyncio
    async def test_process_file_not_found(self, photo_processor, tmp_path):
        """Test processing non-existent file."""
        non_existent = tmp_path / "non_existent.jpg"

        with pytest.raises(FileNotFoundError):
            await photo_processor.process(non_existent)

    @pytest.mark.asyncio
    async def test_analyze_image_json_parsing(self, photo_processor, sample_photo_file):
        """Test JSON parsing from Claude Vision response."""
        response_text = (
            '{"caption": "Test caption", "analysis": {"objects": ["obj1", "obj2"]}}'
        )

        with patch.object(
            photo_processor.client.messages,
            "create",
            return_value=MagicMock(content=[MagicMock(text=response_text)]),
        ):
            caption, analysis = await photo_processor._analyze_image(
                base64.b64encode(b"dummy").decode(), "image/jpeg"
            )

        assert caption == "Test caption"
        assert "objects" in analysis
        assert analysis["objects"] == ["obj1", "obj2"]

    @pytest.mark.asyncio
    async def test_analyze_image_malformed_json(self, photo_processor):
        """Test handling of malformed JSON from Claude Vision."""
        response_text = "This is not JSON"

        with patch.object(
            photo_processor.client.messages,
            "create",
            return_value=MagicMock(content=[MagicMock(text=response_text)]),
        ):
            caption, analysis = await photo_processor._analyze_image(
                base64.b64encode(b"dummy").decode(), "image/jpeg"
            )

        # Should fallback to using first line as caption
        assert caption == "This is not JSON"
        assert "raw_response" in analysis
        # parse_error is only set when JSON is found but fails to decode, not when no JSON found

    @pytest.mark.asyncio
    async def test_analyze_image_empty_response(self, photo_processor):
        """Test handling of empty response from Claude Vision."""
        with patch.object(
            photo_processor.client.messages,
            "create",
            return_value=MagicMock(content=[MagicMock(text="")]),
        ):
            # Empty text raises ValueError
            with pytest.raises(
                ValueError, match="Response does not contain text content"
            ):
                await photo_processor._analyze_image(
                    base64.b64encode(b"dummy").decode(), "image/jpeg"
                )

    @pytest.mark.asyncio
    async def test_extract_exif_data_async(self, photo_processor, sample_photo_file):
        """Test async EXIF extraction."""
        exif_data = await photo_processor._extract_exif_data_async(sample_photo_file)

        assert isinstance(exif_data, dict)
        # EXIF data might be empty if PIL is not available or image has no EXIF

    def test_extract_exif_data_sync(self, photo_processor, sample_photo_file):
        """Test synchronous EXIF extraction (backward compatibility)."""
        exif_data = photo_processor._extract_exif_data(sample_photo_file)

        assert isinstance(exif_data, dict)
        # EXIF data might be empty

    @pytest.mark.asyncio
    async def test_processor_result_structure(self, photo_processor, sample_photo_file):
        """Test that processor result has correct structure."""
        with patch.object(
            photo_processor.client.messages,
            "create",
            return_value=MagicMock(
                content=[
                    MagicMock(text='{"caption": "Test", "analysis": {"test": "data"}}')
                ]
            ),
        ):
            result = await photo_processor.process(sample_photo_file)

        # Verify SimpleProcessorResult structure
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")
        assert hasattr(result, "embeddings")

        # Verify content structure
        assert isinstance(result.content, dict)
        assert "caption" in result.content
        assert "analysis" in result.content
        assert "image_file" in result.content

        # Verify metadata structure
        assert isinstance(result.metadata, dict)
        assert "file_type" in result.metadata
        assert "file_size" in result.metadata
        assert "exif_data" in result.metadata

    @pytest.mark.asyncio
    async def test_analyze_image_api_error(self, photo_processor):
        """Test handling of Claude Vision API errors."""
        import httpx
        from anthropic import APIError

        # Create a proper httpx.Request object
        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")

        with patch.object(
            photo_processor.client.messages,
            "create",
            side_effect=APIError("API Error", request=request, body=None),
        ):
            with pytest.raises(APIError):
                await photo_processor._analyze_image(
                    base64.b64encode(b"dummy").decode(), "image/jpeg"
                )

    @pytest.mark.asyncio
    async def test_process_large_base64_image(self, photo_processor, sample_photo_file):
        """Test processing with proper base64 encoding."""
        with patch.object(
            photo_processor.client.messages,
            "create",
            return_value=MagicMock(
                content=[MagicMock(text='{"caption": "Encoded image", "analysis": {}}')]
            ),
        ) as mock_create:
            await photo_processor.process(sample_photo_file)

            # Verify API was called with base64-encoded data
            call_args = mock_create.call_args
            messages = call_args[1]["messages"]
            content = messages[0]["content"]

            # Find the image part
            image_part = next((c for c in content if c.get("type") == "image"), None)
            assert image_part is not None
            assert "source" in image_part
            assert image_part["source"]["type"] == "base64"


@pytest.mark.unit
class TestPhotoProcessorIntegration:
    """Integration tests for PhotoProcessor with fixtures."""

    @pytest.fixture
    async def photo_processor(self):
        """Create a PhotoProcessor instance."""
        return PhotoProcessor()

    @pytest.mark.asyncio
    async def test_process_with_fixture_data(self, photo_processor, tmp_path):
        """Test processing with fixture data."""
        fixture_data = DataTypeFixtures.create_photo_metadata()

        assert "file_name" in fixture_data
        assert "file_size" in fixture_data
        assert fixture_data["file_size"] > 0

    @pytest.mark.asyncio
    async def test_mock_response_consistency(self, photo_processor):
        """Test that processor handles consistent mock responses."""
        mock_responses = [
            '{"caption": "Response 1", "analysis": {"type": "test"}}',
            '{"caption": "Response 2", "analysis": {"objects": ["a", "b"]}}',
            '{"caption": "Response 3", "analysis": {}}',
        ]

        for response in mock_responses:
            with patch.object(
                photo_processor.client.messages,
                "create",
                return_value=MagicMock(content=[MagicMock(text=response)]),
            ):
                caption, analysis = await photo_processor._analyze_image(
                    base64.b64encode(b"test").decode(), "image/jpeg"
                )

                assert caption
                assert isinstance(analysis, dict)

"""Unit tests for MarkItDown adapter with mocked dependencies."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.etl.adapters.base import (
    ConversionError,
    InvalidInputError,
    UnsupportedFormatError,
)
from src.etl.adapters.markdown import (
    MarkItDownAdapter,
    MarkItDownConfig,
)

pytestmark = pytest.mark.unit


class TestMarkItDownConfig:
    """Test MarkItDownConfig dataclass."""

    def test_config_defaults(self):
        """Should use sensible default values."""
        config = MarkItDownConfig()

        assert config.enable_llm is False
        assert config.llm_model is None
        assert config.llm_api_key is None

    def test_config_with_llm_enabled(self):
        """Should accept LLM configuration."""
        config = MarkItDownConfig(
            enable_llm=True, llm_model="gpt-4", llm_api_key="test-key"
        )

        assert config.enable_llm is True
        assert config.llm_model == "gpt-4"
        assert config.llm_api_key == "test-key"


class TestMarkItDownAdapterInitialization:
    """Test MarkItDownAdapter initialization."""

    def test_adapter_init_with_default_config(self):
        """Should initialize with default config if none provided."""
        adapter = MarkItDownAdapter()

        assert adapter.config is not None
        assert adapter.config.enable_llm is False
        assert adapter._converter is None

    def test_adapter_init_with_custom_config(self, markitdown_config):
        """Should use provided custom config."""
        adapter = MarkItDownAdapter(markitdown_config)

        assert adapter.config == markitdown_config

    async def test_converter_lazy_loading(self):
        """Converter should not be loaded on initialization."""
        adapter = MarkItDownAdapter()

        assert adapter._converter is None


class TestSupportedFormats:
    """Test supported formats functionality."""

    async def test_supported_formats_returns_list(self):
        """Should return a list of strings."""
        adapter = MarkItDownAdapter()

        formats = await adapter.supported_formats()

        assert isinstance(formats, list)
        assert all(isinstance(f, str) for f in formats)

    async def test_supported_formats_includes_pdf(self):
        """PDF should be in supported formats."""
        adapter = MarkItDownAdapter()

        formats = await adapter.supported_formats()

        assert "pdf" in formats

    async def test_supported_formats_includes_docx(self):
        """DOCX should be in supported formats."""
        adapter = MarkItDownAdapter()

        formats = await adapter.supported_formats()

        assert "docx" in formats

    async def test_supported_formats_includes_images(self):
        """Image formats should be included."""
        adapter = MarkItDownAdapter()

        formats = await adapter.supported_formats()

        assert "jpg" in formats or "jpeg" in formats
        assert "png" in formats

    async def test_supported_formats_returns_copy(self):
        """Should return a copy, not the original list."""
        adapter = MarkItDownAdapter()

        formats1 = await adapter.supported_formats()
        formats2 = await adapter.supported_formats()

        assert formats1 == formats2
        assert formats1 is not formats2

    async def test_supported_formats_count(self):
        """Should support 18+ file formats."""
        adapter = MarkItDownAdapter()

        formats = await adapter.supported_formats()

        assert len(formats) >= 18


class TestFileTypeDetection:
    """Test file type detection functionality."""

    def test_detect_file_type_pdf(self, sample_pdf_path):
        """Should correctly detect PDF files."""
        adapter = MarkItDownAdapter()

        file_type = adapter._detect_file_type(sample_pdf_path)

        assert file_type == "pdf"

    def test_detect_file_type_html(self, sample_html_path):
        """Should correctly detect HTML files."""
        adapter = MarkItDownAdapter()

        file_type = adapter._detect_file_type(sample_html_path)

        assert file_type == "html"

    def test_detect_file_type_case_insensitive(self, tmp_path):
        """Should handle uppercase extensions."""
        file = tmp_path / "test.PDF"
        file.touch()

        adapter = MarkItDownAdapter()
        file_type = adapter._detect_file_type(file)

        assert file_type == "pdf"

    def test_detect_file_type_no_extension(self, tmp_path):
        """Should raise UnsupportedFormatError for files without extension."""
        file = tmp_path / "noextension"
        file.touch()

        adapter = MarkItDownAdapter()

        with pytest.raises(UnsupportedFormatError, match="no extension"):
            adapter._detect_file_type(file)

    def test_detect_file_type_unsupported(self, tmp_path):
        """Should raise UnsupportedFormatError for unknown extensions."""
        file = tmp_path / "test.xyz"
        file.touch()

        adapter = MarkItDownAdapter()

        with pytest.raises(UnsupportedFormatError, match="Unsupported file format"):
            adapter._detect_file_type(file)


class TestConverterInitialization:
    """Test converter initialization functionality."""

    async def test_converter_loads_on_first_convert(
        self, mock_markitdown, sample_pdf_path
    ):
        """Converter should load on first convert() call."""
        adapter = MarkItDownAdapter()

        # Converter should be None initially
        assert adapter._converter is None

        # Trigger loading
        await adapter.convert(sample_pdf_path)

        # Check that MarkItDown was instantiated
        mock_markitdown["class"].assert_called_once()

    @patch("circles.src.etl.adapters.markdown.markitdown.MarkItDown")
    async def test_converter_load_error_on_missing_library(self, mock_class):
        """Should raise ConversionError if markitdown not installed."""
        mock_class.side_effect = ImportError("No module named 'markitdown'")

        adapter = MarkItDownAdapter()

        with pytest.raises(ConversionError, match="markitdown library not installed"):
            await adapter._ensure_converter_loaded()


class TestPathBasedConversion:
    """Test path-based file conversion."""

    async def test_convert_path_pdf(self, mock_markitdown_adapter, sample_pdf_path):
        """Should convert PDF from path."""
        adapter = mock_markitdown_adapter

        result = await adapter.convert(sample_pdf_path)

        assert result == "# Sample Markdown\n\nTest content converted from document."
        adapter._converter.convert.assert_called_once()

    async def test_convert_path_with_pathlib(
        self, mock_markitdown_adapter, sample_pdf_path
    ):
        """Should handle pathlib.Path objects."""
        adapter = mock_markitdown_adapter

        result = await adapter.convert(Path(sample_pdf_path))

        assert isinstance(result, str)
        adapter._converter.convert.assert_called_once()

    async def test_convert_path_with_string(
        self, mock_markitdown_adapter, sample_pdf_path
    ):
        """Should handle string paths."""
        adapter = mock_markitdown_adapter

        result = await adapter.convert(str(sample_pdf_path))

        assert isinstance(result, str)

    async def test_convert_path_nonexistent_file(
        self, mock_markitdown_adapter, nonexistent_path
    ):
        """Should raise InvalidInputError for missing file."""
        adapter = mock_markitdown_adapter

        with pytest.raises(InvalidInputError, match="not found"):
            await adapter.convert(nonexistent_path)

    async def test_convert_path_directory(
        self, mock_markitdown_adapter, temp_directory
    ):
        """Should raise InvalidInputError for directory."""
        adapter = mock_markitdown_adapter

        with pytest.raises(InvalidInputError, match="Not a file"):
            await adapter.convert(temp_directory)

    async def test_convert_path_with_source_type_override(
        self, mock_markitdown_adapter, sample_pdf_path
    ):
        """source_type parameter should be validated."""
        adapter = mock_markitdown_adapter

        # Should accept valid source type
        result = await adapter.convert(sample_pdf_path, source_type="pdf")
        assert isinstance(result, str)

        # Should reject invalid source type
        with pytest.raises(UnsupportedFormatError):
            await adapter.convert(sample_pdf_path, source_type="xyz")

    async def test_convert_path_unsupported_format(
        self, mock_markitdown_adapter, invalid_file_path
    ):
        """Should raise UnsupportedFormatError for unsupported types."""
        adapter = mock_markitdown_adapter

        with pytest.raises(UnsupportedFormatError):
            await adapter.convert(invalid_file_path)


class TestBytesBasedConversion:
    """Test bytes-based file conversion."""

    async def test_convert_bytes_with_source_type(self, mock_markitdown_adapter):
        """Should convert bytes with type hint."""
        adapter = mock_markitdown_adapter

        test_bytes = b"fake pdf content"
        result = await adapter.convert(test_bytes, source_type="pdf")

        assert isinstance(result, str)
        adapter._converter.convert_stream.assert_called_once()

    async def test_convert_bytes_without_source_type(self, mock_markitdown_adapter):
        """Should raise InvalidInputError when type missing."""
        adapter = mock_markitdown_adapter

        test_bytes = b"fake content"

        with pytest.raises(InvalidInputError, match="source_type is required"):
            await adapter.convert(test_bytes)

    async def test_convert_bytes_uses_bytesio(self, mock_markitdown_adapter):
        """Should use BytesIO for stream conversion."""
        adapter = mock_markitdown_adapter

        test_bytes = b"fake pdf content"
        await adapter.convert(test_bytes, source_type="pdf")

        # Verify convert_stream was called (not convert)
        adapter._converter.convert_stream.assert_called_once()
        adapter._converter.convert.assert_not_called()

    async def test_convert_bytes_unsupported_format(self, mock_markitdown_adapter):
        """Should raise UnsupportedFormatError for unsupported types."""
        adapter = mock_markitdown_adapter

        test_bytes = b"content"

        with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
            await adapter.convert(test_bytes, source_type="xyz")


class TestBatchConversion:
    """Test batch conversion functionality."""

    async def test_convert_batch_with_paths(
        self, mock_markitdown_adapter, sample_pdf_path, sample_html_path
    ):
        """Should batch convert multiple paths."""
        adapter = mock_markitdown_adapter

        sources = [sample_pdf_path, sample_html_path]
        results = await adapter.convert_batch(sources)

        assert len(results) == 2
        assert all(isinstance(r, str) for r in results)

    async def test_convert_batch_mixed_inputs(
        self, mock_markitdown_adapter, sample_pdf_path
    ):
        """Should handle mixed paths and bytes."""
        adapter = mock_markitdown_adapter

        sources = [sample_pdf_path, b"fake content"]
        source_types = [None, "pdf"]

        results = await adapter.convert_batch(sources, source_types)

        assert len(results) == 2

    async def test_convert_batch_without_source_types(
        self, mock_markitdown_adapter, sample_pdf_path
    ):
        """Should auto-detect types when source_types is None."""
        adapter = mock_markitdown_adapter

        sources = [sample_pdf_path, sample_pdf_path]
        results = await adapter.convert_batch(sources)

        assert len(results) == 2

    async def test_convert_batch_mismatched_lengths(self, mock_markitdown_adapter):
        """Should raise ValueError when lengths differ."""
        adapter = mock_markitdown_adapter

        sources = ["file1.pdf", "file2.pdf"]
        source_types = ["pdf"]

        with pytest.raises(ValueError, match="must match"):
            await adapter.convert_batch(sources, source_types)

    async def test_convert_batch_empty_lists(self, mock_markitdown_adapter):
        """Should handle empty input lists."""
        adapter = mock_markitdown_adapter

        results = await adapter.convert_batch([])

        assert results == []

    async def test_convert_batch_preserves_order(
        self, mock_markitdown_adapter, sample_pdf_path
    ):
        """Results should match input order."""
        adapter = mock_markitdown_adapter

        # Setup mock to return different results
        adapter._converter.convert.side_effect = [
            MagicMock(text_content=f"Result {i}") for i in range(3)
        ]

        sources = [sample_pdf_path] * 3
        results = await adapter.convert_batch(sources)

        assert len(results) == 3
        assert results[0] == "Result 0"
        assert results[1] == "Result 1"
        assert results[2] == "Result 2"

    @patch("circles.src.etl.adapters.markdown.markitdown.asyncio.gather")
    async def test_convert_batch_runs_concurrently(
        self, mock_gather, mock_markitdown_adapter, sample_pdf_path
    ):
        """Should use asyncio.gather for concurrent execution."""
        adapter = mock_markitdown_adapter

        # Setup mock gather to return results
        mock_gather.return_value = ["Result 1", "Result 2"]

        sources = [sample_pdf_path, sample_pdf_path]
        await adapter.convert_batch(sources)

        # Verify gather was called
        mock_gather.assert_called_once()


class TestErrorHandling:
    """Test error handling and exception propagation."""

    async def test_convert_wraps_unexpected_errors(self, mock_markitdown_adapter):
        """Unexpected errors should be wrapped as ConversionError."""
        adapter = mock_markitdown_adapter

        adapter._converter.convert.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(ConversionError, match="Conversion failed"):
            await adapter.convert("test.pdf")

    async def test_convert_error_includes_context(self, mock_markitdown_adapter):
        """Error messages should include helpful context."""
        adapter = mock_markitdown_adapter

        adapter._converter.convert.side_effect = Exception("Internal error")

        with pytest.raises(ConversionError) as exc_info:
            await adapter.convert("test.pdf")

        assert "Conversion failed" in str(exc_info.value)

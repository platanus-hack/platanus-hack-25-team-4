"""Integration tests for MarkItDown adapter with real library.

These tests use the real markitdown library and are slower. They are marked with
@pytest.mark.slow and @pytest.mark.integration and can be skipped with: pytest -m "not slow"
"""

import pytest
from src.etl.adapters.markdown import MarkItDownAdapter

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestMarkItDownRealConversion:
    """Integration tests using real markitdown library."""

    async def test_real_pdf_conversion(self, sample_pdf_path):
        """Should convert real PDF to markdown."""
        adapter = MarkItDownAdapter()

        result = await adapter.convert(sample_pdf_path)

        assert isinstance(result, str)
        assert len(result) > 0
        # PDF should contain some of our test content
        assert "Sample PDF Document" in result or "sample" in result.lower()

    async def test_real_html_conversion(self, sample_html_path):
        """Should convert real HTML to markdown."""
        adapter = MarkItDownAdapter()

        result = await adapter.convert(sample_html_path)

        assert isinstance(result, str)
        assert len(result) > 0
        # HTML should be converted to markdown
        assert "Sample HTML Document" in result or "#" in result

    async def test_real_conversion_output_format(self, sample_pdf_path):
        """Converted markdown should be valid."""
        adapter = MarkItDownAdapter()

        result = await adapter.convert(sample_pdf_path)

        # Basic markdown validation
        assert isinstance(result, str)
        assert result.strip()  # Not empty or just whitespace
        # Should contain text content
        assert any(c.isalnum() for c in result)

    async def test_real_batch_conversion(self, sample_pdf_path, sample_html_path):
        """Should handle batch conversion with real files."""
        adapter = MarkItDownAdapter()

        sources = [sample_pdf_path, sample_html_path]
        results = await adapter.convert_batch(sources)

        assert len(results) == 2
        assert all(isinstance(r, str) for r in results)
        assert all(len(r) > 0 for r in results)

    async def test_supported_formats_comprehensive(self):
        """Should return all supported formats."""
        adapter = MarkItDownAdapter()

        formats = await adapter.supported_formats()

        # Check for key formats
        assert "pdf" in formats
        assert "docx" in formats or "doc" in formats
        assert "html" in formats or "htm" in formats
        assert "xlsx" in formats or "xls" in formats
        # Images
        assert "jpg" in formats or "jpeg" in formats
        assert "png" in formats

    async def test_conversion_with_bytes(self, sample_pdf_path):
        """Should convert from bytes input."""
        adapter = MarkItDownAdapter()

        # Read PDF as bytes
        with open(sample_pdf_path, "rb") as f:
            pdf_bytes = f.read()

        result = await adapter.convert(pdf_bytes, source_type="pdf")

        assert isinstance(result, str)
        assert len(result) > 0

    async def test_concurrent_conversions(self, sample_pdf_path, sample_html_path):
        """Should handle concurrent conversion requests."""
        adapter = MarkItDownAdapter()

        # Run multiple conversions concurrently
        import asyncio

        tasks = [
            adapter.convert(sample_pdf_path),
            adapter.convert(sample_html_path),
            adapter.convert(sample_pdf_path),
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(isinstance(r, str) for r in results)
        assert all(len(r) > 0 for r in results)

    async def test_error_handling_with_invalid_file(self, invalid_file_path):
        """Should properly handle conversion errors."""
        adapter = MarkItDownAdapter()

        # This should raise an appropriate error
        with pytest.raises(Exception):  # Could be UnsupportedFormatError or others
            await adapter.convert(invalid_file_path)

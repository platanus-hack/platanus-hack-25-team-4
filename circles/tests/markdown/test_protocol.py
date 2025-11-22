"""Protocol compliance tests for Markdown converters."""

import inspect

from src.etl.adapters.markdown import MarkItDownAdapter


class TestMarkItDownProtocolCompliance:
    """Test that MarkItDownAdapter conforms to MarkdownConverter protocol."""

    def test_markitdown_has_convert_method(self):
        """MarkItDownAdapter should have a convert method."""
        assert hasattr(MarkItDownAdapter, "convert")
        assert callable(getattr(MarkItDownAdapter, "convert"))

    def test_markitdown_has_convert_batch_method(self):
        """MarkItDownAdapter should have a convert_batch method."""
        assert hasattr(MarkItDownAdapter, "convert_batch")
        assert callable(getattr(MarkItDownAdapter, "convert_batch"))

    def test_markitdown_has_supported_formats_method(self):
        """MarkItDownAdapter should have a supported_formats method."""
        assert hasattr(MarkItDownAdapter, "supported_formats")
        assert callable(getattr(MarkItDownAdapter, "supported_formats"))

    def test_convert_is_async(self):
        """convert method should be async."""
        assert inspect.iscoroutinefunction(MarkItDownAdapter.convert)

    def test_convert_batch_is_async(self):
        """convert_batch method should be async."""
        assert inspect.iscoroutinefunction(MarkItDownAdapter.convert_batch)

    def test_supported_formats_is_async(self):
        """supported_formats method should be async."""
        assert inspect.iscoroutinefunction(MarkItDownAdapter.supported_formats)

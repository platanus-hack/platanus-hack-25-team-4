"""Protocol compliance tests for LLM adapters."""

import inspect

from src.etl.adapters.llm import (
    AnthropicAdapter,
    OpenAIAdapter,
)


class TestOpenAIProtocolCompliance:
    """Test that OpenAIAdapter conforms to LLMAdapter protocol."""

    def test_openai_has_complete_method(self):
        """OpenAIAdapter should have a complete method."""
        assert hasattr(OpenAIAdapter, "complete")
        assert callable(getattr(OpenAIAdapter, "complete"))

    def test_openai_has_complete_batch_method(self):
        """OpenAIAdapter should have a complete_batch method."""
        assert hasattr(OpenAIAdapter, "complete_batch")
        assert callable(getattr(OpenAIAdapter, "complete_batch"))

    def test_openai_has_stream_complete_method(self):
        """OpenAIAdapter should have a stream_complete method."""
        assert hasattr(OpenAIAdapter, "stream_complete")
        assert callable(getattr(OpenAIAdapter, "stream_complete"))

    def test_openai_has_close_method(self):
        """OpenAIAdapter should have a close method."""
        assert hasattr(OpenAIAdapter, "close")
        assert callable(getattr(OpenAIAdapter, "close"))

    def test_openai_has_aenter_method(self):
        """OpenAIAdapter should have __aenter__ for async context manager."""
        assert hasattr(OpenAIAdapter, "__aenter__")
        assert callable(getattr(OpenAIAdapter, "__aenter__"))

    def test_openai_has_aexit_method(self):
        """OpenAIAdapter should have __aexit__ for async context manager."""
        assert hasattr(OpenAIAdapter, "__aexit__")
        assert callable(getattr(OpenAIAdapter, "__aexit__"))

    def test_complete_is_async(self):
        """complete method should be async."""
        assert inspect.iscoroutinefunction(OpenAIAdapter.complete)

    def test_complete_batch_is_async(self):
        """complete_batch method should be async."""
        assert inspect.iscoroutinefunction(OpenAIAdapter.complete_batch)

    def test_stream_complete_is_async_generator(self):
        """stream_complete method should be async generator."""
        assert inspect.isasyncgenfunction(OpenAIAdapter.stream_complete)

    def test_close_is_async(self):
        """close method should be async."""
        assert inspect.iscoroutinefunction(OpenAIAdapter.close)


class TestAnthropicProtocolCompliance:
    """Test that AnthropicAdapter conforms to LLMAdapter protocol."""

    def test_anthropic_has_complete_method(self):
        """AnthropicAdapter should have a complete method."""
        assert hasattr(AnthropicAdapter, "complete")
        assert callable(getattr(AnthropicAdapter, "complete"))

    def test_anthropic_has_complete_batch_method(self):
        """AnthropicAdapter should have a complete_batch method."""
        assert hasattr(AnthropicAdapter, "complete_batch")
        assert callable(getattr(AnthropicAdapter, "complete_batch"))

    def test_anthropic_has_stream_complete_method(self):
        """AnthropicAdapter should have a stream_complete method."""
        assert hasattr(AnthropicAdapter, "stream_complete")
        assert callable(getattr(AnthropicAdapter, "stream_complete"))

    def test_anthropic_has_close_method(self):
        """AnthropicAdapter should have a close method."""
        assert hasattr(AnthropicAdapter, "close")
        assert callable(getattr(AnthropicAdapter, "close"))

    def test_anthropic_has_aenter_method(self):
        """AnthropicAdapter should have __aenter__ for async context manager."""
        assert hasattr(AnthropicAdapter, "__aenter__")
        assert callable(getattr(AnthropicAdapter, "__aenter__"))

    def test_anthropic_has_aexit_method(self):
        """AnthropicAdapter should have __aexit__ for async context manager."""
        assert hasattr(AnthropicAdapter, "__aexit__")
        assert callable(getattr(AnthropicAdapter, "__aexit__"))

    def test_complete_is_async(self):
        """complete method should be async."""
        assert inspect.iscoroutinefunction(AnthropicAdapter.complete)

    def test_complete_batch_is_async(self):
        """complete_batch method should be async."""
        assert inspect.iscoroutinefunction(AnthropicAdapter.complete_batch)

    def test_stream_complete_is_async_generator(self):
        """stream_complete method should be async generator."""
        assert inspect.isasyncgenfunction(AnthropicAdapter.stream_complete)

    def test_close_is_async(self):
        """close method should be async."""
        assert inspect.iscoroutinefunction(AnthropicAdapter.close)

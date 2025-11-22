"""Markdown converter specific fixtures and mocks."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_markitdown():
    """Mock markitdown library with MarkItDown class."""
    mock_converter = MagicMock()
    mock_result = MagicMock()

    # Setup result object with text_content attribute
    mock_result.text_content = (
        "# Sample Markdown\n\nTest content converted from document."
    )

    # Setup converter methods
    mock_converter.convert.return_value = mock_result
    mock_converter.convert_stream.return_value = mock_result

    # Mock the MarkItDown class
    with patch("src.etl.adapters.markdown.markitdown.MarkItDown") as mock_class:
        mock_class.return_value = mock_converter

        yield {
            "class": mock_class,
            "converter": mock_converter,
            "result": mock_result,
        }


@pytest.fixture
def markitdown_config():
    """Default MarkItDown config for testing."""
    from src.etl.adapters.markdown import MarkItDownConfig

    return MarkItDownConfig(enable_llm=False, llm_model=None, llm_api_key=None)


@pytest.fixture
def markitdown_config_with_llm():
    """MarkItDown config with LLM enabled for testing."""
    from src.etl.adapters.markdown import MarkItDownConfig

    return MarkItDownConfig(
        enable_llm=True, llm_model="gpt-4", llm_api_key="test-api-key"
    )


@pytest.fixture
async def mock_markitdown_adapter(markitdown_config, mock_markitdown):
    """Fully mocked MarkItDown adapter ready for testing.

    This fixture provides an adapter with pre-loaded mocks to avoid
    lazy loading complexity in tests.
    """
    from src.etl.adapters.markdown import MarkItDownAdapter

    adapter = MarkItDownAdapter(markitdown_config)

    # Pre-load mock to bypass lazy loading
    adapter._converter = mock_markitdown["converter"]

    return adapter


@pytest.fixture
def mock_markitdown_with_error(mock_markitdown):
    """Mock markitdown that raises errors for testing error handling."""
    mock_markitdown["converter"].convert.side_effect = Exception("Conversion failed")
    mock_markitdown["converter"].convert_stream.side_effect = Exception(
        "Stream conversion failed"
    )
    return mock_markitdown

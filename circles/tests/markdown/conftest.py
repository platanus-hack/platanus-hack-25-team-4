"""Markdown converter specific fixtures and mocks."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_markitdown():
    """Mock markitdown library with MarkItDown class."""
    mock_converter = MagicMock()
    mock_result = MagicMock()

    # Setup result object with text_content attribute
    mock_result.text_content = "# Sample Markdown\n\nTest content converted from document."

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

    return MarkItDownConfig(enable_llm=True, llm_model="gpt-4", llm_api_key="test-api-key")


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
    mock_markitdown["converter"].convert_stream.side_effect = Exception("Stream conversion failed")
    return mock_markitdown


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a sample PDF file for testing."""
    from pathlib import Path

    pdf_path = tmp_path / "sample.pdf"
    # Create a minimal text file as a placeholder (real PDF not needed for mocked tests)
    pdf_path.write_text("Sample PDF content\nThis is a test PDF document.")
    return pdf_path


@pytest.fixture
def sample_html_path(tmp_path):
    """Create a sample HTML file for testing."""
    from pathlib import Path

    html_path = tmp_path / "sample.html"
    html_content = """<!DOCTYPE html>
<html>
<head><title>Test Document</title></head>
<body>
<h1>Sample HTML</h1>
<p>This is a test HTML document.</p>
</body>
</html>"""
    html_path.write_text(html_content)
    return html_path


@pytest.fixture
def sample_markdown_path(tmp_path):
    """Create a sample Markdown file for testing."""
    from pathlib import Path

    md_path = tmp_path / "sample.md"
    md_content = """# Sample Markdown

This is a test markdown document.

## Features
- Item 1
- Item 2

**Bold text** and *italic text*.
"""
    md_path.write_text(md_content)
    return md_path


@pytest.fixture
def sample_docx_path(tmp_path):
    """Create a sample DOCX file for testing."""
    from pathlib import Path

    docx_path = tmp_path / "sample.docx"
    # Create a minimal placeholder (real DOCX not needed for mocked tests)
    docx_path.write_text("Sample DOCX content\nThis is a test Word document.")
    return docx_path


@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample image file for testing."""
    from pathlib import Path

    image_path = tmp_path / "sample.png"
    # Create minimal PNG file (1x1 pixel)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    image_path.write_bytes(png_bytes)
    return image_path

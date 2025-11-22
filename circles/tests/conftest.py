"""Shared pytest fixtures for adapter tests."""

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

# Fixture paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"
DOCUMENTS_DIR = FIXTURES_DIR / "documents"


@pytest.fixture
def sample_image_path():
    """Path to a sample test image (JPEG)."""
    return IMAGES_DIR / "sample.jpg"


@pytest.fixture
def sample_png_path():
    """Path to a sample test PNG image."""
    return IMAGES_DIR / "sample.png"


@pytest.fixture
def sample_image_bytes():
    """Sample image as bytes (100x100 red JPEG)."""
    img = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def sample_png_bytes():
    """Sample PNG image as bytes (100x100 blue PNG)."""
    img = Image.new("RGB", (100, 100), color="blue")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def sample_pdf_path():
    """Path to a sample PDF document."""
    return DOCUMENTS_DIR / "sample.pdf"


@pytest.fixture
def sample_docx_path():
    """Path to a sample DOCX document."""
    return DOCUMENTS_DIR / "sample.docx"


@pytest.fixture
def sample_html_path():
    """Path to a sample HTML document."""
    return DOCUMENTS_DIR / "sample.html"


@pytest.fixture
def invalid_file_path():
    """Path to an invalid file (text file pretending to be image)."""
    return IMAGES_DIR / "invalid.txt"


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing.

    Returns a function that creates a file with custom content and suffix.

    Example:
        file = temp_file(b"test content", ".txt")
    """

    def _create(content: bytes = b"test", suffix: str = ".txt"):
        file = tmp_path / f"test{suffix}"
        file.write_bytes(content)
        return file

    return _create


@pytest.fixture
def nonexistent_path(tmp_path):
    """Path that doesn't exist (for error testing)."""
    return tmp_path / "nonexistent_file.jpg"


@pytest.fixture
def temp_directory(tmp_path):
    """Create a temporary directory for testing."""
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    return dir_path

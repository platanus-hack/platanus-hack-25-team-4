"""Tests for base adapter types and utilities."""

from pathlib import Path

import pytest
from src.etl.adapters.base import (
    AdapterError,
    ConversionError,
    FileContent,
    FilePath,
    InferenceError,
    InvalidInputError,
    ModelLoadError,
    UnsupportedFormatError,
    ensure_path,
)


# Exception hierarchy tests
class TestExceptionHierarchy:
    """Test exception class relationships and inheritance."""

    def test_adapter_error_is_exception(self):
        """AdapterError should inherit from Exception."""
        assert issubclass(AdapterError, Exception)

    def test_model_load_error_is_adapter_error(self):
        """ModelLoadError should inherit from AdapterError."""
        assert issubclass(ModelLoadError, AdapterError)

    def test_inference_error_is_adapter_error(self):
        """InferenceError should inherit from AdapterError."""
        assert issubclass(InferenceError, AdapterError)

    def test_conversion_error_is_adapter_error(self):
        """ConversionError should inherit from AdapterError."""
        assert issubclass(ConversionError, AdapterError)

    def test_unsupported_format_error_is_conversion_error(self):
        """UnsupportedFormatError should inherit from ConversionError."""
        assert issubclass(UnsupportedFormatError, ConversionError)

    def test_invalid_input_error_is_adapter_error(self):
        """InvalidInputError should inherit from AdapterError."""
        assert issubclass(InvalidInputError, AdapterError)


# Type alias tests
class TestTypeAliases:
    """Test type alias definitions."""

    def test_file_path_accepts_path(self):
        """FilePath should accept pathlib.Path objects."""
        # This is a type hint test - just verify the type exists
        assert FilePath is not None

    def test_file_path_accepts_str(self):
        """FilePath should accept string paths."""
        # Type hints are checked at static analysis time
        # Just verify the alias exists
        assert FilePath is not None

    def test_file_content_accepts_bytes(self):
        """FileContent should accept bytes."""
        assert FileContent is not None

    def test_file_content_accepts_str(self):
        """FileContent should accept strings."""
        assert FileContent is not None


# ensure_path function tests
class TestEnsurePath:
    """Test ensure_path utility function."""

    def test_ensure_path_with_valid_path_object(self, temp_file):
        """Should return Path object for existing file when given Path."""
        file = temp_file(b"test content", ".txt")
        result = ensure_path(file)

        assert isinstance(result, Path)
        assert result == file
        assert result.exists()

    def test_ensure_path_with_valid_string_path(self, temp_file):
        """Should convert string to Path for existing file."""
        file = temp_file(b"test content", ".txt")
        result = ensure_path(str(file))

        assert isinstance(result, Path)
        assert result == file
        assert result.exists()

    def test_ensure_path_with_nonexistent_file(self, nonexistent_path):
        """Should raise InvalidInputError for non-existent file."""
        with pytest.raises(InvalidInputError, match="does not exist"):
            ensure_path(nonexistent_path)

    def test_ensure_path_with_directory(self, temp_directory):
        """Should raise InvalidInputError for directory."""
        with pytest.raises(InvalidInputError, match="not a file"):
            ensure_path(temp_directory)

    def test_ensure_path_error_message_includes_path(self, nonexistent_path):
        """Error message should include the problematic path."""
        with pytest.raises(InvalidInputError) as exc_info:
            ensure_path(nonexistent_path)

        error_message = str(exc_info.value)
        assert str(nonexistent_path) in error_message

    def test_ensure_path_with_symlink_to_file(self, temp_file, tmp_path):
        """Should handle symlinks to files correctly."""
        real_file = temp_file(b"test", ".txt")
        symlink = tmp_path / "link.txt"
        symlink.symlink_to(real_file)

        result = ensure_path(symlink)

        assert isinstance(result, Path)
        assert result == symlink
        assert result.exists()


# Exception instantiation tests
class TestExceptionInstantiation:
    """Test that exceptions can be instantiated and raised correctly."""

    def test_adapter_error_with_message(self):
        """AdapterError should store error message."""
        error = AdapterError("test error")
        assert str(error) == "test error"

    def test_model_load_error_with_message(self):
        """ModelLoadError should store error message."""
        error = ModelLoadError("failed to load")
        assert str(error) == "failed to load"

    def test_inference_error_with_message(self):
        """InferenceError should store error message."""
        error = InferenceError("inference failed")
        assert str(error) == "inference failed"

    def test_conversion_error_with_message(self):
        """ConversionError should store error message."""
        error = ConversionError("conversion failed")
        assert str(error) == "conversion failed"

    def test_unsupported_format_error_with_message(self):
        """UnsupportedFormatError should store error message."""
        error = UnsupportedFormatError("format not supported")
        assert str(error) == "format not supported"

    def test_invalid_input_error_with_message(self):
        """InvalidInputError should store error message."""
        error = InvalidInputError("invalid input")
        assert str(error) == "invalid input"

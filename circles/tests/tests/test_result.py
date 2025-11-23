"""
Unit tests for Result monad and exception handling.
"""

import pytest
from src.etl.core import ProcessingError, Result


class TestResultMonad:
    """Test Result[T] monad implementation."""

    def test_result_ok_creation(self):
        """Test creating successful result."""
        result = Result.ok(42)
        assert result.is_ok is True
        assert result.is_error is False
        assert result.value == 42

    def test_result_error_creation(self):
        """Test creating error result."""
        error = ValueError("Something went wrong")
        result = Result.error(error)
        assert result.is_error is True
        assert result.is_ok is False
        assert result.error_value == error

    def test_result_value_from_error_raises(self):
        """Test accessing value from error result raises."""
        result = Result.error(ValueError("error"))
        with pytest.raises(ValueError):
            _ = result.value

    def test_result_error_from_ok_raises(self):
        """Test accessing error from ok result raises."""
        result = Result.ok(42)
        with pytest.raises(ValueError):
            _ = result.error_value

    def test_result_map_success(self):
        """Test mapping over successful result."""
        result = Result.ok(5)
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_ok is True
        assert mapped.value == 10

    def test_result_map_error_skips(self):
        """Test mapping over error skips transformation."""
        error = ValueError("error")
        result = Result.error(error)
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_error is True
        assert mapped.error_value == error

    def test_result_bind_chains_operations(self):
        """Test bind chains operations."""
        result = Result.ok(5)
        chained = result.bind(lambda x: Result.ok(x * 2))
        assert chained.is_ok is True
        assert chained.value == 10

    def test_result_bind_error_propagates(self):
        """Test bind propagates errors."""
        error = ValueError("error")
        result = Result.error(error)
        chained = result.bind(lambda x: Result.ok(x * 2))
        assert chained.is_error is True
        assert chained.error_value == error

    def test_result_bind_intermediate_error(self):
        """Test bind stops on intermediate error."""
        result = Result.ok(5)
        error = ValueError("intermediate error")
        chained = result.bind(lambda x: Result.error(error))
        assert chained.is_error is True
        assert chained.error_value == error

    def test_result_map_error_transforms(self):
        """Test map_error transforms error value."""
        result = Result.error("simple error")
        mapped = result.map_error(lambda e: f"transformed: {e}")
        assert mapped.is_error is True
        assert mapped.error_value == "transformed: simple error"

    def test_result_map_error_on_success_skips(self):
        """Test map_error skips on success."""
        result = Result.ok(42)
        mapped = result.map_error(lambda e: "should not be called")
        assert mapped.is_ok is True
        assert mapped.value == 42

    def test_result_unwrap_or_success(self):
        """Test unwrap_or returns value on success."""
        result = Result.ok(42)
        assert result.unwrap_or(0) == 42

    def test_result_unwrap_or_error(self):
        """Test unwrap_or returns default on error."""
        result = Result.error("error")
        assert result.unwrap_or(0) == 0

    def test_result_unwrap_or_else_success(self):
        """Test unwrap_or_else returns value on success."""
        result = Result.ok(42)
        assert result.unwrap_or_else(lambda e: 0) == 42

    def test_result_unwrap_or_else_error(self):
        """Test unwrap_or_else computes from error."""
        result = Result.error("error")
        assert result.unwrap_or_else(lambda e: len(e)) == 5

    def test_result_and_then_success(self):
        """Test and_then executes on success."""
        result = Result.ok(5)
        chained = result.and_then(lambda: Result.ok(10))
        assert chained.is_ok is True
        assert chained.value == 10

    def test_result_and_then_error_skips(self):
        """Test and_then skips on error."""
        error = ValueError("error")
        result = Result.error(error)
        chained = result.and_then(lambda: Result.ok(10))
        assert chained.is_error is True
        assert chained.error_value == error

    def test_result_repr_ok(self):
        """Test string representation of ok result."""
        result = Result.ok(42)
        assert repr(result) == "Result.ok(42)"

    def test_result_repr_error(self):
        """Test string representation of error result."""
        result = Result.error("error")
        assert "Result.error" in repr(result)

    def test_result_chaining_example(self):
        """Test realistic chaining example."""
        # Simulate: validate -> process -> persist

        def validate(value: int) -> Result[int, str]:
            if value < 0:
                return Result.error("negative number")
            return Result.ok(value)

        def process(value: int) -> Result[int, str]:
            return Result.ok(value * 2)

        def persist(value: int) -> Result[int, str]:
            if value > 100:
                return Result.error("too large")
            return Result.ok(value)

        # Happy path
        result = validate(10).bind(process).bind(persist)
        assert result.is_ok is True
        assert result.value == 20

        # Validation error
        result = validate(-5).bind(process).bind(persist)
        assert result.is_error is True
        assert result.error_value == "negative number"

        # Persistence error
        result = validate(60).bind(process).bind(persist)
        assert result.is_error is True
        assert result.error_value == "too large"


class TestProcessingError:
    """Test ProcessingError exception."""

    def test_processing_error_creation(self):
        """Test creating processing error."""
        error = ProcessingError(
            "Processing failed", error_type="vlm_error", details={"service": "claude"}
        )
        assert error.message == "Processing failed"
        assert error.error_type == "vlm_error"
        assert error.details == {"service": "claude"}

    def test_processing_error_string(self):
        """Test string representation."""
        error = ProcessingError("Failed", error_type="test_error")
        assert str(error) == "test_error: Failed"

    def test_processing_error_repr(self):
        """Test repr representation."""
        error = ProcessingError("Failed", error_type="test_error")
        assert "ProcessingError" in repr(error)
        assert "test_error" in repr(error)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

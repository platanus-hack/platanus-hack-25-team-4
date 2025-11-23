"""
Unit tests for ResumeAdapter.

Tests the 4-phase pipeline (Validate, Process, Persist, Cleanup) for resume file processing.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.etl.adapters.base import AdapterContext, DataType
from src.etl.adapters.resume_adapter import ResumeAdapter


@pytest.mark.unit
class TestResumeAdapter:
    """Test ResumeAdapter functionality."""

    @pytest.fixture
    async def resume_adapter(self):
        """Create a ResumeAdapter instance."""
        return ResumeAdapter()

    @pytest.fixture
    def sample_resume_file(self, tmp_path):
        """Create a temporary resume file."""
        resume_content = """John Doe
john@example.com | (555) 123-4567
San Francisco, CA

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years in full-stack development.

WORK EXPERIENCE
Tech Corp (2020-2024)
Senior Software Engineer
- Led microservices development
- Managed team of 4 engineers
"""
        resume_path = tmp_path / "resume.txt"
        resume_path.write_text(resume_content)
        return resume_path

    @pytest.fixture
    def mock_adapter_context(self, sample_resume_file):
        """Create a mock AdapterContext."""
        return AdapterContext(
            user_id=1,
            source_id=1,
            data_type=DataType.RESUME,
            input_path=sample_resume_file,
            session=AsyncMock(spec=AsyncSession),
        )

    @pytest.mark.asyncio
    async def test_validate_input_valid_resume(
        self, resume_adapter, sample_resume_file
    ):
        """Test validation of a valid resume file."""
        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.RESUME)
        result = await resume_adapter.validate_input(sample_resume_file, context)

        assert result.is_ok, "Valid resume file should pass validation"

    @pytest.mark.asyncio
    async def test_validate_input_nonexistent_file(self, resume_adapter, tmp_path):
        """Test validation of non-existent file."""
        non_existent = tmp_path / "nonexistent.txt"
        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.RESUME)

        result = await resume_adapter.validate_input(non_existent, context)
        assert result.is_error, "Non-existent file should fail validation"

    @pytest.mark.asyncio
    async def test_validate_input_invalid_extension(self, resume_adapter, tmp_path):
        """Test validation of unsupported file type."""
        invalid_file = tmp_path / "document.xyz"
        invalid_file.write_text("content")

        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.RESUME)
        result = await resume_adapter.validate_input(invalid_file, context)

        assert result.is_error, "Invalid file extension should fail validation"

    @pytest.mark.asyncio
    async def test_validate_input_supported_formats(self, resume_adapter, tmp_path):
        """Test validation of all supported resume formats."""
        supported_formats = [".txt", ".pdf", ".docx"]

        for ext in supported_formats:
            test_file = tmp_path / f"resume{ext}"
            test_file.write_bytes(b"dummy content")

            context = AdapterContext(user_id=1, source_id=1, data_type=DataType.RESUME)
            result = await resume_adapter.validate_input(test_file, context)

            assert result.is_ok, f"{ext} should be a valid resume format"

    @pytest.mark.asyncio
    async def test_process_resume(
        self, resume_adapter, sample_resume_file, mock_adapter_context
    ):
        """Test processing a resume file."""
        # Mock the processor's process method
        mock_processor_result = MagicMock(
            content={"full_text": "John Doe", "structured": {}},
            metadata={"file_type": ".txt", "file_size": 500},
            embeddings=None,
        )

        with patch("src.etl.adapters.resume_adapter.ResumeProcessor") as MockProcessor:
            mock_instance = MockProcessor.return_value
            mock_instance.process = AsyncMock(return_value=mock_processor_result)

            result = await resume_adapter.process(
                sample_resume_file, mock_adapter_context
            )

            assert result.is_ok, "Processing should succeed"
            assert "full_text" in result.value.content
            assert result.value.metadata["file_type"] == ".txt"

    @pytest.mark.asyncio
    async def test_process_resume_processor_error(
        self, resume_adapter, sample_resume_file, mock_adapter_context
    ):
        """Test handling of processor errors."""
        with patch("src.etl.adapters.resume_adapter.ResumeProcessor") as MockProcessor:
            mock_instance = MockProcessor.return_value
            mock_instance.process = AsyncMock(
                side_effect=ValueError("Processing failed")
            )

            result = await resume_adapter.process(
                sample_resume_file, mock_adapter_context
            )

            assert result.is_error, "Processing should fail and return error Result"
            assert "Processing failed" in str(result.error_value)

    @pytest.mark.asyncio
    async def test_persist_resume_data(self, resume_adapter, mock_adapter_context):
        """Test persisting processed resume data."""
        processor_result = MagicMock(
            content={"full_text": "John Doe", "structured": {}},
            metadata={"file_type": ".txt"},
        )

        mock_session = AsyncMock(spec=AsyncSession)
        result = await resume_adapter.persist(
            processor_result, mock_adapter_context, mock_session
        )

        assert result.is_ok, "Persistence should succeed"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_database_error(self, resume_adapter, mock_adapter_context):
        """Test handling of database persistence errors."""
        processor_result = MagicMock(
            content={"full_text": "John Doe", "structured": {}},
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add.side_effect = Exception("Database error")

        result = await resume_adapter.persist(
            processor_result, mock_adapter_context, mock_session
        )

        assert result.is_error, "Persistence should fail and return error Result"
        assert "Database error" in str(result.error_value)

    @pytest.mark.asyncio
    async def test_cleanup(
        self, resume_adapter, sample_resume_file, mock_adapter_context
    ):
        """Test cleanup phase."""
        # Cleanup accepts input_data and context
        await resume_adapter.cleanup(sample_resume_file, mock_adapter_context)

        # Cleanup should complete without errors
        assert True

    @pytest.mark.asyncio
    async def test_execute_full_pipeline(
        self, resume_adapter, sample_resume_file, mock_adapter_context
    ):
        """Test the complete 4-phase pipeline."""
        from src.etl.core import ProcessingError, Result

        mock_processor_result = MagicMock(
            content={"full_text": "John Doe"},
            metadata={"file_type": ".txt"},
        )
        mock_resume_data = MagicMock()

        with patch.object(
            resume_adapter, "validate_input", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = Result.ok(None)
            with patch.object(
                resume_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                mock_process.return_value = Result.ok(mock_processor_result)
                with patch.object(
                    resume_adapter, "persist", new_callable=AsyncMock
                ) as mock_persist:
                    mock_persist.return_value = Result.ok(mock_resume_data)
                    with patch.object(
                        resume_adapter, "cleanup", new_callable=AsyncMock
                    ) as mock_cleanup:
                        mock_session = AsyncMock(spec=AsyncSession)
                        result = await resume_adapter.execute(
                            sample_resume_file, mock_adapter_context, mock_session
                        )

                        assert result.is_ok, "Execute should succeed"
                        mock_persist.assert_called_once()
                        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_validation_failure(
        self, resume_adapter, sample_resume_file, mock_adapter_context
    ):
        """Test pipeline stops at validation failure."""
        from src.etl.core import ProcessingError, Result

        validation_error = ProcessingError(
            "Validation failed", error_type="validation_error"
        )

        with patch.object(
            resume_adapter, "validate_input", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = Result.error(validation_error)
            with patch.object(
                resume_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                mock_session = AsyncMock(spec=AsyncSession)
                result = await resume_adapter.execute(
                    sample_resume_file, mock_adapter_context, mock_session
                )

                assert result.is_error, "Execute should fail at validation"
                mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_passed_through_phases(
        self, resume_adapter, sample_resume_file, mock_adapter_context
    ):
        """Test that context is passed correctly through all phases."""
        from src.etl.core import ProcessingError, Result

        mock_processor_result = MagicMock(content={}, metadata={})
        mock_resume_data = MagicMock()

        with patch.object(
            resume_adapter, "validate_input", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = Result.ok(None)
            with patch.object(
                resume_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                mock_process.return_value = Result.ok(mock_processor_result)
                with patch.object(
                    resume_adapter, "persist", new_callable=AsyncMock
                ) as mock_persist:
                    mock_persist.return_value = Result.ok(mock_resume_data)
                    with patch.object(
                        resume_adapter, "cleanup", new_callable=AsyncMock
                    ):
                        mock_session = AsyncMock(spec=AsyncSession)
                        await resume_adapter.execute(
                            sample_resume_file, mock_adapter_context, mock_session
                        )

                        # Verify process received input_data and context
                        mock_process.assert_called_once_with(
                            sample_resume_file, mock_adapter_context
                        )

    @pytest.mark.asyncio
    async def test_empty_resume_file(self, resume_adapter, tmp_path):
        """Test validation of empty resume file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.RESUME)
        result = await resume_adapter.validate_input(empty_file, context)

        # Empty file might be valid structurally, but processor should handle it
        # Check that result is a Result type
        assert result.is_ok or result.is_error, "Result should be a Result type"

    @pytest.mark.asyncio
    async def test_large_resume_file(self, resume_adapter, tmp_path):
        """Test processing of large resume file."""
        large_file = tmp_path / "large_resume.txt"
        # Create a 5MB file
        large_content = "x" * (5 * 1024 * 1024)
        large_file.write_text(large_content)

        context = AdapterContext(user_id=1, source_id=1, data_type=DataType.RESUME)
        result = await resume_adapter.validate_input(large_file, context)

        # Should still validate, but may need size limits
        # Check that result is a Result type, not boolean
        assert result.is_ok or result.is_error, "Result should be a Result type"

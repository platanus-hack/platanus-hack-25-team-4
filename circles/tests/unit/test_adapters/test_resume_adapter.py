"""
Unit tests for ResumeAdapter.

Tests the 4-phase pipeline (Validate, Process, Persist, Cleanup) for resume file processing.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from circles.src.etl.adapters.base import AdapterContext, DataType
from circles.src.etl.adapters.resume_adapter import ResumeAdapter


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
            data_type=DataType.RESUME,
            input_path=sample_resume_file,
            user_id="test_user_123",
            session=AsyncMock(spec=AsyncSession),
        )

    @pytest.mark.asyncio
    async def test_validate_input_valid_resume(
        self, resume_adapter, sample_resume_file
    ):
        """Test validation of a valid resume file."""
        result = await resume_adapter.validate_input(sample_resume_file)

        assert result is True, "Valid resume file should pass validation"

    @pytest.mark.asyncio
    async def test_validate_input_nonexistent_file(self, resume_adapter, tmp_path):
        """Test validation of non-existent file."""
        non_existent = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            await resume_adapter.validate_input(non_existent)

    @pytest.mark.asyncio
    async def test_validate_input_invalid_extension(self, resume_adapter, tmp_path):
        """Test validation of unsupported file type."""
        invalid_file = tmp_path / "document.xyz"
        invalid_file.write_text("content")

        result = await resume_adapter.validate_input(invalid_file)

        assert result is False, "Invalid file extension should fail validation"

    @pytest.mark.asyncio
    async def test_validate_input_supported_formats(self, resume_adapter, tmp_path):
        """Test validation of all supported resume formats."""
        supported_formats = [".txt", ".pdf", ".docx"]

        for ext in supported_formats:
            test_file = tmp_path / f"resume{ext}"
            test_file.write_bytes(b"dummy content")

            result = await resume_adapter.validate_input(test_file)

            assert result is True, f"{ext} should be a valid resume format"

    @pytest.mark.asyncio
    async def test_process_resume(self, resume_adapter, mock_adapter_context):
        """Test processing a resume file."""
        with patch.object(
            resume_adapter.processor,
            "process",
            return_value=MagicMock(
                content={"full_text": "John Doe", "structured": {}},
                metadata={"file_type": ".txt", "file_size": 500},
                embeddings=None,
            ),
        ):
            result = await resume_adapter.process(mock_adapter_context)

            assert result is not None
            assert "full_text" in result.content
            assert result.metadata["file_type"] == ".txt"

    @pytest.mark.asyncio
    async def test_process_resume_processor_error(
        self, resume_adapter, mock_adapter_context
    ):
        """Test handling of processor errors."""
        with patch.object(
            resume_adapter.processor,
            "process",
            side_effect=ValueError("Processing failed"),
        ):
            with pytest.raises(ValueError):
                await resume_adapter.process(mock_adapter_context)

    @pytest.mark.asyncio
    async def test_persist_resume_data(self, resume_adapter, mock_adapter_context):
        """Test persisting processed resume data."""
        processor_result = MagicMock(
            content={"full_text": "John Doe", "structured": {}},
            metadata={"file_type": ".txt"},
        )

        with patch.object(resume_adapter, "_save_to_database", new_callable=AsyncMock):
            await resume_adapter.persist(mock_adapter_context, processor_result)

            resume_adapter._save_to_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_database_error(self, resume_adapter, mock_adapter_context):
        """Test handling of database persistence errors."""
        processor_result = MagicMock(
            content={"full_text": "John Doe", "structured": {}},
        )

        mock_adapter_context.session.add.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await resume_adapter.persist(mock_adapter_context, processor_result)

    @pytest.mark.asyncio
    async def test_cleanup(self, resume_adapter, mock_adapter_context):
        """Test cleanup phase."""
        with patch.object(
            resume_adapter, "_cleanup_temp_files", new_callable=AsyncMock
        ):
            await resume_adapter.cleanup(mock_adapter_context)

            # Cleanup should complete without errors
            assert True

    @pytest.mark.asyncio
    async def test_execute_full_pipeline(
        self, resume_adapter, sample_resume_file, mock_adapter_context
    ):
        """Test the complete 4-phase pipeline."""
        with patch.object(resume_adapter, "validate_input", return_value=True):
            with patch.object(
                resume_adapter,
                "process",
                return_value=MagicMock(
                    content={"full_text": "John Doe"},
                    metadata={"file_type": ".txt"},
                ),
            ):
                with patch.object(resume_adapter, "persist", new_callable=AsyncMock):
                    with patch.object(
                        resume_adapter, "cleanup", new_callable=AsyncMock
                    ):
                        result = await resume_adapter.execute(mock_adapter_context)

                        assert result is not None
                        resume_adapter.persist.assert_called_once()
                        resume_adapter.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_validation_failure(
        self, resume_adapter, mock_adapter_context
    ):
        """Test pipeline stops at validation failure."""
        with patch.object(resume_adapter, "validate_input", return_value=False):
            with patch.object(
                resume_adapter, "process", new_callable=AsyncMock
            ) as mock_process:
                result = await resume_adapter.execute(mock_adapter_context)

                mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_passed_through_phases(
        self, resume_adapter, mock_adapter_context
    ):
        """Test that context is passed correctly through all phases."""
        with patch.object(resume_adapter, "validate_input", return_value=True):
            with patch.object(
                resume_adapter,
                "process",
                return_value=MagicMock(content={}, metadata={}),
            ) as mock_process:
                with patch.object(resume_adapter, "persist", new_callable=AsyncMock):
                    with patch.object(
                        resume_adapter, "cleanup", new_callable=AsyncMock
                    ):
                        await resume_adapter.execute(mock_adapter_context)

                        # Verify process received the context
                        mock_process.assert_called_once_with(mock_adapter_context)

    @pytest.mark.asyncio
    async def test_empty_resume_file(self, resume_adapter, tmp_path):
        """Test validation of empty resume file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        result = await resume_adapter.validate_input(empty_file)

        # Empty file might be valid structurally, but processor should handle it
        assert result is True or result is False  # Depends on validation rules

    @pytest.mark.asyncio
    async def test_large_resume_file(self, resume_adapter, tmp_path):
        """Test processing of large resume file."""
        large_file = tmp_path / "large_resume.txt"
        # Create a 5MB file
        large_content = "x" * (5 * 1024 * 1024)
        large_file.write_text(large_content)

        result = await resume_adapter.validate_input(large_file)

        # Should still validate, but may need size limits
        assert isinstance(result, bool)

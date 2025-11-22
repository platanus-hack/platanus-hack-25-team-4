"""
Unit tests for ResumeProcessor.

Tests resume file processing and structured data extraction.
"""

import pytest

from circles.src.etl.processors.resume_processor import (
    ResumeProcessor,
    SimpleProcessorResult,
)
from circles.tests.fixtures.fixture_factories import DataTypeFixtures
from circles.tests.unit.utils.assertions import (
    assert_content_keys,
    assert_dict_field,
    assert_file_metadata,
    assert_list_field,
    assert_processor_result_structure,
)


@pytest.mark.unit
class TestResumeProcessor:
    """Test ResumeProcessor functionality."""

    @pytest.fixture
    async def resume_processor(self):
        """Create a ResumeProcessor instance."""
        return ResumeProcessor()

    @pytest.fixture
    def sample_resume_txt_file(self, tmp_path):
        """Create a temporary text resume file."""
        resume_content = """
John Doe
john@example.com | (555) 123-4567
San Francisco, CA

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years in full-stack development.

WORK EXPERIENCE
Tech Corp (2020-2024)
Senior Software Engineer
- Led microservices development
- Managed team of 4 engineers

StartUp Inc (2018-2020)
Software Engineer
- Built core platform features
- Implemented CI/CD pipelines

EDUCATION
University of California, B.S. Computer Science (2018)

SKILLS
Python, JavaScript, React, PostgreSQL, Docker, AWS
"""
        resume_path = tmp_path / "resume.txt"
        resume_path.write_text(resume_content)
        return resume_path

    @pytest.fixture
    def sample_resume_with_latin1(self, tmp_path):
        """Create a resume with latin-1 encoding."""
        resume_content = "John Dëé - Software Engineer"
        resume_path = tmp_path / "resume_latin1.txt"
        resume_path.write_bytes(resume_content.encode("latin-1"))
        return resume_path

    @pytest.mark.asyncio
    async def test_process_valid_resume(self, resume_processor, sample_resume_txt_file):
        """Test processing a valid resume file."""
        result = await resume_processor.process(sample_resume_txt_file)

        assert_processor_result_structure(result)
        assert_content_keys(result.content, ["full_text", "structured"])
        assert_file_metadata(result.metadata, ".txt", min_file_size=1)

    @pytest.mark.asyncio
    async def test_extract_text_from_txt_file(
        self, resume_processor, sample_resume_txt_file
    ):
        """Test text extraction from TXT file."""
        text = await resume_processor._extract_text(sample_resume_txt_file)

        assert isinstance(text, str)
        assert len(text) > 0
        assert "John Doe" in text

    @pytest.mark.asyncio
    async def test_extract_text_with_latin1_encoding(
        self, resume_processor, sample_resume_with_latin1
    ):
        """Test text extraction with latin-1 encoding fallback."""
        text = await resume_processor._extract_text(sample_resume_with_latin1)

        assert isinstance(text, str)
        assert len(text) > 0

    @pytest.mark.asyncio
    async def test_process_pdf_placeholder(self, resume_processor, tmp_path):
        """Test that PDF processing returns placeholder (MVP)."""
        pdf_path = tmp_path / "resume.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")  # Minimal PDF header

        result = await resume_processor.process(pdf_path)

        assert isinstance(result, SimpleProcessorResult)
        assert "resume.pdf" in result.content["full_text"]
        assert result.metadata["file_type"] == ".pdf"

    @pytest.mark.asyncio
    async def test_extract_structured_data(self, resume_processor):
        """Test structured data extraction."""
        structured = resume_processor._extract_structured_data("Sample resume text")

        required_fields = [
            "work_experience",
            "education",
            "skills",
            "contact_info",
        ]
        assert_content_keys(structured, required_fields)

        assert_list_field(structured, "work_experience")
        assert_list_field(structured, "education")
        assert_list_field(structured, "skills")
        assert_dict_field(structured, "contact_info")

    @pytest.mark.asyncio
    async def test_process_file_not_found(self, resume_processor, tmp_path):
        """Test processing non-existent file."""
        non_existent = tmp_path / "non_existent.txt"

        with pytest.raises(FileNotFoundError):
            await resume_processor.process(non_existent)

    @pytest.mark.asyncio
    async def test_processor_result_structure(
        self, resume_processor, sample_resume_txt_file
    ):
        """Test that processor result has correct structure."""
        result = await resume_processor.process(sample_resume_txt_file)

        # Verify SimpleProcessorResult structure
        assert_processor_result_structure(result)

        # Verify content structure
        assert_content_keys(result.content, ["full_text", "structured"])

        # Verify metadata structure
        assert_file_metadata(result.metadata, ".txt")

    @pytest.mark.asyncio
    async def test_extract_text_empty_file(self, resume_processor, tmp_path):
        """Test extracting text from empty file."""
        empty_path = tmp_path / "empty.txt"
        empty_path.write_text("")

        text = await resume_processor._extract_text(empty_path)

        assert isinstance(text, str)
        assert len(text) == 0

    @pytest.mark.asyncio
    async def test_process_empty_resume(self, resume_processor, tmp_path):
        """Test processing empty resume file."""
        empty_path = tmp_path / "empty.txt"
        empty_path.write_text("")

        result = await resume_processor.process(empty_path)

        assert isinstance(result, SimpleProcessorResult)
        assert result.content["full_text"] == ""
        assert "structured" in result.content

    @pytest.mark.asyncio
    async def test_process_docx_placeholder(self, resume_processor, tmp_path):
        """Test that DOCX processing returns placeholder (MVP)."""
        docx_path = tmp_path / "resume.docx"
        # Minimal DOCX is a ZIP file, but for MVP we just return placeholder
        docx_path.write_bytes(b"PK\x03\x04")  # ZIP header

        result = await resume_processor.process(docx_path)

        assert isinstance(result, SimpleProcessorResult)
        assert "resume.docx" in result.content["full_text"]
        assert result.metadata["file_type"] == ".docx"


@pytest.mark.unit
class TestResumeProcessorIntegration:
    """Integration tests for ResumeProcessor with fixtures."""

    @pytest.fixture
    async def resume_processor(self):
        """Create a ResumeProcessor instance."""
        return ResumeProcessor()

    @pytest.mark.asyncio
    async def test_process_with_fixture_data(self, resume_processor):
        """Test processing with fixture data."""
        fixture_data = DataTypeFixtures.create_resume_data()

        assert "full_name" in fixture_data
        assert "experience" in fixture_data
        assert "education" in fixture_data
        assert "skills" in fixture_data

        assert len(fixture_data["experience"]) > 0
        assert len(fixture_data["education"]) > 0
        assert len(fixture_data["skills"]) > 0

    @pytest.mark.asyncio
    async def test_structured_data_format(
        self, resume_processor, sample_resume_txt_file
    ):
        """Test that structured data has consistent format."""
        result = await resume_processor.process(sample_resume_txt_file)

        structured = result.content["structured"]

        # Verify all required fields are present
        required_fields = [
            "work_experience",
            "education",
            "skills",
            "contact_info",
        ]
        assert_content_keys(structured, required_fields)

    def test_extract_structured_data_consistency(self, resume_processor):
        """Test consistency of structured data extraction."""
        test_cases = [
            "",
            "Simple text",
            "A" * 1000,
            "Resume with @#$% special characters!",
        ]

        for test_text in test_cases:
            structured = resume_processor._extract_structured_data(test_text)

            # Should always have the required fields
            required_fields = [
                "work_experience",
                "education",
                "skills",
                "contact_info",
            ]
            assert_content_keys(structured, required_fields)

            # All lists should be lists, all dicts should be dicts
            assert_list_field(structured, "work_experience")
            assert_list_field(structured, "education")
            assert_list_field(structured, "skills")
            assert_dict_field(structured, "contact_info")

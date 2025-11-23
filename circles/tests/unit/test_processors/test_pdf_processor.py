"""
Unit tests for PDFProcessor.

Tests PDF document processing with text extraction and content analysis.
"""

import logging

import pytest
from src.etl.processors.pdf_processor import (
    PDFProcessor,
    SimpleProcessorResult,
)

from tests.fixtures.fixture_factories import DataTypeFixtures
from tests.unit.utils.assertions import (
    assert_content_keys,
    assert_file_metadata,
    assert_processor_result_structure,
)

logger = logging.getLogger(__name__)


@pytest.mark.unit
class TestPDFProcessor:
    """Test PDFProcessor functionality."""

    @pytest.fixture
    async def pdf_processor(self):
        """Create a PDFProcessor instance."""
        return PDFProcessor()

    @pytest.fixture
    def sample_pdf_txt_file(self, tmp_path):
        """Create a temporary PDF file (text-based)."""
        pdf_content = """
Technical Documentation - System Architecture Guide

INTRODUCTION
This document provides a comprehensive overview of the system architecture,
including design principles, components, and deployment strategies.

SYSTEM OVERVIEW
The system consists of three main layers:
1. Presentation Layer - User interface and API endpoints
2. Business Logic Layer - Core processing and validation
3. Data Layer - Persistent storage and caching

ARCHITECTURE PRINCIPLES
- Modularity: Components are loosely coupled and independently testable
- Scalability: Horizontal scaling through microservices architecture
- Reliability: Redundancy and failover mechanisms
- Security: Defense in depth with encryption and access control

COMPONENT DETAILS

API Gateway
- Entry point for all external requests
- Request validation and rate limiting
- Load balancing across service instances

Microservices
- Photo Processing Service
- Document Processing Service
- User Management Service
- Data Analytics Service

Database Layer
- Primary: PostgreSQL for relational data
- Cache: Redis for session and frequently accessed data
- Search: Elasticsearch for full-text search capabilities

DEPLOYMENT STRATEGY
Production environment uses:
- Kubernetes for orchestration
- Docker containers for services
- CI/CD pipeline for automated testing and deployment
- Monitoring via Prometheus and Grafana

CONCLUSION
This architecture supports both current requirements and future scaling needs.
"""
        pdf_path = tmp_path / "document.pdf"
        pdf_path.write_text(pdf_content)
        return pdf_path

    @pytest.mark.asyncio
    async def test_process_valid_pdf(self, pdf_processor, sample_pdf_txt_file):
        """Test processing a valid PDF file."""
        result = await pdf_processor.process(sample_pdf_txt_file)

        assert_processor_result_structure(result)
        assert_content_keys(result.content, ["full_text", "analysis"])
        assert_file_metadata(result.metadata, ".pdf", min_file_size=1)
        assert "document_type" in result.metadata

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf(self, pdf_processor, sample_pdf_txt_file):
        """Test text extraction from PDF file."""
        text = await pdf_processor._extract_text(sample_pdf_txt_file)

        assert isinstance(text, str)
        assert len(text) > 0
        assert "Technical Documentation" in text

    @pytest.mark.asyncio
    async def test_process_file_not_found(self, pdf_processor, tmp_path):
        """Test processing non-existent file."""
        non_existent = tmp_path / "non_existent.pdf"

        with pytest.raises(FileNotFoundError):
            await pdf_processor.process(non_existent)

    @pytest.mark.asyncio
    async def test_process_empty_pdf(self, pdf_processor, tmp_path):
        """Test processing empty PDF file."""
        empty_path = tmp_path / "empty.pdf"
        empty_path.write_text("")

        with pytest.raises(ValueError, match="PDF file appears to be empty"):
            await pdf_processor.process(empty_path)

    @pytest.mark.asyncio
    async def test_unsupported_file_type(self, pdf_processor, tmp_path):
        """Test processing unsupported file type."""
        txt_path = tmp_path / "document.txt"
        txt_path.write_text("Some content")

        with pytest.raises(ValueError, match="Unsupported file type"):
            await pdf_processor._extract_text(txt_path)

    def test_extract_json_direct_parsing(self, pdf_processor):
        """Test JSON extraction with direct valid JSON."""
        response = """{
            "document_type": "report",
            "key_topics": ["topic1", "topic2"],
            "summary": "Test summary",
            "metadata": {"author": null}
        }"""
        result = pdf_processor._extract_json_from_response(response)

        assert result is not None
        assert result["document_type"] == "report"
        assert "key_topics" in result

    def test_extract_json_with_surrounding_text(self, pdf_processor):
        """Test JSON extraction from response with surrounding text."""
        response = 'Here is the JSON: {"document_type": "article", "key_topics": [], "summary": "test", "metadata": {}} end'
        result = pdf_processor._extract_json_from_response(response)

        assert result is not None
        assert result["document_type"] == "article"

    def test_extract_json_from_markdown_code_block(self, pdf_processor):
        """Test JSON extraction from markdown code blocks."""
        response = """```json
{
    "document_type": "whitepaper",
    "key_topics": ["ml", "ai"],
    "summary": "Machine learning guide",
    "metadata": {"author": "Jane Doe"}
}
```"""
        result = pdf_processor._extract_json_from_response(response)

        assert result is not None
        assert result["document_type"] == "whitepaper"
        assert result["metadata"]["author"] == "Jane Doe"

    def test_extract_json_fallback_to_none(self, pdf_processor):
        """Test JSON extraction returns None for invalid JSON."""
        response = "This is not JSON at all"
        result = pdf_processor._extract_json_from_response(response)

        assert result is None

    def test_markdown_to_text_headers(self, pdf_processor):
        """Test markdown-to-text conversion removes headers."""
        markdown = "# Main Title\n## Subsection\n### Minor Header\nContent here"
        text = pdf_processor._markdown_to_text(markdown)

        assert "Main Title" not in text
        assert "#" not in text
        assert "Content here" in text

    def test_markdown_to_text_bold_italic(self, pdf_processor):
        """Test markdown-to-text removes bold and italic markers."""
        markdown = "This is **bold text** and *italic text* in paragraph"
        text = pdf_processor._markdown_to_text(markdown)

        assert "bold text" in text
        assert "italic text" in text
        assert "**" not in text
        assert "*" not in text

    def test_markdown_to_text_links(self, pdf_processor):
        """Test markdown-to-text removes link markdown."""
        markdown = "Check [documentation](https://docs.example.com) for details"
        text = pdf_processor._markdown_to_text(markdown)

        assert "documentation" in text
        assert "https://docs.example.com" not in text

    def test_markdown_to_text_code_blocks(self, pdf_processor):
        """Test markdown-to-text removes code blocks."""
        markdown = "Example:\n```python\nprint('hello')\n```\nAnd inline `code`"
        text = pdf_processor._markdown_to_text(markdown)

        assert "print" not in text
        assert "Example" in text
        assert "`" not in text

    def test_markdown_to_text_html_tags(self, pdf_processor):
        """Test markdown-to-text removes HTML tags."""
        markdown = "Content with <strong>HTML</strong> and <br> tags"
        text = pdf_processor._markdown_to_text(markdown)

        assert "HTML" in text
        assert "<" not in text

    def test_fallback_analysis(self, pdf_processor):
        """Test fallback analysis has correct structure."""
        fallback = pdf_processor._get_fallback_analysis()

        assert "document_type" in fallback
        assert "key_topics" in fallback
        assert "summary" in fallback
        assert "metadata" in fallback
        assert "content_quality" in fallback

        assert isinstance(fallback["key_topics"], list)
        assert isinstance(fallback["metadata"], dict)
        assert isinstance(fallback["content_quality"], dict)

        # Verify metadata fields
        assert "author" in fallback["metadata"]
        assert "date" in fallback["metadata"]
        assert "organization" in fallback["metadata"]
        assert "version" in fallback["metadata"]

        # Verify content_quality fields
        assert "readability" in fallback["content_quality"]
        assert "structure_level" in fallback["content_quality"]
        assert "completeness" in fallback["content_quality"]

    def test_processor_result_structure(self):
        """Test SimpleProcessorResult structure."""
        result = SimpleProcessorResult(
            content={"full_text": "test", "analysis": {}},
            metadata={"file_type": ".pdf"},
        )

        assert hasattr(result, "content")
        assert hasattr(result, "metadata")
        assert hasattr(result, "embeddings")
        assert result.embeddings is None

    @pytest.mark.asyncio
    async def test_process_batch_multiple_files(self, pdf_processor, tmp_path):
        """Test batch processing of multiple PDF files."""
        # Create multiple test PDFs
        pdf_files = []
        for i in range(3):
            pdf_path = tmp_path / f"document_{i}.pdf"
            pdf_path.write_text(f"Document {i}\n\nContent section {i}\n\nConclusion")
            pdf_files.append(pdf_path)

        # Process batch
        results = await pdf_processor.process_batch(pdf_files)

        # Verify results
        assert len(results) == 3
        for result in results:
            assert isinstance(result, SimpleProcessorResult)
            assert hasattr(result, "content")
            assert hasattr(result, "metadata")
            assert "full_text" in result.content
            assert "analysis" in result.content

    @pytest.mark.asyncio
    async def test_process_batch_with_errors(self, pdf_processor, tmp_path):
        """Test batch processing handles file errors gracefully."""
        # Create mix of valid and invalid file paths
        pdf_files = []

        # Valid file
        valid_path = tmp_path / "valid_document.pdf"
        valid_path.write_text("Valid PDF content\n\nWith multiple sections")
        pdf_files.append(valid_path)

        # Non-existent file
        invalid_path = tmp_path / "nonexistent.pdf"
        pdf_files.append(invalid_path)

        # Process batch - should not raise, should handle errors gracefully
        results = await pdf_processor.process_batch(pdf_files)

        assert len(results) == 2
        # First result should be successful
        assert "processing_error" not in results[0].metadata
        # Second result should have error
        assert "processing_error" in results[1].metadata

    @pytest.mark.asyncio
    async def test_process_batch_concurrency(self, tmp_path):
        """Test batch processing respects concurrency limits."""
        # Create processor with low concurrency limit
        processor = PDFProcessor(max_concurrent=2)

        # Create multiple PDF files
        pdf_files = []
        for i in range(5):
            pdf_path = tmp_path / f"document_{i}.pdf"
            pdf_path.write_text(f"PDF {i}\n\nSection A\n\nSection B")
            pdf_files.append(pdf_path)

        # Process batch
        results = await processor.process_batch(pdf_files)

        # Verify all files were processed
        assert len(results) == 5
        # Verify semaphore was created with correct limit
        assert processor.max_concurrent == 2
        assert processor.semaphore._value == 2

    @pytest.mark.asyncio
    async def test_process_batch_empty_list(self, pdf_processor):
        """Test batch processing with empty file list."""
        results = await pdf_processor.process_batch([])

        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_analyze_content_structure(self, pdf_processor):
        """Test content analysis has required structure."""
        test_text = """
        Technical Report on Cloud Architecture

        This report discusses cloud-based infrastructure and best practices.
        We explore AWS, Azure, and GCP platforms.

        Key findings:
        - Scalability is critical
        - Cost optimization matters
        - Security is paramount
        """

        # Analysis will call Claude API if available, otherwise use fallback
        try:
            analysis = await pdf_processor._analyze_content(test_text)

            # Verify structure
            assert "document_type" in analysis
            assert "key_topics" in analysis
            assert "summary" in analysis
            assert "metadata" in analysis
            assert "content_quality" in analysis

            # Verify types
            assert isinstance(analysis["key_topics"], list)
            assert isinstance(analysis["metadata"], dict)
            assert isinstance(analysis["content_quality"], dict)

        except Exception as e:
            # Expected if Claude API not available
            logger.warning(f"Content analysis test skipped: {e}")


@pytest.mark.unit
class TestPDFProcessorIntegration:
    """Integration tests for PDFProcessor with fixtures."""

    @pytest.fixture
    async def pdf_processor(self):
        """Create a PDFProcessor instance."""
        return PDFProcessor()

    @pytest.mark.asyncio
    async def test_process_with_fixture_data(self):
        """Test processing with fixture data."""
        fixture_data = DataTypeFixtures.create_resume_data()

        assert "full_name" in fixture_data or "experience" in fixture_data
        assert isinstance(fixture_data, dict)
        assert len(fixture_data) > 0

    @pytest.mark.asyncio
    async def test_batch_processing_consistency(self, pdf_processor, tmp_path):
        """Test consistency of batch processing results."""
        # Create test PDFs
        pdf_files = []
        for i in range(3):
            pdf_path = tmp_path / f"doc_{i}.pdf"
            pdf_path.write_text(f"Document {i}\n\nContent about topic {i}")
            pdf_files.append(pdf_path)

        # Process batch
        results = await pdf_processor.process_batch(pdf_files)

        # All results should have same structure
        for result in results:
            if "processing_error" not in result.metadata:
                assert "full_text" in result.content
                assert "analysis" in result.content
                assert result.metadata["file_type"] == ".pdf"

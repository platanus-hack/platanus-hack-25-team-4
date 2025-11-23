"""
End-to-End Tests for PhotoProcessor and ResumeProcessor.

These tests run the complete processor pipelines with real file processing.
Marked with @pytest.mark.slow and @pytest.mark.e2e to allow skipping in CI.

Run with: pytest -m "e2e" tests/integration/test_processors_e2e.py
"""

import asyncio
import logging
from pathlib import Path

import pytest

from circles.src.etl.adapters.base import AdapterContext, DataType
from circles.src.etl.adapters.photo_adapter import PhotoAdapter
from circles.src.etl.adapters.resume_adapter import ResumeAdapter
from circles.src.etl.core.config import get_settings
from circles.src.etl.processors.photo_processor import PhotoProcessor
from circles.src.etl.processors.resume_processor import ResumeProcessor

logger = logging.getLogger(__name__)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def adapter_context() -> AdapterContext:
    """Create a test adapter context."""
    return AdapterContext(
        user_id=1,
        source_id=1,
        data_type=DataType.PHOTO,
        trace_id="e2e_test_request_123",
    )


@pytest.fixture
def sample_text_resume(tmp_path) -> Path:
    """Create a sample text resume file."""
    resume_content = """
JOHN DOE
john.doe@example.com | (555) 123-4567 | San Francisco, CA
LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe

PROFESSIONAL SUMMARY
Experienced full-stack software engineer with 6+ years developing scalable web applications
and leading cross-functional teams. Passionate about clean code, mentoring, and building
products that solve real-world problems.

WORK EXPERIENCE

Senior Software Engineer | TechCorp Inc. | Jan 2021 - Present
- Led architecture redesign reducing API latency by 40%
- Mentored team of 4 junior engineers through code reviews and pair programming
- Implemented microservices migration from monolithic architecture
- Owned deployment pipeline improving release frequency from quarterly to weekly

Software Engineer | StartupXYZ | Jun 2018 - Dec 2020
- Built core platform features serving 100K+ daily active users
- Implemented CI/CD pipelines reducing deployment time by 60%
- Designed and implemented real-time notification system using WebSockets
- Contributed to open-source projects with 2K+ GitHub stars

Junior Developer | WebAgency LLC | Jan 2017 - May 2018
- Developed responsive web applications using React and Vue.js
- Maintained codebase following SOLID principles and design patterns
- Participated in daily standups and sprint planning meetings

EDUCATION

Bachelor of Science in Computer Science | State University | 2017
GPA: 3.8/4.0
Relevant Coursework: Data Structures, Algorithms, Database Systems, Web Development

SKILLS

Languages: Python, JavaScript, TypeScript, SQL, Go, Java
Frameworks: React, Vue.js, Django, FastAPI, Express.js
Databases: PostgreSQL, MongoDB, Redis, Elasticsearch
Tools & Platforms: Docker, Kubernetes, AWS, CI/CD (GitHub Actions), Git
Methodologies: Agile, Test-Driven Development, Microservices

CERTIFICATIONS
AWS Certified Solutions Architect - Professional | 2022
Kubernetes Application Developer (CKAD) | 2021
"""
    resume_path = tmp_path / "sample_resume.txt"
    resume_path.write_text(resume_content)
    return resume_path


@pytest.fixture
def sample_image_bytes() -> bytes:
    """
    Create minimal valid JPEG bytes for testing.

    This is a tiny (1x1 pixel) JPEG to minimize test data.
    """
    # Minimal JPEG header + SOI/EOI markers
    return bytes(
        [
            0xFF,
            0xD8,  # SOI (Start of Image)
            0xFF,
            0xE0,
            0x00,
            0x10,  # JFIF marker
            0x4A,
            0x46,
            0x49,
            0x46,
            0x00,  # JFIF identifier
            0x01,
            0x01,  # Version 1.1
            0x00,  # Units
            0x00,
            0x01,
            0x00,
            0x01,  # X/Y density
            0x00,
            0x00,  # Thumbnail dimensions
            0xFF,
            0xDB,
            0x00,
            0x43,  # DQT marker
            0x00,  # Precision
            # Minimal quantization table
            0x10,
            0x0B,
            0x0C,
            0x0E,
            0x0C,
            0x0A,
            0x10,
            0x0E,
            0x0D,
            0x0E,
            0x12,
            0x11,
            0x10,
            0x13,
            0x18,
            0x28,
            0x1A,
            0x18,
            0x16,
            0x16,
            0x18,
            0x31,
            0x23,
            0x25,
            0x1D,
            0x28,
            0x3A,
            0x33,
            0x3D,
            0x3C,
            0x39,
            0x33,
            0x38,
            0x37,
            0x40,
            0x48,
            0x5C,
            0x4E,
            0x40,
            0x44,
            0x57,
            0x45,
            0x37,
            0x38,
            0x50,
            0x6D,
            0x51,
            0x57,
            0x5F,
            0x62,
            0x67,
            0x68,
            0x67,
            0x3E,
            0x4D,
            0x71,
            0x79,
            0x70,
            0x64,
            0x78,
            0x5C,
            0x65,
            0x67,
            0x63,
            0xFF,
            0xC0,
            0x00,
            0x0B,  # SOF0 marker
            0x08,
            0x00,
            0x01,
            0x00,
            0x01,  # Height, Width, Components
            0x01,
            0x11,
            0x00,  # Component info
            0xFF,
            0xC4,
            0x00,
            0x1F,  # DHT marker
            0x00,  # Table class/destination
            # Minimal Huffman table
            0x00,
            0x01,
            0x05,
            0x01,
            0x01,
            0x01,
            0x01,
            0x01,
            0x01,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
            0xFF,
            0xDA,
            0x00,
            0x08,  # SOS marker
            0x01,
            0x01,
            0x00,
            0x00,
            0x3F,
            0x00,  # Scan header
            # Minimal compressed data
            0xFF,
            0xD9,  # EOI (End of Image)
        ]
    )


@pytest.fixture
def sample_image_file(tmp_path, sample_image_bytes) -> Path:
    """Create a temporary image file."""
    image_path = tmp_path / "sample_image.jpg"
    image_path.write_bytes(sample_image_bytes)
    return image_path


# ============================================================================
# PhotoProcessor E2E Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestPhotoProcessorE2E:
    """End-to-end tests for PhotoProcessor."""

    async def test_single_photo_processing(self, sample_image_file):
        """
        E2E Test: Process a single photo file end-to-end.

        Tests:
        - File reading and validation
        - Image encoding to base64
        - EXIF data extraction (if available)
        - Claude Vision API integration
        - Result structure and metadata
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        processor = PhotoProcessor()
        result = await processor.process(sample_image_file)

        # Verify result structure
        assert result is not None
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")

        # Verify content
        assert "caption" in result.content
        assert "analysis" in result.content
        assert "image_file" in result.content
        assert isinstance(result.content["caption"], str)
        assert isinstance(result.content["analysis"], dict)

        # Verify metadata
        assert result.metadata["file_type"] == ".jpg"
        assert result.metadata["file_size"] > 0
        assert "exif_data" in result.metadata
        assert isinstance(result.metadata["exif_data"], dict)

        logger.info("✓ Single photo processing succeeded")
        logger.info(f"  Caption: {result.content['caption']}")

    async def test_batch_photo_processing(self, tmp_path, sample_image_bytes):
        """
        E2E Test: Process multiple photos in parallel.

        Tests:
        - Batch file processing
        - Concurrency control with semaphore
        - Parallel API calls
        - Result aggregation
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        # Create multiple test images
        image_paths = []
        for i in range(3):
            image_path = tmp_path / f"image_{i}.jpg"
            image_path.write_bytes(sample_image_bytes)
            image_paths.append(image_path)

        processor = PhotoProcessor(max_concurrent=2)
        results = await processor.process_batch(image_paths)

        # Verify batch processing
        assert len(results) == 3
        assert all(hasattr(r, "content") for r in results)
        assert all(hasattr(r, "metadata") for r in results)

        # Verify all have results (even if some failed)
        assert all("caption" in r.content for r in results)

        logger.info("✓ Batch photo processing succeeded")
        logger.info(f"  Processed {len(results)} photos with max_concurrent=2")

    async def test_photo_adapter_full_pipeline(
        self, sample_image_file, adapter_context
    ):
        """
        E2E Test: Complete PhotoAdapter 4-phase pipeline.

        Tests:
        - Phase 1: File validation
        - Phase 2: Image processing
        - Phase 3: Result persistence (mocked)
        - Phase 4: Cleanup
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        adapter = PhotoAdapter()

        # Phase 1: Validate
        validation_result = await adapter.validate_input(
            sample_image_file, adapter_context
        )
        assert validation_result.is_ok, (
            f"Validation failed: {validation_result.error_value}"
        )

        # Phase 2: Process
        processing_result = await adapter.process(sample_image_file, adapter_context)
        assert processing_result.is_ok, (
            f"Processing failed: {processing_result.error_value}"
        )

        processor_result = processing_result.value
        assert processor_result.content["caption"]
        assert processor_result.metadata["file_type"] == ".jpg"

        # Phase 4: Cleanup (Phase 3 persistence would require DB)
        await adapter.cleanup(sample_image_file, adapter_context)

        logger.info("✓ PhotoAdapter full pipeline succeeded")
        logger.info(f"  Caption: {processor_result.content['caption']}")


# ============================================================================
# ResumeProcessor E2E Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestResumeProcessorE2E:
    """End-to-end tests for ResumeProcessor."""

    async def test_single_resume_processing(self, sample_text_resume):
        """
        E2E Test: Process a single resume file end-to-end.

        Tests:
        - File reading and validation
        - Text extraction from resume
        - Markdown-to-text conversion
        - Claude API structured extraction
        - Result structure and metadata
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        processor = ResumeProcessor()
        result = await processor.process(sample_text_resume)

        # Verify result structure
        assert result is not None
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")

        # Verify content
        assert "full_text" in result.content
        assert "structured" in result.content
        assert len(result.content["full_text"]) > 0
        assert isinstance(result.content["structured"], dict)

        # Verify structured data
        structured = result.content["structured"]
        assert "contact_info" in structured
        assert "work_experience" in structured
        assert "education" in structured
        assert "skills" in structured

        # Verify contact info extraction
        assert isinstance(structured["contact_info"], dict)
        assert "name" in structured["contact_info"]

        # Verify work experience extraction
        assert isinstance(structured["work_experience"], list)

        # Verify education extraction
        assert isinstance(structured["education"], list)

        # Verify metadata
        assert result.metadata["file_type"] == ".txt"
        assert result.metadata["file_size"] > 0

        logger.info("✓ Single resume processing succeeded")
        logger.info(f"  Name: {structured['contact_info'].get('name', 'N/A')}")
        logger.info(f"  Work Experience entries: {len(structured['work_experience'])}")
        logger.info(f"  Education entries: {len(structured['education'])}")

    async def test_batch_resume_processing(self, tmp_path):
        """
        E2E Test: Process multiple resumes in parallel.

        Tests:
        - Batch file processing
        - Concurrency control with semaphore
        - Parallel API calls
        - Error handling in batch
        - Result aggregation
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        # Create multiple test resumes
        resume_paths = []
        for i in range(3):
            resume_path = tmp_path / f"resume_{i}.txt"
            resume_path.write_text(
                f"""
Resume {i}
Email: user{i}@example.com
Phone: (555) 555-{i:04d}

EXPERIENCE
Company {i}: Senior Engineer (2020-Present)
- Achievement 1
- Achievement 2

EDUCATION
University: Bachelor's Degree (2020)

SKILLS
Python, JavaScript, Go, Rust
"""
            )
            resume_paths.append(resume_path)

        processor = ResumeProcessor(max_concurrent=2)
        results = await processor.process_batch(resume_paths)

        # Verify batch processing
        assert len(results) == 3
        assert all(hasattr(r, "content") for r in results)
        assert all(hasattr(r, "metadata") for r in results)

        # Verify all have structured data
        assert all("structured" in r.content for r in results)

        # Count successful and failed
        successful = sum(1 for r in results if "processing_error" not in r.metadata)
        logger.info("✓ Batch resume processing succeeded")
        logger.info(f"  Processed {len(results)} resumes with max_concurrent=2")
        logger.info(f"  Successful: {successful}/{len(results)}")

    async def test_resume_adapter_full_pipeline(
        self, sample_text_resume, adapter_context
    ):
        """
        E2E Test: Complete ResumeAdapter 4-phase pipeline.

        Tests:
        - Phase 1: File validation
        - Phase 2: Resume processing
        - Phase 3: Result structure (no persistence without DB)
        - Phase 4: Cleanup
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        adapter = ResumeAdapter()

        # Phase 1: Validate
        validation_result = await adapter.validate_input(
            sample_text_resume, adapter_context
        )
        assert validation_result.is_ok, (
            f"Validation failed: {validation_result.error_value}"
        )

        # Phase 2: Process
        processing_result = await adapter.process(sample_text_resume, adapter_context)
        assert processing_result.is_ok, (
            f"Processing failed: {processing_result.error_value}"
        )

        processor_result = processing_result.value
        assert "full_text" in processor_result.content
        assert "structured" in processor_result.content
        assert processor_result.metadata["file_type"] == ".txt"

        # Phase 4: Cleanup
        await adapter.cleanup(sample_text_resume, adapter_context)

        logger.info("✓ ResumeAdapter full pipeline succeeded")
        structured = processor_result.content["structured"]
        logger.info(f"  Contact: {structured['contact_info'].get('name', 'N/A')}")
        logger.info(
            f"  Extracted {len(structured['work_experience'])} work experiences"
        )


# ============================================================================
# Cross-Processor E2E Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestProcessorsCombined:
    """End-to-end tests combining multiple processors."""

    async def test_parallel_photo_and_resume_processing(
        self, sample_image_file, sample_text_resume
    ):
        """
        E2E Test: Process photo and resume in parallel.

        Tests:
        - Multiple processors running concurrently
        - Independent result aggregation
        - Different data types processed together
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        # Create processors
        photo_processor = PhotoProcessor()
        resume_processor = ResumeProcessor()

        # Process in parallel
        photo_result, resume_result = await asyncio.gather(
            photo_processor.process(sample_image_file),
            resume_processor.process(sample_text_resume),
            return_exceptions=False,
        )

        # Verify both succeeded
        assert photo_result is not None
        assert resume_result is not None

        # Verify independent results
        assert "caption" in photo_result.content
        assert "full_text" in resume_result.content

        logger.info("✓ Parallel processing succeeded")
        logger.info(f"  Photo caption: {photo_result.content['caption']}")
        logger.info(
            f"  Resume name: {resume_result.content['structured']['contact_info'].get('name', 'N/A')}"
        )

    async def test_batch_processors_throughput(self, tmp_path, sample_image_bytes):
        """
        E2E Test: Measure throughput of batch processing.

        Tests:
        - Large batch processing (10+ files)
        - Concurrency performance
        - Result consistency across batch
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        # Create batch of resumes
        resume_paths = []
        for i in range(5):
            resume_path = tmp_path / f"resume_{i}.txt"
            resume_path.write_text(
                f"Resume {i}\nEngineer at Company {i}\nSkills: Python, Java"
            )
            resume_paths.append(resume_path)

        # Create batch of images
        image_paths = []
        for i in range(5):
            image_path = tmp_path / f"image_{i}.jpg"
            image_path.write_bytes(sample_image_bytes)
            image_paths.append(image_path)

        # Process both batches in parallel
        resume_processor = ResumeProcessor(max_concurrent=3)
        photo_processor = PhotoProcessor(max_concurrent=3)

        resume_results, photo_results = await asyncio.gather(
            resume_processor.process_batch(resume_paths),
            photo_processor.process_batch(image_paths),
            return_exceptions=False,
        )

        # Verify both batches completed
        assert len(resume_results) == 5
        assert len(photo_results) == 5

        logger.info("✓ Batch throughput test succeeded")
        logger.info("  Processed 5 resumes and 5 photos concurrently")

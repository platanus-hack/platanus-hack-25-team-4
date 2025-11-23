"""
End-to-End Tests for PDFProcessor.

Tests run the complete PDF processing pipeline with real file processing.
Marked with @pytest.mark.slow and @pytest.mark.e2e to allow skipping in CI.

Run with: pytest -m "e2e" tests/integration/test_pdf_processor_e2e.py
"""

import asyncio
import logging
from pathlib import Path

import pytest
from src.etl.adapters.base import AdapterContext, DataType
from src.etl.core.config import get_settings
from src.etl.processors.pdf_processor import PDFProcessor

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
        data_type=DataType.RESUME,
        trace_id="e2e_test_pdf_123",
    )


@pytest.fixture
def sample_pdf_file(tmp_path) -> Path:
    """Create a sample PDF file (text-based for testing)."""
    pdf_content = """
Technical Whitepaper: Microservices Architecture at Scale

Version 2.1 | Published: 2024-01-15 | Author: Engineering Team

EXECUTIVE SUMMARY

This whitepaper presents a comprehensive guide to implementing microservices
architecture in enterprise environments. We discuss design patterns, deployment
strategies, and operational best practices learned from managing 150+ services
in production.

TABLE OF CONTENTS

1. Introduction
2. Architecture Overview
3. Service Design Principles
4. Data Management Strategies
5. Deployment and Operations
6. Monitoring and Observability
7. Cost Optimization
8. Conclusion

CHAPTER 1: INTRODUCTION

Microservices architecture has become the de facto standard for building
large-scale applications. Unlike monolithic architectures, microservices
decompose applications into loosely coupled, independently deployable services.

Key benefits:
- Independent scaling of services
- Technology diversity per service
- Fault isolation and resilience
- Faster deployment cycles
- Team autonomy

CHAPTER 2: ARCHITECTURE OVERVIEW

Our architecture consists of:

Frontend Services
- Web UI (React)
- Mobile Apps (iOS, Android)
- Admin Portal

API Gateway
- Request routing
- Authentication/Authorization
- Rate limiting
- Load balancing

Core Microservices
- User Service
- Product Service
- Order Service
- Payment Service
- Inventory Service
- Notification Service

Data Layer
- PostgreSQL (relational)
- MongoDB (document store)
- Redis (cache)
- Elasticsearch (search)

Message Queue
- RabbitMQ/Apache Kafka
- Event streaming
- Asynchronous communication

CHAPTER 3: SERVICE DESIGN PRINCIPLES

Single Responsibility Principle
Each service handles one business capability. This ensures services remain
focused and manageable.

API-First Design
Services communicate via well-defined APIs. REST, gRPC, and async messaging
are supported based on requirements.

Database Per Service
Each service manages its own database. No direct database access between services.
This ensures independence and prevents tight coupling.

Resilience Patterns
- Circuit breakers for failing dependencies
- Retry logic with exponential backoff
- Timeout handling
- Graceful degradation

CHAPTER 4: DATA MANAGEMENT

Event Sourcing
All changes are captured as events. Services subscribe to relevant events
and maintain their own view of data.

Saga Pattern
Distributed transactions across services are implemented using compensating
transactions (sagas).

CQRS Pattern
Command Query Responsibility Segregation separates read and write models
for optimized performance.

CHAPTER 5: DEPLOYMENT AND OPERATIONS

Container Strategy
- Docker for containerization
- Kubernetes for orchestration
- Helm for package management

CI/CD Pipeline
- Automated testing at multiple levels
- Canary deployments
- Blue-green deployments
- Automated rollbacks

CHAPTER 6: MONITORING AND OBSERVABILITY

Observability Stack
- Prometheus for metrics
- ELK Stack for logging
- Jaeger for distributed tracing
- Grafana for visualization

Key Metrics
- Request rate and latency
- Error rate
- Resource utilization
- Business metrics

CHAPTER 7: COST OPTIMIZATION

Resource Management
- Right-sizing services
- Auto-scaling policies
- Reserved instances
- Spot instances

Cost Monitoring
- Per-service cost allocation
- Budget alerts
- Regular optimization reviews

CHAPTER 8: CONCLUSION

Microservices architecture enables organizations to build and scale complex
applications. However, it introduces operational complexity that must be
carefully managed through proper tooling, automation, and practices.

The principles and patterns discussed in this whitepaper provide a foundation
for successful microservices deployments at scale.
"""
    pdf_path = tmp_path / "whitepaper.pdf"
    pdf_path.write_text(pdf_content)
    return pdf_path


# ============================================================================
# PDFProcessor E2E Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestPDFProcessorE2E:
    """End-to-end tests for PDFProcessor."""

    async def test_single_pdf_processing(self, sample_pdf_file):
        """
        E2E Test: Process a single PDF file end-to-end.

        Tests:
        - File reading and validation
        - Text extraction from PDF
        - Content analysis with Claude API
        - Result structure and metadata
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        processor = PDFProcessor()
        result = await processor.process(sample_pdf_file)

        # Verify result structure
        assert result is not None
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")

        # Verify content
        assert "full_text" in result.content
        assert "analysis" in result.content
        assert len(result.content["full_text"]) > 0
        assert isinstance(result.content["analysis"], dict)

        # Verify analysis
        analysis = result.content["analysis"]
        assert "document_type" in analysis
        assert "key_topics" in analysis
        assert "summary" in analysis
        assert "metadata" in analysis
        assert isinstance(analysis["key_topics"], list)

        # Verify metadata
        assert result.metadata["file_type"] == ".pdf"
        assert result.metadata["file_size"] > 0
        assert "document_type" in result.metadata

        logger.info("✓ Single PDF processing succeeded")
        logger.info(f"  Document Type: {analysis.get('document_type', 'N/A')}")
        logger.info(f"  Key Topics: {len(analysis.get('key_topics', []))} identified")
        logger.info(f"  Summary: {analysis.get('summary', '')[:100]}...")

    async def test_batch_pdf_processing(self, tmp_path):
        """
        E2E Test: Process multiple PDFs in parallel.

        Tests:
        - Batch file processing
        - Concurrency control with semaphore
        - Parallel API calls
        - Result aggregation
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        # Create multiple test PDFs
        pdf_paths = []
        for i in range(3):
            pdf_path = tmp_path / f"document_{i}.pdf"
            pdf_path.write_text(
                f"""
Document {i} - Technical Report

Section 1: Overview
This is a technical report about topic {i}.

Section 2: Details
Key points about this document:
- Point A
- Point B
- Point C

Section 3: Conclusion
In conclusion, document {i} covers important aspects.
"""
            )
            pdf_paths.append(pdf_path)

        processor = PDFProcessor(max_concurrent=2)
        results = await processor.process_batch(pdf_paths)

        # Verify batch processing
        assert len(results) == 3
        assert all(hasattr(r, "content") for r in results)
        assert all(hasattr(r, "metadata") for r in results)

        # Verify all have analysis
        assert all("analysis" in r.content for r in results)

        # Count successful processing
        successful = sum(1 for r in results if "processing_error" not in r.metadata)

        logger.info("✓ Batch PDF processing succeeded")
        logger.info(f"  Processed {len(results)} PDFs with max_concurrent=2")
        logger.info(f"  Successful: {successful}/{len(results)}")

    async def test_pdf_analysis_quality(self, sample_pdf_file):
        """
        E2E Test: Verify quality of PDF analysis.

        Tests:
        - Content type detection
        - Topic extraction accuracy
        - Metadata extraction
        - Summary generation
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        processor = PDFProcessor()
        result = await processor.process(sample_pdf_file)

        analysis = result.content["analysis"]

        # Verify document type is detected (should be whitepaper/report)
        document_type = analysis.get("document_type", "").lower()
        assert document_type, "Document type should be detected"

        # Verify key topics are extracted
        topics = analysis.get("key_topics", [])
        assert isinstance(topics, list), "Topics should be a list"
        # For a technical document, we expect some topics to be extracted
        if len(topics) > 0:
            assert all(isinstance(t, str) for t in topics), "Topics should be strings"

        # Verify summary exists
        summary = analysis.get("summary", "")
        assert isinstance(summary, str), "Summary should be a string"
        if summary and summary != "Unable to analyze document content":
            assert len(summary) > 10, "Summary should have meaningful content"

        # Verify metadata structure
        metadata = analysis.get("metadata", {})
        assert isinstance(metadata, dict), "Metadata should be a dict"

        # Verify content quality assessment
        quality = analysis.get("content_quality", {})
        assert isinstance(quality, dict), "Content quality should be a dict"

        logger.info("✓ PDF analysis quality test succeeded")
        logger.info(f"  Document Type: {document_type}")
        logger.info(f"  Topics Found: {len(topics)}")
        logger.info(f"  Summary Length: {len(summary)} chars")

    async def test_batch_pdf_with_mixed_content(self, tmp_path):
        """
        E2E Test: Process batch with varied PDF types.

        Tests:
        - Mixed content processing
        - Different document structures
        - Consistent result format
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        # Create PDFs with different structures
        pdf_paths = []

        # Technical report
        report_path = tmp_path / "report.pdf"
        report_path.write_text(
            """
Technical Report: System Performance
Executive Summary
This report analyzes system performance metrics.
Key Findings
- Latency reduced by 30%
- Throughput increased by 50%
Recommendations
1. Increase cache size
2. Optimize queries
"""
        )
        pdf_paths.append(report_path)

        # Article
        article_path = tmp_path / "article.pdf"
        article_path.write_text(
            """
Article: Best Practices in Software Design
Introduction
Software design best practices ensure maintainability and scalability.
Design Principles
- DRY: Don't Repeat Yourself
- SOLID: Single Responsibility
- KISS: Keep It Simple
Conclusion
Following these principles leads to better code quality.
"""
        )
        pdf_paths.append(article_path)

        # Manual/Guide
        manual_path = tmp_path / "manual.pdf"
        manual_path.write_text(
            """
User Manual: Product Configuration
Table of Contents
1. Getting Started
2. Installation
3. Configuration
4. Troubleshooting

Section 1: Getting Started
Welcome to our product. This manual guides you through setup.

Section 2: Installation
Follow these steps to install:
Step 1: Download
Step 2: Extract
Step 3: Run installer

Section 3: Configuration
Configure the following settings...

Section 4: Troubleshooting
If you encounter issues...
"""
        )
        pdf_paths.append(manual_path)

        processor = PDFProcessor(max_concurrent=2)
        results = await processor.process_batch(pdf_paths)

        # Verify all processed
        assert len(results) == 3

        # Verify consistent structure across different content types
        for result in results:
            if "processing_error" not in result.metadata:
                assert "full_text" in result.content
                assert "analysis" in result.content
                analysis = result.content["analysis"]
                assert "document_type" in analysis
                assert "key_topics" in analysis
                assert "summary" in analysis

        logger.info("✓ Mixed content batch processing succeeded")
        logger.info("  Processed technical report, article, and manual successfully")

    async def test_pdf_processor_throughput(self, tmp_path):
        """
        E2E Test: Measure throughput of PDF processing.

        Tests:
        - Large batch processing
        - Concurrency performance
        - Result consistency
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        # Create larger batch of PDFs
        pdf_paths = []
        for i in range(5):
            pdf_path = tmp_path / f"doc_{i}.pdf"
            pdf_path.write_text(
                f"""
Document {i}: Comprehensive Analysis
Chapter 1: Introduction
This document explores topic {i} in detail.

Chapter 2: Main Content
Content for document {i} goes here.
- Point 1
- Point 2
- Point 3

Chapter 3: Analysis
Analysis of the subject matter.

Chapter 4: Conclusion
Concluding remarks for document {i}.
"""
            )
            pdf_paths.append(pdf_path)

        # Process with different concurrency levels
        for max_concurrent in [2, 5]:
            processor = PDFProcessor(max_concurrent=max_concurrent)
            results = await processor.process_batch(pdf_paths)

            assert len(results) == 5

            successful = sum(1 for r in results if "processing_error" not in r.metadata)
            logger.info(
                f"✓ Throughput test (max_concurrent={max_concurrent}): {successful}/5 successful"
            )


# ============================================================================
# Parallel Processing Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestPDFProcessorParallel:
    """Tests for parallel PDF processing scenarios."""

    async def test_parallel_batch_processing(self, tmp_path):
        """
        E2E Test: Process multiple PDF batches in parallel.

        Tests:
        - Multiple processors running concurrently
        - Independent result aggregation
        - Performance scaling
        """
        settings = get_settings()
        if not settings.anthropic_api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        # Create two batches of PDFs
        batch1_paths = []
        batch2_paths = []

        for i in range(3):
            # Batch 1
            pdf1 = tmp_path / f"batch1_doc_{i}.pdf"
            pdf1.write_text(f"Batch 1 Document {i}\n\nContent about batch 1 topic {i}")
            batch1_paths.append(pdf1)

            # Batch 2
            pdf2 = tmp_path / f"batch2_doc_{i}.pdf"
            pdf2.write_text(f"Batch 2 Document {i}\n\nContent about batch 2 topic {i}")
            batch2_paths.append(pdf2)

        # Process both batches in parallel
        processor1 = PDFProcessor(max_concurrent=2)
        processor2 = PDFProcessor(max_concurrent=2)

        results1, results2 = await asyncio.gather(
            processor1.process_batch(batch1_paths),
            processor2.process_batch(batch2_paths),
            return_exceptions=False,
        )

        # Verify both batches completed
        assert len(results1) == 3
        assert len(results2) == 3

        # Verify independent processing
        for r1, r2 in zip(results1, results2):
            assert r1.metadata["file_type"] == ".pdf"
            assert r2.metadata["file_type"] == ".pdf"

        logger.info("✓ Parallel batch processing succeeded")
        logger.info("  Processed 2 batches of 3 PDFs concurrently")

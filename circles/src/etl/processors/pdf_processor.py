"""
PDF Processor - Converts PDF documents to structured text with analysis.

Uses MarkItDown for universal PDF conversion and Claude API for content analysis.
Supports both single and batch processing with concurrent API calls.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic

from ..adapters.markdown.markitdown import MarkItDownAdapter, MarkItDownConfig
from ..core import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SimpleProcessorResult:
    """Simple processor result."""

    content: Dict[str, Any]
    metadata: Dict[str, Any]
    embeddings: Optional[Dict[str, Any]] = None


class PDFProcessor:
    """Process PDF documents with text extraction and content analysis with batch support."""

    def __init__(self, max_concurrent: int = 5):
        """
        Initialize PDFProcessor with MarkItDown and Claude API.

        Args:
            max_concurrent: Maximum concurrent Claude API calls (default 5)
        """
        self.markdown_adapter = MarkItDownAdapter(
            config=MarkItDownConfig(enable_llm=False)
        )
        settings = get_settings()
        self.claude_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process(self, file_path: Path) -> SimpleProcessorResult:
        """
        Process PDF document into structured data.

        Args:
            file_path: Path to PDF file

        Returns:
            ProcessorResult with extracted text and analysis

        Raises:
            ValueError: If file processing fails
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            # Extract text content from PDF
            text_content = await self._extract_text(file_path)

            if not text_content or text_content.strip() == "":
                raise ValueError("PDF file appears to be empty")

            # Extract document metadata and key info
            analysis = await self._analyze_content(text_content)

            return SimpleProcessorResult(
                content={
                    "full_text": text_content,
                    "analysis": analysis,
                },
                metadata={
                    "file_type": file_path.suffix.lower(),
                    "file_size": file_path.stat().st_size,
                    "document_type": analysis.get("document_type", "unknown"),
                },
            )

        except Exception as e:
            logger.error(
                f"Error processing PDF {file_path.name}: {e}",
                exc_info=True,
                extra={"file_path": str(file_path)},
            )
            raise ValueError(f"Failed to process PDF: {str(e)}") from e

    async def _extract_text(self, file_path: Path) -> str:
        """
        Extract text from PDF file using MarkItDown.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content

        Raises:
            ValueError: If extraction fails
        """
        suffix = file_path.suffix.lower()

        if suffix != ".pdf":
            raise ValueError(f"Unsupported file type for PDFProcessor: {suffix}")

        try:
            # Use MarkItDown for PDF conversion
            markdown_content = await self.markdown_adapter.convert(file_path)
            # Extract text from markdown (remove markdown syntax)
            return self._markdown_to_text(markdown_content)

        except Exception as e:
            logger.error(f"Text extraction failed for {file_path.name}: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}") from e

    @staticmethod
    def _markdown_to_text(markdown_content: str) -> str:
        """
        Convert markdown to plain text by removing markdown syntax.

        Args:
            markdown_content: Markdown formatted text

        Returns:
            Plain text content
        """
        import re

        # Remove markdown links [text](url) -> text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", markdown_content)

        # Remove markdown headers #, ##, ### etc
        text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

        # Remove markdown bold **text** -> text
        text = re.sub(r"\*\*([^\*]+)\*\*", r"\1", text)

        # Remove markdown italic *text* -> text
        text = re.sub(r"\*([^\*]+)\*", r"\1", text)

        # Remove markdown code blocks ```
        text = re.sub(r"```[^\`]*```", "", text, flags=re.DOTALL)

        # Remove inline code `text` -> text
        text = re.sub(r"`([^\`]+)`", r"\1", text)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Clean up excessive whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = text.strip()

        return text

    async def _analyze_content(self, text: str) -> Dict[str, Any]:
        """
        Analyze PDF content using Claude API.

        Args:
            text: Full PDF text

        Returns:
            Dictionary with analysis results:
            - document_type: Type of document (report, article, manual, etc.)
            - key_topics: Main topics covered
            - summary: Brief summary of content
            - metadata: Document metadata if detected

        Raises:
            ValueError: If Claude API call fails
        """
        prompt = """
        Analyze the following document text and extract:
        1. Document type (e.g., report, article, manual, whitepaper, etc.)
        2. Key topics or main themes
        3. Brief summary (2-3 sentences)
        4. Any metadata detected (author, date, organization, etc.)

        IMPORTANT: Return ONLY valid JSON, no markdown, no explanations.

        Document text:
        {document_text}

        Extract and return exactly this JSON structure:
        {{
            "document_type": "string",
            "key_topics": ["string"],
            "summary": "string",
            "metadata": {{
                "author": "string or null",
                "date": "string or null",
                "organization": "string or null",
                "version": "string or null"
            }},
            "content_quality": {{
                "readability": "high|medium|low",
                "structure_level": "well-structured|moderate|minimal",
                "completeness": 0.0-1.0
            }}
        }}
        """.format(
            document_text=text[:4000]  # Limit to first 4000 chars for API efficiency
        )

        try:
            # Call Claude API in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}],
                ),
            )

            # Extract and parse JSON response
            if not response.content or len(response.content) == 0:
                raise ValueError("Empty response from Claude API")

            first_block = response.content[0]
            response_text = getattr(first_block, "text", None)
            if not response_text:
                raise ValueError("Response does not contain text content")

            # Try to extract JSON from response
            json_match = self._extract_json_from_response(response_text)

            if json_match:
                return json_match
            else:
                logger.warning("Claude API returned non-JSON response, using fallback")
                return self._get_fallback_analysis()

        except anthropic.APIError as e:
            logger.error(f"Claude API error during content analysis: {e}")
            # Return fallback analysis on API errors
            return self._get_fallback_analysis()
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return self._get_fallback_analysis()

    @staticmethod
    def _extract_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from Claude API response with fallbacks.

        Args:
            response_text: Raw response text from Claude API

        Returns:
            Parsed JSON dictionary or None if parsing fails
        """
        import re

        try:
            # Try direct JSON parsing first
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}")

        if json_start >= 0 and json_end > json_start:
            try:
                json_str = response_text[json_start : json_end + 1]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Try removing markdown code blocks
        json_pattern = r"```(?:json)?\s*({.*?})\s*```"
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _get_fallback_analysis() -> Dict[str, Any]:
        """
        Get fallback analysis when extraction fails.

        Returns:
            Valid but minimal analysis dictionary
        """
        return {
            "document_type": "unknown",
            "key_topics": [],
            "summary": "Unable to analyze document content",
            "metadata": {
                "author": None,
                "date": None,
                "organization": None,
                "version": None,
            },
            "content_quality": {
                "readability": "unknown",
                "structure_level": "unknown",
                "completeness": 0.0,
            },
        }

    async def process_batch(
        self, file_paths: List[Path]
    ) -> List[SimpleProcessorResult]:
        """
        Process multiple PDF files in parallel with concurrency control.

        Uses semaphore to limit concurrent Claude API calls while maximizing throughput.

        Args:
            file_paths: List of PDF file paths

        Returns:
            List of SimpleProcessorResult for each PDF

        Note:
            Failures are captured in results with error metadata instead of raising.
            This allows batch processing to continue even if some files fail.
        """
        logger.info(
            f"Processing batch of {len(file_paths)} PDFs "
            f"(max {self.max_concurrent} concurrent)"
        )

        # Create tasks with semaphore control
        tasks = [self._process_with_semaphore(file_path) for file_path in file_paths]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results - convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing PDF {file_paths[i].name}: {result}")
                # Create error result with fallback analysis
                error_result = SimpleProcessorResult(
                    content={
                        "full_text": "",
                        "analysis": self._get_fallback_analysis(),
                    },
                    metadata={
                        "file_type": file_paths[i].suffix.lower(),
                        "file_size": 0,
                        "document_type": "unknown",
                        "processing_error": str(result),
                    },
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)

        successful = len(
            [r for r in processed_results if "processing_error" not in r.metadata]
        )
        failed = len(processed_results) - successful

        logger.info(
            f"Batch processing complete: {successful} successful, {failed} failed"
        )
        return processed_results

    async def _process_with_semaphore(self, file_path: Path) -> SimpleProcessorResult:
        """
        Process PDF with semaphore to control concurrency.

        Args:
            file_path: Path to PDF file

        Returns:
            SimpleProcessorResult

        Raises:
            Exception if processing fails (caught by gather in process_batch)
        """
        async with self.semaphore:
            return await self.process(file_path)

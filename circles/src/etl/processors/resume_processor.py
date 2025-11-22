"""
Resume Processor - Converts PDF/DOCX/TXT to structured data.

Uses MarkItDown for universal document conversion and Claude API for NLP extraction.
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


class ResumeProcessor:
    """Process resume files into structured data with batch support."""

    def __init__(self, max_concurrent: int = 10):
        """
        Initialize ResumeProcessor with MarkItDown and Claude API.

        Args:
            max_concurrent: Maximum concurrent Claude API calls (default 10)
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
        Process resume file into structured data.

        Args:
            file_path: Path to resume file (PDF, DOCX, TXT)

        Returns:
            ProcessorResult with structured data and full text

        Raises:
            ValueError: If file processing fails
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        try:
            # Extract text content from file
            text_content = await self._extract_text(file_path)

            if not text_content or text_content.strip() == "":
                raise ValueError("Resume file appears to be empty")

            # Extract structured data using Claude API
            structured = await self._extract_structured_data(text_content)

            return SimpleProcessorResult(
                content={"full_text": text_content, "structured": structured},
                metadata={
                    "file_type": file_path.suffix.lower(),
                    "file_size": file_path.stat().st_size,
                },
            )

        except Exception as e:
            logger.error(
                f"Error processing resume {file_path.name}: {e}",
                exc_info=True,
                extra={"file_path": str(file_path)},
            )
            raise ValueError(f"Failed to process resume: {str(e)}") from e

    async def _extract_text(self, file_path: Path) -> str:
        """
        Extract text from resume file using MarkItDown for PDF/DOCX or direct read for TXT.

        Args:
            file_path: Path to resume file

        Returns:
            Extracted text content

        Raises:
            ValueError: If extraction fails
        """
        suffix = file_path.suffix.lower()

        try:
            if suffix == ".txt":
                # Direct text file reading with encoding fallback
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()
                except UnicodeDecodeError:
                    with open(file_path, "r", encoding="latin-1") as f:
                        return f.read()

            elif suffix in [".pdf", ".docx"]:
                # Use MarkItDown for PDF and DOCX files
                markdown_content = await self.markdown_adapter.convert(file_path)
                # Extract text from markdown (remove markdown syntax)
                return self._markdown_to_text(markdown_content)

            else:
                raise ValueError(f"Unsupported file type: {suffix}")

        except Exception as e:
            logger.error(f"Text extraction failed for {file_path.name}: {e}")
            raise ValueError(f"Failed to extract text from resume: {str(e)}") from e

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

    async def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from resume text using Claude API.

        Args:
            text: Full resume text

        Returns:
            Dictionary with structured resume fields:
            - work_experience: List of work experiences
            - education: List of education entries
            - skills: List of skills
            - contact_info: Dictionary with contact information

        Raises:
            ValueError: If Claude API call fails
        """
        prompt = """
        Analyze the following resume and extract structured information in JSON format.

        IMPORTANT: Return ONLY valid JSON, no markdown, no explanations.

        Resume text:
        {resume_text}

        Extract and return exactly this JSON structure:
        {{
            "contact_info": {{
                "name": "string or null",
                "email": "string or null",
                "phone": "string or null",
                "location": "string or null",
                "linkedin": "string or null",
                "website": "string or null"
            }},
            "work_experience": [
                {{
                    "company": "string",
                    "position": "string",
                    "start_date": "string or null",
                    "end_date": "string or null",
                    "current": "boolean",
                    "description": "string",
                    "achievements": ["string"]
                }}
            ],
            "education": [
                {{
                    "institution": "string",
                    "degree": "string",
                    "field": "string or null",
                    "graduation_date": "string or null",
                    "gpa": "string or null",
                    "achievements": ["string"]
                }}
            ],
            "skills": [
                {{
                    "category": "string",
                    "items": ["string"]
                }}
            ]
        }}
        """.format(
            resume_text=text[:3000]  # Limit to first 3000 chars for API efficiency
        )

        try:
            # Call Claude API synchronously in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                ),
            )

            # Extract and parse JSON response
            response_text = response.content[0].text

            # Try to extract JSON from response
            json_match = self._extract_json_from_response(response_text)

            if json_match:
                return json_match
            else:
                logger.warning("Claude API returned non-JSON response, using fallback")
                return self._get_fallback_structure()

        except anthropic.APIError as e:
            logger.error(f"Claude API error during structured extraction: {e}")
            # Return fallback structure on API errors
            return self._get_fallback_structure()
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return self._get_fallback_structure()

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
    def _get_fallback_structure() -> Dict[str, Any]:
        """
        Get fallback structure when extraction fails.

        Returns:
            Empty but valid structured data dictionary
        """
        return {
            "contact_info": {
                "name": None,
                "email": None,
                "phone": None,
                "location": None,
                "linkedin": None,
                "website": None,
            },
            "work_experience": [],
            "education": [],
            "skills": [],
        }

    async def process_batch(
        self, file_paths: List[Path]
    ) -> List[SimpleProcessorResult]:
        """
        Process multiple resume files in parallel with concurrency control.

        Uses semaphore to limit concurrent Claude API calls while maximizing throughput.

        Args:
            file_paths: List of resume file paths

        Returns:
            List of SimpleProcessorResult for each resume

        Note:
            Failures are captured in results with error metadata instead of raising.
            This allows batch processing to continue even if some files fail.
        """
        logger.info(
            f"Processing batch of {len(file_paths)} resumes "
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
                logger.error(f"Error processing resume {file_paths[i].name}: {result}")
                # Create error result with fallback structure
                error_result = SimpleProcessorResult(
                    content={
                        "full_text": "",
                        "structured": self._get_fallback_structure(),
                    },
                    metadata={
                        "file_type": file_paths[i].suffix.lower(),
                        "file_size": 0,
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
        Process resume with semaphore to control concurrency.

        Args:
            file_path: Path to resume file

        Returns:
            SimpleProcessorResult

        Raises:
            Exception if processing fails (caught by gather in process_batch)
        """
        async with self.semaphore:
            return await self.process(file_path)

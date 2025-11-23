"""
Calendar Processor - Parse ICS/iCal format calendar files.

Extracts:
- Calendar events
- Event patterns
- Inferred interests from event titles/descriptions
- Event frequency analysis and scheduling insights

Handles batch processing with concurrency control and comprehensive error handling.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SimpleProcessorResult:
    """Simple result container for processor outputs."""

    content: Dict[str, Any]
    metadata: Dict[str, Any]
    embeddings: Optional[Dict[str, Any]] = None


class CalendarProcessor:
    """Process calendar files in ICS/iCal format with batch processing support."""

    def __init__(self, max_concurrent: int = 5):
        """
        Initialize processor with concurrency control.

        Args:
            max_concurrent: Maximum concurrent calendar file processing (default 5)
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process(self, file_path: Path) -> SimpleProcessorResult:
        """
        Process calendar file asynchronously.

        Args:
            file_path: Path to .ics calendar file

        Returns:
            SimpleProcessorResult with parsed events and patterns

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid format
        """
        try:
            # Check file exists
            if not file_path.exists():
                raise FileNotFoundError(f"Calendar file not found: {file_path}")

            # Read ICS file asynchronously
            def _read_file():
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()

            ics_content = await asyncio.to_thread(_read_file)

            # Validate file has content
            if not ics_content.strip():
                raise ValueError("Calendar file appears to be empty")

            # Parse and analyze events
            events = self._parse_ics_events(ics_content)
            date_range = self._get_date_range(events)
            interests = self._extract_interests(events)
            patterns = self._analyze_patterns(events)

            # Get file size asynchronously
            file_size = (await asyncio.to_thread(file_path.stat)).st_size

            # Build result
            result_content = {
                "events": events[:50],  # Limit for DB storage
                "event_count": len(events),
                "date_range_start": date_range[0],
                "date_range_end": date_range[1],
                "interests": interests,
            }

            metadata = {
                "file_type": file_path.suffix.lower(),
                "file_size": file_size,
                "event_patterns": patterns,
            }

            return SimpleProcessorResult(content=result_content, metadata=metadata)

        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid calendar file {file_path.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing calendar file {file_path.name}: {e}")
            raise

    @staticmethod
    def _parse_ics_events(ics_content: str) -> list[dict]:
        """Parse events from ICS file content."""
        events = []
        current_event = {}

        for line in ics_content.split("\n"):
            line = line.strip()

            if line.startswith("BEGIN:VEVENT"):
                current_event = {}
            elif line.startswith("END:VEVENT"):
                if current_event:
                    events.append(current_event)
            elif line.startswith("SUMMARY:"):
                current_event["title"] = line.replace("SUMMARY:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                current_event["description"] = line.replace("DESCRIPTION:", "").strip()[
                    :500
                ]
            elif line.startswith("DTSTART"):
                current_event["start"] = CalendarProcessor._parse_datetime(line)
            elif line.startswith("DTEND"):
                current_event["end"] = CalendarProcessor._parse_datetime(line)
            elif line.startswith("LOCATION:"):
                current_event["location"] = line.replace("LOCATION:", "").strip()

        return events

    @staticmethod
    def _parse_datetime(line: str) -> Optional[str]:
        """Extract datetime from DTSTART/DTEND line."""
        match = re.search(r":(\d{8}T?\d*Z?)", line)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _get_date_range(events: list) -> tuple[Optional[str], Optional[str]]:
        """Get earliest and latest event dates."""
        if not events:
            return None, None

        dates = []
        for event in events:
            if "start" in event:
                dates.append(event["start"])
            if "end" in event:
                dates.append(event["end"])

        if dates:
            dates.sort()
            return dates[0], dates[-1]
        return None, None

    @staticmethod
    def _extract_interests(events: list) -> list[str]:
        """Extract inferred interests from event titles."""
        interests = set()
        keywords = {
            "development": ["dev", "coding", "programming", "github", "sprint"],
            "fitness": ["gym", "workout", "run", "exercise", "yoga"],
            "travel": ["flight", "trip", "vacation", "hotel", "travel"],
            "work": ["meeting", "standup", "review", "conference", "presentation"],
            "learning": ["course", "learning", "training", "webinar", "lecture"],
            "social": ["dinner", "lunch", "coffee", "party", "hangout"],
        }

        text = " ".join([e.get("title", "").lower() for e in events])

        for category, keywords_list in keywords.items():
            for keyword in keywords_list:
                if keyword in text:
                    interests.add(category)
                    break

        return list(interests)

    @staticmethod
    def _analyze_patterns(events: list) -> dict:
        """Analyze event patterns."""
        if not events:
            return {}

        # Count events by approximate time of day (from title/description)
        busy_level = "moderate" if len(events) > 50 else "light"
        if len(events) > 100:
            busy_level = "heavy"

        return {
            "total_events": len(events),
            "busy_level": busy_level,
            "types": ["meetings", "personal", "fitness", "travel"],
        }

    async def process_batch(
        self, file_paths: List[Path]
    ) -> List[SimpleProcessorResult]:
        """
        Process multiple calendar files in parallel with concurrency control.

        Uses semaphore to limit concurrent file processing while maximizing throughput.

        Args:
            file_paths: List of calendar file paths

        Returns:
            List of SimpleProcessorResult for each calendar file

        Note:
            Failures are captured in results with error metadata instead of raising.
            This allows batch processing to continue even if some files fail.
        """
        logger.info(
            f"Processing batch of {len(file_paths)} calendar files "
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
                logger.error(
                    f"Error processing calendar {file_paths[i].name}: {result}"
                )
                # Create error result with fallback data
                error_result = SimpleProcessorResult(
                    content={
                        "events": [],
                        "event_count": 0,
                        "date_range_start": None,
                        "date_range_end": None,
                        "interests": [],
                    },
                    metadata={
                        "file_type": file_paths[i].suffix.lower(),
                        "file_size": 0,
                        "event_patterns": {},
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
        Process calendar with semaphore to control concurrency.

        Args:
            file_path: Path to calendar file

        Returns:
            SimpleProcessorResult

        Raises:
            Exception if processing fails (caught by gather in process_batch)
        """
        async with self.semaphore:
            return await self.process(file_path)

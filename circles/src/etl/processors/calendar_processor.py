"""
Calendar Processor - Parse ICS/iCal format calendar files.

Extracts:
- Calendar events
- Event patterns
- Inferred interests from event titles/descriptions
"""

import re
from pathlib import Path
from typing import Any, Dict, Optional


class SimpleProcessorResult:
    """Simple result container for processor outputs."""

    def __init__(
        self,
        content: Dict[str, Any],
        metadata: Dict[str, Any],
        embeddings: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.metadata = metadata
        self.embeddings = embeddings or {}


class CalendarProcessor:
    """Process calendar files in ICS/iCal format."""

    async def process(self, file_path: Path) -> SimpleProcessorResult:
        """
        Process calendar file.

        Args:
            file_path: Path to .ics calendar file

        Returns:
            SimpleProcessorResult with parsed events and patterns
        """
        # Read and parse ICS file
        with open(file_path, "r", encoding="utf-8") as f:
            ics_content = f.read()

        events = self._parse_ics_events(ics_content)
        date_range = self._get_date_range(events)
        interests = self._extract_interests(events)
        patterns = self._analyze_patterns(events)

        result_content = {
            "events": events[:50],  # Limit for DB storage
            "event_count": len(events),
            "date_range_start": date_range[0],
            "date_range_end": date_range[1],
            "interests": interests,
        }

        return SimpleProcessorResult(
            content=result_content,
            metadata={
                "file_type": file_path.suffix.lower(),
                "file_size": file_path.stat().st_size,
                "event_patterns": patterns,
            },
        )

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

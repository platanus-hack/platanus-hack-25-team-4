"""
Unit tests for CalendarProcessor.

Tests ICS/iCal calendar file processing and event extraction.
"""

import pytest

from circles.src.etl.processors.calendar_processor import (
    CalendarProcessor,
    SimpleProcessorResult,
)
from circles.tests.fixtures.fixture_factories import DataTypeFixtures


@pytest.mark.unit
class TestCalendarProcessor:
    """Test CalendarProcessor functionality."""

    @pytest.fixture
    async def calendar_processor(self):
        """Create a CalendarProcessor instance."""
        return CalendarProcessor()

    @pytest.fixture
    def sample_ics_file(self, tmp_path):
        """Create a sample ICS calendar file."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
SUMMARY:Team Standup
DESCRIPTION:Daily team synchronization
DTSTART:20240115T090000Z
DTEND:20240115T093000Z
LOCATION:Conference Room A
END:VEVENT
BEGIN:VEVENT
SUMMARY:Project Review
DESCRIPTION:Monthly project status review
DTSTART:20240115T140000Z
DTEND:20240115T153000Z
LOCATION:Virtual - Zoom
END:VEVENT
BEGIN:VEVENT
SUMMARY:Coffee Meeting
DTSTART:20240116T100000Z
DTEND:20240116T110000Z
END:VEVENT
END:VCALENDAR
"""
        ics_path = tmp_path / "calendar.ics"
        ics_path.write_text(ics_content)
        return ics_path

    @pytest.fixture
    def empty_ics_file(self, tmp_path):
        """Create an empty ICS file."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
END:VCALENDAR
"""
        ics_path = tmp_path / "empty.ics"
        ics_path.write_text(ics_content)
        return ics_path

    @pytest.mark.asyncio
    async def test_process_valid_calendar(self, calendar_processor, sample_ics_file):
        """Test processing a valid ICS calendar file."""
        result = await calendar_processor.process(sample_ics_file)

        assert isinstance(result, SimpleProcessorResult)
        assert "events" in result.content
        assert "event_count" in result.content
        assert "date_range_start" in result.content
        assert "date_range_end" in result.content
        assert "interests" in result.content
        assert result.metadata["file_type"] == ".ics"

    @pytest.mark.asyncio
    async def test_parse_ics_events(self, calendar_processor, sample_ics_file):
        """Test parsing ICS events."""
        with open(sample_ics_file, "r") as f:
            ics_content = f.read()

        events = calendar_processor._parse_ics_events(ics_content)

        assert len(events) == 3
        assert events[0]["title"] == "Team Standup"
        assert events[1]["title"] == "Project Review"
        assert events[2]["title"] == "Coffee Meeting"

    def test_parse_ics_events_empty(self, calendar_processor):
        """Test parsing ICS with no events."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
END:VCALENDAR
"""
        events = calendar_processor._parse_ics_events(ics_content)

        assert events == []

    def test_parse_datetime(self, calendar_processor):
        """Test datetime parsing from DTSTART/DTEND lines."""
        test_cases = [
            ("DTSTART:20240115T090000Z", "20240115T090000Z"),
            ("DTSTART:20240115T090000", "20240115T090000"),
            ("DTSTART:20240115", "20240115"),
            ("DTEND;TZID=UTC:20240115T093000Z", "20240115T093000Z"),
        ]

        for line, expected in test_cases:
            result = calendar_processor._parse_datetime(line)
            assert result == expected

    def test_parse_datetime_invalid(self, calendar_processor):
        """Test datetime parsing with invalid format."""
        result = calendar_processor._parse_datetime("INVALID:LINE")

        assert result is None

    def test_get_date_range(self, calendar_processor):
        """Test extracting date range from events."""
        events = [
            {"start": "20240110T100000Z", "end": "20240110T110000Z"},
            {"start": "20240115T140000Z", "end": "20240115T153000Z"},
            {"start": "20240120T100000Z"},  # Only start date
        ]

        start, end = calendar_processor._get_date_range(events)

        assert start == "20240110T100000Z"
        assert end == "20240120T100000Z"

    def test_get_date_range_empty(self, calendar_processor):
        """Test date range with empty events."""
        start, end = calendar_processor._get_date_range([])

        assert start is None
        assert end is None

    def test_extract_interests(self, calendar_processor):
        """Test interest extraction from event titles."""
        events = [
            {"title": "GitHub sprint planning"},
            {"title": "Yoga and workout session"},
            {"title": "Flight to New York"},
            {"title": "Team standup meeting"},
            {"title": "Python course webinar"},
            {"title": "Dinner with friends"},
        ]

        interests = calendar_processor._extract_interests(events)

        assert "development" in interests
        assert "fitness" in interests
        assert "travel" in interests
        assert "work" in interests
        assert "learning" in interests
        assert "social" in interests

    def test_extract_interests_case_insensitive(self, calendar_processor):
        """Test that interest extraction is case-insensitive."""
        events = [
            {"title": "GYM WORKOUT"},
            {"title": "Programming Sprint"},
            {"title": "FLIGHT BOOKING"},
        ]

        interests = calendar_processor._extract_interests(events)

        assert "fitness" in interests
        assert "development" in interests
        assert "travel" in interests

    def test_extract_interests_empty(self, calendar_processor):
        """Test interest extraction with empty events."""
        interests = calendar_processor._extract_interests([])

        assert interests == []

    def test_extract_interests_no_matches(self, calendar_processor):
        """Test interest extraction with no matching keywords."""
        events = [
            {"title": "Lorem ipsum dolor"},
            {"title": "Random event"},
        ]

        interests = calendar_processor._extract_interests(events)

        assert interests == []

    def test_analyze_patterns(self, calendar_processor):
        """Test event pattern analysis."""
        events = [{"title": f"Event {i}"} for i in range(75)]

        patterns = calendar_processor._analyze_patterns(events)

        assert "total_events" in patterns
        assert patterns["total_events"] == 75
        assert patterns["busy_level"] == "heavy"
        assert "types" in patterns

    def test_analyze_patterns_light_busy(self, calendar_processor):
        """Test pattern analysis with light busy level."""
        events = [{"title": f"Event {i}"} for i in range(10)]

        patterns = calendar_processor._analyze_patterns(events)

        assert patterns["busy_level"] == "light"

    def test_analyze_patterns_moderate_busy(self, calendar_processor):
        """Test pattern analysis with moderate busy level."""
        events = [{"title": f"Event {i}"} for i in range(75)]

        patterns = calendar_processor._analyze_patterns(events)

        assert patterns["busy_level"] == "heavy"

    def test_analyze_patterns_empty(self, calendar_processor):
        """Test pattern analysis with no events."""
        patterns = calendar_processor._analyze_patterns([])

        assert patterns == {}

    @pytest.mark.asyncio
    async def test_process_empty_calendar(self, calendar_processor, empty_ics_file):
        """Test processing empty calendar file."""
        result = await calendar_processor.process(empty_ics_file)

        assert isinstance(result, SimpleProcessorResult)
        assert result.content["event_count"] == 0
        assert result.content["events"] == []

    @pytest.mark.asyncio
    async def test_process_file_not_found(self, calendar_processor, tmp_path):
        """Test processing non-existent file."""
        non_existent = tmp_path / "non_existent.ics"

        with pytest.raises(FileNotFoundError):
            await calendar_processor.process(non_existent)

    @pytest.mark.asyncio
    async def test_processor_result_structure(
        self, calendar_processor, sample_ics_file
    ):
        """Test that processor result has correct structure."""
        result = await calendar_processor.process(sample_ics_file)

        # Verify SimpleProcessorResult structure
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")
        assert hasattr(result, "embeddings")

        # Verify content structure
        assert isinstance(result.content, dict)
        assert "events" in result.content
        assert "event_count" in result.content
        assert "date_range_start" in result.content
        assert "date_range_end" in result.content
        assert "interests" in result.content

        # Verify metadata structure
        assert isinstance(result.metadata, dict)
        assert "file_type" in result.metadata
        assert "file_size" in result.metadata
        assert "event_patterns" in result.metadata


@pytest.mark.unit
class TestCalendarProcessorIntegration:
    """Integration tests for CalendarProcessor with fixtures."""

    @pytest.fixture
    async def calendar_processor(self):
        """Create a CalendarProcessor instance."""
        return CalendarProcessor()

    @pytest.mark.asyncio
    async def test_process_with_fixture_data(self, calendar_processor):
        """Test processing with fixture data."""
        fixture_data = DataTypeFixtures.create_calendar_data()

        assert "calendar_owner" in fixture_data
        assert "total_events" in fixture_data
        assert "events" in fixture_data

        assert len(fixture_data["events"]) > 0

    @pytest.mark.asyncio
    async def test_event_structure_consistency(
        self, calendar_processor, sample_ics_file
    ):
        """Test that parsed events have consistent structure."""
        with open(sample_ics_file, "r") as f:
            ics_content = f.read()

        events = calendar_processor._parse_ics_events(ics_content)

        for event in events:
            assert isinstance(event, dict)
            assert "title" in event

    def test_parse_ics_with_descriptions(self, calendar_processor):
        """Test parsing ICS events with descriptions."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Test Event
DESCRIPTION:This is a test description
END:VEVENT
END:VCALENDAR
"""
        events = calendar_processor._parse_ics_events(ics_content)

        assert len(events) == 1
        assert "description" in events[0]
        assert events[0]["description"] == "This is a test description"

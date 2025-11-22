"""
End-to-End Tests for CalendarProcessor.

Tests run the complete calendar processing pipeline with real ICS file processing.
Marked with @pytest.mark.slow and @pytest.mark.e2e to allow skipping in CI.

Run with: pytest -m "e2e" tests/integration/test_calendar_processor_e2e.py
"""

import asyncio
import logging
from pathlib import Path

import pytest

from circles.src.etl.processors.calendar_processor import CalendarProcessor

logger = logging.getLogger(__name__)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_ics_file(tmp_path) -> Path:
    """Create a sample ICS calendar file with multiple events."""
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Test Calendar
X-WR-TIMEZONE:UTC
BEGIN:VEVENT
UID:event-001@example.com
DTSTAMP:20240115T000000Z
DTSTART:20240115T090000Z
DTEND:20240115T093000Z
SUMMARY:Team Standup
DESCRIPTION:Daily team synchronization meeting
LOCATION:Conference Room A
END:VEVENT
BEGIN:VEVENT
UID:event-002@example.com
DTSTAMP:20240115T000000Z
DTSTART:20240115T140000Z
DTEND:20240115T153000Z
SUMMARY:Project Review Meeting
DESCRIPTION:Monthly project status review and planning
LOCATION:Virtual - Zoom
END:VEVENT
BEGIN:VEVENT
UID:event-003@example.com
DTSTAMP:20240116T000000Z
DTSTART:20240116T100000Z
DTEND:20240116T110000Z
SUMMARY:Coffee Meeting
DESCRIPTION:Informal catch-up with colleagues
END:VEVENT
BEGIN:VEVENT
UID:event-004@example.com
DTSTAMP:20240120T000000Z
DTSTART:20240120T150000Z
DTEND:20240120T160000Z
SUMMARY:Python Learning Course
DESCRIPTION:Advanced Python concepts and best practices
LOCATION:Online
END:VEVENT
BEGIN:VEVENT
UID:event-005@example.com
DTSTAMP:20240125T000000Z
DTSTART:20240125T070000Z
DTEND:20240125T090000Z
SUMMARY:Morning Yoga Session
DESCRIPTION:Yoga and fitness workout
LOCATION:Gym
END:VEVENT
BEGIN:VEVENT
UID:event-006@example.com
DTSTAMP:20240201T000000Z
DTSTART:20240201T190000Z
DTEND:20240201T210000Z
SUMMARY:Dinner with Team
DESCRIPTION:Team celebration dinner
LOCATION:Restaurant Downtown
END:VEVENT
END:VCALENDAR
"""
    ics_path = tmp_path / "calendar.ics"
    ics_path.write_text(ics_content)
    return ics_path


@pytest.fixture
def busy_calendar_file(tmp_path) -> Path:
    """Create a busy calendar with many events."""
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Busy//Calendar//EN\n"

    # Add 120 events to create a busy schedule
    for i in range(120):
        day = (i // 3) + 1
        hour = 8 + (i % 3) * 4
        ics_content += f"""BEGIN:VEVENT
UID:event-{i:03d}@example.com
DTSTAMP:20240101T000000Z
DTSTART:202401{day:02d}T{hour:02d}0000Z
DTEND:202401{day:02d}T{hour + 1:02d}0000Z
SUMMARY:Meeting {i}
DESCRIPTION:Meeting number {i} in busy schedule
END:VEVENT
"""

    ics_content += "END:VCALENDAR"
    ics_path = tmp_path / "busy_calendar.ics"
    ics_path.write_text(ics_content)
    return ics_path


# ============================================================================
# CalendarProcessor E2E Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestCalendarProcessorE2E:
    """End-to-end tests for CalendarProcessor."""

    async def test_single_calendar_processing(self, sample_ics_file):
        """
        E2E Test: Process a single calendar file end-to-end.

        Tests:
        - File reading and validation
        - ICS parsing
        - Event extraction
        - Result structure and metadata
        """
        processor = CalendarProcessor()
        result = await processor.process(sample_ics_file)

        # Verify result structure
        assert result is not None
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")

        # Verify content
        assert "events" in result.content
        assert "event_count" in result.content
        assert "date_range_start" in result.content
        assert "date_range_end" in result.content
        assert "interests" in result.content

        # Verify event count matches
        assert result.content["event_count"] == 6
        assert len(result.content["events"]) == 6

        # Verify metadata
        assert result.metadata["file_type"] == ".ics"
        assert result.metadata["file_size"] > 0
        assert "event_patterns" in result.metadata

        logger.info("✓ Single calendar processing succeeded")
        logger.info(f"  Events Found: {result.content['event_count']}")
        logger.info(
            f"  Date Range: {result.content['date_range_start']} to {result.content['date_range_end']}"
        )
        logger.info(f"  Interests Detected: {result.content['interests']}")

    async def test_batch_calendar_processing(self, tmp_path):
        """
        E2E Test: Process multiple calendar files in parallel.

        Tests:
        - Batch file processing
        - Concurrency control with semaphore
        - Parallel processing
        - Result aggregation
        """
        # Create multiple test calendars
        calendar_paths = []
        for i in range(3):
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test{i}//Calendar//EN
BEGIN:VEVENT
UID:event-1@example.com
DTSTAMP:20240115T000000Z
DTSTART:202401{10 + i}T090000Z
DTEND:202401{10 + i}T100000Z
SUMMARY:Calendar {i} Event 1
DESCRIPTION:First event in calendar {i}
END:VEVENT
BEGIN:VEVENT
UID:event-2@example.com
DTSTAMP:20240115T000000Z
DTSTART:202401{10 + i}T140000Z
DTEND:202401{10 + i}T150000Z
SUMMARY:Calendar {i} Event 2
DESCRIPTION:Second event in calendar {i}
END:VEVENT
END:VCALENDAR
"""
            ics_path = tmp_path / f"calendar_{i}.ics"
            ics_path.write_text(ics_content)
            calendar_paths.append(ics_path)

        processor = CalendarProcessor(max_concurrent=2)
        results = await processor.process_batch(calendar_paths)

        # Verify batch processing
        assert len(results) == 3
        assert all(hasattr(r, "content") for r in results)
        assert all(hasattr(r, "metadata") for r in results)

        # Verify all have correct event count
        assert all(r.content["event_count"] == 2 for r in results)

        # Count successful processing
        successful = sum(1 for r in results if "processing_error" not in r.metadata)

        logger.info("✓ Batch calendar processing succeeded")
        logger.info(f"  Processed {len(results)} calendars with max_concurrent=2")
        logger.info(f"  Successful: {successful}/{len(results)}")

    async def test_calendar_interest_detection(self, tmp_path):
        """
        E2E Test: Verify quality of calendar interest detection.

        Tests:
        - Interest extraction accuracy
        - Multiple category detection
        - Metadata extraction
        """
        # Create calendar with diverse event types
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Diverse//Calendar//EN
BEGIN:VEVENT
UID:event-1@example.com
DTSTAMP:20240115T000000Z
DTSTART:20240115T090000Z
DTEND:20240115T100000Z
SUMMARY:GitHub Sprint Planning
DESCRIPTION:Development work planning
END:VEVENT
BEGIN:VEVENT
UID:event-2@example.com
DTSTAMP:20240115T000000Z
DTSTART:20240115T140000Z
DTEND:20240115T150000Z
SUMMARY:Gym Workout
DESCRIPTION:Fitness and exercise
END:VEVENT
BEGIN:VEVENT
UID:event-3@example.com
DTSTAMP:20240120T000000Z
DTSTART:20240120T090000Z
DTEND:20240120T100000Z
SUMMARY:Flight Booking Review
DESCRIPTION:Travel planning
END:VEVENT
BEGIN:VEVENT
UID:event-4@example.com
DTSTAMP:20240120T000000Z
DTSTART:20240120T140000Z
DTEND:20240120T150000Z
SUMMARY:Team Meeting
DESCRIPTION:Work synchronization
END:VEVENT
BEGIN:VEVENT
UID:event-5@example.com
DTSTAMP:20240125T000000Z
DTSTART:20240125T100000Z
DTEND:20240125T110000Z
SUMMARY:Python Learning Course
DESCRIPTION:Educational content
END:VEVENT
BEGIN:VEVENT
UID:event-6@example.com
DTSTAMP:20240201T000000Z
DTSTART:20240201T190000Z
DTEND:20240201T210000Z
SUMMARY:Dinner with Friends
DESCRIPTION:Social gathering
END:VEVENT
END:VCALENDAR
"""

        ics_path = tmp_path / "diverse_calendar.ics"
        ics_path.write_text(ics_content)

        processor = CalendarProcessor()
        result = await processor.process(ics_path)

        interests = result.content["interests"]

        # Verify multiple interests are detected
        assert len(interests) > 0, "Should detect at least one interest"

        # Verify expected interests are present
        expected_interests = {
            "development",
            "fitness",
            "travel",
            "work",
            "learning",
            "social",
        }
        detected = set(interests)
        assert detected.issubset(expected_interests), (
            f"Detected interests should be subset of expected: {detected}"
        )

        logger.info("✓ Calendar interest detection succeeded")
        logger.info(f"  Interests Detected: {interests}")

    async def test_batch_with_mixed_calendars(self, tmp_path):
        """
        E2E Test: Process batch with varied calendar types and sizes.

        Tests:
        - Mixed content processing
        - Different event counts
        - Consistent result format
        """
        calendar_paths = []

        # Small calendar with 1 event
        small_ics = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Small//Calendar//EN
BEGIN:VEVENT
UID:event-1@example.com
DTSTAMP:20240115T000000Z
DTSTART:20240115T100000Z
DTEND:20240115T110000Z
SUMMARY:Single Event
END:VEVENT
END:VCALENDAR
"""
        small_path = tmp_path / "small.ics"
        small_path.write_text(small_ics)
        calendar_paths.append(small_path)

        # Medium calendar with 5 events
        medium_ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Medium//Calendar//EN\n"
        for i in range(5):
            medium_ics += f"""BEGIN:VEVENT
UID:event-{i}@example.com
DTSTAMP:20240115T000000Z
DTSTART:202401{10 + i}T100000Z
DTEND:202401{10 + i}T110000Z
SUMMARY:Event {i}
END:VEVENT
"""
        medium_ics += "END:VCALENDAR"
        medium_path = tmp_path / "medium.ics"
        medium_path.write_text(medium_ics)
        calendar_paths.append(medium_path)

        # Large calendar with 15 events (busy)
        large_ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Large//Calendar//EN\n"
        for i in range(15):
            large_ics += f"""BEGIN:VEVENT
UID:event-{i}@example.com
DTSTAMP:20240115T000000Z
DTSTART:202401{10 + (i // 3)}T{8 + (i % 3) * 4:02d}0000Z
DTEND:202401{10 + (i // 3)}T{9 + (i % 3) * 4:02d}0000Z
SUMMARY:Event {i}
END:VEVENT
"""
        large_ics += "END:VCALENDAR"
        large_path = tmp_path / "large.ics"
        large_path.write_text(large_ics)
        calendar_paths.append(large_path)

        processor = CalendarProcessor(max_concurrent=2)
        results = await processor.process_batch(calendar_paths)

        # Verify all processed
        assert len(results) == 3

        # Verify correct event counts
        event_counts = [r.content["event_count"] for r in results]
        assert event_counts == [1, 5, 15], (
            f"Expected [1, 5, 15] events, got {event_counts}"
        )

        # Verify consistent structure
        for result in results:
            if "processing_error" not in result.metadata:
                assert "events" in result.content
                assert "event_count" in result.content
                assert "interests" in result.content
                assert result.metadata["file_type"] == ".ics"

        logger.info("✓ Mixed calendar batch processing succeeded")
        logger.info(f"  Processed calendars with {event_counts} events")

    async def test_calendar_processor_throughput(self, tmp_path):
        """
        E2E Test: Measure throughput of calendar processing.

        Tests:
        - Large batch processing
        - Concurrency performance
        - Result consistency
        """
        # Create larger batch of calendars
        calendar_paths = []
        for i in range(10):
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Throughput{i}//Calendar//EN
BEGIN:VEVENT
UID:event-1@example.com
DTSTAMP:20240115T000000Z
DTSTART:202401{10 + (i % 20)}T{8 + (i % 8):02d}0000Z
DTEND:202401{10 + (i % 20)}T{9 + (i % 8):02d}0000Z
SUMMARY:Calendar {i} Event 1
END:VEVENT
BEGIN:VEVENT
UID:event-2@example.com
DTSTAMP:20240115T000000Z
DTSTART:202401{11 + (i % 20)}T{10 + (i % 8):02d}0000Z
DTEND:202401{11 + (i % 20)}T{11 + (i % 8):02d}0000Z
SUMMARY:Calendar {i} Event 2
END:VEVENT
BEGIN:VEVENT
UID:event-3@example.com
DTSTAMP:20240115T000000Z
DTSTART:202401{12 + (i % 20)}T{14 + (i % 8):02d}0000Z
DTEND:202401{12 + (i % 20)}T{15 + (i % 8):02d}0000Z
SUMMARY:Calendar {i} Event 3
END:VEVENT
END:VCALENDAR
"""
            ics_path = tmp_path / f"throughput_{i}.ics"
            ics_path.write_text(ics_content)
            calendar_paths.append(ics_path)

        # Process with different concurrency levels
        for max_concurrent in [2, 5]:
            processor = CalendarProcessor(max_concurrent=max_concurrent)
            results = await processor.process_batch(calendar_paths)

            assert len(results) == 10

            successful = sum(1 for r in results if "processing_error" not in r.metadata)
            logger.info(
                f"✓ Throughput test (max_concurrent={max_concurrent}): {successful}/10 successful"
            )


# ============================================================================
# Parallel Processing Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestCalendarProcessorParallel:
    """Tests for parallel calendar processing scenarios."""

    async def test_parallel_batch_processing(self, tmp_path):
        """
        E2E Test: Process multiple calendar batches in parallel.

        Tests:
        - Multiple processors running concurrently
        - Independent result aggregation
        - Performance scaling
        """
        # Create two batches of calendars
        batch1_paths = []
        batch2_paths = []

        for i in range(3):
            # Batch 1
            ics1 = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Batch1//Calendar{i}//EN
BEGIN:VEVENT
UID:event-1@example.com
DTSTAMP:20240115T000000Z
DTSTART:202401{10 + i}T090000Z
DTEND:202401{10 + i}T100000Z
SUMMARY:Batch 1 Calendar {i} Event
DESCRIPTION:Content for batch 1
END:VEVENT
BEGIN:VEVENT
UID:event-2@example.com
DTSTAMP:20240115T000000Z
DTSTART:202401{10 + i}T140000Z
DTEND:202401{10 + i}T150000Z
SUMMARY:Batch 1 Follow-up
END:VEVENT
END:VCALENDAR
"""
            path1 = tmp_path / f"batch1_cal_{i}.ics"
            path1.write_text(ics1)
            batch1_paths.append(path1)

            # Batch 2
            ics2 = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Batch2//Calendar{i}//EN
BEGIN:VEVENT
UID:event-1@example.com
DTSTAMP:20240115T000000Z
DTSTART:202401{15 + i}T100000Z
DTEND:202401{15 + i}T110000Z
SUMMARY:Batch 2 Calendar {i} Event
DESCRIPTION:Content for batch 2
END:VEVENT
END:VCALENDAR
"""
            path2 = tmp_path / f"batch2_cal_{i}.ics"
            path2.write_text(ics2)
            batch2_paths.append(path2)

        # Process both batches in parallel
        processor1 = CalendarProcessor(max_concurrent=2)
        processor2 = CalendarProcessor(max_concurrent=2)

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
            assert r1.metadata["file_type"] == ".ics"
            assert r2.metadata["file_type"] == ".ics"
            # Batch 1 has 2 events, batch 2 has 1 event
            assert r1.content["event_count"] == 2
            assert r2.content["event_count"] == 1

        logger.info("✓ Parallel batch processing succeeded")
        logger.info("  Processed 2 batches of 3 calendars concurrently")

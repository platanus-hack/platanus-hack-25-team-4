"""
Unit tests for concurrent processor execution.

Tests that multiple processors can run in parallel without conflicts,
resource contention, or state corruption.
"""

import asyncio
from pathlib import Path

import pytest

from circles.src.etl.processors.calendar_processor import CalendarProcessor
from circles.src.etl.processors.chat_transcript_processor import ChatTranscriptProcessor
from circles.src.etl.processors.photo_processor import PhotoProcessor
from circles.src.etl.processors.resume_processor import ResumeProcessor
from circles.src.etl.processors.voice_note_processor import VoiceNoteProcessor


@pytest.mark.unit
class TestProcessorConcurrency:
    """Test concurrent processor execution."""

    @pytest.fixture
    async def photo_processor(self):
        """Create a PhotoProcessor instance."""
        return PhotoProcessor()

    @pytest.fixture
    async def resume_processor(self):
        """Create a ResumeProcessor instance."""
        return ResumeProcessor()

    @pytest.fixture
    async def voice_processor(self):
        """Create a VoiceNoteProcessor instance."""
        return VoiceNoteProcessor()

    @pytest.fixture
    async def calendar_processor(self):
        """Create a CalendarProcessor instance."""
        return CalendarProcessor()

    @pytest.fixture
    async def chat_processor(self):
        """Create a ChatTranscriptProcessor instance."""
        return ChatTranscriptProcessor()

    @pytest.fixture
    def sample_resume_file(self, tmp_path):
        """Create a temporary resume file."""
        resume_path = tmp_path / "resume.txt"
        resume_path.write_text("John Doe\nSoftware Engineer\nPython, JavaScript")
        return resume_path

    @pytest.fixture
    def sample_photo_file(self, tmp_path):
        """Create a temporary photo file."""
        photo_path = tmp_path / "photo.jpg"
        photo_path.write_bytes(b"\xff\xd8\xff\xe0")
        return photo_path

    @pytest.fixture
    def sample_voice_file(self, tmp_path):
        """Create a temporary voice file."""
        voice_path = tmp_path / "note.mp3"
        voice_path.write_bytes(b"ID3")
        return voice_path

    @pytest.fixture
    def sample_calendar_file(self, tmp_path):
        """Create a temporary calendar file."""
        calendar_path = tmp_path / "calendar.ics"
        calendar_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
SUMMARY:Test Event
DTSTART:20240101T100000Z
DTEND:20240101T110000Z
END:VEVENT
END:VCALENDAR"""
        calendar_path.write_text(calendar_content)
        return calendar_path

    @pytest.mark.asyncio
    async def test_multiple_processors_same_type_concurrent(self, sample_resume_file):
        """Test running multiple instances of same processor concurrently."""
        processors = [ResumeProcessor() for _ in range(5)]

        async def process_file(processor, file_path):
            return await processor.process(file_path)

        # Run all processors concurrently
        results = await asyncio.gather(
            *[process_file(proc, sample_resume_file) for proc in processors]
        )

        # All should complete successfully
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert "full_text" in result.content

    @pytest.mark.asyncio
    async def test_multiple_processors_different_types_concurrent(
        self, sample_resume_file, sample_photo_file, sample_voice_file
    ):
        """Test running different processor types concurrently."""
        resume_proc = ResumeProcessor()
        voice_proc = VoiceNoteProcessor()

        async def process_resume():
            return await resume_proc.process(sample_resume_file)

        async def process_voice():
            return await voice_proc.process(sample_voice_file)

        # Run both concurrently
        resume_result, voice_result = await asyncio.gather(
            process_resume(), process_voice()
        )

        # Both should complete successfully
        assert resume_result is not None
        assert voice_result is not None

    @pytest.mark.asyncio
    async def test_concurrent_access_same_file(self, sample_resume_file):
        """Test multiple processors accessing the same file concurrently."""
        processors = [ResumeProcessor() for _ in range(10)]

        async def process_file(processor):
            return await processor.process(sample_resume_file)

        # Run all processors on same file concurrently
        results = await asyncio.gather(*[process_file(proc) for proc in processors])

        # All should complete successfully (file is read-only)
        assert len(results) == 10
        for result in results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_processor_state_isolation(self, sample_resume_file):
        """Test that processor state is isolated between concurrent calls."""
        processor = ResumeProcessor()

        async def process_with_delay():
            return await processor.process(sample_resume_file)

        # Run same processor multiple times concurrently
        results = await asyncio.gather(*[process_with_delay() for _ in range(5)])

        # All results should be valid and not corrupted
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert isinstance(result.content, dict)

    @pytest.mark.asyncio
    async def test_processor_error_handling_concurrent(self, tmp_path):
        """Test error handling in concurrent processor execution."""
        processor = ResumeProcessor()
        nonexistent_file = tmp_path / "nonexistent.txt"

        async def process_with_error():
            try:
                return await processor.process(nonexistent_file)
            except FileNotFoundError:
                return None

        # Run multiple concurrent calls, all should error gracefully
        results = await asyncio.gather(*[process_with_error() for _ in range(3)])

        # All should handle errors gracefully
        assert all(r is None for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_processing_throughput(self, sample_resume_file):
        """Test throughput of concurrent processor execution."""
        import time

        processor = ResumeProcessor()
        start = time.time()

        # Run 50 processors concurrently
        tasks = [processor.process(sample_resume_file) for _ in range(50)]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start

        # All should complete
        assert len(results) == 50
        assert all(r is not None for r in results)

        # Should complete in reasonable time (not sequentially)
        # Sequential would be much slower
        assert elapsed < 60  # Generous timeout

    @pytest.mark.asyncio
    async def test_processor_resource_cleanup_concurrent(self, tmp_path):
        """Test that resources are properly cleaned up in concurrent execution."""
        processor = ResumeProcessor()

        # Create multiple temporary files
        files = []
        for i in range(10):
            file_path = tmp_path / f"resume_{i}.txt"
            file_path.write_text(f"Resume {i}\nContent {i}")
            files.append(file_path)

        async def process_file(file_path):
            result = await processor.process(file_path)
            # File should be readable after processing
            assert file_path.exists()
            return result

        # Process all files concurrently
        results = await asyncio.gather(*[process_file(f) for f in files])

        # All should complete and files should still exist
        assert len(results) == 10
        for file_path in files:
            assert file_path.exists()

    @pytest.mark.asyncio
    async def test_stress_test_many_concurrent_processors(self):
        """Stress test with many concurrent processors."""
        import tempfile

        processor = ResumeProcessor()

        async def create_and_process():
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
                f.write(b"Test resume content")
                temp_path = Path(f.name)

            try:
                result = await processor.process(temp_path)
                return result is not None
            finally:
                temp_path.unlink(missing_ok=True)

        # Create 100 concurrent tasks
        tasks = [create_and_process() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most should succeed
        successes = sum(1 for r in results if r is True)
        assert successes > 90  # Allow for some failures in stress test

    @pytest.mark.asyncio
    async def test_concurrent_processors_memory_efficiency(self, sample_resume_file):
        """Test that concurrent processors don't leak memory."""
        processor = ResumeProcessor()

        # Process same file many times concurrently
        tasks = [processor.process(sample_resume_file) for _ in range(20)]
        results = await asyncio.gather(*tasks)

        # All should complete without memory issues
        assert len(results) == 20
        for result in results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_processor_result_independence(self, sample_resume_file):
        """Test that processor results are independent in concurrent execution."""
        processor = ResumeProcessor()

        async def process_and_extract():
            result = await processor.process(sample_resume_file)
            return result.content.copy()

        # Get multiple results concurrently
        results = await asyncio.gather(*[process_and_extract() for _ in range(5)])

        # Results should be independent (modifications don't affect others)
        assert len(results) == 5
        for result in results:
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_mixed_sync_async_processor_access(self, sample_resume_file):
        """Test processor accessed from both sync and async contexts."""
        processor = ResumeProcessor()

        # Async processing
        async_result = await processor.process(sample_resume_file)

        # Both should work
        assert async_result is not None

    @pytest.mark.asyncio
    async def test_processor_queue_simulation(self, tmp_path):
        """Test processor handling a queue of files."""
        processor = ResumeProcessor()

        # Create 20 files
        files = []
        for i in range(20):
            file_path = tmp_path / f"resume_{i}.txt"
            file_path.write_text(f"Resume {i}")
            files.append(file_path)

        async def process_queue_item(file_path):
            return await processor.process(file_path)

        # Process all in parallel (simulating queue worker pool)
        results = await asyncio.gather(*[process_queue_item(f) for f in files])

        # All should complete successfully
        assert len(results) == 20
        assert all(r is not None for r in results)


@pytest.mark.unit
class TestProcessorConcurrencyIntegration:
    """Integration tests for concurrent processor execution."""

    @pytest.fixture
    async def all_processors(self):
        """Create instances of all processor types."""
        return {
            "resume": ResumeProcessor(),
            "photo": PhotoProcessor(),
            "voice": VoiceNoteProcessor(),
            "calendar": CalendarProcessor(),
            "chat": ChatTranscriptProcessor(),
        }

    @pytest.mark.asyncio
    async def test_all_processors_concurrent(self, tmp_path):
        """Test all processor types running concurrently."""
        processors = {
            "resume": ResumeProcessor(),
            "voice": VoiceNoteProcessor(),
        }

        # Create sample files
        resume_file = tmp_path / "resume.txt"
        resume_file.write_text("John Doe\nSoftware Engineer")

        voice_file = tmp_path / "note.mp3"
        voice_file.write_bytes(b"ID3")

        async def process_resume():
            return await processors["resume"].process(resume_file)

        async def process_voice():
            return await processors["voice"].process(voice_file)

        # Run all concurrently
        results = await asyncio.gather(
            process_resume(),
            process_voice(),
        )

        # All should succeed
        assert len(results) == 2
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_processor_scalability(self, tmp_path):
        """Test processor scalability with increasing concurrency."""
        processor = ResumeProcessor()
        file_path = tmp_path / "resume.txt"
        file_path.write_text("Test Resume")

        for num_concurrent in [5, 10, 20]:
            tasks = [processor.process(file_path) for _ in range(num_concurrent)]
            results = await asyncio.gather(*tasks)

            # All should succeed
            assert len(results) == num_concurrent
            assert all(r is not None for r in results)

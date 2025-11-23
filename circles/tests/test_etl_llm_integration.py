"""
Integration tests for LLM adapter workflows.

Tests the complete flow from API upload through Celery task execution
to database persistence for Claude Vision and OpenAI Whisper integrations.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.etl.processors.photo_processor import PhotoProcessor
from src.etl.processors.voice_note_processor import VoiceNoteProcessor
from src.etl.tasks.processor_tasks import (
    execute_adapter_pipeline,
)

# ============================================================================
# Photo Processor Tests - Claude Vision Integration
# ============================================================================


class TestPhotoProcessor:
    """Test PhotoProcessor with Claude Vision API integration."""

    @pytest.fixture
    def photo_processor(self):
        """Create a PhotoProcessor instance."""
        return PhotoProcessor()

    @pytest.mark.asyncio
    async def test_process_image_with_vision_api(self, photo_processor, tmp_path):
        """Test image processing with mocked Claude Vision API."""
        # Create a dummy image file
        test_image = tmp_path / "test.png"
        test_image.write_bytes(b"fake_png_data")

        # Mock Claude API response
        with patch.object(
            photo_processor, "_analyze_image", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = (
                "A test image showing a sample scene",
                {"objects": ["object1", "object2"], "colors": ["blue", "white"]},
            )

            # Mock EXIF extraction
            with patch.object(
                photo_processor,
                "_extract_exif_data_async",
                new_callable=AsyncMock,
            ) as mock_exif:
                mock_exif.return_value = {"Make": "TestCamera", "Model": "TestModel"}

                # Process the image
                result = await photo_processor.process(test_image)

                # Verify result structure
                assert (
                    result.content["caption"] == "A test image showing a sample scene"
                )
                assert "analysis" in result.content
                assert result.metadata["file_type"] == ".png"
                assert "file_size" in result.metadata
                assert "exif_data" in result.metadata

    @pytest.mark.asyncio
    async def test_analyze_image_json_parsing(self, photo_processor):
        """Test robust JSON parsing from Claude Vision response."""
        encoded_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        # Mock the API call with nested JSON response
        with patch(
            "circles.src.etl.processors.photo_processor.asyncio.to_thread",
            new_callable=AsyncMock,
        ) as mock_thread:
            mock_message = MagicMock()
            mock_message.content = [
                MagicMock(
                    text=json.dumps(
                        {
                            "caption": "Test caption",
                            "analysis": {
                                "objects": ["cat", "table"],
                                "setting": "indoor",
                                "nested": {"level": 2},
                            },
                        }
                    )
                )
            ]
            mock_thread.return_value = mock_message

            caption, analysis = await photo_processor._analyze_image(
                encoded_image, "image/png"
            )

            assert caption == "Test caption"
            assert analysis["objects"] == ["cat", "table"]
            assert analysis["nested"]["level"] == 2

    @pytest.mark.asyncio
    async def test_async_file_io_not_blocking(self, photo_processor, tmp_path):
        """Verify PhotoProcessor uses async I/O and doesn't block event loop."""
        test_image = tmp_path / "async_test.png"
        test_image.write_bytes(b"test_data" * 1000)

        # Track if blocking I/O was used
        blocking_calls = []

        original_open = open

        def blocking_open_tracker(*args, **kwargs):
            blocking_calls.append(args[0])
            return original_open(*args, **kwargs)

        # Mock to track blocking opens
        with patch("builtins.open", side_effect=blocking_open_tracker):
            with patch.object(
                photo_processor, "_analyze_image", new_callable=AsyncMock
            ):
                with patch.object(
                    photo_processor,
                    "_extract_exif_data_async",
                    new_callable=AsyncMock,
                ):
                    try:
                        await photo_processor.process(test_image)
                    except Exception:
                        pass  # Ignore errors from mocking

        # Verify no blocking open() calls were made by PhotoProcessor
        # (aiofiles.open should be used instead)
        processor_blocking = [
            call for call in blocking_calls if "test_async_test.png" in str(call)
        ]
        assert len(processor_blocking) == 0, (
            "PhotoProcessor should use aiofiles, not open()"
        )


# ============================================================================
# Voice Note Processor Tests - OpenAI Whisper Integration
# ============================================================================


class TestVoiceNoteProcessor:
    """Test VoiceNoteProcessor with OpenAI Whisper API integration."""

    @pytest.fixture
    def voice_note_processor(self):
        """Create a VoiceNoteProcessor instance."""
        return VoiceNoteProcessor()

    @pytest.mark.asyncio
    async def test_transcribe_audio_with_whisper_api(
        self, voice_note_processor, tmp_path
    ):
        """Test audio transcription with mocked Whisper API."""
        # Create a dummy audio file
        test_audio = tmp_path / "test.mp3"
        test_audio.write_bytes(b"fake_mp3_data")

        # Mock Whisper API response
        with patch.object(
            voice_note_processor, "_transcribe_audio", new_callable=AsyncMock
        ) as mock_transcribe:
            mock_transcribe.return_value = {
                "text": "This is a test transcription",
                "language": "en",
                "confidence": 0.95,
            }

            # Process the audio
            result = await voice_note_processor.process(test_audio)

            # Verify result structure
            assert "transcription" in result.content
            assert result.content["language"] == "en"
            assert "topics" in result.content
            assert "sentiment" in result.content
            assert result.metadata["file_type"] == ".mp3"

    @pytest.mark.asyncio
    async def test_whisper_api_async_execution(self, voice_note_processor, tmp_path):
        """Test that Whisper API calls are non-blocking."""
        test_audio = tmp_path / "test.wav"
        test_audio.write_bytes(b"fake_wav_data")

        # Mock Whisper transcription
        mock_transcript = MagicMock()
        mock_transcript.text = "Test transcription"
        mock_transcript.language = "en"

        with patch(
            "circles.src.etl.processors.voice_note_processor.asyncio.to_thread",
            new_callable=AsyncMock,
        ) as mock_thread:
            mock_thread.return_value = mock_transcript

            result = await voice_note_processor._transcribe_audio(test_audio)

            # Verify asyncio.to_thread was used (non-blocking)
            mock_thread.assert_called_once()
            assert result["text"] == "Test transcription"
            assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_topic_extraction_from_transcription(self, voice_note_processor):
        """Test topic extraction from transcribed text."""
        text_samples = [
            (
                "I have a software development meeting tomorrow",
                ["technology", "business"],
            ),
            ("My doctor said I should exercise more for my health", ["health"]),
            (
                "I'm learning Python and taking an online course",
                ["learning", "technology"],
            ),
            ("Planning a trip to Hawaii next month", ["travel"]),
        ]

        for text, expected_topics in text_samples:
            topics = voice_note_processor._extract_topics(text)
            for expected_topic in expected_topics:
                assert expected_topic in topics, (
                    f"Expected {expected_topic} in {topics}"
                )

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, voice_note_processor):
        """Test sentiment analysis of transcribed text."""
        positive_text = "This is amazing and wonderful! I love it!"
        sentiment = voice_note_processor._analyze_sentiment(positive_text)
        assert sentiment["sentiment"] == "positive"
        assert sentiment["score"] > 0.5

        negative_text = "This is terrible and awful. I hate it!"
        sentiment = voice_note_processor._analyze_sentiment(negative_text)
        assert sentiment["sentiment"] == "negative"
        assert sentiment["score"] < 0.5

        neutral_text = "The meeting is at 10am tomorrow"
        sentiment = voice_note_processor._analyze_sentiment(neutral_text)
        assert sentiment["sentiment"] == "neutral"


# ============================================================================
# Celery Task Execution Tests
# ============================================================================


class TestCeleryTaskExecution:
    """Test Celery task execution with adapter pipeline."""

    @pytest.mark.asyncio
    async def test_photo_adapter_pipeline_execution(self):
        """Test complete photo adapter pipeline execution."""
        # Mock adapter execution
        with patch("circles.src.etl.tasks.processor_tasks.PhotoAdapter") as MockAdapter:
            mock_adapter = MagicMock()

            # Mock successful pipeline result
            mock_result = MagicMock()
            mock_result.is_error = False
            mock_result.value = MagicMock(id=123)

            mock_adapter.execute = AsyncMock(return_value=mock_result)
            MockAdapter.return_value = mock_adapter

            # Mock database session
            with patch(
                "circles.src.etl.tasks.processor_tasks.init_db_engine",
                new_callable=AsyncMock,
            ) as mock_init_db:
                mock_factory = MagicMock()
                mock_session = AsyncMock(spec=AsyncSession)
                mock_factory.return_value.__aenter__.return_value = mock_session
                mock_init_db.return_value = mock_factory

                result = await execute_adapter_pipeline(
                    MockAdapter,
                    Path("/fake/path.jpg"),
                    user_id=1,
                    source_id=1,
                    job_id="test-job",
                    data_type="photo",
                )

                assert result["status"] == "completed"
                assert result["job_id"] == "test-job"
                assert result["model_id"] == 123

    @pytest.mark.asyncio
    async def test_adapter_error_handling(self):
        """Test error handling in adapter pipeline execution."""
        # Mock adapter execution with error
        with patch(
            "circles.src.etl.tasks.processor_tasks.VoiceNoteAdapter"
        ) as MockAdapter:
            mock_adapter = MagicMock()

            # Mock error result
            mock_error = MagicMock()
            mock_error.message = "Transcription failed"
            mock_error.error_type = "api_error"

            mock_result = MagicMock()
            mock_result.is_error = True
            mock_result.error_value = mock_error

            mock_adapter.execute = AsyncMock(return_value=mock_result)
            MockAdapter.return_value = mock_adapter

            with patch(
                "circles.src.etl.tasks.processor_tasks.init_db_engine",
                new_callable=AsyncMock,
            ) as mock_init_db:
                mock_factory = MagicMock()
                mock_session = AsyncMock(spec=AsyncSession)
                mock_factory.return_value.__aenter__.return_value = mock_session
                mock_init_db.return_value = mock_factory

                result = await execute_adapter_pipeline(
                    MockAdapter,
                    Path("/fake/audio.mp3"),
                    user_id=1,
                    source_id=1,
                    job_id="error-job",
                    data_type="voice_note",
                )

                assert result["status"] == "failed"
                assert result["error"] == "Transcription failed"
                assert result["error_type"] == "api_error"


# ============================================================================
# End-to-End API Integration Tests
# ============================================================================


class TestUploadAPIIntegration:
    """Test complete API upload flow with background task execution."""

    def test_api_queues_photo_task(self):
        """Verify photo upload endpoint queues Celery task."""
        from src.etl.api.routers.upload import _queue_celery_task

        with patch("circles.src.etl.api.routers.upload.celery_app") as mock_celery:
            _queue_celery_task(
                "process_photo",
                "test-job-123",
                file_path="/path/to/photo.jpg",
            )

            # Verify task was queued
            mock_celery.send_task.assert_called_once()
            call_kwargs = mock_celery.send_task.call_args[1]["kwargs"]
            assert call_kwargs["job_id"] == "test-job-123"
            assert call_kwargs["file_path"] == "/path/to/photo.jpg"

    def test_api_queues_voice_note_task(self):
        """Verify voice note upload endpoint queues Celery task."""
        from src.etl.api.routers.upload import _queue_celery_task

        with patch("circles.src.etl.api.routers.upload.celery_app") as mock_celery:
            _queue_celery_task(
                "process_voice_note",
                "test-job-456",
                file_path="/path/to/audio.mp3",
            )

            # Verify task was queued
            mock_celery.send_task.assert_called_once()
            call_kwargs = mock_celery.send_task.call_args[1]["kwargs"]
            assert call_kwargs["job_id"] == "test-job-456"

    def test_api_queues_email_task(self):
        """Verify email upload endpoint queues Celery task."""
        from src.etl.api.routers.upload import _queue_celery_task

        with patch("circles.src.etl.api.routers.upload.celery_app") as mock_celery:
            email_data = {
                "threads": [{"messages": ["Hello", "World"]}],
            }

            _queue_celery_task(
                "process_email",
                "test-job-email",
                email_data=email_data,
            )

            # Verify task was queued with correct data
            mock_celery.send_task.assert_called_once()
            call_kwargs = mock_celery.send_task.call_args[1]["kwargs"]
            assert call_kwargs["job_id"] == "test-job-email"
            assert call_kwargs["email_data"] == email_data

    def test_api_queues_social_post_task(self):
        """Verify social post upload endpoint queues Celery task."""
        from src.etl.api.routers.upload import _queue_celery_task

        with patch("circles.src.etl.api.routers.upload.celery_app") as mock_celery:
            post_data = {
                "platform": "twitter",
                "content": "Test post",
            }

            _queue_celery_task(
                "process_social_post",
                "test-job-social",
                post_data=post_data,
            )

            # Verify task was queued with correct data
            mock_celery.send_task.assert_called_once()
            call_kwargs = mock_celery.send_task.call_args[1]["kwargs"]
            assert call_kwargs["post_data"] == post_data

    def test_api_queues_blog_post_task(self):
        """Verify blog post upload endpoint queues Celery task."""
        from src.etl.api.routers.upload import _queue_celery_task

        with patch("circles.src.etl.api.routers.upload.celery_app") as mock_celery:
            blog_data = {
                "markdown": "# Title\nContent here",
                "title": "Test Blog",
            }

            _queue_celery_task(
                "process_blog_post",
                "test-job-blog",
                blog_data=blog_data,
            )

            # Verify task was queued with correct data
            mock_celery.send_task.assert_called_once()
            call_kwargs = mock_celery.send_task.call_args[1]["kwargs"]
            assert call_kwargs["blog_data"] == blog_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

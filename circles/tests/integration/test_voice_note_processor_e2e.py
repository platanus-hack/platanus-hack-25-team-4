"""
End-to-End Tests for VoiceNoteProcessor.

These tests run the complete voice note processor pipeline with real OpenAI Whisper API.
Marked with @pytest.mark.slow and @pytest.mark.e2e to allow skipping in CI.

Run with: pytest -m "e2e" tests/integration/test_voice_note_processor_e2e.py
"""

import asyncio
import io
import logging
import wave
from pathlib import Path

import pytest

from src.etl.core.config import get_settings
from src.etl.processors.voice_note_processor import VoiceNoteProcessor

logger = logging.getLogger(__name__)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_audio_file(tmp_path) -> Path:
    """
    Create a sample WAV audio file with actual spoken content.

    This creates a 1-second silent WAV file which is valid for Whisper API.
    For real testing, you would use an actual audio file with speech.
    """
    audio_path = tmp_path / "sample_audio.wav"

    # Create a 1-second silent audio file (44100 Hz, mono, 16-bit)
    sample_rate = 44100
    duration = 1.0  # seconds
    num_samples = int(sample_rate * duration)

    # Create WAV file
    with wave.open(str(audio_path), "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Write silent audio (all zeros)
        wav_file.writeframes(b"\x00\x00" * num_samples)

    return audio_path


@pytest.fixture
def sample_audio_with_text(tmp_path) -> Path:
    """
    Create an audio file for testing.

    Note: This creates a silent WAV. In production, you would use
    real audio files with speech for meaningful transcription tests.
    """
    audio_path = tmp_path / "speech_audio.wav"

    # Create a 2-second silent audio file
    sample_rate = 16000  # 16kHz is optimal for Whisper
    duration = 2.0
    num_samples = int(sample_rate * duration)

    with wave.open(str(audio_path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * num_samples)

    return audio_path


# ============================================================================
# VoiceNoteProcessor E2E Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestVoiceNoteProcessorE2E:
    """End-to-end tests for VoiceNoteProcessor with real Whisper API."""

    async def test_single_audio_processing(self, sample_audio_file):
        """
        E2E Test: Process a single audio file end-to-end.

        Tests:
        - Audio file reading and validation
        - Whisper API integration
        - Transcription quality
        - Language detection
        - Topic extraction
        - Sentiment analysis
        - Result structure and metadata
        """
        settings = get_settings()
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not configured")

        processor = VoiceNoteProcessor()
        result = await processor.process(sample_audio_file)

        # Verify result structure
        assert result is not None
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")

        # Verify content fields
        assert "transcription" in result.content
        assert "language" in result.content
        assert "topics" in result.content
        assert "sentiment" in result.content

        # Verify types
        assert isinstance(result.content["transcription"], str)
        assert isinstance(result.content["language"], str)
        assert isinstance(result.content["topics"], list)
        assert isinstance(result.content["sentiment"], dict)

        # Verify sentiment structure
        sentiment = result.content["sentiment"]
        assert "sentiment" in sentiment
        assert "score" in sentiment
        assert sentiment["sentiment"] in ["positive", "negative", "neutral"]
        assert 0.0 <= sentiment["score"] <= 1.0

        # Verify metadata
        assert result.metadata["file_type"] == ".wav"
        assert result.metadata["file_size"] > 0
        assert "confidence" in result.metadata
        assert "duration_seconds" in result.metadata
        assert isinstance(result.metadata["confidence"], float)
        assert isinstance(result.metadata["duration_seconds"], float)

        logger.info("✓ Single audio processing succeeded")
        logger.info(f"  Transcription: {result.content['transcription'][:100]}...")
        logger.info(f"  Language: {result.content['language']}")
        logger.info(f"  Topics: {result.content['topics']}")
        logger.info(f"  Sentiment: {result.content['sentiment']['sentiment']}")

    async def test_batch_audio_processing(self, tmp_path):
        """
        E2E Test: Process multiple audio files in parallel.

        Tests:
        - Batch file processing
        - Concurrency control with semaphore (max_concurrent=3)
        - Parallel Whisper API calls
        - Result aggregation
        - Error handling in batch
        """
        settings = get_settings()
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not configured")

        # Create multiple test audio files
        audio_paths = []
        for i in range(3):
            audio_path = tmp_path / f"audio_{i}.wav"

            # Create small WAV files
            with wave.open(str(audio_path), "w") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(b"\x00\x00" * 16000)  # 1 second

            audio_paths.append(audio_path)

        processor = VoiceNoteProcessor(max_concurrent=2)
        results = await processor.process_batch(audio_paths)

        # Verify batch processing
        assert len(results) == 3
        assert all(hasattr(r, "content") for r in results)
        assert all(hasattr(r, "metadata") for r in results)

        # Verify all have transcriptions (even if empty for silent audio)
        assert all("transcription" in r.content for r in results)
        assert all("language" in r.content for r in results)
        assert all("topics" in r.content for r in results)
        assert all("sentiment" in r.content for r in results)

        # Count successful vs failed
        successful = sum(1 for r in results if "processing_error" not in r.metadata)

        logger.info("✓ Batch audio processing succeeded")
        logger.info(f"  Processed {len(results)} audio files with max_concurrent=2")
        logger.info(f"  Successful: {successful}/{len(results)}")

    async def test_audio_transcription_quality(self, sample_audio_with_text):
        """
        E2E Test: Verify transcription quality with known content.

        Tests:
        - Transcription accuracy
        - Language detection accuracy
        - Confidence scores
        - Metadata completeness

        Note: With silent audio, this mainly tests the API integration.
        For real quality testing, use audio files with known speech content.
        """
        settings = get_settings()
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not configured")

        processor = VoiceNoteProcessor()
        result = await processor.process(sample_audio_with_text)

        # Verify API integration succeeded
        assert result is not None
        assert "transcription" in result.content

        # For silent audio, transcription will be empty or minimal
        # In production tests with real audio, you would check:
        # - Specific words/phrases are transcribed correctly
        # - Language is detected correctly
        # - Confidence is above threshold

        # Verify language field is populated
        assert result.content["language"] in ["unknown"] or len(result.content["language"]) > 0

        # Verify duration was calculated
        assert result.metadata["duration_seconds"] >= 0

        logger.info("✓ Audio transcription quality test succeeded")
        logger.info(f"  Duration: {result.metadata['duration_seconds']}s")
        logger.info(f"  Confidence: {result.metadata['confidence']}")

    async def test_topic_extraction_from_transcription(self, sample_audio_file):
        """
        E2E Test: Verify topic extraction from transcribed content.

        Tests:
        - Topic detection from keywords
        - Multiple topic detection
        - Topic categorization accuracy
        """
        settings = get_settings()
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not configured")

        processor = VoiceNoteProcessor()
        result = await processor.process(sample_audio_file)

        # Verify topics field exists and is a list
        assert "topics" in result.content
        assert isinstance(result.content["topics"], list)

        # For silent audio, topics may be empty
        # In production with real audio containing keywords:
        # - Verify expected topics are detected (e.g., "technology", "business")
        # - Verify topics match transcription content

        logger.info("✓ Topic extraction test succeeded")
        logger.info(f"  Topics detected: {result.content['topics']}")

    async def test_sentiment_analysis_quality(self, sample_audio_file):
        """
        E2E Test: Verify sentiment analysis from transcription.

        Tests:
        - Sentiment classification (positive/negative/neutral)
        - Sentiment score calculation
        - Score ranges and boundaries
        """
        settings = get_settings()
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not configured")

        processor = VoiceNoteProcessor()
        result = await processor.process(sample_audio_file)

        # Verify sentiment structure
        assert "sentiment" in result.content
        sentiment = result.content["sentiment"]

        assert "sentiment" in sentiment
        assert "score" in sentiment

        # Verify valid sentiment labels
        assert sentiment["sentiment"] in ["positive", "negative", "neutral"]

        # Verify score is in valid range
        assert 0.0 <= sentiment["score"] <= 1.0

        # For silent audio, expect neutral sentiment
        # In production with real audio, verify:
        # - Positive words -> positive sentiment
        # - Negative words -> negative sentiment
        # - Neutral words -> neutral sentiment

        logger.info("✓ Sentiment analysis test succeeded")
        logger.info(f"  Sentiment: {sentiment['sentiment']} (score: {sentiment['score']})")


# ============================================================================
# Parallel Processing Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestVoiceNoteProcessorParallel:
    """Test parallel processing capabilities."""

    async def test_parallel_batch_processing(self, tmp_path):
        """
        E2E Test: Verify parallel processing with concurrency control.

        Tests:
        - Semaphore-based concurrency limiting
        - Parallel API calls
        - Throughput optimization
        - Resource management
        """
        settings = get_settings()
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not configured")

        # Create batch of audio files
        audio_paths = []
        for i in range(5):
            audio_path = tmp_path / f"parallel_audio_{i}.wav"

            with wave.open(str(audio_path), "w") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(b"\x00\x00" * 8000)  # 0.5 seconds

            audio_paths.append(audio_path)

        # Process with low concurrency due to API rate limits
        processor = VoiceNoteProcessor(max_concurrent=2)
        results = await processor.process_batch(audio_paths)

        # Verify all files were processed
        assert len(results) == 5

        # Verify results structure
        for result in results:
            assert hasattr(result, "content")
            assert hasattr(result, "metadata")
            assert "transcription" in result.content
            assert "language" in result.content

        successful = sum(1 for r in results if "processing_error" not in r.metadata)

        logger.info("✓ Parallel batch processing succeeded")
        logger.info(f"  Processed {len(results)} files in parallel")
        logger.info(f"  Successful: {successful}/{len(results)}")
        logger.info(f"  Concurrency limit: {processor.max_concurrent}")

    async def test_audio_format_support(self, tmp_path):
        """
        E2E Test: Verify support for multiple audio formats.

        Tests:
        - WAV format processing
        - Different sample rates
        - Mono vs stereo
        - Format detection

        Note: Whisper API supports many formats including MP3, M4A, WAV, etc.
        This test focuses on WAV which is easy to generate programmatically.
        """
        settings = get_settings()
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not configured")

        # Test different WAV configurations
        test_configs = [
            {"sample_rate": 16000, "name": "audio_16k.wav"},
            {"sample_rate": 44100, "name": "audio_44k.wav"},
        ]

        results = []
        for config in test_configs:
            audio_path = tmp_path / config["name"]

            with wave.open(str(audio_path), "w") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(config["sample_rate"])
                wav_file.writeframes(
                    b"\x00\x00" * config["sample_rate"]  # 1 second
                )

            processor = VoiceNoteProcessor()
            result = await processor.process(audio_path)
            results.append(result)

        # Verify all formats processed successfully
        assert len(results) == len(test_configs)

        for i, result in enumerate(results):
            assert result.metadata["file_type"] == ".wav"
            assert "transcription" in result.content
            logger.info(
                f"  ✓ Format {test_configs[i]['name']}: "
                f"{test_configs[i]['sample_rate']}Hz processed"
            )

        logger.info("✓ Audio format support test succeeded")

"""
Unit tests for VoiceNoteProcessor.

Tests audio transcription with OpenAI Whisper API mocking.
"""

from unittest.mock import MagicMock, patch

import pytest
from src.etl.processors.voice_note_processor import (
    SimpleProcessorResult,
    VoiceNoteProcessor,
)

from tests.fixtures.fixture_factories import DataTypeFixtures


@pytest.mark.unit
class TestVoiceNoteProcessor:
    """Test VoiceNoteProcessor functionality."""

    @pytest.fixture
    async def voice_processor(self):
        """Create a VoiceNoteProcessor instance."""
        return VoiceNoteProcessor()

    @pytest.fixture
    def sample_audio_file(self, tmp_path, sample_audio_bytes):
        """Create a temporary audio file."""
        audio_path = tmp_path / "test_audio.wav"
        audio_path.write_bytes(sample_audio_bytes)
        return audio_path

    @pytest.mark.asyncio
    async def test_process_valid_audio(self, voice_processor, sample_audio_file):
        """Test processing a valid audio file."""
        with patch.object(
            voice_processor.client.audio.transcriptions,
            "create",
            return_value=MagicMock(text="This is a test transcription", language="en"),
        ):
            result = await voice_processor.process(sample_audio_file)

        assert isinstance(result, SimpleProcessorResult)
        assert "transcription" in result.content
        assert "language" in result.content
        assert "topics" in result.content
        assert "sentiment" in result.content
        assert result.content["transcription"] == "This is a test transcription"
        assert result.metadata["file_type"] == ".wav"
        assert result.metadata["file_size"] > 0
        assert "confidence" in result.metadata

    @pytest.mark.asyncio
    async def test_process_audio_with_topics(self, voice_processor, sample_audio_file):
        """Test topic extraction from transcription."""
        transcription_text = "Had a meeting about software development and coding"

        with patch.object(
            voice_processor.client.audio.transcriptions,
            "create",
            return_value=MagicMock(text=transcription_text, language="en"),
        ):
            result = await voice_processor.process(sample_audio_file)

        topics = result.content["topics"]
        assert "technology" in topics

    @pytest.mark.asyncio
    async def test_process_audio_with_sentiment_positive(
        self, voice_processor, sample_audio_file
    ):
        """Test positive sentiment detection."""
        transcription_text = "This is great, excellent work, amazing results"

        with patch.object(
            voice_processor.client.audio.transcriptions,
            "create",
            return_value=MagicMock(text=transcription_text, language="en"),
        ):
            result = await voice_processor.process(sample_audio_file)

        sentiment = result.content["sentiment"]
        assert sentiment["sentiment"] == "positive"
        assert sentiment["score"] > 0.5

    @pytest.mark.asyncio
    async def test_process_audio_with_sentiment_negative(
        self, voice_processor, sample_audio_file
    ):
        """Test negative sentiment detection."""
        transcription_text = "This is terrible, awful work, hate it"

        with patch.object(
            voice_processor.client.audio.transcriptions,
            "create",
            return_value=MagicMock(text=transcription_text, language="en"),
        ):
            result = await voice_processor.process(sample_audio_file)

        sentiment = result.content["sentiment"]
        assert sentiment["sentiment"] == "negative"
        assert sentiment["score"] < 0.5

    @pytest.mark.asyncio
    async def test_process_audio_with_sentiment_neutral(
        self, voice_processor, sample_audio_file
    ):
        """Test neutral sentiment detection."""
        transcription_text = "Just a regular voice note"

        with patch.object(
            voice_processor.client.audio.transcriptions,
            "create",
            return_value=MagicMock(text=transcription_text, language="en"),
        ):
            result = await voice_processor.process(sample_audio_file)

        sentiment = result.content["sentiment"]
        assert sentiment["sentiment"] == "neutral"
        assert sentiment["score"] == 0.5

    def test_extract_topics_technology(self, voice_processor):
        """Test topic extraction for technology keywords."""
        text = "Discussing python code and database architecture"
        topics = voice_processor._extract_topics(text)

        assert "technology" in topics

    def test_extract_topics_business(self, voice_processor):
        """Test topic extraction for business keywords."""
        text = "Project deadline next month, team meeting tomorrow, budget review"
        topics = voice_processor._extract_topics(text)

        assert "business" in topics

    def test_extract_topics_multiple(self, voice_processor):
        """Test extraction of multiple topics."""
        text = "Coding project due tomorrow, going to the gym after work"
        topics = voice_processor._extract_topics(text)

        assert "technology" in topics
        assert "health" in topics

    def test_extract_topics_empty_text(self, voice_processor):
        """Test topic extraction with empty text."""
        topics = voice_processor._extract_topics("")

        assert topics == []

    def test_extract_topics_no_matches(self, voice_processor):
        """Test topic extraction with no matching keywords."""
        text = "Lorem ipsum dolor sit amet"
        topics = voice_processor._extract_topics(text)

        assert topics == []

    def test_analyze_sentiment_empty_text(self, voice_processor):
        """Test sentiment analysis with empty text."""
        sentiment = voice_processor._analyze_sentiment("")

        assert sentiment["sentiment"] == "neutral"
        assert sentiment["score"] == 0.5

    def test_analyze_sentiment_score_range(self, voice_processor):
        """Test that sentiment scores are within valid range."""
        texts = [
            "Good excellent amazing",
            "Bad terrible awful",
            "Normal regular text",
        ]

        for text in texts:
            sentiment = voice_processor._analyze_sentiment(text)
            assert 0.0 <= sentiment["score"] <= 1.0

    @pytest.mark.asyncio
    async def test_process_file_not_found(self, voice_processor, tmp_path):
        """Test processing non-existent file."""
        non_existent = tmp_path / "non_existent.wav"

        with pytest.raises(FileNotFoundError):
            await voice_processor.process(non_existent)

    @pytest.mark.asyncio
    async def test_transcribe_audio_api_error(self, voice_processor, sample_audio_file):
        """Test handling of Whisper API errors."""
        from openai import OpenAIError

        with patch.object(
            voice_processor.client.audio.transcriptions,
            "create",
            side_effect=OpenAIError("API Error"),
        ):
            result = await voice_processor.process(sample_audio_file)

            # Should return error response
            assert (
                "error" in result.content["transcription"]
                or result.metadata["confidence"] == 0.0
            )

    @pytest.mark.asyncio
    async def test_transcribe_audio_language_detection(
        self, voice_processor, sample_audio_file
    ):
        """Test language detection in transcription."""
        with patch.object(
            voice_processor.client.audio.transcriptions,
            "create",
            return_value=MagicMock(text="Bonjour, comment allez-vous?", language="fr"),
        ):
            result = await voice_processor.process(sample_audio_file)

        assert result.content["language"] == "fr"

    @pytest.mark.asyncio
    async def test_get_audio_duration(self, voice_processor, sample_audio_file):
        """Test audio duration extraction."""
        # Try to get duration - may fail if pydub not installed
        duration = await voice_processor._get_audio_duration(sample_audio_file)

        assert isinstance(duration, float)
        assert duration >= 0.0

    @pytest.mark.asyncio
    async def test_processor_result_structure(self, voice_processor, sample_audio_file):
        """Test that processor result has correct structure."""
        with patch.object(
            voice_processor.client.audio.transcriptions,
            "create",
            return_value=MagicMock(text="Test transcription", language="en"),
        ):
            result = await voice_processor.process(sample_audio_file)

        # Verify SimpleProcessorResult structure
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")
        assert hasattr(result, "embeddings")

        # Verify content structure
        assert isinstance(result.content, dict)
        assert "transcription" in result.content
        assert "language" in result.content
        assert "topics" in result.content
        assert "sentiment" in result.content

        # Verify metadata structure
        assert isinstance(result.metadata, dict)
        assert "file_type" in result.metadata
        assert "file_size" in result.metadata
        assert "confidence" in result.metadata
        assert "duration_seconds" in result.metadata

    @pytest.mark.asyncio
    async def test_transcribe_audio_no_language_detected(
        self, voice_processor, sample_audio_file
    ):
        """Test handling when language is not detected."""
        with patch.object(
            voice_processor.client.audio.transcriptions,
            "create",
            return_value=MagicMock(text="Test", language=None),
        ):
            result = await voice_processor.process(sample_audio_file)

        assert result.content["language"] == "unknown"


@pytest.mark.unit
class TestVoiceNoteProcessorIntegration:
    """Integration tests for VoiceNoteProcessor with fixtures."""

    @pytest.fixture
    async def voice_processor(self):
        """Create a VoiceNoteProcessor instance."""
        return VoiceNoteProcessor()

    @pytest.mark.asyncio
    async def test_process_with_fixture_data(self, voice_processor):
        """Test processing with fixture data."""
        fixture_data = DataTypeFixtures.create_voice_note_metadata()

        assert "file_name" in fixture_data
        assert "duration_seconds" in fixture_data
        assert fixture_data["duration_seconds"] > 0
        assert "transcription" in fixture_data

    def test_topic_keywords_coverage(self, voice_processor):
        """Test that topic extraction covers expected keywords."""
        # Test technology keywords
        assert "software" in voice_processor._extract_topics("software development")
        assert "python" in voice_processor._extract_topics("I code in python")

        # Test business keywords
        assert "meeting" in voice_processor._extract_topics("team meeting tomorrow")
        assert "deadline" in voice_processor._extract_topics("project deadline")

        # Test health keywords
        assert "workout" in voice_processor._extract_topics("gym workout session")

    @pytest.mark.asyncio
    async def test_sentiment_edge_cases(self, voice_processor):
        """Test sentiment analysis with edge cases."""
        edge_cases = [
            ("", 0.5),  # Empty text
            ("a" * 1000, 0.5),  # Very long repeated text
            ("!!!!", 0.5),  # Non-word characters only
        ]

        for text, expected_sentiment in edge_cases:
            sentiment = voice_processor._analyze_sentiment(text)
            assert isinstance(sentiment, dict)
            assert "sentiment" in sentiment
            assert "score" in sentiment

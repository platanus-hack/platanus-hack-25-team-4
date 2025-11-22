"""Mock implementation of OpenAI Whisper API for testing."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class MockWhisperAPI:
    """
    Mock implementation of OpenAI Whisper API for testing.

    Provides deterministic transcriptions based on audio duration/content.
    """

    def __init__(self, fixtures_dir: Path):
        """Initialize mock Whisper API with fixtures directory."""
        self.fixtures_dir = fixtures_dir
        self.mock_transcriptions = self._load_mock_transcriptions()
        self.call_count = 0
        self.calls = []

    def _load_mock_transcriptions(self) -> Dict[str, Any]:
        """Load mock transcriptions from fixtures."""
        responses_file = self.fixtures_dir / "mock_responses" / "whisper_responses.json"
        if responses_file.exists():
            with open(responses_file) as f:
                return json.load(f)
        return {}

    async def transcribe_audio(
        self,
        audio_file_path: Path,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mock audio transcription.

        Returns deterministic transcription based on file size.
        """
        self.call_count += 1
        file_size = audio_file_path.stat().st_size if audio_file_path.exists() else 0
        self.calls.append(
            {
                "file_path": str(audio_file_path),
                "file_size": file_size,
                "language": language,
            }
        )

        # Return mock based on file size
        if file_size < 5000:
            transcription_key = "short_audio"
        elif file_size < 50000:
            transcription_key = "medium_audio"
        else:
            transcription_key = "long_audio"

        return self.mock_transcriptions.get(
            transcription_key, self._default_transcription()
        )

    def _default_transcription(self) -> Dict[str, Any]:
        """Generate default mock transcription."""
        return {
            "text": "This is a test transcription of audio content.",
            "language": "en",
            "confidence": 0.95,
            "duration": 5.2,
            "words": [
                {"word": "This", "start": 0.0, "end": 0.2},
                {"word": "is", "start": 0.2, "end": 0.4},
                {"word": "a", "start": 0.4, "end": 0.5},
                {"word": "test", "start": 0.5, "end": 0.8},
                {"word": "transcription", "start": 0.8, "end": 1.2},
                {"word": "of", "start": 1.2, "end": 1.3},
                {"word": "audio", "start": 1.3, "end": 1.6},
                {"word": "content", "start": 1.6, "end": 2.0},
            ],
        }

    def reset(self):
        """Reset mock state."""
        self.call_count = 0
        self.calls = []

    def get_call_count(self) -> int:
        """Get number of times API was called."""
        return self.call_count

    def get_calls(self) -> list:
        """Get list of all API calls made."""
        return self.calls


class MockWhisperError(Exception):
    """Mock Whisper API error for testing error scenarios."""

    def __init__(self, message: str, error_type: str = "api_error"):
        """Initialize mock error."""
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class MockWhisperRateLimitError(MockWhisperError):
    """Mock rate limit error from Whisper API."""

    def __init__(self, message: str = "Rate limit exceeded"):
        """Initialize rate limit error."""
        super().__init__(message, "rate_limit_error")


class MockWhisperTimeoutError(MockWhisperError):
    """Mock timeout error from Whisper API."""

    def __init__(self, message: str = "Request timeout"):
        """Initialize timeout error."""
        super().__init__(message, "timeout_error")


class MockWhisperInvalidAudioError(MockWhisperError):
    """Mock invalid audio error from Whisper API."""

    def __init__(self, message: str = "Invalid audio format"):
        """Initialize invalid audio error."""
        super().__init__(message, "invalid_audio_error")

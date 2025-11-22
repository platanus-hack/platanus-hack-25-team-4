"""Mock implementation of Claude Vision API for testing."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class MockClaudeVisionAPI:
    """
    Mock implementation of Claude Vision API for testing.

    Provides deterministic responses based on input images.
    Can load responses from fixtures or generate on-the-fly.
    """

    def __init__(self, fixtures_dir: Path):
        """Initialize mock Claude Vision API with fixtures directory."""
        self.fixtures_dir = fixtures_dir
        self.mock_responses = self._load_mock_responses()
        self.call_count = 0
        self.calls = []

    def _load_mock_responses(self) -> Dict[str, Any]:
        """Load mock responses from fixtures."""
        responses_file = (
            self.fixtures_dir / "mock_responses" / "claude_vision_responses.json"
        )
        if responses_file.exists():
            with open(responses_file) as f:
                return json.load(f)
        return {}

    async def analyze_image(
        self,
        image_data: bytes,
        mime_type: str,
        prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mock image analysis.

        Returns deterministic response based on image size/type.
        """
        self.call_count += 1
        self.calls.append(
            {"image_size": len(image_data), "mime_type": mime_type, "prompt": prompt}
        )

        # Return mock response based on image characteristics
        if len(image_data) < 1000:
            return self.mock_responses.get("small_image", self._default_response())
        elif len(image_data) < 100000:
            return self.mock_responses.get("standard_image", self._default_response())
        else:
            return self.mock_responses.get("large_image", self._default_response())

    def _default_response(self) -> Dict[str, Any]:
        """Generate default mock response."""
        return {
            "caption": "A test image showing various objects and scenes",
            "analysis": {
                "objects": ["test_object_1", "test_object_2"],
                "setting": "test_environment",
                "people_count": 0,
                "text_detected": [],
                "dominant_colors": ["blue", "white"],
                "mood": "neutral",
            },
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


class MockClaudeVisionError(Exception):
    """Mock Claude Vision API error for testing error scenarios."""

    def __init__(self, message: str, error_type: str = "api_error"):
        """Initialize mock error."""
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class MockClaudeRateLimitError(MockClaudeVisionError):
    """Mock rate limit error from Claude Vision API."""

    def __init__(self, message: str = "Rate limit exceeded"):
        """Initialize rate limit error."""
        super().__init__(message, "rate_limit_error")


class MockClaudeTimeoutError(MockClaudeVisionError):
    """Mock timeout error from Claude Vision API."""

    def __init__(self, message: str = "Request timeout"):
        """Initialize timeout error."""
        super().__init__(message, "timeout_error")

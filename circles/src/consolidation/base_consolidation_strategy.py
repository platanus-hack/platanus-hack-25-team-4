"""
Base implementation for consolidation strategies with common functionality.
"""

import logging
from typing import Any, Dict

from pydantic import ValidationError

from ..etl.core.result import Result
from ..profile_schema import UserProfile

logger = logging.getLogger(__name__)


class BaseConsolidationStrategy:
    """Base implementation for consolidation strategies with common functionality."""

    def __init__(self, user_id: str):
        """Initialize with user ID."""
        self.user_id = user_id

    def _validate_profile(
        self, profile_data: Dict[str, Any]
    ) -> Result[UserProfile, Exception]:
        """
        Validate and construct UserProfile from consolidated data.

        Args:
            profile_data: Dictionary with profile fields

        Returns:
            Result[UserProfile, Exception]: Validated profile or validation error
        """
        try:
            profile_data["user_id"] = self.user_id
            profile = UserProfile(**profile_data)
            logger.debug(f"Profile validation successful for user {self.user_id}")
            return Result.ok(profile)
        except ValidationError as e:
            logger.error(f"Profile validation error for user {self.user_id}: {e}")
            return Result.error(e)
        except Exception as e:
            logger.error(
                f"Unexpected error validating profile for user {self.user_id}: {e}"
            )
            return Result.error(e)

    @staticmethod
    def _has_data(raw_data: Dict[str, Any]) -> bool:
        """Check if raw data contains any information."""
        return any(
            raw_data.get(key)
            for key in [
                "resume",
                "photos",
                "voice_notes",
                "chat_transcripts",
                "calendar_events",
                "emails",
                "social_posts",
                "blog_posts",
                "screenshots",
                "shared_images",
            ]
        )

    @staticmethod
    def _summarize_raw_data(raw_data: Dict[str, Any]) -> str:
        """Create a summary of raw data for LLM context."""
        summary_parts = []

        if raw_data.get("resume"):
            summary_parts.append(f"Resume: {raw_data['resume']}")

        if raw_data.get("photos"):
            photos = raw_data["photos"]
            count = len(photos) if isinstance(photos, list) else 1
            summary_parts.append(f"Photos: {count} photo(s) analyzed")

        if raw_data.get("voice_notes"):
            voice = raw_data["voice_notes"]
            count = len(voice) if isinstance(voice, list) else 1
            summary_parts.append(f"Voice notes: {count} note(s) transcribed")

        if raw_data.get("chat_transcripts"):
            chats = raw_data["chat_transcripts"]
            count = len(chats) if isinstance(chats, list) else 1
            summary_parts.append(f"Chat transcripts: {count} transcript(s)")

        if raw_data.get("calendar_events"):
            events = raw_data["calendar_events"]
            count = len(events) if isinstance(events, list) else 1
            summary_parts.append(f"Calendar events: {count} event(s)")

        if raw_data.get("emails"):
            emails = raw_data["emails"]
            count = len(emails) if isinstance(emails, list) else 1
            summary_parts.append(f"Emails: {count} email(s)")

        if raw_data.get("social_posts"):
            social = raw_data["social_posts"]
            count = len(social) if isinstance(social, list) else 1
            summary_parts.append(f"Social posts: {count} post(s)")

        if raw_data.get("blog_posts"):
            blogs = raw_data["blog_posts"]
            count = len(blogs) if isinstance(blogs, list) else 1
            summary_parts.append(f"Blog posts: {count} post(s)")

        if raw_data.get("screenshots"):
            screenshots = raw_data["screenshots"]
            count = len(screenshots) if isinstance(screenshots, list) else 1
            summary_parts.append(f"Screenshots: {count} screenshot(s)")

        if raw_data.get("shared_images"):
            images = raw_data["shared_images"]
            count = len(images) if isinstance(images, list) else 1
            summary_parts.append(f"Shared images: {count} image(s)")

        return "\n".join(summary_parts)

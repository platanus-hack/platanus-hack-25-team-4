"""
Data Aggregator - Collects and structures all user data sources for consolidation.

Queries the database for all available data types and returns them in a structured format
suitable for LLM consolidation.

Uses asyncio.gather for parallel query execution to maximize performance.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..etl.core.result import Result
from ..etl.models import (
    BlogPost,
    CalendarEvent,
    ChatTranscript,
    EmailData,
    Photo,
    ResumeData,
    Screenshot,
    SharedImage,
    SocialMediaPost,
    VoiceNote,
)

logger = logging.getLogger(__name__)


class DataAggregator:
    """Aggregates all user data sources from database."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def aggregate_user_data(
        self, user_id: str
    ) -> Result[Dict[str, Any], Exception]:
        """
        Aggregate all available user data from multiple sources in parallel.

        Executes all database queries concurrently using asyncio.gather for
        optimal performance. Individual query failures are logged but don't
        prevent aggregation of other data sources.

        Args:
            user_id: The user ID to aggregate data for

        Returns:
            Result[Dict[str, Any], Exception]: Dictionary with all user data or error
        """
        try:
            # Validate user_id format
            self._validate_user_id(user_id)

            # Execute all queries in parallel for performance
            logger.debug(f"Starting parallel data aggregation for user {user_id}")

            (
                resume,
                photos,
                voice_notes,
                chat_transcripts,
                calendar_events,
                emails,
                social_posts,
                blog_posts,
                screenshots,
                shared_images,
            ) = await asyncio.gather(
                self._get_resume_data(user_id),
                self._get_photo_data(user_id),
                self._get_voice_note_data(user_id),
                self._get_chat_transcript_data(user_id),
                self._get_calendar_event_data(user_id),
                self._get_email_data(user_id),
                self._get_social_post_data(user_id),
                self._get_blog_post_data(user_id),
                self._get_screenshot_data(user_id),
                self._get_shared_image_data(user_id),
            )

            aggregated_data = {
                "resume": resume,
                "photos": photos,
                "voice_notes": voice_notes,
                "chat_transcripts": chat_transcripts,
                "calendar_events": calendar_events,
                "emails": emails,
                "social_posts": social_posts,
                "blog_posts": blog_posts,
                "screenshots": screenshots,
                "shared_images": shared_images,
            }

            logger.info(f"Successfully aggregated data for user {user_id}")
            return Result.ok(aggregated_data)

        except Exception as e:
            logger.error(f"Error aggregating user data for {user_id}: {e}")
            return Result.error(e)

    async def _get_resume_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data for user."""
        try:
            stmt = select(ResumeData).where(ResumeData.user_id == user_id)
            result = await self.session.execute(stmt)
            resume = result.scalars().first()

            if resume:
                return {
                    "full_text": resume.full_text,
                    "structured_data": resume.structured_data,
                }
            return None
        except Exception as e:
            logger.debug(f"Error fetching resume for user {user_id}: {e}")
            return None

    async def _get_photo_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get photo analyses for user."""
        try:
            stmt = select(Photo).where(Photo.user_id == user_id)
            result = await self.session.execute(stmt)
            photos = result.scalars().all()

            return [
                {
                    "file_reference": photo.file_reference,
                    "vlm_caption": photo.vlm_caption,
                    "vlm_analysis": photo.vlm_analysis,
                    "exif_data": photo.exif_data,
                }
                for photo in photos
            ]
        except Exception as e:
            logger.debug(f"Error fetching photos for user {user_id}: {e}")
            return []

    async def _get_voice_note_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get voice note transcriptions for user."""
        try:
            stmt = select(VoiceNote).where(VoiceNote.user_id == user_id)
            result = await self.session.execute(stmt)
            voice_notes = result.scalars().all()

            return [
                {
                    "transcription": note.transcription,
                    "language": note.language,
                    "extracted_topics": note.extracted_topics,
                    "sentiment": note.sentiment,
                }
                for note in voice_notes
            ]
        except Exception as e:
            logger.debug(f"Error fetching voice notes for user {user_id}: {e}")
            return []

    async def _get_chat_transcript_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get chat transcript data for user."""
        try:
            stmt = select(ChatTranscript).where(ChatTranscript.user_id == user_id)
            result = await self.session.execute(stmt)
            chats = result.scalars().all()

            return [
                {
                    "platform": chat.platform,
                    "participants": chat.participants,
                    "message_count": chat.message_count,
                    "messages": chat.messages,
                }
                for chat in chats
            ]
        except Exception as e:
            logger.debug(f"Error fetching chat transcripts for user {user_id}: {e}")
            return []

    async def _get_calendar_event_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get calendar event data for user."""
        try:
            stmt = select(CalendarEvent).where(CalendarEvent.user_id == user_id)
            result = await self.session.execute(stmt)
            events = result.scalars().all()

            return [
                {
                    "events": event.events,
                    "patterns": event.patterns,
                    "interests": event.interests,
                    "timezone": event.timezone,
                }
                for event in events
            ]
        except Exception as e:
            logger.debug(f"Error fetching calendar events for user {user_id}: {e}")
            return []

    async def _get_email_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get email data for user."""
        try:
            stmt = select(EmailData).where(EmailData.user_id == user_id)
            result = await self.session.execute(stmt)
            emails = result.scalars().all()

            return [
                {
                    "threads": email.threads,
                    "professional_interests": email.professional_interests,
                    "communication_style": email.communication_style,
                }
                for email in emails
            ]
        except Exception as e:
            logger.debug(f"Error fetching email data for user {user_id}: {e}")
            return []

    async def _get_social_post_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get social media post data for user."""
        try:
            stmt = select(SocialMediaPost).where(SocialMediaPost.user_id == user_id)
            result = await self.session.execute(stmt)
            posts = result.scalars().all()

            return [
                {
                    "platform": post.platform,
                    "caption": post.caption,
                    "vlm_outputs": post.vlm_outputs,
                    "tags": post.tags,
                }
                for post in posts
            ]
        except Exception as e:
            logger.debug(f"Error fetching social posts for user {user_id}: {e}")
            return []

    async def _get_blog_post_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get blog post data for user."""
        try:
            stmt = select(BlogPost).where(BlogPost.user_id == user_id)
            result = await self.session.execute(stmt)
            blogs = result.scalars().all()

            return [
                {
                    "markdown_content": blog.markdown_content,
                    "topics": blog.topics,
                    "tags": blog.tags,
                    "writing_style": blog.writing_style,
                }
                for blog in blogs
            ]
        except Exception as e:
            logger.debug(f"Error fetching blog posts for user {user_id}: {e}")
            return []

    async def _get_screenshot_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get screenshot data for user."""
        try:
            stmt = select(Screenshot).where(Screenshot.user_id == user_id)
            result = await self.session.execute(stmt)
            screenshots = result.scalars().all()

            return [
                {
                    "file_reference": screenshot.file_reference,
                    "vlm_analysis": screenshot.vlm_analysis,
                    "markdown_content": screenshot.markdown_content,
                    "privacy_sensitive": screenshot.privacy_sensitive,
                }
                for screenshot in screenshots
            ]
        except Exception as e:
            logger.debug(f"Error fetching screenshots for user {user_id}: {e}")
            return []

    async def _get_shared_image_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get shared image data for user."""
        try:
            stmt = select(SharedImage).where(SharedImage.user_id == user_id)
            result = await self.session.execute(stmt)
            images = result.scalars().all()

            return [
                {
                    "file_reference": image.file_reference,
                    "user_context": image.user_context,
                    "vlm_caption": image.vlm_caption,
                    "sharing_platform": image.sharing_platform,
                }
                for image in images
            ]
        except Exception as e:
            logger.debug(f"Error fetching shared images for user {user_id}: {e}")
            return []

    def _validate_user_id(self, user_id: str) -> None:
        """
        Validate user_id is a positive integer.

        Args:
            user_id: User ID to validate

        Raises:
            ValueError: If user_id is invalid
        """
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")

        if user_id <= 0:
            raise ValueError("user_id must be a positive integer")

        logger.debug(f"user_id validation passed: {user_id}")

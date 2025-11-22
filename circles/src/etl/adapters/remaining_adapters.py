"""
Remaining Adapters - Complete implementations for 7 data types.

Includes: ChatTranscript, Calendar, Email, SocialPost, BlogPost, Screenshot, SharedImage
"""

from pathlib import Path
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from ..core import ProcessingError, Result, SecureFileValidator
from ..models import (
    BlogPost,
    CalendarEvent,
    ChatTranscript,
    EmailData,
    Screenshot,
    SharedImage,
    SocialMediaPost,
)
from ..processors.calendar_processor import CalendarProcessor
from ..processors.chat_transcript_processor import ChatTranscriptProcessor
from .base import AdapterContext, BaseAdapter, DataType, ProcessorResult


# Chat Transcript Adapter
class ChatTranscriptAdapter(BaseAdapter[Dict[str, Any], ChatTranscript]):
    """Chat transcript adapter for conversation data."""

    @property
    def data_type(self) -> DataType:
        return DataType.CHAT_TRANSCRIPT

    @property
    def processor_class(self) -> type:
        return ChatTranscriptProcessor

    @property
    def repository_class(self) -> type:
        return None

    async def validate_input(
        self, input_data: Dict[str, Any], context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """Validate chat transcript data."""
        if not input_data:
            return Result.error(
                ProcessingError(
                    "Empty chat transcript data", error_type="validation_error"
                )
            )
        return Result.ok(None)

    async def process(
        self, input_data: Dict[str, Any], context: AdapterContext
    ) -> Result[ProcessorResult, ProcessingError]:
        """Process chat transcript."""
        try:
            messages = input_data.get("messages", [])
            platform = input_data.get("platform", "unknown")
            chat_name = input_data.get("chat_name", "")
            participants = list(
                set([m.get("sender") for m in messages if "sender" in m])
            )

            splits = self._split_messages(messages, chunk_size=100)

            class SimpleResult:
                def __init__(self):
                    self.content = {
                        "splits": splits,
                        "participants": participants,
                        "message_count": len(messages),
                        "total_splits": len(splits),
                        "platform": platform,
                        "chat_name": chat_name,
                    }
                    self.metadata = {"platform": platform}

            return Result.ok(SimpleResult())
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Chat processing failed: {e}", error_type="processing_error"
                )
            )

    @staticmethod
    def _split_messages(messages: list, chunk_size: int) -> list[dict]:
        """Split messages into chunks of specified size."""
        if not messages:
            return []

        splits = []
        total_messages = len(messages)

        for i in range(0, total_messages, chunk_size):
            chunk_messages = messages[i : i + chunk_size]
            chunk_start_idx = i
            chunk_end_idx = min(i + chunk_size - 1, total_messages - 1)

            chunk_data = {
                "messages": chunk_messages,
                "chunk_index": len(splits),
                "chunk_start_idx": chunk_start_idx,
                "chunk_end_idx": chunk_end_idx,
                "chunk_message_count": len(chunk_messages),
            }

            splits.append(chunk_data)

        return splits

    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[ChatTranscript, ProcessingError]:
        """Persist chat transcript to database, storing all splits."""
        try:
            content = processor_result.content
            platform = content.get("platform", "unknown")
            chat_name = content.get("chat_name", "")
            participants = content.get("participants", [])

            splits = content.get("splits", [])
            if not splits:
                return Result.error(
                    ProcessingError(
                        "No splits to persist", error_type="persistence_error"
                    )
                )

            transcripts = []
            for split in splits:
                transcript = ChatTranscript(
                    user_id=context.user_id,
                    source_id=context.source_id,
                    platform=platform,
                    chat_name=chat_name,
                    messages=split.get("messages", []),
                    participants=participants,
                    message_count=split.get("chunk_message_count", 0),
                )
                session.add(transcript)
                transcripts.append(transcript)

            await session.flush()
            return Result.ok(transcripts[0])
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Persistence failed: {e}", error_type="persistence_error"
                )
            )


# Calendar Adapter
class CalendarAdapter(BaseAdapter[Path, CalendarEvent]):
    """Calendar adapter for ICS calendar files."""

    @property
    def data_type(self) -> DataType:
        return DataType.CALENDAR

    @property
    def processor_class(self) -> type:
        return CalendarProcessor

    @property
    def repository_class(self) -> type:
        return None

    async def validate_input(
        self, input_data: Path, context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """Validate calendar file."""
        if not input_data.exists():
            return Result.error(
                ProcessingError(
                    f"File not found: {input_data}", error_type="file_not_found"
                )
            )

        try:
            with open(input_data, "rb") as f:
                content = f.read()
        except Exception as e:
            return Result.error(
                ProcessingError(f"Read failed: {e}", error_type="file_read_error")
            )

        validation = await SecureFileValidator.validate_file(
            input_data.name, content, "calendar"
        )
        if not validation.is_valid:
            return Result.error(
                ProcessingError(validation.error, error_type="validation_error")
            )
        return Result.ok(None)

    async def process(
        self, input_data: Path, context: AdapterContext
    ) -> Result[ProcessorResult, ProcessingError]:
        """Process calendar file."""
        try:
            processor = CalendarProcessor()
            result = await processor.process(input_data)
            return Result.ok(result)
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Processing failed: {e}", error_type="processing_error"
                )
            )

    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[CalendarEvent, ProcessingError]:
        """Persist calendar to database."""
        try:
            content = processor_result.content
            event = CalendarEvent(
                user_id=context.user_id,
                source_id=context.source_id,
                events=content.get("events", []),
                patterns=processor_result.metadata.get("event_patterns", {}),
                interests=content.get("interests", []),
                total_events=content.get("event_count", 0),
            )
            session.add(event)
            await session.flush()
            return Result.ok(event)
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Persistence failed: {e}", error_type="persistence_error"
                )
            )


# Email Adapter
class EmailAdapter(BaseAdapter[Dict[str, Any], EmailData]):
    """Email adapter for email data."""

    @property
    def data_type(self) -> DataType:
        return DataType.EMAIL

    @property
    def processor_class(self) -> type:
        return None

    @property
    def repository_class(self) -> type:
        return None

    async def validate_input(
        self, input_data: Dict[str, Any], context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """Validate email data."""
        if not input_data:
            return Result.error(
                ProcessingError("Empty email data", error_type="validation_error")
            )
        return Result.ok(None)

    async def process(
        self, input_data: Dict[str, Any], context: AdapterContext
    ) -> Result[ProcessorResult, ProcessingError]:
        """Process email data."""
        try:

            class SimpleResult:
                def __init__(self):
                    self.content = input_data
                    self.metadata = {}

            return Result.ok(SimpleResult())
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Processing failed: {e}", error_type="processing_error"
                )
            )

    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[EmailData, ProcessingError]:
        """Persist email to database."""
        try:
            content = processor_result.content
            email = EmailData(
                user_id=context.user_id,
                source_id=context.source_id,
                threads=content.get("threads", []),
                total_emails=content.get("total_emails", 0),
                senders=content.get("senders", []),
                recipients=content.get("recipients", []),
            )
            session.add(email)
            await session.flush()
            return Result.ok(email)
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Persistence failed: {e}", error_type="persistence_error"
                )
            )


# Social Media Post Adapter
class SocialPostAdapter(BaseAdapter[Dict[str, Any], SocialMediaPost]):
    """Social media post adapter."""

    @property
    def data_type(self) -> DataType:
        return DataType.SOCIAL_POST

    @property
    def processor_class(self) -> type:
        return None

    @property
    def repository_class(self) -> type:
        return None

    async def validate_input(
        self, input_data: Dict[str, Any], context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """Validate social media post data."""
        if not input_data:
            return Result.error(
                ProcessingError("Empty post data", error_type="validation_error")
            )
        return Result.ok(None)

    async def process(
        self, input_data: Dict[str, Any], context: AdapterContext
    ) -> Result[ProcessorResult, ProcessingError]:
        """Process social media post."""
        try:

            class SimpleResult:
                def __init__(self):
                    self.content = input_data
                    self.metadata = {}

            return Result.ok(SimpleResult())
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Processing failed: {e}", error_type="processing_error"
                )
            )

    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[SocialMediaPost, ProcessingError]:
        """Persist social post to database."""
        try:
            content = processor_result.content
            post = SocialMediaPost(
                user_id=context.user_id,
                source_id=context.source_id,
                platform=content.get("platform", "unknown"),
                platform_post_id=content.get("post_id", ""),
                post_type=content.get("type", "post"),
                caption=content.get("caption", ""),
                media_files=content.get("media", []),
            )
            session.add(post)
            await session.flush()
            return Result.ok(post)
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Persistence failed: {e}", error_type="persistence_error"
                )
            )


# Blog Post Adapter
class BlogPostAdapter(BaseAdapter[Dict[str, Any], BlogPost]):
    """Blog post adapter."""

    @property
    def data_type(self) -> DataType:
        return DataType.BLOG_POST

    @property
    def processor_class(self) -> type:
        return None

    @property
    def repository_class(self) -> type:
        return None

    async def validate_input(
        self, input_data: Dict[str, Any], context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """Validate blog post data."""
        if not input_data or "markdown" not in input_data:
            return Result.error(
                ProcessingError("Invalid blog data", error_type="validation_error")
            )
        return Result.ok(None)

    async def process(
        self, input_data: Dict[str, Any], context: AdapterContext
    ) -> Result[ProcessorResult, ProcessingError]:
        """Process blog post."""
        try:

            class SimpleResult:
                def __init__(self):
                    self.content = input_data
                    self.metadata = {}

            return Result.ok(SimpleResult())
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Processing failed: {e}", error_type="processing_error"
                )
            )

    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[BlogPost, ProcessingError]:
        """Persist blog post to database."""
        try:
            content = processor_result.content
            post = BlogPost(
                user_id=context.user_id,
                source_id=context.source_id,
                markdown_content=content.get("markdown", ""),
                title=content.get("title", "Untitled"),
                summary=content.get("summary", ""),
                topics=content.get("topics", []),
                tags=content.get("tags", []),
            )
            session.add(post)
            await session.flush()
            return Result.ok(post)
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Persistence failed: {e}", error_type="persistence_error"
                )
            )


# Screenshot Adapter
class ScreenshotAdapter(BaseAdapter[Path, Screenshot]):
    """Screenshot adapter."""

    @property
    def data_type(self) -> DataType:
        return DataType.SCREENSHOT

    @property
    def processor_class(self) -> type:
        return None

    @property
    def repository_class(self) -> type:
        return None

    async def validate_input(
        self, input_data: Path, context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """Validate screenshot file."""
        if not input_data.exists():
            return Result.error(
                ProcessingError(
                    f"File not found: {input_data}", error_type="file_not_found"
                )
            )

        try:
            with open(input_data, "rb") as f:
                content = f.read()
        except Exception as e:
            return Result.error(
                ProcessingError(f"Read failed: {e}", error_type="file_read_error")
            )

        validation = await SecureFileValidator.validate_file(
            input_data.name, content, "image"
        )
        if not validation.is_valid:
            return Result.error(
                ProcessingError(validation.error, error_type="validation_error")
            )
        return Result.ok(None)

    async def process(
        self, input_data: Path, context: AdapterContext
    ) -> Result[ProcessorResult, ProcessingError]:
        """Process screenshot."""
        try:

            class SimpleResult:
                def __init__(self):
                    self.content = {"file": str(input_data)}
                    self.metadata = {}

            return Result.ok(SimpleResult())
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Processing failed: {e}", error_type="processing_error"
                )
            )

    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[Screenshot, ProcessingError]:
        """Persist screenshot to database."""
        try:
            screenshot = Screenshot(
                user_id=context.user_id,
                source_id=context.source_id,
                file_reference={"path": processor_result.content.get("file", "")},
                privacy_sensitive=False,
            )
            session.add(screenshot)
            await session.flush()
            return Result.ok(screenshot)
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Persistence failed: {e}", error_type="persistence_error"
                )
            )


# Shared Image Adapter
class SharedImageAdapter(BaseAdapter[Path, SharedImage]):
    """Shared image adapter."""

    @property
    def data_type(self) -> DataType:
        return DataType.SHARED_IMAGE

    @property
    def processor_class(self) -> type:
        return None

    @property
    def repository_class(self) -> type:
        return None

    async def validate_input(
        self, input_data: Path, context: AdapterContext
    ) -> Result[None, ProcessingError]:
        """Validate shared image file."""
        if not input_data.exists():
            return Result.error(
                ProcessingError(
                    f"File not found: {input_data}", error_type="file_not_found"
                )
            )

        try:
            with open(input_data, "rb") as f:
                content = f.read()
        except Exception as e:
            return Result.error(
                ProcessingError(f"Read failed: {e}", error_type="file_read_error")
            )

        validation = await SecureFileValidator.validate_file(
            input_data.name, content, "image"
        )
        if not validation.is_valid:
            return Result.error(
                ProcessingError(validation.error, error_type="validation_error")
            )
        return Result.ok(None)

    async def process(
        self, input_data: Path, context: AdapterContext
    ) -> Result[ProcessorResult, ProcessingError]:
        """Process shared image."""
        try:

            class SimpleResult:
                def __init__(self):
                    self.content = {"file": str(input_data)}
                    self.metadata = {}

            return Result.ok(SimpleResult())
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Processing failed: {e}", error_type="processing_error"
                )
            )

    async def persist(
        self,
        processor_result: ProcessorResult,
        context: AdapterContext,
        session: AsyncSession,
    ) -> Result[SharedImage, ProcessingError]:
        """Persist shared image to database."""
        try:
            image = SharedImage(
                user_id=context.user_id,
                source_id=context.source_id,
                file_reference={"path": processor_result.content.get("file", "")},
                user_context="",
            )
            session.add(image)
            await session.flush()
            return Result.ok(image)
        except Exception as e:
            return Result.error(
                ProcessingError(
                    f"Persistence failed: {e}", error_type="persistence_error"
                )
            )

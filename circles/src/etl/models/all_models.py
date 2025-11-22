"""
Complete SQLModel definitions for all ETL entities.

Includes User, AgentPersona, RawDataSource, and 10 data type models.
"""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import JSON, Text
from sqlmodel import Column, Field, Index, Relationship, SQLModel

# ============================================================================
# CORE MODELS
# ============================================================================


class User(SQLModel, table=True):
    """User account model."""

    __tablename__ = "users"

    id: int = Field(primary_key=True)
    phone_number: Optional[str] = Field(unique=True, index=True, max_length=20)
    email: Optional[str] = Field(unique=True, index=True, max_length=255)
    auth_provider: str = Field(max_length=50)
    display_name: str = Field(max_length=100)
    avatar_url: Optional[str] = Field(max_length=512)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)


class RawDataSource(SQLModel, table=True):
    """Raw data upload metadata."""

    __tablename__ = "raw_data_sources"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_type: str = Field(max_length=50, index=True)
    source_platform: Optional[str] = Field(max_length=50)

    content_text: Optional[str] = Field(sa_column=Column(Text))
    content_json: Optional[dict] = Field(sa_column=Column(JSON))

    processing_status: str = Field(default="pending", max_length=20, index=True)
    processed_at: Optional[datetime] = None
    processing_error: Optional[str] = Field(sa_column=Column(Text))

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# DATA TYPE MODELS - 10 Types
# ============================================================================


class ResumeData(SQLModel, table=True):
    """Resume documents."""

    __tablename__ = "resume_data"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(foreign_key="raw_data_sources.id")

    # Content
    full_text: str = Field(sa_column=Column(Text))
    structured_data: dict = Field(sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)


class Photo(SQLModel, table=True):
    """Personal photos with VLM analysis."""

    __tablename__ = "photos"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(foreign_key="raw_data_sources.id")

    # File reference
    file_reference: dict = Field(sa_column=Column(JSON))

    # VLM caption and analysis
    vlm_caption: Optional[str] = Field(sa_column=Column(Text))
    vlm_analysis: dict = Field(default={}, sa_column=Column(JSON))

    # EXIF data
    exif_data: Optional[dict] = Field(sa_column=Column(JSON))
    taken_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceNote(SQLModel, table=True):
    """Voice note transcriptions."""

    __tablename__ = "voice_notes"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(foreign_key="raw_data_sources.id")

    # Audio metadata
    audio_file: dict = Field(sa_column=Column(JSON))

    # Transcription
    transcription: str = Field(sa_column=Column(Text))
    transcription_confidence: float = Field(default=0.0)
    language: str = Field(max_length=10)

    # Insights
    extracted_topics: list[str] = Field(default=[], sa_column=Column(JSON))
    sentiment: Optional[dict] = Field(sa_column=Column(JSON))

    recorded_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatTranscript(SQLModel, table=True):
    """Chat conversation transcripts."""

    __tablename__ = "chat_transcripts"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(foreign_key="raw_data_sources.id")

    # Chat metadata
    platform: str = Field(max_length=50)
    chat_name: Optional[str] = Field(max_length=255)

    # Structured data
    messages: dict = Field(sa_column=Column(JSON))
    participants: list[str] = Field(default=[], sa_column=Column(JSON))
    message_count: int = Field(default=0)

    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class CalendarEvent(SQLModel, table=True):
    """Calendar events from .ics files."""

    __tablename__ = "calendar_events"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(foreign_key="raw_data_sources.id")

    # Event data
    events: dict = Field(sa_column=Column(JSON))
    patterns: dict = Field(default={}, sa_column=Column(JSON))
    interests: list[str] = Field(default=[], sa_column=Column(JSON))

    total_events: int = Field(default=0)
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    timezone: str = Field(default="UTC", max_length=50)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class EmailData(SQLModel, table=True):
    """Email threads and professional context."""

    __tablename__ = "email_data"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(foreign_key="raw_data_sources.id")

    # Threads
    threads: dict = Field(sa_column=Column(JSON))

    # Metadata
    total_emails: int = Field(default=0)
    senders: list[str] = Field(default=[], sa_column=Column(JSON))
    recipients: list[str] = Field(default=[], sa_column=Column(JSON))

    # Analysis
    professional_interests: list[str] = Field(default=[], sa_column=Column(JSON))
    communication_style: dict = Field(default={}, sa_column=Column(JSON))

    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class SocialMediaPost(SQLModel, table=True):
    """Social media posts with VLM analysis."""

    __tablename__ = "social_media_posts"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(foreign_key="raw_data_sources.id")

    # Post metadata
    platform: str = Field(max_length=50, index=True)
    platform_post_id: str = Field(max_length=255)
    post_type: str = Field(max_length=50)

    # Content
    caption: Optional[str] = Field(sa_column=Column(Text))

    # Media and analysis
    media_files: list[dict] = Field(default=[], sa_column=Column(JSON))
    vlm_outputs: Optional[dict] = Field(sa_column=Column(JSON))

    # Metadata
    tags: list[str] = Field(default=[], sa_column=Column(JSON))
    metadata: dict = Field(default={}, sa_column=Column(JSON))

    posted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BlogPost(SQLModel, table=True):
    """Blog posts and long-form writing."""

    __tablename__ = "blog_posts"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(foreign_key="raw_data_sources.id")

    # Content
    markdown_content: str = Field(sa_column=Column(Text))
    title: Optional[str] = Field(max_length=500)
    summary: Optional[str] = Field(sa_column=Column(Text))

    # Analysis
    topics: list[str] = Field(default=[], sa_column=Column(JSON))
    tags: list[str] = Field(default=[], sa_column=Column(JSON))
    writing_style: dict = Field(default={}, sa_column=Column(JSON))

    # Metrics
    word_count: int = Field(default=0)
    reading_time_minutes: int = Field(default=0)

    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Screenshot(SQLModel, table=True):
    """Screenshots with digital behavior analysis."""

    __tablename__ = "screenshots"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(foreign_key="raw_data_sources.id")

    # File reference
    file_reference: dict = Field(sa_column=Column(JSON))

    # VLM analysis
    vlm_analysis: dict = Field(default={}, sa_column=Column(JSON))
    markdown_content: Optional[str] = Field(sa_column=Column(Text))

    # Privacy
    privacy_sensitive: bool = Field(default=False)

    taken_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SharedImage(SQLModel, table=True):
    """Shared images with context."""

    __tablename__ = "shared_images"

    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(foreign_key="raw_data_sources.id")

    # File and context
    file_reference: dict = Field(sa_column=Column(JSON))
    user_context: Optional[str] = Field(sa_column=Column(Text))

    # VLM analysis
    vlm_caption: Optional[str] = Field(sa_column=Column(Text))
    vlm_analysis: dict = Field(default={}, sa_column=Column(JSON))

    # Sharing metadata
    sharing_platform: Optional[str] = Field(max_length=50)
    shared_with: list[str] = Field(default=[], sa_column=Column(JSON))

    shared_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

"""
Adapters - Data type specific processors.

Each adapter handles one data type (resume, photo, email, etc.)
and implements the 4-phase pipeline defined in BaseAdapter.
"""

from .base import AdapterContext, BaseAdapter, DataType, ProcessorResult
from .photo_adapter import PhotoAdapter
from .registry import AdapterRegistry, get_registry, set_registry
from .remaining_adapters import (
    BlogPostAdapter,
    CalendarAdapter,
    ChatTranscriptAdapter,
    EmailAdapter,
    ScreenshotAdapter,
    SharedImageAdapter,
    SocialPostAdapter,
)
from .resume_adapter import ResumeAdapter
from .voice_note_adapter import VoiceNoteAdapter

__all__ = [
    "BaseAdapter",
    "DataType",
    "AdapterContext",
    "ProcessorResult",
    "AdapterRegistry",
    "get_registry",
    "set_registry",
    "ResumeAdapter",
    "PhotoAdapter",
    "VoiceNoteAdapter",
    "ChatTranscriptAdapter",
    "CalendarAdapter",
    "EmailAdapter",
    "SocialPostAdapter",
    "BlogPostAdapter",
    "ScreenshotAdapter",
    "SharedImageAdapter",
]

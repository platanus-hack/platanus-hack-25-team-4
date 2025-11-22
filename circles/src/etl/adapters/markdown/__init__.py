"""Markdown converter adapters for the ETL pipeline.

This module provides adapters for converting various file formats (PDF, DOCX,
PPTX, XLSX, images, etc.) to markdown. Currently includes MarkItDown backend.
"""

from .markitdown import MarkItDownAdapter, MarkItDownConfig
from .protocol import MarkdownConverter

__all__ = [
    "MarkdownConverter",
    "MarkItDownAdapter",
    "MarkItDownConfig",
]

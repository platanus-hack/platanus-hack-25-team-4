"""ETL Adapters for the Active Circles project.

This package provides adapter implementations following the adapter pattern for
various ETL operations including:

- VLM (Vision-Language Model) inference
- Markdown conversion from various file formats

Each adapter module provides both protocol definitions and concrete implementations,
allowing for easy extension and testing.
"""

# Base types and exceptions
from .base import (
    AdapterError,
    ConversionError,
    FileContent,
    FilePath,
    InferenceError,
    InvalidInputError,
    ModelLoadError,
    UnsupportedFormatError,
    ensure_path,
)

# Markdown converters
from .markdown import MarkdownConverter, MarkItDownAdapter, MarkItDownConfig

# VLM adapters
from .vlm import SmolVLMAdapter, SmolVLMConfig, VLMAdapter

__all__ = [
    # Base
    "AdapterError",
    "ConversionError",
    "FilePath",
    "FileContent",
    "InferenceError",
    "InvalidInputError",
    "ModelLoadError",
    "UnsupportedFormatError",
    "ensure_path",
    # VLM
    "VLMAdapter",
    "SmolVLMAdapter",
    "SmolVLMConfig",
    # Markdown
    "MarkdownConverter",
    "MarkItDownAdapter",
    "MarkItDownConfig",
]

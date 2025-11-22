"""ETL Adapters for the Active Circles project.

This package provides adapter implementations following the adapter pattern for
various ETL operations including:

- VLM (Vision-Language Model) inference
- Markdown conversion from various file formats
- LLM (Large Language Model) text generation

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

# LLM adapters
from .llm import (
    AnthropicAdapter,
    AnthropicConfig,
    LLMAdapter,
    OpenAIAdapter,
    OpenAIConfig,
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
    # LLM
    "LLMAdapter",
    "OpenAIAdapter",
    "OpenAIConfig",
    "AnthropicAdapter",
    "AnthropicConfig",
    # VLM
    "VLMAdapter",
    "SmolVLMAdapter",
    "SmolVLMConfig",
    # Markdown
    "MarkdownConverter",
    "MarkItDownAdapter",
    "MarkItDownConfig",
]

"""LLM (Large Language Model) adapters for the ETL pipeline.

This module provides adapters for large language models including OpenAI's GPT
and Anthropic's Claude. All adapters support async/await and streaming.
"""

from .anthropic_adapter import AnthropicAdapter, AnthropicConfig
from .openai_adapter import OpenAIAdapter, OpenAIConfig
from .protocol import LLMAdapter

__all__ = [
    "LLMAdapter",
    "OpenAIAdapter",
    "OpenAIConfig",
    "AnthropicAdapter",
    "AnthropicConfig",
]

"""VLM (Vision-Language Model) adapters for the ETL pipeline.

This module provides adapters for vision-language models that can generate
text descriptions from images. Currently includes SmolVLM-Instruct from HuggingFace.
"""

from .protocol import VLMAdapter
from .smolvlm import SmolVLMAdapter, SmolVLMConfig

__all__ = [
    "VLMAdapter",
    "SmolVLMAdapter",
    "SmolVLMConfig",
]

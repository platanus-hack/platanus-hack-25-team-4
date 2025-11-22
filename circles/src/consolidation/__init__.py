"""
Profile Consolidation Module - Synthesizes user data into comprehensive profiles.

This module implements a pipeline for consolidating multiple data sources
(resume, photos, voice notes, etc.) into a complete UserProfile using LLM-based synthesis.

Key features:
- Single consolidation strategy with injected LLM providers
- Supports Anthropic Claude and OpenAI GPT-4 via LLMProviderFactory
- Dependency injection for custom strategies and LLM providers
- Railway-Oriented Programming with Result monad for error handling
"""

from .data_aggregator import DataAggregator
from .llm_adapter import (
    AnthropicLLMProvider,
    LLMProvider,
    LLMProviderFactory,
    OpenAILLMProvider,
)
from .orchestrator import ProfileConsolidationOrchestrator
from .strategy import ConsolidationStrategy, DefaultConsolidationStrategy

__all__ = [
    "ProfileConsolidationOrchestrator",
    "ConsolidationStrategy",
    "DefaultConsolidationStrategy",
    "DataAggregator",
    "LLMProvider",
    "LLMProviderFactory",
    "AnthropicLLMProvider",
    "OpenAILLMProvider",
]

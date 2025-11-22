"""
LLM Adapter for Profile Consolidation - Unified interface for LLM providers.

Supports both Anthropic Claude and OpenAI GPT-4 through a common interface.
Allows easy switching between providers via dependency injection.
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, Protocol

import anthropic
from openai import OpenAI

from ..etl.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    async def call(self, prompt: str) -> str:
        """
        Call the LLM with a prompt.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            The LLM's text response
        """
        ...

    def get_provider_name(self) -> str:
        """Get the name of the provider."""
        ...


class AnthropicLLMProvider:
    """Anthropic Claude LLM provider."""

    def __init__(self):
        """Initialize with Anthropic client."""
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"

    async def call(self, prompt: str) -> str:
        """
        Call Claude API with the prompt.

        Args:
            prompt: The consolidation prompt

        Returns:
            Claude's text response
        """
        try:

            def _api_call():
                return self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                )

            # Execute in thread pool to avoid blocking
            message = await asyncio.to_thread(_api_call)
            return message.content[0].text

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Anthropic API: {e}")
            raise


class OpenAILLMProvider:
    """OpenAI GPT-4 LLM provider."""

    def __init__(self):
        """Initialize with OpenAI client."""
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4"

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "openai"

    async def call(self, prompt: str) -> str:
        """
        Call OpenAI API with the prompt.

        Args:
            prompt: The consolidation prompt

        Returns:
            OpenAI's text response
        """
        try:

            def _api_call():
                return self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                )

            # Execute in thread pool to avoid blocking
            response = await asyncio.to_thread(_api_call)
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create(provider_name: str = "anthropic") -> LLMProvider:
        """
        Create LLM provider instance.

        Args:
            provider_name: Provider name ('anthropic' or 'openai')

        Returns:
            LLMProvider instance

        Raises:
            ValueError: If provider_name is not supported
        """
        if provider_name.lower() == "openai":
            return OpenAILLMProvider()
        elif provider_name.lower() == "anthropic":
            return AnthropicLLMProvider()
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM response.

    Args:
        response_text: The LLM's text response

    Returns:
        Parsed JSON as dictionary

    Raises:
        ValueError: If JSON cannot be parsed
    """
    try:
        # First try direct JSON parsing
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from response using regex
        json_match = re.search(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_text, re.DOTALL
        )
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse extracted JSON: {e}")
                raise ValueError("Could not parse JSON from LLM response") from e
        else:
            raise ValueError("No JSON found in LLM response")

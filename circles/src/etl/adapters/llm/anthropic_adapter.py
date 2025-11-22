"""Anthropic adapter implementation using the anthropic library.

This module provides an LLM adapter implementation using Anthropic's API
with support for Claude models.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator

from ..base import InferenceError, InvalidInputError


@dataclass
class AnthropicConfig:
    """Configuration for Anthropic adapter.

    Attributes:
        api_key: Anthropic API key.
        model: Model identifier (e.g., 'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229').
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature for generation.
        base_url: Optional custom base URL for API calls.
        timeout: Request timeout in seconds.
    """

    api_key: str
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 1000
    temperature: float = 0.7
    base_url: str | None = None
    timeout: float = 60.0


class AnthropicAdapter:
    """LLM adapter using Anthropic's API.

    This adapter provides async completion capabilities using Anthropic's
    messages API with support for streaming.

    Example:
        ```python
        async with AnthropicAdapter(config) as adapter:
            result = await adapter.complete(
                prompt="What is the capital of France?",
                system="You are a helpful assistant"
            )
            print(result)
        ```
    """

    def __init__(self, config: AnthropicConfig) -> None:
        """Initialize the Anthropic adapter.

        Args:
            config: Configuration for the adapter.
        """
        self.config = config
        self._client: Any | None = None

    async def _ensure_client_initialized(self) -> None:
        """Ensure the Anthropic client is initialized (lazy loading).

        Raises:
            InferenceError: If client initialization fails.
        """
        if self._client is not None:
            return

        try:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        except ImportError as e:
            raise InferenceError(
                "anthropic library not installed. Install with: pip install anthropic"
            ) from e
        except Exception as e:
            raise InferenceError(f"Failed to initialize Anthropic client: {e}") from e

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate a completion using Anthropic's messages API.

        Args:
            prompt: The user prompt/message to complete.
            system: Optional system prompt/instructions.
            max_tokens: Maximum tokens to generate (overrides config).
            temperature: Sampling temperature (overrides config).

        Returns:
            Generated text completion from the model.

        Raises:
            InferenceError: If completion generation fails.
            InvalidInputError: If prompt is invalid.
        """
        if not prompt or not prompt.strip():
            raise InvalidInputError("Prompt cannot be empty")

        await self._ensure_client_initialized()

        try:
            # Build request parameters
            request_params = {
                "model": self.config.model,
                "max_tokens": max_tokens or self.config.max_tokens,
                "temperature": temperature
                if temperature is not None
                else self.config.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }

            if system:
                request_params["system"] = system

            # Generate completion
            response = await self._client.messages.create(**request_params)

            # Extract content
            if not response.content or not response.content[0].text:
                raise InferenceError("Empty response from Anthropic API")

            return response.content[0].text

        except InvalidInputError:
            raise
        except Exception as e:
            raise InferenceError(f"Anthropic completion failed: {e}") from e

    async def complete_batch(
        self,
        prompts: list[str],
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> list[str]:
        """Generate completions for multiple prompts in batch.

        Args:
            prompts: List of user prompts/messages.
            system: Optional system prompt applied to all requests.
            max_tokens: Maximum tokens to generate (overrides config).
            temperature: Sampling temperature (overrides config).

        Returns:
            List of generated text completions.

        Raises:
            InferenceError: If batch completion fails.
            InvalidInputError: If any prompt is invalid.
        """
        # Run completions concurrently
        tasks = [
            self.complete(prompt, system, max_tokens, temperature) for prompt in prompts
        ]
        return await asyncio.gather(*tasks)

    async def stream_complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream a completion token by token.

        Args:
            prompt: The user prompt/message to complete.
            system: Optional system prompt/instructions.
            max_tokens: Maximum tokens to generate (overrides config).
            temperature: Sampling temperature (overrides config).

        Yields:
            Chunks of generated text as they become available.

        Raises:
            InferenceError: If streaming fails.
            InvalidInputError: If prompt is invalid.
        """
        if not prompt or not prompt.strip():
            raise InvalidInputError("Prompt cannot be empty")

        await self._ensure_client_initialized()

        try:
            # Build request parameters
            request_params = {
                "model": self.config.model,
                "max_tokens": max_tokens or self.config.max_tokens,
                "temperature": temperature
                if temperature is not None
                else self.config.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }

            if system:
                request_params["system"] = system

            # Stream completion
            async with self._client.messages.stream(**request_params) as stream:
                async for text in stream.text_stream:
                    yield text

        except InvalidInputError:
            raise
        except Exception as e:
            raise InferenceError(f"Anthropic streaming failed: {e}") from e

    async def close(self) -> None:
        """Release resources and cleanup."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def __aenter__(self) -> "AnthropicAdapter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup."""
        await self.close()

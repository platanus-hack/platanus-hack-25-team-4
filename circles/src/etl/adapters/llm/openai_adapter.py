"""OpenAI adapter implementation using the openai library.

This module provides an LLM adapter implementation using OpenAI's API
with support for GPT models.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator

from ..base import InferenceError, InvalidInputError


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI adapter.

    Attributes:
        api_key: OpenAI API key.
        model: Model identifier (e.g., 'gpt-4', 'gpt-3.5-turbo').
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature for generation.
        base_url: Optional custom base URL for API calls.
        timeout: Request timeout in seconds.
    """

    api_key: str
    model: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.7
    base_url: str | None = None
    timeout: float = 60.0


class OpenAIAdapter:
    """LLM adapter using OpenAI's API.

    This adapter provides async completion capabilities using OpenAI's
    chat completion API with support for streaming.

    Example:
        ```python
        async with OpenAIAdapter(config) as adapter:
            result = await adapter.complete(
                prompt="What is the capital of France?",
                system="You are a helpful assistant"
            )
            print(result)
        ```
    """

    def __init__(self, config: OpenAIConfig) -> None:
        """Initialize the OpenAI adapter.

        Args:
            config: Configuration for the adapter.
        """
        self.config = config
        self._client: Any | None = None

    async def _ensure_client_initialized(self) -> None:
        """Ensure the OpenAI client is initialized (lazy loading).

        Raises:
            InferenceError: If client initialization fails.
        """
        if self._client is not None:
            return

        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        except ImportError as e:
            raise InferenceError(
                "openai library not installed. Install with: pip install openai"
            ) from e
        except Exception as e:
            raise InferenceError(f"Failed to initialize OpenAI client: {e}") from e

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate a completion using OpenAI's chat API.

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
            # Build messages
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Generate completion
            response = await self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature
                if temperature is not None
                else self.config.temperature,
            )

            # Extract content
            if not response.choices or not response.choices[0].message.content:
                raise InferenceError("Empty response from OpenAI API")

            return response.choices[0].message.content

        except InvalidInputError:
            raise
        except Exception as e:
            raise InferenceError(f"OpenAI completion failed: {e}") from e

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
            # Build messages
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Stream completion
            stream = await self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature
                if temperature is not None
                else self.config.temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except InvalidInputError:
            raise
        except Exception as e:
            raise InferenceError(f"OpenAI streaming failed: {e}") from e

    async def close(self) -> None:
        """Release resources and cleanup."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def __aenter__(self) -> "OpenAIAdapter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup."""
        await self.close()

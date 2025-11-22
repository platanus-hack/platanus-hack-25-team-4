"""Protocol definition for LLM (Large Language Model) adapters.

This module defines the LLMAdapter protocol that all LLM implementations
must follow for consistent integration in the ETL pipeline.
"""

from typing import AsyncIterator, Protocol


class LLMAdapter(Protocol):
    """Protocol for Large Language Model adapters.

    LLM adapters provide a consistent interface for text generation using
    language models like OpenAI's GPT or Anthropic's Claude.
    """

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate a completion for the given prompt.

        Args:
            prompt: The user prompt/message to complete.
            system: Optional system prompt/instructions.
            max_tokens: Maximum tokens to generate (overrides default config).
            temperature: Sampling temperature 0.0-1.0 (overrides default config).

        Returns:
            Generated text completion from the model.

        Raises:
            InferenceError: If completion generation fails.
            InvalidInputError: If prompt is invalid.
        """
        ...

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
            max_tokens: Maximum tokens to generate (overrides default config).
            temperature: Sampling temperature (overrides default config).

        Returns:
            List of generated text completions, one per prompt.

        Raises:
            InferenceError: If batch completion fails.
            InvalidInputError: If any prompt is invalid.
        """
        ...

    async def stream_complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream a completion for the given prompt (token by token).

        Args:
            prompt: The user prompt/message to complete.
            system: Optional system prompt/instructions.
            max_tokens: Maximum tokens to generate (overrides default config).
            temperature: Sampling temperature (overrides default config).

        Yields:
            Chunks of generated text as they become available.

        Raises:
            InferenceError: If streaming fails.
            InvalidInputError: If prompt is invalid.
        """
        ...

    async def close(self) -> None:
        """Release resources and cleanup.

        Should be called when the adapter is no longer needed.
        """
        ...

    async def __aenter__(self) -> "LLMAdapter":
        """Async context manager entry."""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup."""
        ...

"""Protocol definition for Vision-Language Model (VLM) adapters.

This module defines the VLMAdapter protocol that all VLM implementations
must follow for consistent integration in the ETL pipeline.
"""

from pathlib import Path
from typing import Protocol


class VLMAdapter(Protocol):
    """Protocol for Vision-Language Model adapters.

    VLM adapters provide a consistent interface for generating text from images
    using vision-language models. Implementations should support both single
    and batch inference operations asynchronously.
    """

    async def infer(
        self,
        image: Path | bytes,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate text from an image using the VLM.

        Args:
            image: Path to image file or raw image bytes.
            prompt: Text prompt to guide the model's generation.
            max_tokens: Maximum tokens to generate (overrides default config).
            temperature: Sampling temperature (overrides default config).

        Returns:
            Generated text response from the model.

        Raises:
            InferenceError: If inference fails.
            InvalidInputError: If image is invalid or cannot be loaded.
        """
        ...

    async def batch_infer(
        self,
        images: list[Path | bytes],
        prompts: list[str],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> list[str]:
        """Generate text from multiple images in batch.

        Args:
            images: List of image paths or raw image bytes.
            prompts: List of prompts corresponding to each image.
            max_tokens: Maximum tokens to generate (overrides default config).
            temperature: Sampling temperature (overrides default config).

        Returns:
            List of generated text responses, one per image.

        Raises:
            InferenceError: If batch inference fails.
            InvalidInputError: If any image is invalid.
            ValueError: If images and prompts lists have different lengths.
        """
        ...

    async def close(self) -> None:
        """Release model resources and cleanup.

        Should be called when the adapter is no longer needed to free
        GPU/CPU memory and other resources.
        """
        ...

    async def __aenter__(self) -> "VLMAdapter":
        """Async context manager entry."""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup."""
        ...

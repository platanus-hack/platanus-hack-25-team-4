"""SmolVLM adapter implementation using HuggingFace transformers.

This module provides a VLM adapter implementation using the SmolVLM-Instruct
model from HuggingFace, with support for MPS (Apple Silicon GPU), CUDA, and CPU.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from ..base import InferenceError, InvalidInputError, ModelLoadError


@dataclass
class SmolVLMConfig:
    """Configuration for SmolVLM adapter.

    Attributes:
        model_id: HuggingFace model identifier.
        device: Device to run inference on ('auto', 'mps', 'cuda', 'cpu').
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature for generation.
        do_sample: Whether to use sampling (vs greedy decoding).
        cache_dir: Directory to cache model files.
    """

    model_id: str = "HuggingFaceTB/SmolVLM-Instruct"
    device: str = "auto"
    max_tokens: int = 512
    temperature: float = 0.7
    do_sample: bool = True
    cache_dir: Path | None = None


class SmolVLMAdapter:
    """VLM adapter using SmolVLM-Instruct from HuggingFace.

    This adapter provides async inference capabilities using the SmolVLM model,
    with automatic device detection and lazy model loading.

    Example:
        ```python
        async with SmolVLMAdapter() as adapter:
            result = await adapter.infer(
                image="photo.jpg",
                prompt="Describe this image"
            )
            print(result)
        ```
    """

    def __init__(self, config: SmolVLMConfig | None = None) -> None:
        """Initialize the SmolVLM adapter.

        Args:
            config: Configuration for the adapter. Uses defaults if None.
        """
        self.config = config or SmolVLMConfig()
        self._model: Any | None = None
        self._processor: Any | None = None
        self._device: str | None = None
        self._lock = asyncio.Lock()

    async def _ensure_model_loaded(self) -> None:
        """Ensure the model and processor are loaded (lazy loading).

        Raises:
            ModelLoadError: If model loading fails.
        """
        if self._model is not None:
            return

        async with self._lock:
            # Double-check after acquiring lock
            if self._model is not None:
                return

            try:
                # Import torch here to avoid import errors if not installed
                import torch
                from transformers import AutoModelForVision2Seq, AutoProcessor

                # Determine device
                self._device = await self._detect_device()

                # Load processor and model in thread pool to avoid blocking
                loop = asyncio.get_event_loop()

                self._processor = await loop.run_in_executor(
                    None,
                    lambda: AutoProcessor.from_pretrained(
                        self.config.model_id,
                        cache_dir=self.config.cache_dir,
                    ),
                )

                self._model = await loop.run_in_executor(
                    None,
                    lambda: AutoModelForVision2Seq.from_pretrained(
                        self.config.model_id,
                        cache_dir=self.config.cache_dir,
                        torch_dtype=torch.float16
                        if self._device in ("mps", "cuda")
                        else torch.float32,
                    ).to(self._device),
                )

            except Exception as e:
                raise ModelLoadError(f"Failed to load SmolVLM model: {e}") from e

    async def _detect_device(self) -> str:
        """Detect the best available device for inference.

        Returns:
            Device string: 'mps', 'cuda', or 'cpu'.
        """
        if self.config.device != "auto":
            return self.config.device

        try:
            import torch

            if torch.backends.mps.is_available():
                return "mps"
            elif torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        except ImportError:
            return "cpu"

    async def _load_image(self, image: Path | bytes) -> Image.Image:
        """Load an image from path or bytes.

        Args:
            image: Path to image file or raw image bytes.

        Returns:
            PIL Image object.

        Raises:
            InvalidInputError: If image cannot be loaded.
        """
        try:
            if isinstance(image, bytes):
                from io import BytesIO

                return Image.open(BytesIO(image)).convert("RGB")
            else:
                path = Path(image)
                if not path.exists():
                    raise InvalidInputError(f"Image file not found: {path}")
                return Image.open(path).convert("RGB")
        except Exception as e:
            raise InvalidInputError(f"Failed to load image: {e}") from e

    async def infer(
        self,
        image: Path | bytes,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate text from an image using SmolVLM.

        Args:
            image: Path to image file or raw image bytes.
            prompt: Text prompt to guide the model's generation.
            max_tokens: Maximum tokens to generate (overrides config).
            temperature: Sampling temperature (overrides config).

        Returns:
            Generated text response from the model.

        Raises:
            InferenceError: If inference fails.
            InvalidInputError: If image is invalid.
        """
        await self._ensure_model_loaded()

        try:
            # Load image
            pil_image = await self._load_image(image)

            # Format prompt for SmolVLM-Instruct
            formatted_prompt = f"<image>\n{prompt}"

            # Prepare inputs
            loop = asyncio.get_event_loop()
            inputs = await loop.run_in_executor(
                None,
                lambda: self._processor(
                    text=formatted_prompt,
                    images=pil_image,
                    return_tensors="pt",
                ).to(self._device),
            )

            # Generate
            generation_kwargs = {
                "max_new_tokens": max_tokens or self.config.max_tokens,
                "temperature": temperature or self.config.temperature,
                "do_sample": self.config.do_sample,
            }

            outputs = await loop.run_in_executor(
                None, lambda: self._model.generate(**inputs, **generation_kwargs)
            )

            # Decode output
            result = await loop.run_in_executor(
                None,
                lambda: self._processor.batch_decode(outputs, skip_special_tokens=True)[
                    0
                ],
            )

            return result.strip()

        except InvalidInputError:
            raise
        except Exception as e:
            raise InferenceError(f"Inference failed: {e}") from e

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
            max_tokens: Maximum tokens to generate (overrides config).
            temperature: Sampling temperature (overrides config).

        Returns:
            List of generated text responses.

        Raises:
            InferenceError: If batch inference fails.
            InvalidInputError: If any image is invalid.
            ValueError: If images and prompts lists have different lengths.
        """
        if len(images) != len(prompts):
            raise ValueError(
                f"Number of images ({len(images)}) must match "
                f"number of prompts ({len(prompts)})"
            )

        # For simplicity, run inferences sequentially
        # Could be optimized with true batching in the future
        results = []
        for image, prompt in zip(images, prompts):
            result = await self.infer(image, prompt, max_tokens, temperature)
            results.append(result)

        return results

    async def close(self) -> None:
        """Release model resources and cleanup."""
        if self._model is not None:
            # Move model to CPU and clear cache
            try:
                import torch

                self._model.cpu()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif torch.backends.mps.is_available():
                    torch.mps.empty_cache()
            except Exception:
                pass  # Best effort cleanup

            self._model = None
            self._processor = None
            self._device = None

    async def __aenter__(self) -> "SmolVLMAdapter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup."""
        await self.close()

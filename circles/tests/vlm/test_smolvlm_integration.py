"""Integration tests for SmolVLM adapter with real models.

These tests use real models and are slow. They are marked with @pytest.mark.slow
and @pytest.mark.integration and can be skipped with: pytest -m "not slow"
"""

import pytest
from src.etl.adapters.vlm import SmolVLMAdapter, SmolVLMConfig

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestSmolVLMRealInference:
    """Integration tests using real SmolVLM model."""

    @pytest.mark.requires_network
    async def test_real_inference_with_cpu(self, sample_image_path):
        """Should perform real inference on CPU (slow test)."""
        pytest.skip("Skipping real model test - requires model download")

        config = SmolVLMConfig(device="cpu", max_tokens=50)

        async with SmolVLMAdapter(config) as adapter:
            result = await adapter.infer(
                sample_image_path, "Describe this image in one sentence"
            )

            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.requires_network
    async def test_real_inference_output_quality(self, sample_image_path):
        """Should generate coherent text (slow test)."""
        pytest.skip("Skipping real model test - requires model download")

        async with SmolVLMAdapter() as adapter:
            result = await adapter.infer(sample_image_path, "What do you see?")

            # Very basic quality checks
            assert isinstance(result, str)
            assert len(result.split()) > 3  # At least a few words
            assert any(c.isalpha() for c in result)  # Contains letters

    @pytest.mark.requires_network
    async def test_real_batch_inference(self, sample_image_path, sample_png_path):
        """Should handle batch processing with real model (slow test)."""
        pytest.skip("Skipping real model test - requires model download")

        config = SmolVLMConfig(max_tokens=30)

        async with SmolVLMAdapter(config) as adapter:
            images = [sample_image_path, sample_png_path]
            prompts = ["Describe this", "What is in this image?"]

            results = await adapter.batch_infer(images, prompts)

            assert len(results) == 2
            assert all(isinstance(r, str) for r in results)
            assert all(len(r) > 0 for r in results)

    async def test_context_manager_cleanup(self):
        """Should properly cleanup resources after context manager."""
        adapter = SmolVLMAdapter()

        async with adapter:
            # Model should be available in context
            pass

        # After context, model should be cleaned up
        assert adapter._model is None
        assert adapter._processor is None

    async def test_manual_close_cleanup(self):
        """Should properly cleanup resources with manual close."""
        adapter = SmolVLMAdapter()

        await adapter.close()

        assert adapter._model is None
        assert adapter._processor is None
        assert adapter._device is None

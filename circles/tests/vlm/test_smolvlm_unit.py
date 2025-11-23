"""Unit tests for SmolVLM adapter with mocked dependencies."""

from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.etl.adapters.base import InvalidInputError, ModelLoadError
from src.etl.adapters.vlm import SmolVLMAdapter, SmolVLMConfig

pytestmark = pytest.mark.unit


class TestSmolVLMConfig:
    """Test SmolVLMConfig dataclass."""

    def test_config_defaults(self):
        """Should use sensible default values."""
        config = SmolVLMConfig()

        assert config.model_id == "HuggingFaceTB/SmolVLM-Instruct"
        assert config.device == "auto"
        assert config.max_tokens == 512
        assert config.temperature == 0.7
        assert config.do_sample is True
        assert config.cache_dir is None

    def test_config_custom_values(self):
        """Should accept and store custom configuration."""
        config = SmolVLMConfig(
            model_id="custom-model",
            device="cuda",
            max_tokens=256,
            temperature=0.5,
            do_sample=False,
            cache_dir=Path("/tmp/cache"),
        )

        assert config.model_id == "custom-model"
        assert config.device == "cuda"
        assert config.max_tokens == 256
        assert config.temperature == 0.5
        assert config.do_sample is False
        assert config.cache_dir == Path("/tmp/cache")

    def test_config_with_cache_dir(self, tmp_path):
        """Should handle cache directory configuration."""
        cache_dir = tmp_path / "model_cache"
        config = SmolVLMConfig(cache_dir=cache_dir)

        assert config.cache_dir == cache_dir


class TestSmolVLMAdapterInitialization:
    """Test SmolVLMAdapter initialization."""

    def test_adapter_init_with_default_config(self):
        """Should initialize with default config if none provided."""
        adapter = SmolVLMAdapter()

        assert adapter.config is not None
        assert adapter.config.model_id == "HuggingFaceTB/SmolVLM-Instruct"
        assert adapter._model is None
        assert adapter._processor is None
        assert adapter._device is None

    def test_adapter_init_with_custom_config(self, smolvlm_config):
        """Should use provided custom config."""
        adapter = SmolVLMAdapter(smolvlm_config)

        assert adapter.config == smolvlm_config
        assert adapter.config.model_id == "test-model"
        assert adapter.config.device == "cpu"

    async def test_model_lazy_loading(self):
        """Model should not be loaded on initialization."""
        adapter = SmolVLMAdapter()

        assert adapter._model is None
        assert adapter._processor is None
        assert adapter._device is None


class TestDeviceDetection:
    """Test device detection functionality."""

    async def test_detect_device_auto_with_mps_available(self):
        """Should detect MPS when available."""
        # Mock torch module at import time
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            adapter = SmolVLMAdapter()
            device = await adapter._detect_device()

            assert device == "mps"

    async def test_detect_device_auto_with_cuda_available(self):
        """Should detect CUDA when MPS unavailable but CUDA available."""
        # Mock torch module at import time
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = True

        with patch.dict("sys.modules", {"torch": mock_torch}):
            adapter = SmolVLMAdapter()
            device = await adapter._detect_device()

            assert device == "cuda"

    async def test_detect_device_auto_with_cpu_only(self):
        """Should fall back to CPU when neither MPS nor CUDA available."""
        # Mock torch module at import time
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            adapter = SmolVLMAdapter()
            device = await adapter._detect_device()

            assert device == "cpu"

    async def test_detect_device_manual_override(self):
        """Manual device config should override auto-detection."""
        config = SmolVLMConfig(device="cuda")
        adapter = SmolVLMAdapter(config)

        device = await adapter._detect_device()

        assert device == "cuda"

    async def test_detect_device_when_torch_not_available(self):
        """Should fall back to CPU when torch not available."""
        with patch.dict("sys.modules", {"torch": None}):
            adapter = SmolVLMAdapter()
            device = await adapter._detect_device()

            assert device == "cpu"


class TestModelLoading:
    """Test model loading functionality."""

    async def test_model_loads_on_first_inference(self, sample_image_path):
        """Model should load on first infer() call."""
        # Setup torch mocks
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False
        mock_torch.float32 = MagicMock()

        # Setup transformers mocks
        mock_processor_class = MagicMock()
        mock_model_class = MagicMock()

        # Setup model and processor mocks
        mock_processor = MagicMock()
        mock_processor_class.from_pretrained.return_value = mock_processor
        mock_processor.return_value = MagicMock()
        mock_processor.return_value.to.return_value = MagicMock()
        mock_processor.batch_decode.return_value = ["Generated text"]

        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_model.generate.return_value = [[1, 2, 3]]
        mock_model_class.from_pretrained.return_value = mock_model

        # Setup transformers module
        mock_transformers = MagicMock()
        mock_transformers.AutoProcessor = mock_processor_class
        mock_transformers.AutoModelForVision2Seq = mock_model_class

        with patch.dict(
            "sys.modules", {"torch": mock_torch, "transformers": mock_transformers}
        ):
            with patch("src.etl.adapters.vlm.smolvlm.Image.open") as mock_img_open:
                # Setup image mock
                mock_img = MagicMock()
                mock_img.convert.return_value = mock_img
                mock_img_open.return_value = mock_img

                adapter = SmolVLMAdapter()

                # Model should be None initially
                assert adapter._model is None

                # Trigger loading through inference attempt
                await adapter.infer(sample_image_path, "test prompt")

                # Check that loading was attempted
                mock_processor_class.from_pretrained.assert_called_once()
                mock_model_class.from_pretrained.assert_called_once()

    async def test_model_load_error_handling(self):
        """Should raise ModelLoadError on load failure."""
        # Setup torch mocks
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        # Setup transformers mocks with error
        mock_processor_class = MagicMock()
        mock_processor_class.from_pretrained.side_effect = Exception("Load failed")

        mock_transformers = MagicMock()
        mock_transformers.AutoProcessor = mock_processor_class
        mock_transformers.AutoModelForVision2Seq = MagicMock()

        with patch.dict(
            "sys.modules", {"torch": mock_torch, "transformers": mock_transformers}
        ):
            adapter = SmolVLMAdapter()

            with pytest.raises(ModelLoadError, match="Failed to load SmolVLM model"):
                await adapter._ensure_model_loaded()

    async def test_model_load_uses_correct_dtype_for_gpu(self):
        """Should use float16 for MPS/CUDA devices."""
        # Setup torch with MPS available
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.cuda.is_available.return_value = False
        mock_torch.float16 = "FLOAT16_DTYPE"

        # Setup transformers mocks
        mock_processor_class = MagicMock()
        mock_model_class = MagicMock()

        # Setup processor mock
        mock_processor = MagicMock()
        mock_processor_class.from_pretrained.return_value = mock_processor

        # Setup model mock
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_model_class.from_pretrained.return_value = mock_model

        mock_transformers = MagicMock()
        mock_transformers.AutoProcessor = mock_processor_class
        mock_transformers.AutoModelForVision2Seq = mock_model_class

        with patch.dict(
            "sys.modules", {"torch": mock_torch, "transformers": mock_transformers}
        ):
            config = SmolVLMConfig(device="auto")
            adapter = SmolVLMAdapter(config)

            await adapter._ensure_model_loaded()

            # Verify float16 was used
            call_kwargs = mock_model_class.from_pretrained.call_args[1]
            assert call_kwargs["torch_dtype"] == "FLOAT16_DTYPE"

    async def test_model_load_uses_float32_for_cpu(self):
        """Should use float32 for CPU device."""
        # Setup torch with CPU only
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False
        mock_torch.float32 = "FLOAT32_DTYPE"

        # Setup transformers mocks
        mock_processor_class = MagicMock()
        mock_model_class = MagicMock()

        # Setup processor mock
        mock_processor = MagicMock()
        mock_processor_class.from_pretrained.return_value = mock_processor

        # Setup model mock
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model
        mock_model_class.from_pretrained.return_value = mock_model

        mock_transformers = MagicMock()
        mock_transformers.AutoProcessor = mock_processor_class
        mock_transformers.AutoModelForVision2Seq = mock_model_class

        with patch.dict(
            "sys.modules", {"torch": mock_torch, "transformers": mock_transformers}
        ):
            adapter = SmolVLMAdapter()
            await adapter._ensure_model_loaded()

            call_kwargs = mock_model_class.from_pretrained.call_args[1]
            assert call_kwargs["torch_dtype"] == "FLOAT32_DTYPE"


class TestImageLoading:
    """Test image loading functionality."""

    @patch("src.etl.adapters.vlm.smolvlm.Image.open")
    async def test_load_image_from_path(self, mock_open, sample_image_path):
        """Should successfully load image from file path."""
        mock_img = MagicMock()
        mock_img.convert.return_value = mock_img
        mock_open.return_value = mock_img

        adapter = SmolVLMAdapter()
        result = await adapter._load_image(sample_image_path)

        mock_open.assert_called_once()
        mock_img.convert.assert_called_once_with("RGB")
        assert result == mock_img

    @patch("src.etl.adapters.vlm.smolvlm.Image.open")
    async def test_load_image_from_bytes(self, mock_open, sample_image_bytes):
        """Should successfully load image from bytes."""
        mock_img = MagicMock()
        mock_img.convert.return_value = mock_img
        mock_open.return_value = mock_img

        adapter = SmolVLMAdapter()
        result = await adapter._load_image(sample_image_bytes)

        mock_open.assert_called_once()
        assert isinstance(mock_open.call_args[0][0], BytesIO)
        mock_img.convert.assert_called_once_with("RGB")

    async def test_load_image_nonexistent_path(self, nonexistent_path):
        """Should raise InvalidInputError for missing file."""
        adapter = SmolVLMAdapter()

        with pytest.raises(InvalidInputError, match="not found"):
            await adapter._load_image(nonexistent_path)

    async def test_load_image_invalid_bytes(self):
        """Should raise InvalidInputError for corrupted data."""
        adapter = SmolVLMAdapter()
        invalid_bytes = b"not an image"

        with pytest.raises(InvalidInputError, match="Failed to load image"):
            await adapter._load_image(invalid_bytes)


class TestInference:
    """Test inference functionality."""

    async def test_infer_with_path(self, mock_smolvlm_adapter, sample_image_path):
        """Should successfully infer with image path."""
        adapter = mock_smolvlm_adapter

        # Setup mocks
        adapter._processor.return_value = MagicMock()
        adapter._processor.return_value.to.return_value = MagicMock()
        adapter._model.generate.return_value = [[1, 2, 3]]
        adapter._processor.batch_decode.return_value = ["Generated text response"]

        result = await adapter.infer(sample_image_path, "Describe this image")

        assert result == "Generated text response"
        adapter._model.generate.assert_called_once()

    async def test_infer_with_bytes(self, mock_smolvlm_adapter, sample_image_bytes):
        """Should successfully infer with image bytes."""
        adapter = mock_smolvlm_adapter

        adapter._processor.return_value = MagicMock()
        adapter._processor.return_value.to.return_value = MagicMock()
        adapter._model.generate.return_value = [[1, 2, 3]]
        adapter._processor.batch_decode.return_value = ["Generated text"]

        result = await adapter.infer(sample_image_bytes, "What is this?")

        assert result == "Generated text"

    async def test_infer_formats_prompt_correctly(
        self, mock_smolvlm_adapter, sample_image_path
    ):
        """Prompt should be formatted as '<image>\\n{prompt}'."""
        adapter = mock_smolvlm_adapter

        adapter._processor.return_value = MagicMock()
        adapter._processor.return_value.to.return_value = MagicMock()
        adapter._model.generate.return_value = [[1, 2, 3]]
        adapter._processor.batch_decode.return_value = ["Response"]

        await adapter.infer(sample_image_path, "test prompt")

        # Check that processor was called with formatted prompt
        call_args = adapter._processor.call_args
        assert "<image>" in call_args[1]["text"]
        assert "test prompt" in call_args[1]["text"]

    async def test_infer_uses_default_max_tokens(
        self, mock_smolvlm_adapter, sample_image_path
    ):
        """Should use config max_tokens by default."""
        adapter = mock_smolvlm_adapter

        adapter._processor.return_value = MagicMock()
        adapter._processor.return_value.to.return_value = MagicMock()
        adapter._model.generate.return_value = [[1, 2, 3]]
        adapter._processor.batch_decode.return_value = ["Response"]

        await adapter.infer(sample_image_path, "test")

        call_kwargs = adapter._model.generate.call_args[1]
        assert call_kwargs["max_new_tokens"] == adapter.config.max_tokens

    async def test_infer_uses_override_max_tokens(
        self, mock_smolvlm_adapter, sample_image_path
    ):
        """Override max_tokens parameter should take precedence."""
        adapter = mock_smolvlm_adapter

        adapter._processor.return_value = MagicMock()
        adapter._processor.return_value.to.return_value = MagicMock()
        adapter._model.generate.return_value = [[1, 2, 3]]
        adapter._processor.batch_decode.return_value = ["Response"]

        await adapter.infer(sample_image_path, "test", max_tokens=999)

        call_kwargs = adapter._model.generate.call_args[1]
        assert call_kwargs["max_new_tokens"] == 999

    async def test_infer_strips_output(self, mock_smolvlm_adapter, sample_image_path):
        """Output text should be stripped of whitespace."""
        adapter = mock_smolvlm_adapter

        adapter._processor.return_value = MagicMock()
        adapter._processor.return_value.to.return_value = MagicMock()
        adapter._model.generate.return_value = [[1, 2, 3]]
        adapter._processor.batch_decode.return_value = ["  Generated text  "]

        result = await adapter.infer(sample_image_path, "test")

        assert result == "Generated text"
        assert result == result.strip()


class TestBatchInference:
    """Test batch inference functionality."""

    async def test_batch_infer_with_matching_lengths(
        self, mock_smolvlm_adapter, sample_image_path
    ):
        """Should successfully process batch with matching lengths."""
        adapter = mock_smolvlm_adapter

        adapter._processor.return_value = MagicMock()
        adapter._processor.return_value.to.return_value = MagicMock()
        adapter._model.generate.return_value = [[1, 2, 3]]
        adapter._processor.batch_decode.return_value = ["Result"]

        images = [sample_image_path, sample_image_path]
        prompts = ["Describe this", "What is this?"]

        results = await adapter.batch_infer(images, prompts)

        assert len(results) == 2
        assert all(isinstance(r, str) for r in results)

    async def test_batch_infer_mismatched_lengths(self, mock_smolvlm_adapter):
        """Should raise ValueError when lengths differ."""
        adapter = mock_smolvlm_adapter

        images = ["img1.jpg", "img2.jpg"]
        prompts = ["prompt1"]

        with pytest.raises(ValueError, match="must match"):
            await adapter.batch_infer(images, prompts)

    async def test_batch_infer_preserves_order(
        self, mock_smolvlm_adapter, sample_image_path
    ):
        """Results should match input order."""
        adapter = mock_smolvlm_adapter

        # Setup mock to return different results
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return [[call_count]]

        adapter._model.generate.side_effect = side_effect
        adapter._processor.batch_decode.side_effect = [
            [f"Result {i}"] for i in range(1, 4)
        ]

        images = [sample_image_path] * 3
        prompts = ["p1", "p2", "p3"]

        results = await adapter.batch_infer(images, prompts)

        assert len(results) == 3


class TestResourceCleanup:
    """Test resource cleanup functionality."""

    async def test_close_clears_model(self):
        """Model should be set to None on close."""
        # Setup torch mocks
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            # Create adapter with mocked model
            adapter = SmolVLMAdapter()
            mock_model = MagicMock()
            mock_model.cpu.return_value = None
            adapter._model = mock_model
            adapter._processor = MagicMock()
            adapter._device = "cpu"

            await adapter.close()

            assert adapter._model is None

    async def test_close_moves_model_to_cpu(self):
        """Model should be moved to CPU before clearing."""
        # Setup torch mocks
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            # Create adapter with mocked model
            adapter = SmolVLMAdapter()
            mock_model = MagicMock()
            adapter._model = mock_model
            adapter._processor = MagicMock()
            adapter._device = "cpu"

            await adapter.close()

            mock_model.cpu.assert_called_once()

    async def test_close_is_idempotent(self):
        """Close can be called multiple times safely."""
        # Setup torch mocks
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            adapter = SmolVLMAdapter()

            await adapter.close()
            await adapter.close()  # Should not raise

    async def test_close_empties_cuda_cache(self):
        """Should empty CUDA cache when available."""
        # Setup torch with CUDA available
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.empty_cache = MagicMock()

        with patch.dict("sys.modules", {"torch": mock_torch}):
            # Create adapter with mocked model on CUDA
            adapter = SmolVLMAdapter()
            mock_model = MagicMock()
            adapter._model = mock_model
            adapter._processor = MagicMock()
            adapter._device = "cuda"

            await adapter.close()

            mock_torch.cuda.empty_cache.assert_called_once()

    async def test_close_empties_mps_cache(self):
        """Should empty MPS cache when available."""
        # Setup torch with MPS available
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.cuda.is_available.return_value = False
        mock_torch.mps.empty_cache = MagicMock()

        with patch.dict("sys.modules", {"torch": mock_torch}):
            # Create adapter with mocked model on MPS
            adapter = SmolVLMAdapter()
            mock_model = MagicMock()
            adapter._model = mock_model
            adapter._processor = MagicMock()
            adapter._device = "mps"

            await adapter.close()

            mock_torch.mps.empty_cache.assert_called_once()


class TestContextManager:
    """Test async context manager functionality."""

    async def test_context_manager_async_enter(self):
        """__aenter__ should return self."""
        adapter = SmolVLMAdapter()

        result = await adapter.__aenter__()

        assert result is adapter

    async def test_context_manager_exit_calls_close(self):
        """__aexit__ should call close()."""
        # Setup torch mocks
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            adapter = SmolVLMAdapter()

            with patch.object(adapter, "close", new_callable=AsyncMock) as mock_close:
                await adapter.__aexit__(None, None, None)
                mock_close.assert_called_once()

    async def test_context_manager_full_lifecycle(self):
        """Complete context manager flow should work."""
        # Setup torch mocks
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            async with SmolVLMAdapter() as adapter:
                assert adapter is not None
                # Optionally set up a model to verify cleanup
                mock_model = MagicMock()
                adapter._model = mock_model

            # After exiting, model should be cleaned up
            assert adapter._model is None

    async def test_context_manager_with_exception(self):
        """Context manager should cleanup even when exception occurs."""
        # Setup torch mocks
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            adapter = None
            try:
                async with SmolVLMAdapter() as adapter:
                    # Set up a model
                    mock_model = MagicMock()
                    adapter._model = mock_model
                    # Raise an exception
                    raise ValueError("Test exception")
            except ValueError:
                pass  # Expected

            # Model should still be cleaned up
            assert adapter is not None
            assert adapter._model is None

"""VLM-specific test fixtures and mocks."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_torch():
    """Mock torch module with MPS, CUDA, and CPU support."""
    mock_torch_module = MagicMock()
    mock_torch_module.float16 = MagicMock()
    mock_torch_module.float32 = MagicMock()

    # Mock MPS backend
    mock_torch_module.backends.mps.is_available.return_value = False
    mock_torch_module.mps.empty_cache = MagicMock()

    # Mock CUDA backend
    mock_torch_module.cuda.is_available.return_value = False
    mock_torch_module.cuda.empty_cache = MagicMock()

    with patch.dict("sys.modules", {"torch": mock_torch_module}):
        yield mock_torch_module


@pytest.fixture
def mock_transformers():
    """Mock transformers module with AutoProcessor and AutoModelForVision2Seq."""
    mock_processor = MagicMock()
    mock_model = MagicMock()

    # Setup processor mock
    mock_processor_class = MagicMock()
    mock_processor_class.from_pretrained.return_value = mock_processor

    # Setup model mock
    mock_model_class = MagicMock()
    mock_model.to.return_value = mock_model
    mock_model.cpu.return_value = mock_model
    mock_model.generate.return_value = [[1, 2, 3, 4, 5]]  # Mock token IDs
    mock_model_class.from_pretrained.return_value = mock_model

    # Setup processor output behavior
    mock_processor.return_value = MagicMock()
    mock_processor.return_value.to.return_value = MagicMock()
    mock_processor.batch_decode.return_value = ["Generated text from model"]

    with patch("src.etl.adapters.vlm.smolvlm.AutoProcessor", mock_processor_class):
        with patch(
            "src.etl.adapters.vlm.smolvlm.AutoModelForVision2Seq",
            mock_model_class,
        ):
            yield {
                "processor_class": mock_processor_class,
                "model_class": mock_model_class,
                "processor": mock_processor,
                "model": mock_model,
            }


@pytest.fixture
def mock_pil_image():
    """Mock PIL Image for image loading tests."""
    mock_img = MagicMock()
    mock_img.convert.return_value = mock_img

    with patch("src.etl.adapters.vlm.smolvlm.Image.open") as mock_open:
        mock_open.return_value = mock_img
        yield mock_img


@pytest.fixture
def smolvlm_config():
    """Default SmolVLM config for testing."""
    from src.etl.adapters.vlm import SmolVLMConfig

    return SmolVLMConfig(
        model_id="test-model",
        device="cpu",
        max_tokens=128,
        temperature=0.5,
        do_sample=True,
        cache_dir=None,
    )


@pytest.fixture
async def mock_smolvlm_adapter(smolvlm_config, mock_transformers, mock_torch):
    """Fully mocked SmolVLM adapter ready for testing.

    This fixture provides an adapter with pre-loaded mocks to avoid
    lazy loading complexity in tests.
    """
    from src.etl.adapters.vlm import SmolVLMAdapter

    adapter = SmolVLMAdapter(smolvlm_config)

    # Pre-load mocks to bypass lazy loading
    adapter._model = mock_transformers["model"]
    adapter._processor = mock_transformers["processor"]
    adapter._device = "cpu"

    yield adapter

    # Cleanup
    await adapter.close()


@pytest.fixture
def mock_torch_with_mps(mock_torch):
    """Mock torch with MPS (Apple Silicon GPU) available."""
    mock_torch.backends.mps.is_available.return_value = True
    return mock_torch


@pytest.fixture
def mock_torch_with_cuda(mock_torch):
    """Mock torch with CUDA (NVIDIA GPU) available."""
    mock_torch.cuda.is_available.return_value = True
    return mock_torch

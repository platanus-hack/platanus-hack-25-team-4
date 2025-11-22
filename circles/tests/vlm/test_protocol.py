"""Protocol compliance tests for VLM adapters."""

import inspect

from src.etl.adapters.vlm import SmolVLMAdapter


class TestSmolVLMProtocolCompliance:
    """Test that SmolVLMAdapter conforms to VLMAdapter protocol."""

    def test_smolvlm_has_infer_method(self):
        """SmolVLMAdapter should have an infer method."""
        assert hasattr(SmolVLMAdapter, "infer")
        assert callable(getattr(SmolVLMAdapter, "infer"))

    def test_smolvlm_has_batch_infer_method(self):
        """SmolVLMAdapter should have a batch_infer method."""
        assert hasattr(SmolVLMAdapter, "batch_infer")
        assert callable(getattr(SmolVLMAdapter, "batch_infer"))

    def test_smolvlm_has_close_method(self):
        """SmolVLMAdapter should have a close method."""
        assert hasattr(SmolVLMAdapter, "close")
        assert callable(getattr(SmolVLMAdapter, "close"))

    def test_smolvlm_has_aenter_method(self):
        """SmolVLMAdapter should have __aenter__ for async context manager."""
        assert hasattr(SmolVLMAdapter, "__aenter__")
        assert callable(getattr(SmolVLMAdapter, "__aenter__"))

    def test_smolvlm_has_aexit_method(self):
        """SmolVLMAdapter should have __aexit__ for async context manager."""
        assert hasattr(SmolVLMAdapter, "__aexit__")
        assert callable(getattr(SmolVLMAdapter, "__aexit__"))

    def test_infer_is_async(self):
        """infer method should be async."""
        assert inspect.iscoroutinefunction(SmolVLMAdapter.infer)

    def test_batch_infer_is_async(self):
        """batch_infer method should be async."""
        assert inspect.iscoroutinefunction(SmolVLMAdapter.batch_infer)

    def test_close_is_async(self):
        """close method should be async."""
        assert inspect.iscoroutinefunction(SmolVLMAdapter.close)

    def test_aenter_is_async(self):
        """__aenter__ method should be async."""
        assert inspect.iscoroutinefunction(SmolVLMAdapter.__aenter__)

    def test_aexit_is_async(self):
        """__aexit__ method should be async."""
        assert inspect.iscoroutinefunction(SmolVLMAdapter.__aexit__)

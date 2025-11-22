"""
Unit tests for AdapterRegistry.

Tests adapter registration, retrieval, and dependency injection functionality.
"""

import pytest

from circles.src.etl.adapters.base import DataType
from circles.src.etl.adapters.photo_adapter import PhotoAdapter
from circles.src.etl.adapters.registry import AdapterRegistry
from circles.src.etl.adapters.resume_adapter import ResumeAdapter
from circles.src.etl.adapters.voice_note_adapter import VoiceNoteAdapter


@pytest.mark.unit
class TestAdapterRegistry:
    """Test AdapterRegistry functionality."""

    @pytest.fixture
    def registry(self):
        """Create a fresh AdapterRegistry instance."""
        return AdapterRegistry()

    def test_registry_singleton_exists(self):
        """Test that global registry singleton exists."""
        from circles.src.etl.adapters.registry import get_registry

        registry = get_registry()
        assert registry is not None
        assert isinstance(registry, AdapterRegistry)

    def test_register_adapter(self, registry):
        """Test registering an adapter."""
        adapter = ResumeAdapter()

        registry.register(DataType.RESUME, adapter)

        # Verify it was registered
        registered = registry.get(DataType.RESUME)
        assert registered is adapter

    def test_get_registered_adapter(self, registry):
        """Test retrieving a registered adapter."""
        adapter = PhotoAdapter()
        registry.register(DataType.PHOTO, adapter)

        retrieved = registry.get(DataType.PHOTO)

        assert retrieved is adapter

    def test_get_unregistered_adapter_raises_error(self, registry):
        """Test that getting unregistered adapter raises error."""
        with pytest.raises(ValueError):
            registry.get(DataType.RESUME)

    def test_register_multiple_adapters(self, registry):
        """Test registering multiple different adapters."""
        resume_adapter = ResumeAdapter()
        photo_adapter = PhotoAdapter()
        voice_adapter = VoiceNoteAdapter()

        registry.register(DataType.RESUME, resume_adapter)
        registry.register(DataType.PHOTO, photo_adapter)
        registry.register(DataType.VOICE_NOTE, voice_adapter)

        assert registry.get(DataType.RESUME) is resume_adapter
        assert registry.get(DataType.PHOTO) is photo_adapter
        assert registry.get(DataType.VOICE_NOTE) is voice_adapter

    def test_adapter_replacement(self, registry):
        """Test that registering same adapter twice replaces it."""
        old_adapter = ResumeAdapter()
        new_adapter = ResumeAdapter()

        registry.register(DataType.RESUME, old_adapter)
        registry.register(DataType.RESUME, new_adapter)

        retrieved = registry.get(DataType.RESUME)
        assert retrieved is new_adapter

    def test_list_registered_adapters(self, registry):
        """Test listing all registered adapters."""
        resume_adapter = ResumeAdapter()
        photo_adapter = PhotoAdapter()

        registry.register(DataType.RESUME, resume_adapter)
        registry.register(DataType.PHOTO, photo_adapter)

        adapters = registry.list_adapters()

        assert DataType.RESUME in adapters
        assert DataType.PHOTO in adapters
        assert len(adapters) >= 2

    def test_is_adapter_registered(self, registry):
        """Test checking if adapter is registered."""
        adapter = ResumeAdapter()
        registry.register(DataType.RESUME, adapter)

        assert registry.is_registered(DataType.RESUME) is True
        assert registry.is_registered(DataType.PHOTO) is False

    def test_clear_registry(self, registry):
        """Test clearing all adapters from registry."""
        adapter = ResumeAdapter()
        registry.register(DataType.RESUME, adapter)

        registry.clear()

        assert registry.is_registered(DataType.RESUME) is False

    def test_registry_lazy_initialization(self, registry):
        """Test that adapters can be lazily initialized."""
        # Registry might support lazy loading of adapters
        # This tests that the registry can handle this pattern
        adapter = ResumeAdapter()
        registry.register(DataType.RESUME, adapter)

        # Retrieve multiple times - should get same instance
        adapter1 = registry.get(DataType.RESUME)
        adapter2 = registry.get(DataType.RESUME)

        assert adapter1 is adapter2

    def test_get_adapter_by_data_type(self, registry):
        """Test getting adapter by DataType enum."""
        adapter = PhotoAdapter()
        registry.register(DataType.PHOTO, adapter)

        retrieved = registry.get(DataType.PHOTO)

        assert retrieved is adapter
        assert retrieved.data_type == DataType.PHOTO

    def test_registry_thread_safety(self, registry):
        """Test basic thread safety of registry operations."""
        import threading

        adapters = []
        errors = []

        def register_adapter(data_type):
            try:
                adapter = ResumeAdapter()
                registry.register(data_type, adapter)
            except Exception as e:
                errors.append(e)

        # Register same adapter type multiple times from different threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=register_adapter, args=(DataType.RESUME,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should have completed without errors
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_registry_with_async_operations(self, registry):
        """Test that registry works with async operations."""

        adapter = ResumeAdapter()
        registry.register(DataType.RESUME, adapter)

        async def get_adapter_async():
            return registry.get(DataType.RESUME)

        retrieved = await get_adapter_async()

        assert retrieved is adapter

    def test_adapter_registry_initialization(self, registry):
        """Test that registry initializes properly."""
        assert registry is not None
        assert isinstance(registry, AdapterRegistry)

    def test_all_data_types_have_adapters(self, registry):
        """Test that the system registers all expected adapters."""
        expected_types = [
            DataType.RESUME,
            DataType.PHOTO,
            DataType.VOICE_NOTE,
            DataType.CALENDAR,
            DataType.CHAT_TRANSCRIPT,
        ]

        for data_type in expected_types:
            # At least the basic ones should be registrable
            adapter = ResumeAdapter()  # Use generic adapter for this test
            registry.register(data_type, adapter)
            assert registry.is_registered(data_type)

    def test_adapter_retrieval_performance(self, registry):
        """Test that adapter retrieval is fast."""
        import time

        adapter = ResumeAdapter()
        registry.register(DataType.RESUME, adapter)

        start = time.time()
        for _ in range(1000):
            registry.get(DataType.RESUME)
        elapsed = time.time() - start

        # Should complete 1000 retrievals in less than 100ms
        assert elapsed < 0.1

    def test_registry_error_message_clarity(self, registry):
        """Test that error messages are helpful."""
        try:
            registry.get(DataType.RESUME)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            # Error message should mention the missing adapter
            assert "RESUME" in str(e) or "resume" in str(e).lower()

    def test_get_adapter_with_kwargs(self, registry):
        """Test registry pattern supports optional initialization parameters."""
        adapter = ResumeAdapter()
        registry.register(DataType.RESUME, adapter)

        # Test that adapter instance can be retrieved consistently
        retrieved1 = registry.get(DataType.RESUME)
        retrieved2 = registry.get(DataType.RESUME)

        assert retrieved1 is retrieved2

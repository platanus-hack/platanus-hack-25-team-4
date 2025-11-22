"""
Adapter Registry - Dependency Injection container for all adapters.

Manages registration, retrieval, and initialization of adapters.
Implements the Service Locator pattern for flexible adapter discovery.
"""

from typing import Dict, List, Optional

from ..core import ProcessingError, Result
from .base import BaseAdapter


class AdapterRegistry:
    """
    Central registry for all ETL adapters.

    Provides:
    - Adapter registration and retrieval
    - Dependency injection container
    - Lazy initialization support
    - Adapter listing and discovery

    Usage:
        registry = AdapterRegistry()
        registry.register("resume", ResumeAdapter())
        adapter = registry.get_adapter("resume")
        result = await adapter.execute(input_data, context, session)
    """

    def __init__(self):
        """Initialize empty registry."""
        self._adapters: Dict[str, BaseAdapter] = {}
        self._initialized = False
        self._initialization_errors: Dict[str, str] = {}

    def register(self, data_type: str, adapter: BaseAdapter) -> Result[None, str]:
        """
        Register an adapter for a data type.

        Args:
            data_type: String identifier (e.g., "resume", "photo")
            adapter: BaseAdapter instance

        Returns:
            Result.ok(None) if registered successfully
            Result.error(str) if data_type already registered
        """
        if data_type in self._adapters:
            error = f"Adapter already registered for: {data_type}"
            return Result.error(error)

        self._adapters[data_type] = adapter
        return Result.ok(None)

    def get_adapter(self, data_type: str) -> Result[BaseAdapter, ProcessingError]:
        """
        Get adapter for a data type.

        Args:
            data_type: String identifier (e.g., "resume", "photo")

        Returns:
            Result.ok(BaseAdapter) if registered
            Result.error(ProcessingError) if not found
        """
        adapter = self._adapters.get(data_type)
        if not adapter:
            error = ProcessingError(
                f"No adapter registered for: {data_type}",
                error_type="adapter_not_found",
                details={"available_adapters": list(self._adapters.keys())},
            )
            return Result.error(error)
        return Result.ok(adapter)

    def list_adapters(self) -> List[str]:
        """
        List all registered adapter types.

        Returns:
            List of registered data type strings
        """
        return list(self._adapters.keys())

    def is_registered(self, data_type: str) -> bool:
        """Check if adapter is registered for data type."""
        return data_type in self._adapters

    async def initialize_all(self) -> Result[None, str]:
        """
        Initialize all registered adapters.

        Useful for warming up resources (loading models, connecting to services).
        Can be called at application startup.

        Returns:
            Result.ok(None) if all initialized
            Result.error(str) if any initialization fails
        """
        if self._initialized:
            return Result.ok(None)

        self._initialization_errors.clear()

        for data_type, adapter in self._adapters.items():
            try:
                if hasattr(adapter, "initialize"):
                    result = await adapter.initialize()  # type: ignore
                    if isinstance(result, Result) and result.is_error:
                        self._initialization_errors[data_type] = result.error_value
            except Exception as e:
                self._initialization_errors[data_type] = str(e)

        if self._initialization_errors:
            error_msg = "Initialization errors: " + str(self._initialization_errors)
            return Result.error(error_msg)

        self._initialized = True
        return Result.ok(None)

    def __repr__(self) -> str:
        """String representation."""
        adapter_list = ", ".join(self.list_adapters())
        return f"AdapterRegistry(adapters=[{adapter_list}])"


# Global registry instance - singleton for application-wide use
_global_registry: Optional[AdapterRegistry] = None


def get_registry() -> AdapterRegistry:
    """
    Get or create the global adapter registry.

    Returns:
        The global AdapterRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AdapterRegistry()
    return _global_registry


def set_registry(registry: AdapterRegistry) -> None:
    """
    Set the global adapter registry (useful for testing).

    Args:
        registry: AdapterRegistry instance to use globally
    """
    global _global_registry
    _global_registry = registry

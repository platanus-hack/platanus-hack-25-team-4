"""Test environment configuration and settings."""

from typing import Optional

from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    """Test-specific configuration that overrides production settings."""

    # ========================================================================
    # Test Database Configuration
    # ========================================================================
    test_database_url: str = (
        "postgresql+asyncpg://circles_test:circles_test@localhost:5433/circles_test"
    )
    test_database_pool_size: int = 5
    test_database_max_overflow: int = 10

    # ========================================================================
    # Test Redis Configuration
    # ========================================================================
    test_redis_url: str = "redis://localhost:6380/0"
    use_real_redis: bool = False  # Use fakeredis by default for speed

    # ========================================================================
    # Celery Test Configuration
    # ========================================================================
    celery_broker_url: str = "redis://localhost:6380/0"
    celery_result_backend: str = "redis://localhost:6380/1"
    use_real_celery: bool = False  # Use eager mode (synchronous) by default

    # ========================================================================
    # LLM API Configuration
    # ========================================================================
    test_anthropic_api_key: str = "sk-ant-test-mock-key-12345"
    test_openai_api_key: str = "sk-test-mock-key-67890"
    use_real_apis: bool = False  # Use mocked APIs by default

    # ========================================================================
    # File Storage Configuration
    # ========================================================================
    test_upload_dir: str = "/tmp/circles_test_uploads"
    test_fixtures_dir: str = "tests/fixtures"

    # ========================================================================
    # Test Behavior Configuration
    # ========================================================================
    use_real_db: bool = True  # Use real PostgreSQL for better isolation
    use_transaction_rollback: bool = True  # Rollback transactions after tests

    # ========================================================================
    # Test Timeout Configuration
    # ========================================================================
    test_timeout_seconds: int = 30
    async_test_timeout_seconds: int = 60

    # ========================================================================
    # Coverage Threshold Configuration
    # ========================================================================
    coverage_threshold_unit: int = 90  # Unit tests should have 90% coverage
    coverage_threshold_integration: int = 80  # Integration tests 80%
    coverage_threshold_e2e: int = 70  # E2E tests 70%
    coverage_threshold_total: int = 85  # Total coverage 85%

    # ========================================================================
    # Test Parallelization
    # ========================================================================
    max_parallel_workers: int = 4  # Use pytest-xdist for parallel execution

    class Config:
        """Pydantic configuration."""

        env_file = ".env.test"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_prefix = "TEST_"

    def get_database_url(self) -> str:
        """Get the appropriate database URL based on configuration."""
        return self.test_database_url

    def get_redis_url(self) -> str:
        """Get the appropriate Redis URL based on configuration."""
        return self.test_redis_url

    def get_anthropic_api_key(self) -> str:
        """Get Anthropic API key (mock or real based on configuration)."""
        if self.use_real_apis:
            import os

            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set. Set USE_REAL_APIS=false to use mocks."
                )
            return key
        return self.test_anthropic_api_key

    def get_openai_api_key(self) -> str:
        """Get OpenAI API key (mock or real based on configuration)."""
        if self.use_real_apis:
            import os

            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError(
                    "OPENAI_API_KEY not set. Set USE_REAL_APIS=false to use mocks."
                )
            return key
        return self.test_openai_api_key

    def __repr__(self) -> str:
        """String representation (redacts sensitive values)."""
        return (
            f"TestSettings("
            f"database_url=***,"
            f"redis_url={self.test_redis_url},"
            f"use_real_apis={self.use_real_apis},"
            f"use_real_db={self.use_real_db},"
            f"use_real_redis={self.use_real_redis},"
            f"use_real_celery={self.use_real_celery}"
            f")"
        )


# Global test settings instance
_test_settings: Optional[TestSettings] = None


def get_test_settings() -> TestSettings:
    """Get the global test settings instance."""
    global _test_settings
    if _test_settings is None:
        _test_settings = TestSettings()
    return _test_settings


def set_test_settings(settings: TestSettings) -> None:
    """Set the global test settings instance (useful for test overrides)."""
    global _test_settings
    _test_settings = settings

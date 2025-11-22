"""
Configuration - Settings for the ETL system.

Loads configuration from environment variables using Pydantic.
All settings are validated at application startup.
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Example .env file:
        DATABASE_URL=postgresql+asyncpg://user:pass@localhost/circles
        ANTHROPIC_API_KEY=sk-ant-...
        OPENAI_API_KEY=sk-...
        REDIS_URL=redis://localhost:6379
        UPLOAD_DIR=/tmp/uploads
    """

    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================
    database_url: str = "postgresql+asyncpg://circles:circles@localhost/circles"
    database_pool_size: int = 20
    database_max_overflow: int = 40

    # ========================================================================
    # REDIS & CELERY CONFIGURATION
    # ========================================================================
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    # Default to Redis URLs if not specified
    @property
    def _celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def _celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    # ========================================================================
    # API KEY CONFIGURATION - REQUIRED
    # ========================================================================
    anthropic_api_key: str = ""  # sk-ant-...
    openai_api_key: str = ""  # sk-...

    # ========================================================================
    # JWT AUTHENTICATION CONFIGURATION
    # ========================================================================
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # ========================================================================
    # FILE UPLOAD CONFIGURATION
    # ========================================================================
    upload_dir: str = "/tmp/etl_uploads"
    max_upload_size: int = 50 * 1024 * 1024  # 50 MB
    upload_cleanup_hours: int = 24  # Delete uploads after 24 hours

    # ========================================================================
    # ADAPTER CONFIGURATION
    # ========================================================================
    # Resume adapter settings
    resume_min_size: int = 1024  # 1 KB minimum
    resume_max_size: int = 10 * 1024 * 1024  # 10 MB

    # Photo/Image settings
    photo_max_size: int = 25 * 1024 * 1024  # 25 MB
    vlm_model: str = "claude-3-5-sonnet-20241022"

    # Audio settings
    audio_max_size: int = 50 * 1024 * 1024  # 50 MB
    whisper_model: str = "whisper-1"

    # Calendar settings
    calendar_max_size: int = 5 * 1024 * 1024  # 5 MB

    # ========================================================================
    # APPLICATION CONFIGURATION
    # ========================================================================
    app_name: str = "Circles ETL"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # ========================================================================
    # PROCESSING CONFIGURATION
    # ========================================================================
    max_processing_time_seconds: int = 300  # 5 minutes
    max_retries: int = 3
    retry_delay_seconds: int = 5

    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    batch_size: int = 10
    max_concurrent_tasks: int = 5

    # ========================================================================
    # CLEANUP CONFIGURATION
    # ========================================================================
    auto_cleanup_failed_uploads: bool = True
    cleanup_interval_hours: int = 1

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def validate_required_keys(self) -> list[str]:
        """
        Validate that required API keys are configured.

        Returns:
            List of missing required keys (empty if all present)
        """
        missing = []

        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")

        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")

        return missing

    @property
    def upload_dir_path(self) -> Path:
        """Get upload directory as Path object."""
        return Path(self.upload_dir)

    def __repr__(self) -> str:
        """String representation (redacts sensitive values)."""
        return (
            f"Settings("
            f"database_url=***,"
            f"anthropic_api_key={'set' if self.anthropic_api_key else 'NOT SET'},"
            f"openai_api_key={'set' if self.openai_api_key else 'NOT SET'},"
            f"redis_url={self.redis_url},"
            f"upload_dir={self.upload_dir},"
            f"debug={self.debug}"
            f")"
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def set_settings(settings: Settings) -> None:
    """Set the global settings instance (useful for testing)."""
    global _settings
    _settings = settings

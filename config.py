"""
Application configuration management using Pydantic Settings.
Loads configuration from environment variables with validation and defaults.
"""

import logging
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Required settings (no default)
    instagram_username: str = Field(
        ...,
        description="Instagram account username",
        validation_alias="INSTAGRAM_USERNAME"
    )
    instagram_password: SecretStr = Field(
        ...,
        description="Instagram account password or app-specific password",
        validation_alias="INSTAGRAM_PASSWORD"
    )

    # API settings
    api_port: int = Field(
        default=5000,
        description="Port for API server",
        ge=1024,
        le=65535,
        validation_alias="API_PORT"
    )
    api_host: str = Field(
        default="0.0.0.0",
        description="Host binding for API server",
        validation_alias="API_HOST"
    )

    # Template settings
    template_path: Path = Field(
        default=Path("/app/templates"),
        description="Path to story templates directory",
        validation_alias="TEMPLATE_PATH"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        validation_alias="LOG_LEVEL"
    )

    # Advanced settings
    request_timeout: int = Field(
        default=120,
        description="HTTP request timeout in seconds",
        ge=10,
        le=600,
        validation_alias="REQUEST_TIMEOUT"
    )
    instagram_session_path: Path = Field(
        default=Path("/app/session"),
        description="Path for Instagram session storage",
        validation_alias="INSTAGRAM_SESSION_PATH"
    )
    max_concurrent_requests: int = Field(
        default=5,
        description="Max simultaneous story posts",
        ge=1,
        le=20,
        validation_alias="MAX_CONCURRENT_REQUESTS"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate template path exists (only in non-Docker environments)
        # In Docker, the path may not exist yet, so we only warn
        if not self.template_path.exists():
            logger = logging.getLogger(__name__)
            logger.warning(f"Template path does not exist: {self.template_path}")


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()


def log_configuration():
    """Log loaded configuration on startup (mask sensitive values)."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Application Configuration Loaded")
    logger.info("=" * 60)
    logger.info(f"Instagram Username: {settings.instagram_username}")
    logger.info(f"Instagram Password: {'*' * 8}")
    logger.info(f"API Host: {settings.api_host}")
    logger.info(f"API Port: {settings.api_port}")
    logger.info(f"Template Path: {settings.template_path}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"Request Timeout: {settings.request_timeout}s")
    logger.info(f"Instagram Session Path: {settings.instagram_session_path}")
    logger.info(f"Max Concurrent Requests: {settings.max_concurrent_requests}")
    logger.info("=" * 60)

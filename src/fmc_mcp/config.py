"""Configuration management for FMC MCP Server."""

import logging
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class FMCSettings(BaseSettings):
    """FMC connection settings loaded from environment variables."""

    # Required settings
    fmc_host: str
    fmc_username: str
    fmc_password: SecretStr

    # Optional settings with defaults
    fmc_verify_ssl: bool = False  # Disabled by default for lab environments
    fmc_domain_uuid: str | None = None  # Auto-discovered if not provided
    fmc_timeout: int = 60  # Request timeout in seconds

    # Rate limiting settings
    fmc_rate_limit: int = 120  # Max requests per minute
    fmc_max_connections: int = 10  # Max concurrent connections

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def log_config(self) -> None:
        """Log configuration (without sensitive data)."""
        logger.info("FMC Configuration:")
        logger.info("  Host: %s", self.fmc_host)
        logger.info("  Username: %s", self.fmc_username)
        logger.info("  SSL Verify: %s", self.fmc_verify_ssl)
        logger.info("  Timeout: %ds", self.fmc_timeout)
        logger.info("  Rate Limit: %d req/min", self.fmc_rate_limit)
        logger.info("  Max Connections: %d", self.fmc_max_connections)
        if self.fmc_domain_uuid:
            logger.info("  Domain UUID: %s", self.fmc_domain_uuid)
        else:
            logger.info("  Domain UUID: (auto-discover)")

        if not self.fmc_verify_ssl:
            logger.warning(
                "SSL verification is DISABLED. This is insecure for production use."
            )


@lru_cache
def get_settings() -> FMCSettings:
    """Get cached settings instance."""
    return FMCSettings()  # type: ignore[call-arg]  # Loaded from env

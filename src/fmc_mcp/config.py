"""Configuration management for FMC MCP Server."""

import logging
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
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
    fmc_timeout: int = Field(default=60, gt=0)  # Request timeout in seconds

    # Rate limiting settings
    fmc_rate_limit: int = Field(default=120, gt=0)  # Max requests per minute
    fmc_max_connections: int = Field(default=10, gt=0)  # Max concurrent connections

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("fmc_host", mode="before")
    @classmethod
    def validate_fmc_host(cls, value: object) -> str:
        """Normalize and validate the host-only FMC address."""
        if not isinstance(value, str):
            raise ValueError("FMC_HOST must be a host name or address")
        host = value.strip()
        if not host or "://" in host or "/" in host:
            raise ValueError("FMC_HOST must contain only a host name or address")
        return host

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
            logger.warning("SSL verification is DISABLED. This is insecure for production use.")


class MCPSettings(BaseSettings):
    """MCP listener settings loaded independently from FMC credentials."""

    mcp_transport: Literal["stdio", "http"] = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = Field(default=8080, ge=1, le=65535)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("mcp_transport", mode="before")
    @classmethod
    def normalize_transport(cls, value: object) -> object:
        """Normalize transport before Literal validation."""
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("mcp_host", mode="before")
    @classmethod
    def validate_mcp_host(cls, value: object) -> str:
        """Require a non-empty bind host."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("MCP_HOST must be a non-empty host name or address")
        return value.strip()


@lru_cache
def get_settings() -> FMCSettings:
    """Get cached settings instance."""
    return FMCSettings()  # type: ignore[call-arg]  # Loaded from env


@lru_cache
def get_mcp_settings() -> MCPSettings:
    """Get cached MCP listener settings."""
    return MCPSettings()

"""Tests for validated FMC and MCP configuration."""

import pytest
from pydantic import ValidationError

from fmc_mcp.config import FMCSettings, MCPSettings

BASE_FMC_SETTINGS = {
    "fmc_host": "fmc.test.local",
    "fmc_username": "testuser",
    "fmc_password": "testpass",
}


@pytest.mark.parametrize("field", ["fmc_timeout", "fmc_rate_limit", "fmc_max_connections"])
@pytest.mark.parametrize("value", [0, -1])
def test_fmc_settings_reject_non_positive_operational_values(field: str, value: int) -> None:
    """Operational limits must fail validation before runtime primitives are built."""
    values = {**BASE_FMC_SETTINGS, field: value}

    with pytest.raises(ValidationError):
        FMCSettings(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("host", ["", "   ", "https://fmc.test.local", "fmc.test.local/path"])
def test_fmc_settings_reject_invalid_host(host: str) -> None:
    """FMC_HOST is a host only, not an empty value or URL."""
    with pytest.raises(ValidationError):
        FMCSettings(**{**BASE_FMC_SETTINGS, "fmc_host": host})  # type: ignore[arg-type]


def test_fmc_settings_normalize_host_whitespace() -> None:
    """Benign surrounding whitespace is removed."""
    settings = FMCSettings(**{**BASE_FMC_SETTINGS, "fmc_host": " fmc.test.local "})  # type: ignore[arg-type]

    assert settings.fmc_host == "fmc.test.local"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mcp_transport", "websocket"),
        ("mcp_host", "   "),
        ("mcp_port", 0),
        ("mcp_port", 65536),
    ],
)
def test_mcp_settings_reject_invalid_values(field: str, value: str | int) -> None:
    """MCP listener settings fail closed instead of silently falling back."""
    with pytest.raises(ValidationError):
        MCPSettings(**{field: value})  # type: ignore[arg-type]


def test_mcp_settings_normalize_transport_and_host() -> None:
    """Valid transport and host values are normalized."""
    settings = MCPSettings(mcp_transport=" HTTP ", mcp_host=" 127.0.0.1 ")  # type: ignore[arg-type]

    assert settings.mcp_transport == "http"
    assert settings.mcp_host == "127.0.0.1"

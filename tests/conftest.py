"""Pytest fixtures for FMC MCP tests."""

import re

import pytest
from pytest_httpx import HTTPXMock

from fmc_mcp.client import FMCClient
from fmc_mcp.config import FMCSettings


@pytest.fixture
def fmc_settings() -> FMCSettings:
    """Create test FMC settings."""
    return FMCSettings(
        fmc_host="fmc.test.local",
        fmc_username="testuser",
        fmc_password="testpass",  # type: ignore[arg-type]
        fmc_verify_ssl=False,
        fmc_domain_uuid="test-domain-uuid",
    )


@pytest.fixture
def fmc_client(fmc_settings: FMCSettings) -> FMCClient:
    """Create FMC client with test settings."""
    return FMCClient(fmc_settings)


@pytest.fixture
def mock_auth_response(httpx_mock: HTTPXMock) -> None:
    """Mock successful authentication response."""
    httpx_mock.add_response(
        method="POST",
        url="https://fmc.test.local/api/fmc_platform/v1/auth/generatetoken",
        status_code=204,
        headers={
            "X-auth-access-token": "test-access-token",
            "X-auth-refresh-token": "test-refresh-token",
            "DOMAIN_UUID": "test-domain-uuid",
        },
    )


@pytest.fixture
def mock_server_version(httpx_mock: HTTPXMock) -> None:
    """Mock server version response."""
    httpx_mock.add_response(
        method="GET",
        url="https://fmc.test.local/api/fmc_platform/v1/info/serverversion",
        json={
            "serverVersion": "7.4.2.3",
            "geoVersion": "2024-01-01",
            "vdbVersion": "123",
        },
    )


@pytest.fixture
def mock_devices(httpx_mock: HTTPXMock) -> None:
    """Mock device records response."""
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r".*devices/devicerecords.*"),
        json={
            "items": [
                {
                    "name": "FTD-01",
                    "id": "device-1",
                    "hostName": "ftd-01.test.local",
                    "type": "Device",
                    "healthStatus": "green",
                    "model": "Firepower 2110",
                    "sw_version": "7.4.2",
                },
                {
                    "name": "FTD-02",
                    "id": "device-2",
                    "hostName": "ftd-02.test.local",
                    "type": "Device",
                    "healthStatus": "green",
                    "model": "Firepower 2120",
                    "sw_version": "7.4.2",
                },
            ],
            "paging": {"offset": 0, "limit": 1000, "count": 2, "pages": 1},
        },
    )


@pytest.fixture
def mock_network_objects(httpx_mock: HTTPXMock) -> None:
    """Mock network objects response."""
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r".*object/networks.*"),
        json={
            "items": [
                {
                    "name": "Internal-Network",
                    "id": "net-1",
                    "value": "10.10.10.0/24",
                    "type": "Network",
                    "description": "Internal network",
                },
                {
                    "name": "DMZ-Network",
                    "id": "net-2",
                    "value": "192.168.1.0/24",
                    "type": "Network",
                    "description": "DMZ network",
                },
            ],
            "paging": {"offset": 0, "limit": 1000, "count": 2, "pages": 1},
        },
    )


@pytest.fixture
def mock_host_objects(httpx_mock: HTTPXMock) -> None:
    """Mock host objects response."""
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r".*object/hosts.*"),
        json={
            "items": [
                {
                    "name": "WebServer",
                    "id": "host-1",
                    "value": "10.10.10.5",
                    "type": "Host",
                    "description": "Web server",
                },
            ],
            "paging": {"offset": 0, "limit": 1000, "count": 1, "pages": 1},
        },
    )


@pytest.fixture
def mock_deployable_devices(httpx_mock: HTTPXMock) -> None:
    """Mock deployable devices response."""
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r".*deployment/deployabledevices.*"),
        json={
            "items": [
                {
                    "name": "FTD-01",
                    "id": "device-1",
                    "type": "Device",
                    "canBeDeployed": True,
                    "upToDate": False,
                },
            ],
            "paging": {"offset": 0, "limit": 1000, "count": 1, "pages": 1},
        },
    )

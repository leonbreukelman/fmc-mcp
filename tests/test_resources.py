"""Tests for MCP resources and tools."""

import json

import pytest
from pytest_httpx import HTTPXMock

from fmc_mcp import resources, tools
from fmc_mcp.client import FMCClient
from fmc_mcp.config import FMCSettings


@pytest.fixture
async def initialized_client(
    fmc_settings: FMCSettings,
    httpx_mock: HTTPXMock,
) -> FMCClient:
    """Create an initialized FMC client with mocked auth."""
    httpx_mock.add_response(
        method="POST",
        url="https://fmc.test.local/api/fmc_platform/v1/auth/generatetoken",
        status_code=204,
        headers={
            "X-auth-access-token": "test-token",
            "X-auth-refresh-token": "test-refresh",
            "DOMAIN_UUID": "test-domain-uuid",
        },
    )

    client = FMCClient(fmc_settings)
    await client.connect()
    resources.set_client(client)
    yield client
    await client.close()


class TestResources:
    """Tests for MCP resources."""

    @pytest.mark.asyncio
    async def test_get_system_info(
        self,
        initialized_client: FMCClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test system info resource."""
        httpx_mock.add_response(
            method="GET",
            url="https://fmc.test.local/api/fmc_platform/v1/info/serverversion",
            json={"serverVersion": "7.4.2.3"},
        )

        result = await resources.get_system_info()
        data = json.loads(result)
        assert data["serverVersion"] == "7.4.2.3"

    @pytest.mark.asyncio
    async def test_list_devices(
        self,
        initialized_client: FMCClient,
        mock_devices: None,
    ) -> None:
        """Test devices list resource."""
        result = await resources.list_devices()
        data = json.loads(result)
        assert data["count"] == 2
        assert data["devices"][0]["name"] == "FTD-01"

    @pytest.mark.asyncio
    async def test_list_network_objects(
        self,
        initialized_client: FMCClient,
        mock_network_objects: None,
    ) -> None:
        """Test network objects resource."""
        result = await resources.list_network_objects()
        data = json.loads(result)
        assert data["count"] == 2
        assert data["networkObjects"][0]["name"] == "Internal-Network"


class TestTools:
    """Tests for MCP tools."""

    @pytest.mark.asyncio
    async def test_search_object_by_ip_found(
        self,
        initialized_client: FMCClient,
        mock_network_objects: None,
        mock_host_objects: None,
    ) -> None:
        """Test IP search with match."""
        result = await tools.search_object_by_ip("10.10.10.5")
        data = json.loads(result)

        assert data["searchedIP"] == "10.10.10.5"
        assert data["count"] >= 1

        # Should find the host object and the network containing it
        names = [m["name"] for m in data["matches"]]
        assert "WebServer" in names or "Internal-Network" in names

    @pytest.mark.asyncio
    async def test_search_object_by_ip_not_found(
        self,
        initialized_client: FMCClient,
        mock_network_objects: None,
        mock_host_objects: None,
    ) -> None:
        """Test IP search with no match."""
        result = await tools.search_object_by_ip("8.8.8.8")
        data = json.loads(result)

        assert data["count"] == 0
        assert len(data["matches"]) == 0

    @pytest.mark.asyncio
    async def test_search_object_invalid_ip(
        self,
        initialized_client: FMCClient,
    ) -> None:
        """Test IP search with invalid IP."""
        result = await tools.search_object_by_ip("not-an-ip")
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_check_deployment_status(
        self,
        initialized_client: FMCClient,
        mock_deployable_devices: None,
    ) -> None:
        """Test deployment status check."""
        result = await tools.check_deployment_status()
        data = json.loads(result)

        assert data["count"] == 1
        assert data["allDevicesSynced"] is False
        assert data["devices"][0]["name"] == "FTD-01"

    @pytest.mark.asyncio
    async def test_check_deployment_status_filtered(
        self,
        initialized_client: FMCClient,
        mock_deployable_devices: None,
    ) -> None:
        """Test deployment status with device filter."""
        result = await tools.check_deployment_status("FTD-01")
        data = json.loads(result)

        assert data["filter"] == "FTD-01"
        assert data["count"] == 1

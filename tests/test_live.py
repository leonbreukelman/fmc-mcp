"""Opt-in read-only integration test against a real Cisco FMC instance."""

import json
import os

import pytest

from fmc_mcp import resources, tools
from fmc_mcp.client import FMCClient


@pytest.mark.live
@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("FMC_LIVE_TEST") != "1",
    reason="set FMC_LIVE_TEST=1 with read-only FMC credentials to run",
)
async def test_read_only_fmc_smoke() -> None:
    """Fail on required read-path errors; deployment permission denial stays explicit."""
    async with FMCClient() as client:
        resources.set_client(client)

        version = await client.get_server_version()
        assert isinstance(version, dict)
        assert version

        devices = await client.get_devices()
        networks = await client.get_network_objects()
        hosts = await client.get_host_objects()
        assert isinstance(devices, list)
        assert isinstance(networks, list)
        assert isinstance(hosts, list)

        system_info = json.loads(await resources.get_system_info())
        device_resource = json.loads(await resources.list_devices())
        search_result = json.loads(await tools.search_object_by_ip("192.0.2.1"))
        deployment = json.loads(await tools.check_deployment_status())

        assert system_info
        assert device_resource["count"] == len(devices)
        assert isinstance(search_result["matches"], list)
        assert deployment["status"] in {"ok", "unavailable"}
        if deployment["status"] == "unavailable":
            assert deployment["reason"] == "permission_denied"

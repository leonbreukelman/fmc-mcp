"""MCP Resource definitions for FMC data."""

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fmc_mcp.client import FMCClient

logger = logging.getLogger(__name__)

# Global client instance (set by server.py during startup)
_fmc_client: "FMCClient | None" = None


def set_client(client: "FMCClient") -> None:
    """Set the global FMC client instance."""
    global _fmc_client
    _fmc_client = client


def get_client() -> "FMCClient":
    """Get the global FMC client instance."""
    if _fmc_client is None:
        raise RuntimeError("FMC client not initialized")
    return _fmc_client


async def get_system_info() -> str:
    """Get FMC system information.

    Returns:
        JSON string with server version and system info
    """
    client = get_client()
    version = await client.get_server_version()
    return json.dumps(version, indent=2)


async def list_devices() -> str:
    """List all managed firewall devices.

    Returns:
        JSON string with device list
    """
    client = get_client()
    devices = await client.get_devices()

    # Create a summary for each device
    summary = []
    for device in devices:
        summary.append({
            "name": device.get("name"),
            "id": device.get("id"),
            "hostName": device.get("hostName"),
            "type": device.get("type"),
            "healthStatus": device.get("healthStatus"),
            "model": device.get("model"),
            "sw_version": device.get("sw_version"),
        })

    return json.dumps({"devices": summary, "count": len(summary)}, indent=2)


async def list_network_objects() -> str:
    """List all network objects.

    Returns:
        JSON string with network objects
    """
    client = get_client()
    objects = await client.get_network_objects()

    # Create a summary for each object
    summary = []
    for obj in objects:
        summary.append({
            "name": obj.get("name"),
            "id": obj.get("id"),
            "value": obj.get("value"),
            "type": obj.get("type"),
            "description": obj.get("description"),
        })

    return json.dumps({"networkObjects": summary, "count": len(summary)}, indent=2)


async def get_deployment_status() -> str:
    """Get deployment status of all devices.

    Returns:
        JSON string with deployment status
    """
    client = get_client()
    deployable = await client.get_deployable_devices()

    summary = []
    for device in deployable:
        summary.append({
            "name": device.get("name"),
            "id": device.get("id"),
            "type": device.get("type"),
            "canBeDeployed": device.get("canBeDeployed"),
            "upToDate": device.get("upToDate"),
        })

    return json.dumps({
        "deployableDevices": summary,
        "count": len(summary),
        "hasPendingChanges": len(summary) > 0,
    }, indent=2)

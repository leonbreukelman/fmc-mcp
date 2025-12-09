"""MCP Tool definitions for FMC queries."""

import ipaddress
import json
import logging

from fmc_mcp.resources import get_client

logger = logging.getLogger(__name__)


async def search_object_by_ip(ip_address: str) -> str:
    """Find network objects containing the specified IP address.

    Args:
        ip_address: IP address to search for (e.g., "10.10.10.5")

    Returns:
        JSON string with matching objects
    """
    try:
        search_ip = ipaddress.ip_address(ip_address)
    except ValueError:
        return json.dumps({"error": f"Invalid IP address: {ip_address}"})

    client = get_client()

    # Search network objects
    networks = await client.get_network_objects()
    hosts = await client.get_host_objects()

    matches = []

    # Check network objects (subnets)
    for obj in networks:
        value = obj.get("value", "")
        try:
            if "/" in value:
                # It's a network/subnet
                network = ipaddress.ip_network(value, strict=False)
                if search_ip in network:
                    matches.append({
                        "type": "network",
                        "name": obj.get("name"),
                        "value": value,
                        "id": obj.get("id"),
                        "description": obj.get("description"),
                    })
            else:
                # It's a single IP
                if ipaddress.ip_address(value) == search_ip:
                    matches.append({
                        "type": "network",
                        "name": obj.get("name"),
                        "value": value,
                        "id": obj.get("id"),
                        "description": obj.get("description"),
                    })
        except (ValueError, TypeError):
            continue

    # Check host objects
    for obj in hosts:
        value = obj.get("value", "")
        try:
            if ipaddress.ip_address(value) == search_ip:
                matches.append({
                    "type": "host",
                    "name": obj.get("name"),
                    "value": value,
                    "id": obj.get("id"),
                    "description": obj.get("description"),
                })
        except (ValueError, TypeError):
            continue

    return json.dumps({
        "searchedIP": ip_address,
        "matches": matches,
        "count": len(matches),
    }, indent=2)


async def check_deployment_status(device_name: str | None = None) -> str:
    """Check if devices have pending changes awaiting deployment.

    Args:
        device_name: Optional device name to filter (checks all if not provided)

    Returns:
        JSON string with deployment status
    """
    client = get_client()
    deployable = await client.get_deployable_devices()

    if device_name:
        # Filter to specific device
        deployable = [d for d in deployable if d.get("name", "").lower() == device_name.lower()]

    results = []
    for device in deployable:
        results.append({
            "name": device.get("name"),
            "id": device.get("id"),
            "canBeDeployed": device.get("canBeDeployed"),
            "upToDate": device.get("upToDate"),
            "hasPendingChanges": not device.get("upToDate", True),
        })

    all_synced = all(r.get("upToDate", True) for r in results)

    return json.dumps({
        "filter": device_name or "all devices",
        "devices": results,
        "count": len(results),
        "allDevicesSynced": all_synced if results else True,
        "summary": "All devices are in sync" if all_synced else f"{sum(1 for r in results if not r.get('upToDate'))} device(s) have pending changes",
    }, indent=2)

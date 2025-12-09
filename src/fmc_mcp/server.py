"""FastMCP server for Cisco FMC."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from fmc_mcp import resources, tools
from fmc_mcp.client import FMCClient
from fmc_mcp.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global FMC client
_client: FMCClient | None = None


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Lifecycle manager for FMC client."""
    global _client

    logger.info("Starting FMC MCP Server")

    # Initialize FMC client
    settings = get_settings()
    _client = FMCClient(settings)
    await _client.connect()

    # Set client in resources module
    resources.set_client(_client)

    try:
        yield
    finally:
        logger.info("Shutting down FMC MCP Server")
        if _client:
            await _client.close()
            _client = None


# Create FastMCP server instance
mcp = FastMCP(
    "fmc-mcp",
    lifespan=lifespan,
)


# Register Resources
@mcp.resource("fmc://system/info")
async def system_info_resource() -> str:
    """Get FMC system version and health information."""
    return await resources.get_system_info()


@mcp.resource("fmc://devices/list")
async def devices_list_resource() -> str:
    """List all managed firewall devices."""
    return await resources.list_devices()


@mcp.resource("fmc://objects/network")
async def network_objects_resource() -> str:
    """List all network objects (IP addresses, subnets)."""
    return await resources.list_network_objects()


@mcp.resource("fmc://deployment/status")
async def deployment_status_resource() -> str:
    """Get deployment status showing devices with pending changes."""
    return await resources.get_deployment_status()


# Register Tools
@mcp.tool()
async def search_object_by_ip(ip_address: str) -> str:
    """Find network objects containing a specific IP address.

    Args:
        ip_address: The IP address to search for (e.g., "10.10.10.5")

    Returns:
        JSON with matching network and host objects
    """
    return await tools.search_object_by_ip(ip_address)


@mcp.tool()
async def get_deployment_status(device_name: str | None = None) -> str:
    """Check deployment status of firewall devices.

    Args:
        device_name: Optional device name to check (checks all if not provided)

    Returns:
        JSON with deployment status and pending changes
    """
    return await tools.check_deployment_status(device_name)


def main() -> None:
    """Run the FMC MCP server."""
    logger.info("FMC MCP Server starting...")
    mcp.run()


if __name__ == "__main__":
    main()

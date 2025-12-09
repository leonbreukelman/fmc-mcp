"""Cisco FMC MCP Server - Read-only Model Context Protocol server for Firepower Management Center."""

__version__ = "0.1.0"

from fmc_mcp.server import main, mcp

__all__ = ["mcp", "main", "__version__"]

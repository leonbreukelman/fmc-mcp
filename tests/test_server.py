"""Tests for MCP registration wrappers and transport selection."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from fmc_mcp import resources, server, tools


@pytest.mark.asyncio
async def test_resource_and_tool_wrappers_delegate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registered MCP handlers preserve the underlying resource/tool results."""
    system_info = AsyncMock(return_value='{"system": true}')
    devices = AsyncMock(return_value='{"devices": []}')
    networks = AsyncMock(return_value='{"networkObjects": []}')
    deployment_resource = AsyncMock(return_value='{"status": "ok"}')
    search = AsyncMock(return_value='{"matches": []}')
    deployment_tool = AsyncMock(return_value='{"status": "ok"}')

    monkeypatch.setattr(resources, "get_system_info", system_info)
    monkeypatch.setattr(resources, "list_devices", devices)
    monkeypatch.setattr(resources, "list_network_objects", networks)
    monkeypatch.setattr(resources, "get_deployment_status", deployment_resource)
    monkeypatch.setattr(tools, "search_object_by_ip", search)
    monkeypatch.setattr(tools, "check_deployment_status", deployment_tool)

    assert await server.system_info_resource() == '{"system": true}'
    assert await server.devices_list_resource() == '{"devices": []}'
    assert await server.network_objects_resource() == '{"networkObjects": []}'
    assert await server.deployment_status_resource() == '{"status": "ok"}'
    assert await server.search_object_by_ip("192.0.2.5") == '{"matches": []}'
    assert await server.get_deployment_status("FTD-01") == '{"status": "ok"}'

    search.assert_awaited_once_with("192.0.2.5")
    deployment_tool.assert_awaited_once_with("FTD-01")


def test_main_selects_stdio_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    """stdio remains the default MCP transport."""
    run = Mock()
    monkeypatch.setattr(
        server,
        "get_mcp_settings",
        Mock(return_value=SimpleNamespace(mcp_transport="stdio")),
    )
    monkeypatch.setattr(server.mcp, "run", run)

    server.main()

    run.assert_called_once_with()


def test_main_selects_http_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP mode runs the FastMCP SSE coroutine with validated bind settings."""
    run_sse = AsyncMock()
    monkeypatch.setattr(
        server,
        "get_mcp_settings",
        Mock(
            return_value=SimpleNamespace(
                mcp_transport="http",
                mcp_host="127.0.0.1",
                mcp_port=8080,
            )
        ),
    )
    monkeypatch.setattr(server.mcp, "run_sse_async", run_sse)

    server.main()

    run_sse.assert_awaited_once_with()

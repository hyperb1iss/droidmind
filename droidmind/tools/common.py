"""Shared helpers for DroidMind MCP tools."""

from __future__ import annotations

from typing import Any, Protocol

from mcp.server.fastmcp import Context


class _DeviceManager(Protocol):
    async def get_device(self, serial: str) -> Any: ...


async def get_connected_device(*, serial: str, ctx: Context, device_manager: _DeviceManager) -> Any | None:
    """Fetch a connected device or report an error to the MCP context."""
    device = await device_manager.get_device(serial)
    if not device:
        await ctx.error(f"Device {serial} not connected or not found.")
        return None
    return device

"""
Intent helpers shared across tools.

This module contains intent-related logic that is used by multiple tools
without registering additional MCP tools.
"""

from __future__ import annotations

from mcp.server.fastmcp import Context

from droidmind.log import logger
from droidmind.tools.common import _DeviceManager, get_connected_device


async def start_intent(
    *,
    serial: str,
    package: str,
    activity: str,
    ctx: Context,
    extras: dict[str, str] | None = None,
    device_manager: _DeviceManager,
) -> str:
    """Start an explicit activity intent for a package."""
    try:
        device = await get_connected_device(serial=serial, ctx=ctx, device_manager=device_manager)
        if not device:
            return f"Error: Device {serial} not connected or not found."

        extras_display = f" with extras: {extras}" if extras else ""
        await ctx.info(f"Starting activity {package}/{activity}{extras_display} on device {serial}...")
        await device.start_activity(package, activity, extras)
        await ctx.info(f"Activity {package}/{activity} started successfully.")
        return f"Successfully started {package}/{activity}"
    except Exception as e:
        logger.exception("Error starting activity: %s", e)
        await ctx.error(f"Error starting activity: {e!s}")
        return f"Error: {e!s}"

"""
Media Tools - MCP tools for capturing media from Android devices.

This module provides MCP tools for capturing screenshots and other media from Android devices.
"""

import logging

from mcp.server.fastmcp import Context, Image

from droidmind.context import mcp
from droidmind.devices import get_device_manager

logger = logging.getLogger("droidmind")


@mcp.tool()
async def screenshot(serial: str, ctx: Context) -> Image:
    """
    Get a screenshot from a device.

    Args:
        serial: Device serial number

    Returns:
        The device screenshot as an image
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return Image(data=b"", format="png")

        # Take a screenshot using the Device abstraction
        await ctx.info(f"Capturing screenshot from device {serial}...")
        screenshot_data = await device.take_screenshot()

        await ctx.info(f"Screenshot captured successfully ({len(screenshot_data)} bytes)")
        return Image(data=screenshot_data, format="png")
    except Exception as e:
        logger.exception("Error capturing screenshot: %s", e)
        await ctx.error(f"Error capturing screenshot: {e!s}")
        return Image(data=b"", format="png")

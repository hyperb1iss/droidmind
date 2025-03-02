"""
DroidMind Resources - Resource implementations for the DroidMind MCP server.

This module provides resource implementations for the DroidMind MCP server,
allowing AI assistants to access device data in a structured way.

Resources are like read-only endpoints that expose data to the AI assistant.
"""

import logging

from droidmind.adb.service import get_adb
from droidmind.mcp_instance import mcp

logger = logging.getLogger("droidmind")


@mcp.resource("devices://list")
async def get_devices_list() -> str:
    """
    Get a list of all connected devices as a resource.

    Returns:
        A markdown-formatted list of connected devices
    """
    adb = await get_adb()
    devices = await adb.get_devices()

    if not devices:
        return "No devices connected."

    result = "# Connected Devices\n\n"
    for device in devices:
        result += f"- **{device.get('model', 'Unknown')}** (`{device.get('serial', 'Unknown')}`)\n"

    return result

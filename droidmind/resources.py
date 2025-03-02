"""
DroidMind Resources - Resource implementations for the DroidMind MCP server.

This module provides resource implementations for the DroidMind MCP server,
allowing AI assistants to access device data in a structured way.

Resources are like read-only endpoints that expose data to the AI assistant.
"""

import logging

from droidmind.devices import DeviceManager
from droidmind.mcp_instance import mcp

logger = logging.getLogger("droidmind")


@mcp.resource("devices://list")
async def get_devices_list() -> str:
    """
    Get a list of all connected devices as a resource.

    Returns:
        A markdown-formatted list of connected devices
    """
    devices = await DeviceManager.list_devices()

    if not devices:
        return "No devices connected."

    result = "# Connected Devices\n\n"
    for i, device in enumerate(devices, 1):
        model = await device.model
        android_version = await device.android_version
        result += f"## Device {i}: {model}\n"
        result += f"- **Serial**: `{device.serial}`\n"
        result += f"- **Android Version**: {android_version}\n"

    return result

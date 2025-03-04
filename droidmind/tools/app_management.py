"""
App Management Tools - MCP tools for installing and managing Android applications.

This module provides MCP tools for installing, uninstalling, and managing Android applications.
"""

import logging
import os

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager

logger = logging.getLogger("droidmind")


@mcp.tool()
async def install_app(
    serial: str,
    apk_path: str,
    ctx: Context,
    reinstall: bool = False,
    grant_permissions: bool = True,
) -> str:
    """
    Install an APK on the device.

    Args:
        serial: Device serial number
        apk_path: Path to the APK file (local to the server)
        reinstall: Whether to reinstall if app exists
        grant_permissions: Whether to grant all requested permissions

    Returns:
        Installation result message
    """
    try:
        # Check if APK exists
        if not os.path.isfile(apk_path):
            return f"Error: APK file not found at {apk_path}"

        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Install the app
        await ctx.info(f"Installing APK {apk_path} on device {serial}...")
        result = await device.install_app(apk_path, reinstall, grant_permissions)

        if "Success" in result:
            return f"✅ Successfully installed APK on device {serial}"

        return f"❌ Failed to install APK: {result}"
    except Exception as e:
        logger.exception("Error installing APK: %s", e)
        return f"Error installing APK: {e!s}"

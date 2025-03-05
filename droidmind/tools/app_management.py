"""
App Management Tools - MCP tools for installing and managing Android applications.

This module provides MCP tools for installing, uninstalling, and managing Android applications.
"""

import os

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger


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


@mcp.tool()
async def uninstall_app(serial: str, package: str, ctx: Context, keep_data: bool = False) -> str:
    """
    Uninstall an app from the device.

    Args:
        serial: Device serial number
        package: Package name to uninstall
        keep_data: Whether to keep app data and cache directories

    Returns:
        Uninstallation result message
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Uninstall the app
        await ctx.info(f"Uninstalling package {package} from device {serial}...")
        result = await device.uninstall_app(package, keep_data)

        if "Success" in result:
            data_msg = " (keeping app data)" if keep_data else ""
            return f"✅ Successfully uninstalled {package} from device {serial}{data_msg}"

        return f"❌ Failed to uninstall {package}: {result}"
    except Exception as e:
        logger.exception("Error uninstalling app: %s", e)
        return f"Error uninstalling app: {e!s}"


@mcp.tool()
async def start_app(serial: str, package: str, ctx: Context, activity: str = "") -> str:
    """
    Start an app on the device.

    Args:
        serial: Device serial number
        package: Package name to start
        activity: Optional activity name to start (if empty, launches the default activity)

    Returns:
        Result message
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Start the app
        activity_str = f" (activity: {activity})" if activity else ""
        await ctx.info(f"Starting app {package}{activity_str} on device {serial}...")
        result = await device.start_app(package, activity)

        if "Error" in result:
            return f"❌ {result}"

        return f"✅ {result}"
    except Exception as e:
        logger.exception("Error starting app: %s", e)
        return f"Error starting app: {e!s}"


@mcp.tool()
async def stop_app(serial: str, package: str, ctx: Context) -> str:
    """
    Force stop an app on the device.

    Args:
        serial: Device serial number
        package: Package name to stop

    Returns:
        Result message
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Stop the app
        await ctx.info(f"Stopping app {package} on device {serial}...")
        result = await device.stop_app(package)

        return f"✅ {result}"
    except Exception as e:
        logger.exception("Error stopping app: %s", e)
        return f"Error stopping app: {e!s}"


@mcp.tool()
async def clear_app_data(serial: str, package: str, ctx: Context) -> str:
    """
    Clear app data and cache for the specified package.

    Args:
        serial: Device serial number
        package: Package name to clear data for

    Returns:
        Result message
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Clear app data
        await ctx.info(f"Clearing data for app {package} on device {serial}...")
        result = await device.clear_app_data(package)

        if "Successfully" in result:
            return f"✅ {result}"

        return f"❌ {result}"
    except Exception as e:
        logger.exception("Error clearing app data: %s", e)
        return f"Error clearing app data: {e!s}"


@mcp.tool()
async def list_packages(serial: str, ctx: Context, include_system_apps: bool = False) -> str:
    """
    List installed packages on the device.

    Args:
        serial: Device serial number
        include_system_apps: Whether to include system apps in the list

    Returns:
        Formatted list of installed packages
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Get app list
        await ctx.info(f"Retrieving installed packages from device {serial}...")
        app_list = await device.get_app_list(include_system_apps)

        if not app_list:
            return "No packages found on the device."

        result = "# Installed Packages\n\n"
        result += "| Package Name | APK Path |\n"
        result += "|-------------|----------|\n"

        for app in app_list:
            package_name = app.get("package", "Unknown")
            apk_path = app.get("path", "Unknown")
            result += f"| `{package_name}` | `{apk_path}` |\n"

        return result
    except Exception as e:
        logger.exception("Error listing packages: %s", e)
        return f"Error listing packages: {e!s}"

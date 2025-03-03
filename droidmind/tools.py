"""
DroidMind Tools - MCP tools for controlling Android devices.

This module provides MCP tools for controlling Android devices via ADB.

Note: Tools in this module catch broad exceptions (Exception) intentionally.
Since these functions are exposed as MCP tools to external clients,
we want to catch all possible errors and return them as formatted messages
rather than letting exceptions propagate and potentially crash the server.
This is a deliberate design choice for better user experience and stability.
"""

import logging
import os
import re

from mcp.server.fastmcp import Context, Image

from droidmind.context import mcp
from droidmind.devices import DeviceManager

logger = logging.getLogger("droidmind")


@mcp.tool()
async def devicelist(ctx: Context) -> str:
    """
    List all connected Android devices.

    Returns:
        A formatted list of connected devices with their basic information.
    """
    try:
        devices = await DeviceManager.list_devices()

        if not devices:
            return "No devices connected. Use the connect_device tool to connect to a device."

        # Format the device information
        result = f"# Connected Android Devices ({len(devices)})\n\n"

        for i, device in enumerate(devices, 1):
            model = await device.model
            android_version = await device.android_version
            result += f"""## Device {i}: {model}
- **Serial**: `{device.serial}`
- **Android Version**: {android_version}
"""

        return result
    except Exception as e:
        logger.exception("Error listing devices: %s", e)
        return f"Error listing devices: {e!s}"


@mcp.tool()
async def device_properties(serial: str, ctx: Context) -> str:
    """
    Get detailed properties of a specific device.

    Args:
        serial: Device serial number

    Returns:
        Formatted device properties as text
    """
    try:
        device = await DeviceManager.get_device(serial)

        if not device:
            return f"Device {serial} not found or not connected."

        properties = await device.get_properties()

        # Format the properties
        result = f"# Device Properties for {serial}\n\n"

        # Add formatted sections for important properties
        model = await device.model
        brand = await device.brand
        android_version = await device.android_version
        sdk_level = await device.sdk_level
        build_number = await device.build_number

        result += f"**Model**: {model}\n"
        result += f"**Brand**: {brand}\n"
        result += f"**Android Version**: {android_version}\n"
        result += f"**SDK Level**: {sdk_level}\n"
        result += f"**Build Number**: {build_number}\n\n"

        # Add all properties in a code block
        result += "## All Properties\n\n```properties\n"

        # Sort properties for consistent output
        for key in sorted(properties.keys()):
            value = properties[key]
            result += f"{key}={value}\n"

        result += "```"
        return result
    except Exception as e:
        logger.exception("Error retrieving device properties: %s", e)
        return f"Error retrieving device properties: {e!s}"


@mcp.tool()
async def device_logcat(serial: str, ctx: Context) -> str:
    """
    Get recent logcat output from a device.

    Args:
        serial: Device serial number

    Returns:
        Recent logcat entries
    """
    try:
        device = await DeviceManager.get_device(serial)

        if not device:
            return f"Device {serial} not found or not connected."

        logcat = await device.get_logcat()

        if not logcat:
            return f"No logcat output available for device {serial}."

        return f"# Logcat for device {serial}\n\n```\n{logcat}\n```"
    except Exception as e:
        logger.exception("Error retrieving logcat: %s", e)
        return f"Error retrieving logcat: {e!s}"


@mcp.tool()
async def list_directory(serial: str, path: str, ctx: Context) -> str:
    """
    List contents of a directory on the device.

    Args:
        serial: Device serial number
        path: Directory path to list

    Returns:
        Directory listing
    """
    try:
        device = await DeviceManager.get_device(serial)

        if not device:
            return f"Device {serial} not found or not connected."

        # Run the ls command
        output = await device.list_directory(path)

        if not output or "No such file or directory" in output:
            return f"Directory {path} not found on device {serial}."

        return f"# Directory listing for {path} on device {serial}\n\n```\n{output}\n```"
    except Exception as e:
        logger.exception("Error listing directory: %s", e)
        return f"Error listing directory: {e!s}"


@mcp.tool()
async def connect_device(ctx: Context, ip_address: str, port: int = 5555) -> str:
    """
    Connect to an Android device over TCP/IP.

    Args:
        ip_address: The IP address of the device to connect to
        port: The port to connect to (default: 5555)

    Returns:
        A message indicating success or failure
    """
    # Validate IP address format
    ip_pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
    if not re.match(ip_pattern, ip_address):
        return "❌ Invalid IP address format. Please use the format: xxx.xxx.xxx.xxx"

    # Validate port range
    if port < 1 or port > 65535:
        return "❌ Invalid port number. Port must be between 1 and 65535."

    try:
        # Attempt to connect to the device
        device = await DeviceManager.connect(ip_address, port)

        if device:
            model = await device.model
            android_version = await device.android_version

            return f"""
# ✨ Device Connected Successfully! ✨

- **Device**: {model}
- **Connection**: {ip_address}:{port}
- **Android Version**: {android_version}

The device is now available for commands and operations.
            """

        return f"❌ Failed to connect to device at {ip_address}:{port}"
    except Exception as e:
        logger.exception("Error connecting to device: %s", e)
        return f"❌ Error connecting to device: {e!s}"


@mcp.tool()
async def disconnect_device(serial: str, ctx: Context) -> str:
    """
    Disconnect from an Android device.

    Args:
        serial: Device serial number

    Returns:
        Disconnection result message
    """
    try:
        await ctx.info(f"Disconnecting from device {serial}...")
        success = await DeviceManager.disconnect(serial)

        if success:
            return f"Successfully disconnected from device {serial}"

        return f"Device {serial} was not connected"
    except Exception as e:
        logger.exception("Error disconnecting from device: %s", e)
        return f"Error disconnecting from device: {e!s}"


@mcp.tool()
async def shell_command(serial: str, command: str, ctx: Context) -> str:
    """
    Run a shell command on the device.

    Args:
        serial: Device serial number
        command: Shell command to run

    Returns:
        Command output
    """
    try:
        device = await DeviceManager.get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Run the shell command
        result = await device.run_shell(command)

        # Format the output
        if not result.strip():
            return f"Command executed on device {serial} (no output)"

        return f"# Command Output from {serial}\n\n```\n{result}\n```"
    except Exception as e:
        logger.exception("Error executing shell command: %s", e)
        return f"Error executing shell command: {e!s}"


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

        device = await DeviceManager.get_device(serial)

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
async def reboot_device(serial: str, ctx: Context, mode: str = "normal") -> str:
    """
    Reboot the device.

    Args:
        serial: Device serial number
        mode: Reboot mode - "normal", "recovery", or "bootloader"

    Returns:
        Reboot result message
    """
    valid_modes = ["normal", "recovery", "bootloader"]
    if mode not in valid_modes:
        return f"Invalid reboot mode: {mode}. Must be one of: {', '.join(valid_modes)}"

    try:
        device = await DeviceManager.get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Reboot the device
        await ctx.info(f"Rebooting device {serial} in {mode} mode...")
        await device.reboot(mode)

        return f"Device {serial} is rebooting in {mode} mode"
    except Exception as e:
        logger.exception("Error rebooting device: %s", e)
        return f"Error rebooting device: {e!s}"


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
        device = await DeviceManager.get_device(serial)
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

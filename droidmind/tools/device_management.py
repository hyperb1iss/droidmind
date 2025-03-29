"""
Device Management Tools - MCP tools for managing Android device connections.

This module provides MCP tools for listing, connecting to, disconnecting from,
and rebooting Android devices, as well as retrieving device information.
"""

import re

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger


@mcp.tool()
async def list_devices(ctx: Context) -> str:
    """
    List all connected Android devices.

    Returns:
        A formatted list of connected devices with their basic information.
    """
    try:
        devices = await get_device_manager().list_devices()

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
        logger.exception("Error in list_devices tool: %s", e)
        return f"❌ Error listing devices: {e}\n\nCheck logs for detailed traceback."


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
        device = await get_device_manager().connect(ip_address, port)

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
        success = await get_device_manager().disconnect(serial)

        if success:
            return f"Successfully disconnected from device {serial}"

        return f"Device {serial} was not connected"
    except Exception as e:
        logger.exception("Error disconnecting from device: %s", e)
        return f"Error disconnecting from device: {e!s}"


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
        device = await get_device_manager().get_device(serial)

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
async def device_logcat(
    serial: str, ctx: Context, lines: int = 1000, filter_expr: str = "", max_size: int | None = 100000
) -> str:
    """
    Get recent logcat output from a device.

    Args:
        serial: Device serial number
        lines: Number of recent lines to fetch (default: 1000, max recommended: 20000)
               Higher values may impact performance and context window limits.
        filter_expr: Optional filter expression (e.g., "ActivityManager:I *:S")
                     Use to focus on specific tags or priority levels
        max_size: Maximum output size in characters (default: 100000)
                  Set to None for unlimited (not recommended)

    Returns:
        Recent logcat entries
    """
    device = await get_device_manager().get_device(serial)
    if device is None:
        return f"Error: Device {serial} not found."

    try:
        # Build logcat command
        cmd = ["logcat", "-d", "-v", "threadtime"]

        # Add line limit if specified
        if lines > 0:
            cmd.extend(["-t", str(lines)])

        # Add filter if specified
        if filter_expr:
            cmd.extend(filter_expr.split())

        # Join command parts
        logcat_cmd = " ".join(cmd)

        # Get logcat output
        output = await device.run_shell(logcat_cmd)

        # Truncate if needed
        if max_size and len(output) > max_size:
            output = output[:max_size] + "\n... [Output truncated due to size limit]"

        # Format the output
        result = ["# Device Logcat Output 📱\n"]
        result.append(f"## Last {lines} Lines")
        if filter_expr:
            result.append(f"\nFilter: `{filter_expr}`")
        result.append("\n```log")
        result.append(output)
        result.append("```")

        return "\n".join(result)

    except Exception as e:
        logger.exception("Error getting logcat output")
        return f"Error retrieving logcat output: {e!s}"


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
        device = await get_device_manager().get_device(serial)

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

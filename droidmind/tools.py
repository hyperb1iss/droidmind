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
import tempfile

import aiofiles
from mcp.server.fastmcp import Context, Image

from droidmind.adb.service import get_adb, get_temp_dir
from droidmind.mcp_instance import mcp

logger = logging.getLogger("droidmind")


@mcp.tool()
async def devicelist(ctx: Context) -> str:
    """
    List all connected Android devices.

    Returns:
        A formatted list of connected devices with their basic information.
    """
    # Get ADB directly from the service instead of context
    adb = await get_adb()

    try:
        # Get the list of devices
        devices = await adb.get_devices()

        if not devices:
            return "No devices connected. Use the connect_device tool to connect to a device."

        # Format the device information
        result = f"# Connected Android Devices ({len(devices)})\n\n"

        for i, device in enumerate(devices, 1):
            serial = device.get("serial", "Unknown")
            model = device.get("model", "Unknown model")
            android_version = device.get("android_version", "Unknown version")

            result += f"""## Device {i}: {model}
- **Serial**: `{serial}`
- **Android Version**: {android_version}
"""

        return result

    except Exception as e:
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
    # Get ADB directly from the service instead of context
    adb = await get_adb()

    try:
        properties = await adb.get_device_properties(serial)
    except Exception as e:
        return f"Error retrieving device properties: {e!s}"

    if not properties:
        return f"No properties found for device {serial}."

    # Format the properties
    result = f"# Device Properties for {serial}\n\n"

    # Add formatted sections for important properties
    model = properties.get("ro.product.model", "Unknown")
    brand = properties.get("ro.product.brand", "Unknown")
    android_version = properties.get("ro.build.version.release", "Unknown")
    sdk_level = properties.get("ro.build.version.sdk", "Unknown")
    build_number = properties.get("ro.build.display.id", "Unknown")

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


@mcp.tool()
async def device_logcat(serial: str, ctx: Context) -> str:
    """
    Get recent logcat output from a device.

    Args:
        serial: Device serial number

    Returns:
        Recent logcat entries
    """
    # Get ADB directly from the service instead of context
    adb = await get_adb()

    try:
        # Get the logcat output (limited to last 200 lines for performance)
        logcat = await adb.shell(serial, "logcat -d -v time -T 200")

        if not logcat:
            return f"No logcat output available for device {serial}."

        return f"# Logcat for device {serial}\n\n```\n{logcat}\n```"

    except Exception as e:
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
    # Get ADB directly from the service instead of context
    adb = await get_adb()

    try:
        # Run the ls command
        output = await adb.shell(serial, f"ls -la {path}")

        if not output or "No such file or directory" in output:
            return f"Directory {path} not found on device {serial}."

        return f"# Directory listing for {path} on device {serial}\n\n```\n{output}\n```"

    except Exception as e:
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
        return "❌ Invalid IP address format. Please provide a valid IPv4 address."

    # Validate port range
    if port < 1 or port > 65535:
        return "❌ Invalid port number. Port must be between 1 and 65535."

    # Get ADB directly from the service
    adb = await get_adb()

    try:
        # Attempt to connect to the device
        result = await adb.connect_device_tcp(ip_address, port)

        if isinstance(result, str) and ":" in result:
            # Get device info for a more helpful response
            devices = await adb.get_devices()
            for device in devices:
                if ip_address in device.get("serial", ""):
                    model = device.get("model", "Unknown model")
                    android_version = device.get("android_version", "Unknown version")
                    return f"""
# ✨ Device Connected Successfully! ✨

- **Device**: {model}
- **Connection**: {ip_address}:{port}
- **Android Version**: {android_version}

The device is now available for commands and operations.
                    """

            # If we couldn't get detailed device info
            return f"✅ Successfully connected to device at {ip_address}:{port}"
        return f"❌ Failed to connect to device at {ip_address}:{port}: {result}"

    except Exception as e:
        logger.exception("Error connecting to device: %s", e)
        return f"❌ Error connecting to device at {ip_address}:{port}: {e!s}"


@mcp.tool()
async def disconnect_device(serial: str, ctx: Context) -> str:
    """
    Disconnect from an Android device.

    Args:
        serial: Device serial number

    Returns:
        Disconnection result message
    """
    # Get ADB directly from the service instead of context
    adb = await get_adb()

    try:
        # Try to disconnect from the device
        await ctx.info(f"Disconnecting from device {serial}...")
        success = await adb.disconnect_device(serial)

        if success:
            return f"Successfully disconnected from device {serial}"
        return f"Device {serial} was not connected"

    except Exception as e:
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
    # Get ADB directly from the service instead of context
    adb = await get_adb()

    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]

    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."

    try:
        # Run the command
        await ctx.info(f"Running command on {serial}: {command}")
        output = await adb.shell(serial, command)

        return f"Command output from {serial}:\n\n```\n{output}\n```"

    except Exception as e:
        return f"Error running command: {e!s}"


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
    # Get ADB directly from the service instead of context
    adb = await get_adb()

    try:
        await ctx.report_progress(0, 2)
        await ctx.info(f"Installing {apk_path} on device {serial}...")

        # Check if file exists
        if not os.path.exists(apk_path):
            return f"Error: APK file not found at {apk_path}"

        # Push to device first (more reliable than direct install)
        device_apk_path = f"/data/local/tmp/{os.path.basename(apk_path)}"
        await adb.push_file(serial, apk_path, device_apk_path)

        await ctx.report_progress(1, 2)

        # Install from the pushed file
        result = await adb.install_app(serial, device_apk_path, reinstall, grant_permissions)

        # Clean up
        await adb.shell(serial, f"rm {device_apk_path}")

        await ctx.report_progress(2, 2)

        return str(result)  # Ensure we return a string

    except Exception as e:
        return f"Error installing app: {e!s}"


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
    # Get ADB directly from the service instead of context
    adb = await get_adb()

    await ctx.report_progress(0, 1)
    await ctx.info(f"Preparing to reboot device {serial} into {mode} mode...")

    valid_modes = ["normal", "recovery", "bootloader"]
    if mode not in valid_modes:
        return f"Error: Invalid reboot mode. Must be one of: {', '.join(valid_modes)}"

    try:
        # Reboot the device
        await ctx.info(f"Rebooting device {serial} into {mode} mode...")
        result = await adb.reboot_device(serial, mode)
        await ctx.report_progress(1, 1)
        return str(result)  # Ensure we return a string

    except Exception as e:
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
    # Handle URL-encoded serial numbers (convert %3A back to :)
    if "%3A" in serial:
        serial = serial.replace("%3A", ":")

    # Get ADB and temp_dir
    adb = await get_adb()
    temp_dir = await get_temp_dir()

    if temp_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="droidmind_screenshot_")

    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]

    if serial not in device_serials:
        await ctx.error(f"Screenshot requested for disconnected device: {serial}")
        raise ValueError(f"Device {serial} not connected or not found.")

    # Create a temporary file path
    screenshot_filename = f"{serial.replace(':', '_')}_screenshot.png"
    screenshot_path = os.path.join(temp_dir, screenshot_filename)

    try:
        await ctx.info(f"Capturing screenshot from {serial}...")
        await ctx.report_progress(0, 3)

        # Take screenshot on device
        await adb.shell(serial, "screencap -p /sdcard/screenshot.png")
        await ctx.report_progress(1, 3)

        # Pull screenshot to local machine
        await adb.pull_file(serial, "/sdcard/screenshot.png", screenshot_path)
        await ctx.report_progress(2, 3)

        # Clean up on device
        await adb.shell(serial, "rm /sdcard/screenshot.png")

        # Read the image data using aiofiles for async file operations
        async with aiofiles.open(screenshot_path, "rb") as f:
            image_data = await f.read()

        await ctx.info(f"Screenshot captured successfully ({len(image_data)} bytes)")
        await ctx.report_progress(3, 3)

        # Return as MCP Image object
        return Image(data=image_data, format="png")
    except Exception as e:
        await ctx.error(f"Error capturing screenshot from {serial}: {e}")

        # Clean up any temporary files if they exist
        if os.path.exists(screenshot_path):
            try:
                os.unlink(screenshot_path)
            except Exception as cleanup_error:
                await ctx.warning(f"Failed to clean up temporary screenshot file: {cleanup_error}")

        # Re-raise the exception for proper handling
        raise

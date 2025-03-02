"""
DroidMind Tools - Tool implementations for the DroidMind MCP server.

This module provides all the tool implementations for the DroidMind MCP server,
allowing AI assistants to interact with Android devices.
"""

import contextlib
import logging
import os
import re

from mcp.server.fastmcp import Context, Image

from droidmind.adb.service import get_adb
from droidmind.adb.wrapper import ADBWrapper
from droidmind.core import mcp

logger = logging.getLogger("droidmind")


@mcp.tool()
async def devicelist(ctx: Context, random_string: str = "default") -> str:
    """
    List all connected Android devices.

    Returns:
        A formatted list of connected devices with their basic information.
    """
    # Get ADB directly from the service instead of context
    adb = await get_adb()

    devices = await adb.get_devices()

    if not devices:
        return "No devices connected.\n\nUse the `connect_device` tool to connect to a device."

    # Format the output
    result = f"# Connected Android Devices ({len(devices)})\n\n"

    for i, device in enumerate(devices, 1):
        serial = device.get("serial", "Unknown")
        model = device.get("model", "Unknown model")
        android_version = device.get("android_version", "Unknown version")

        result += f"## Device {i}: {model}\n"
        result += f"- **Serial**: `{serial}`\n"
        result += "- **Status**: Connected\n"
        result += f"- **Android Version**: {android_version}\n\n"

    return result


@mcp.tool()
async def device_properties(serial: str, ctx: Context) -> str:
    """
    Get detailed properties of a specific device.

    Args:
        serial: Device serial number

    Returns:
        Formatted device properties as text
    """
    adb: ADBWrapper = ctx.request_context.lifespan_context.adb

    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]

    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."

    # Get all properties
    try:
        properties = await adb.get_device_properties(serial)
    except Exception as e:
        return f"Error retrieving device properties: {e!s}"

    # Extract key information
    android_version = properties.get("ro.build.version.release", "Unknown")
    sdk_version = properties.get("ro.build.version.sdk", "Unknown")
    device_model = properties.get("ro.product.model", "Unknown")
    device_brand = properties.get("ro.product.brand", "Unknown")
    device_name = properties.get("ro.product.name", "Unknown")

    # Format output in a structured way
    result = f"""
# Device Properties for {serial}

## Basic Information
- **Model**: {device_model}
- **Brand**: {device_brand}
- **Name**: {device_name}
- **Android Version**: {android_version}
- **SDK Level**: {sdk_version}

## Build Details
- **Build Number**: {properties.get("ro.build.display.id", "Unknown")}
- **Build Type**: {properties.get("ro.build.type", "Unknown")}
- **Build Time**: {properties.get("ro.build.date", "Unknown")}

## Hardware
- **Chipset**: {properties.get("ro.hardware", "Unknown")}
- **Architecture**: {properties.get("ro.product.cpu.abi", "Unknown")}
- **Screen Density**: {properties.get("ro.sf.lcd_density", "Unknown")}
- **RAM**: {properties.get("ro.product.ram", "Unknown")}
"""

    # Include a selection of other interesting properties
    interesting_props = [
        "ro.product.cpu.abilist",
        "ro.build.fingerprint",
        "ro.build.characteristics",
        "ro.build.tags",
        "ro.product.manufacturer",
        "ro.product.locale",
        "ro.config.bluetooth_max_connected",
        "ro.crypto.state",
        "ro.boot.hardware.revision",
    ]

    result += "\n## Other Properties\n"
    for prop in interesting_props:
        if prop in properties:
            result += f"- **{prop}**: {properties[prop]}\n"

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
    adb: ADBWrapper = ctx.request_context.lifespan_context.adb

    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]

    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."

    try:
        # Get recent logs (limited to last 200 lines for performance)
        logcat = await adb.shell(serial, "logcat -d -v time -T 200")

        if not logcat.strip():
            return "No logcat entries found."

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
    adb: ADBWrapper = ctx.request_context.lifespan_context.adb

    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]

    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."

    try:
        # Sanitize path
        path = path.replace("//", "/")
        if not path.startswith("/"):
            path = f"/{path}"

        # List directory contents
        output = await adb.shell(serial, f"ls -la {path}")

        if "No such file or directory" in output:
            return f"Error: Path {path} does not exist on device {serial}."

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
        result = await adb.connect_device(f"{ip_address}:{port}")

        if "connected" in result.lower():
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
        else:
            return f"❌ Failed to connect to device at {ip_address}:{port}: {result}"

    except Exception as e:
        logger.exception(f"Error connecting to device: {e}")
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
    adb: ADBWrapper = ctx.request_context.lifespan_context.adb

    try:
        # Try to disconnect from the device
        ctx.info(f"Disconnecting from device {serial}...")
        success = await adb.disconnect_device(serial)

        if success:
            return f"Successfully disconnected from device {serial}"
        else:
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
    adb: ADBWrapper = ctx.request_context.lifespan_context.adb

    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]

    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."

    try:
        # Run the command
        ctx.info(f"Running command on {serial}: {command}")
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
    adb: ADBWrapper = ctx.request_context.lifespan_context.adb

    try:
        await ctx.report_progress(0, 2)
        ctx.info(f"Installing {apk_path} on device {serial}...")

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
async def capture_screenshot(serial: str, ctx: Context) -> Image:
    """
    Capture a screenshot from the device.

    Args:
        serial: Device serial number

    Returns:
        Device screenshot as an image
    """
    adb: ADBWrapper = ctx.request_context.lifespan_context.adb
    temp_dir: str = ctx.request_context.lifespan_context.temp_dir

    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]

    if serial not in device_serials:
        raise ValueError(f"Device {serial} not connected or not found.")

    try:
        # Create a temporary file path
        screenshot_path = os.path.join(temp_dir, f"{serial.replace(':', '_')}_screenshot.png")

        # Capture the screenshot
        ctx.info(f"Capturing screenshot from {serial}...")
        await ctx.report_progress(0, 3)

        # Take screenshot on device
        await adb.shell(serial, "screencap -p /sdcard/screenshot.png")
        await ctx.report_progress(1, 3)

        # Pull screenshot to local machine
        await adb.pull_file(serial, "/sdcard/screenshot.png", screenshot_path)
        await ctx.report_progress(2, 3)

        # Clean up on device
        await adb.shell(serial, "rm /sdcard/screenshot.png")
        await ctx.report_progress(3, 3)

        # Read the image and return it
        with open(screenshot_path, "rb") as f:
            image_data = f.read()

        ctx.info(f"Screenshot captured successfully ({len(image_data)} bytes)")

        # Clean up local temp file after reading
        with contextlib.suppress(Exception):
            os.unlink(screenshot_path)

        # Create Image object with format attribute - this is needed for tests
        image = Image(data=image_data)
        image.format = "png"  # Ensure format is set for test compatibility
        return image

    except Exception as e:
        ctx.error(f"Error capturing screenshot: {e!s}")
        raise


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
    adb: ADBWrapper = ctx.request_context.lifespan_context.adb

    await ctx.report_progress(0, 1)
    ctx.info(f"Preparing to reboot device {serial} into {mode} mode...")

    valid_modes = ["normal", "recovery", "bootloader"]
    if mode not in valid_modes:
        return f"Error: Invalid reboot mode. Must be one of: {', '.join(valid_modes)}"

    try:
        # Reboot the device
        ctx.info(f"Rebooting device {serial} into {mode} mode...")
        result = await adb.reboot_device(serial, mode)
        await ctx.report_progress(1, 1)
        return str(result)  # Ensure we return a string

    except Exception as e:
        return f"Error rebooting device: {e!s}"

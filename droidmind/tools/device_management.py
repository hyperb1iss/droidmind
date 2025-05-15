"""
Device Management Tools - MCP tools for managing Android device connections.

This module provides MCP tools for listing, connecting to, disconnecting from,
and rebooting Android devices, as well as retrieving device information.
"""

from enum import Enum
import re

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger


class DeviceAction(str, Enum):
    """Defines the available sub-actions for the 'android-device' tool."""

    LIST_DEVICES = "list_devices"
    CONNECT_DEVICE = "connect_device"
    DISCONNECT_DEVICE = "disconnect_device"
    REBOOT_DEVICE = "reboot_device"
    DEVICE_PROPERTIES = "device_properties"


async def _list_devices_impl(ctx: Context) -> str:
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
        logger.exception("Error in list_devices_impl: %s", e)
        return f"❌ Error listing devices: {e}\n\nCheck logs for detailed traceback."


async def _connect_device_impl(ctx: Context, ip_address: str, port: int = 5555) -> str:
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
        logger.exception("Error connecting to device in _connect_device_impl: %s", e)
        return f"❌ Error connecting to device: {e!s}"


async def _disconnect_device_impl(serial: str, ctx: Context) -> str:
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
        logger.exception("Error disconnecting from device in _disconnect_device_impl: %s", e)
        return f"Error disconnecting from device: {e!s}"


async def _reboot_device_impl(serial: str, ctx: Context, mode: str = "normal") -> str:
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
        logger.exception("Error rebooting device in _reboot_device_impl: %s", e)
        return f"Error rebooting device: {e!s}"


async def _device_properties_impl(serial: str, ctx: Context) -> str:
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
        logger.exception("Error retrieving device properties in _device_properties_impl: %s", e)
        return f"Error retrieving device properties: {e!s}"


@mcp.tool(name="android-device")
async def android_device(
    action: DeviceAction,
    ctx: Context,
    serial: str | None = None,
    ip_address: str | None = None,
    port: int = 5555,
    mode: str = "normal",
) -> str:
    """
    Perform various device management operations on Android devices.

    This single tool consolidates various device-related actions.
    The 'action' parameter determines the operation.

    Args:
        action: The specific device operation to perform.
        ctx: MCP Context for logging and interaction.
        serial (Optional[str]): Device serial number. Required by most actions except connect/list.
        ip_address (Optional[str]): IP address for 'connect_device' action.
        port (Optional[int]): Port for 'connect_device' action (default: 5555).
        mode (Optional[str]): Reboot mode for 'reboot_device' action (default: "normal").

    Returns:
        A string message indicating the result or status of the operation.

    ---
    Available Actions and their specific argument usage:

    1.  `action="list_devices"`
        - No specific arguments required beyond `ctx`.
    2.  `action="connect_device"`
        - Requires: `ip_address`
        - Optional: `port`
    3.  `action="disconnect_device"`
        - Requires: `serial`
    4.  `action="reboot_device"`
        - Requires: `serial`
        - Optional: `mode` (e.g., "normal", "recovery", "bootloader")
    5.  `action="device_properties"`
        - Requires: `serial`
    ---
    """
    try:
        # Argument checks based on action
        if (
            action
            in [
                DeviceAction.DISCONNECT_DEVICE,
                DeviceAction.REBOOT_DEVICE,
                DeviceAction.DEVICE_PROPERTIES,
            ]
            and serial is None
        ):
            return f"❌ Error: 'serial' is required for action '{action.value}'."

        if action == DeviceAction.CONNECT_DEVICE and ip_address is None:
            return "❌ Error: 'ip_address' is required for action 'connect_device'."

        # Dispatch to implementations
        if action == DeviceAction.LIST_DEVICES:
            return await _list_devices_impl(ctx)
        if action == DeviceAction.CONNECT_DEVICE:
            # ip_address is checked not None above
            return await _connect_device_impl(ctx, ip_address, port)  # type: ignore
        if action == DeviceAction.DISCONNECT_DEVICE:
            return await _disconnect_device_impl(serial, ctx)  # type: ignore
        if action == DeviceAction.REBOOT_DEVICE:
            return await _reboot_device_impl(serial, ctx, mode)  # type: ignore
        if action == DeviceAction.DEVICE_PROPERTIES:
            return await _device_properties_impl(serial, ctx)  # type: ignore

        # Should not be reached if DeviceAction enum is comprehensive
        valid_actions = ", ".join([act.value for act in DeviceAction])
        logger.error("Invalid device action '%s' received. Valid actions are: %s", action, valid_actions)
        return f"❌ Error: Unknown device action '{action}'. Valid actions are: {valid_actions}."

    except Exception as e:
        logger.exception("Unexpected error during device operation %s for serial '%s': %s", action, serial, e)
        return f"❌ Error: An unexpected error occurred during '{action.value}': {e!s}"

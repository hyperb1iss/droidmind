"""
UI Automation Tools - MCP tools for interacting with Android device UI.

This module provides MCP tools for touch interaction, input, and UI navigation.
"""

import logging

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager

logger = logging.getLogger("droidmind")


@mcp.tool()
async def tap(serial: str, x: int, y: int, ctx: Context) -> str:
    """
    Tap on the device screen at specific coordinates.

    Args:
        serial: Device serial number
        x: X coordinate to tap
        y: Y coordinate to tap

    Returns:
        The result of the tap operation
    """
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return f"Error: Device {serial} not connected or not found."

        await ctx.info(f"Tapping at coordinates ({x}, {y}) on device {serial}...")
        await device.tap(x, y)
        await ctx.info("Tap operation completed successfully.")
        return f"Successfully tapped at ({x}, {y})"
    except Exception as e:
        logger.exception("Error executing tap operation: %s", e)
        await ctx.error(f"Error executing tap operation: {e!s}")
        return f"Error: {e!s}"


@mcp.tool()
async def swipe(
    serial: str, start_x: int, start_y: int, end_x: int, end_y: int, ctx: Context, duration_ms: int = 300
) -> str:
    """
    Perform a swipe gesture from one point to another on the device screen.

    Args:
        serial: Device serial number
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        ctx: Context
        duration_ms: Duration of the swipe in milliseconds (default: 300)

    Returns:
        The result of the swipe operation
    """
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return f"Error: Device {serial} not connected or not found."

        await ctx.info(
            f"Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y}) "
            f"with duration {duration_ms}ms on device {serial}..."
        )
        await device.swipe(start_x, start_y, end_x, end_y, duration_ms)
        await ctx.info("Swipe operation completed successfully.")
        return f"Successfully swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})"
    except Exception as e:
        logger.exception("Error executing swipe operation: %s", e)
        await ctx.error(f"Error executing swipe operation: {e!s}")
        return f"Error: {e!s}"


@mcp.tool()
async def input_text(serial: str, text: str, ctx: Context) -> str:
    """
    Input text on the device.

    Args:
        serial: Device serial number
        text: Text to input (will be typed as if from keyboard)

    Returns:
        The result of the text input operation
    """
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return f"Error: Device {serial} not connected or not found."

        await ctx.info(f"Inputting text on device {serial}...")
        await device.input_text(text)
        await ctx.info("Text input completed successfully.")
        return "Successfully input text on device"
    except Exception as e:
        logger.exception("Error executing text input operation: %s", e)
        await ctx.error(f"Error executing text input operation: {e!s}")
        return f"Error: {e!s}"


@mcp.tool()
async def press_key(serial: str, keycode: int, ctx: Context) -> str:
    """
    Press a key on the device.

    Common keycodes:
    - 3: HOME
    - 4: BACK
    - 24: VOLUME UP
    - 25: VOLUME DOWN
    - 26: POWER
    - 82: MENU

    Args:
        serial: Device serial number
        keycode: Android keycode to press

    Returns:
        The result of the key press operation
    """
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return f"Error: Device {serial} not connected or not found."

        # Map keycode to human-readable name for better logging
        key_names = {
            3: "HOME",
            4: "BACK",
            24: "VOLUME UP",
            25: "VOLUME DOWN",
            26: "POWER",
            82: "MENU",
        }
        key_name = key_names.get(keycode, str(keycode))

        await ctx.info(f"Pressing key {key_name} on device {serial}...")
        await device.press_key(keycode)
        await ctx.info(f"Key press ({key_name}) completed successfully.")
        return f"Successfully pressed key {key_name}"
    except Exception as e:
        logger.exception("Error executing key press operation: %s", e)
        await ctx.error(f"Error executing key press operation: {e!s}")
        return f"Error: {e!s}"


@mcp.tool()
async def start_intent(
    serial: str, package: str, activity: str, ctx: Context, extras: dict[str, str] | None = None
) -> str:
    """
    Start an app activity using an intent.

    Args:
        serial: Device serial number
        package: Package name (e.g., "com.android.settings")
        activity: Activity name (e.g., ".Settings")
        ctx: Context
        extras: Optional intent extras as key-value pairs

    Returns:
        The result of the intent operation
    """
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return f"Error: Device {serial} not connected or not found."

        # Format extras for logging
        extras_display = ""
        if extras:
            extras_display = f" with extras: {extras}"

        await ctx.info(f"Starting activity {package}/{activity}{extras_display} on device {serial}...")
        await device.start_activity(package, activity, extras)
        await ctx.info(f"Activity {package}/{activity} started successfully.")
        return f"Successfully started {package}/{activity}"
    except Exception as e:
        logger.exception("Error starting activity: %s", e)
        await ctx.error(f"Error starting activity: {e!s}")
        return f"Error: {e!s}"

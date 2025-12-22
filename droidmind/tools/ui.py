"""
UI Automation Tools - MCP tools for interacting with Android device UI.

This module provides MCP tools for touch interaction, input, and UI navigation.
"""

from enum import Enum

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger
from droidmind.tools.intents import start_intent


class UIAction(Enum):
    """Actions available for UI automation."""

    TAP = "tap"
    SWIPE = "swipe"
    INPUT_TEXT = "input_text"
    PRESS_KEY = "press_key"
    START_INTENT = "start_intent"


async def _tap_impl(serial: str, x: int, y: int, ctx: Context) -> str:
    """Implementation for the tap action."""
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


async def _swipe_impl(
    serial: str, start_x: int, start_y: int, end_x: int, end_y: int, ctx: Context, duration_ms: int = 300
) -> str:
    """Implementation for the swipe action."""
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


async def _input_text_impl(serial: str, text: str, ctx: Context) -> str:
    """Implementation for the input_text action."""
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


async def _press_key_impl(serial: str, keycode: int, ctx: Context) -> str:
    """Implementation for the press_key action."""
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


@mcp.tool(name="android-ui")
async def android_ui(  # pylint: disable=too-many-arguments
    ctx: Context,
    serial: str,
    action: UIAction,
    x: int | None = None,
    y: int | None = None,
    start_x: int | None = None,
    start_y: int | None = None,
    end_x: int | None = None,
    end_y: int | None = None,
    duration_ms: int = 300,  # Default for swipe
    text: str | None = None,
    keycode: int | None = None,
    package: str | None = None,
    activity: str | None = None,
    extras: dict[str, str] | None = None,
) -> str:
    """
    Perform various UI interaction operations on an Android device.

    Args:
        ctx: MCP Context.
        serial: Device serial number.
        action: The UI action to perform.
        x: X coordinate (for tap).
        y: Y coordinate (for tap).
        start_x: Starting X coordinate (for swipe).
        start_y: Starting Y coordinate (for swipe).
        end_x: Ending X coordinate (for swipe).
        end_y: Ending Y coordinate (for swipe).
        duration_ms: Duration of the swipe in milliseconds (default: 300).
        text: Text to input (for input_text).
        keycode: Android keycode to press (for press_key).
        package: Package name (for start_intent).
        activity: Activity name (for start_intent).
        extras: Optional intent extras (for start_intent).

    Returns:
        A string message indicating the result of the operation.
    """
    if action == UIAction.TAP:
        if x is None or y is None:
            msg = "Error: 'x' and 'y' coordinates are required for tap action."
            await ctx.error(msg)
            return msg
        return await _tap_impl(serial=serial, x=x, y=y, ctx=ctx)

    if action == UIAction.SWIPE:
        if start_x is None or start_y is None or end_x is None or end_y is None:
            msg = "Error: 'start_x', 'start_y', 'end_x', and 'end_y' are required for swipe action."
            await ctx.error(msg)
            return msg
        # duration_ms has a default, so no explicit None check needed if we pass it through
        return await _swipe_impl(
            serial=serial,
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            ctx=ctx,
            duration_ms=duration_ms,
        )

    if action == UIAction.INPUT_TEXT:
        if text is None:
            msg = "Error: 'text' is required for input_text action."
            await ctx.error(msg)
            return msg
        return await _input_text_impl(serial=serial, text=text, ctx=ctx)

    if action == UIAction.PRESS_KEY:
        if keycode is None:
            msg = "Error: 'keycode' is required for press_key action."
            await ctx.error(msg)
            return msg
        return await _press_key_impl(serial=serial, keycode=keycode, ctx=ctx)

    if action == UIAction.START_INTENT:
        if package is None or activity is None:
            msg = "Error: 'package' and 'activity' are required for start_intent action."
            await ctx.error(msg)
            return msg
        # extras is optional
        device_manager = get_device_manager()
        return await start_intent(
            ctx=ctx,
            serial=serial,
            package=package,
            activity=activity,
            device_manager=device_manager,
            extras=extras,
        )

    # Should not be reached if action is a valid UIAction member
    unhandled_action_msg = f"Error: Unhandled UI action '{action}'."
    logger.error(unhandled_action_msg)
    await ctx.error(unhandled_action_msg)
    return unhandled_action_msg

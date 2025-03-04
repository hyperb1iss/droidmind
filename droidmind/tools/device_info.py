"""
Device Information Tools - MCP tools for retrieving device information.

This module provides MCP tools for retrieving properties and logs from connected Android devices.
"""

import logging

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager

logger = logging.getLogger("droidmind")


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
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Device {serial} not found or not connected."

        # Safety cap to prevent extremely large outputs
        if lines > 100000:
            lines = 100000
            warning = "⚠️ Line limit was capped at 100,000 to prevent excessive output."
        elif lines > 10000:
            warning = "⚠️ Requesting a large number of logcat lines may impact performance and context window limits."
        else:
            warning = ""

        # Get logcat with optional filter
        filter_to_use = filter_expr if filter_expr else None
        logcat = await device.get_logcat(lines, filter_to_use)

        if not logcat:
            return f"No logcat output available for device {serial}."

        # Truncate if needed based on max_size
        if max_size and len(logcat) > max_size:
            logcat_lines: list[str] = logcat.splitlines()
            total_lines = len(logcat_lines)

            # Keep beginning and end, with a notice in the middle
            keep_lines = 200  # Lines to keep from beginning and end
            beginning = "\n".join(logcat_lines[:keep_lines])
            ending = "\n".join(logcat_lines[-keep_lines:])

            omitted = total_lines - (2 * keep_lines)
            middle_notice = (
                f"\n\n... {omitted} lines omitted ({len(logcat) - len(beginning) - len(ending)} chars) ...\n\n"
            )

            logcat = beginning + middle_notice + ending
            truncation_notice = f"\n\n⚠️ Output truncated from {len(logcat) / 1024:.1f}KB to protect context limits"
            logcat += truncation_notice

        # Format the output
        result = f"# Logcat for device {serial}\n\n"

        # Add filter info if present
        if filter_expr:
            result += f"**Filter**: `{filter_expr}`\n\n"

        if warning:
            result += f"{warning}\n\n"

        # Add common filter examples for large outputs
        if len(logcat) > 50000 and not filter_expr:
            result += (
                "**🔍 Pro Tip**: Large output detected. Try these filters to narrow results:\n"
                "- `ActivityManager:I *:S` - Show only ActivityManager info logs\n"
                "- `*:E` - Show only error logs\n"
                "- `System.err:W *:S` - Show only System.err warnings\n\n"
            )

        result += f"```\n{logcat}\n```"
        return result
    except Exception as e:
        logger.exception("Error retrieving logcat: %s", e)
        return f"Error retrieving logcat: {e!s}"

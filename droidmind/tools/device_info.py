"""
Device Information Tools - MCP tools for retrieving device information.

This module provides MCP tools for retrieving properties and logs from connected Android devices.
"""


from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger


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

"""
Shell Tools - MCP tools for executing shell commands on Android devices.

This module provides MCP tools for running shell commands on connected Android devices.
"""

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger
from droidmind.security import RiskLevel, assess_command_risk


@mcp.tool("android-shell")
async def shell_command(
    serial: str, command: str, ctx: Context, max_lines: int | None = 1000, max_size: int | None = 100000
) -> str:
    """
    Run a shell command on the device.

    Args:
        serial: Device serial number
        command: Shell command to run
        max_lines: Maximum lines of output to return (default: 1000)
                  Use positive numbers for first N lines, negative for last N lines
                  Set to None for unlimited (not recommended for large outputs)
        max_size: Maximum output size in characters (default: 100000)
                  Limits total response size regardless of line count

    Returns:
        Command output
    """
    device = await get_device_manager().get_device(serial)
    if device is None:
        return f"Error: Device {serial} not found."

    # Assess command risk level
    risk_level = assess_command_risk(command)

    # Add warning for high-risk commands
    warning = ""
    if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        warning = f"⚠️ WARNING: This command has been assessed as {risk_level.name} risk.\n\n"
        logger.warning("High risk command requested: %s (Risk: %s)", command, risk_level.name)

    try:
        result = await device.run_shell(command, max_lines, max_size)

        # If the result starts with "Error: Command rejected", it means security validation failed
        if result.startswith("Error: Command rejected"):
            return f"{warning}{result}"

        # Format the output to match the expected format in tests
        output = f"# Command Output from {serial}\n\n"
        if warning:
            output += f"{warning}\n\n"

        # Add the command output
        output += f"```\n{result}\n```"

        return output
    except Exception as e:
        logger.exception("Error executing shell command: %s", e)
        return f"Error executing shell command: {e!s}"

"""
Shell Tools - MCP tools for executing shell commands on Android devices.

This module provides MCP tools for running shell commands on connected Android devices.
"""

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger


@mcp.tool()
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
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Generate warning based on output size parameters
        warning = ""
        if (max_lines is None or max_lines <= 0) and (max_size is None or max_size <= 0):
            warning = "⚠️ Running command with unlimited output. This may impact performance and context window limits."
            max_lines = None
            max_size = None
        elif max_lines is not None and max_lines > 10000:
            warning = "⚠️ Requesting a large number of output lines may impact performance."
            # Cap at 100k lines for safety
            if max_lines > 100000:
                max_lines = 100000
                warning = "⚠️ Line limit was capped at 100,000 to prevent excessive output."

        # Check for commands that typically produce large outputs
        large_output_commands = ["dumpsys", "logcat", "cat ", "pm list", "find "]
        if any(cmd in command for cmd in large_output_commands) and not any(
            limiter in command for limiter in ["| head", "| tail", "| grep"]
        ):
            await ctx.info(f"⚠️ Command '{command}' may produce large output - applying automatic limits")

        # Run the shell command with size limits
        result = await device.run_shell(command, max_lines, max_size)

        # Format the output
        if not result.strip():
            return f"Command executed on device {serial} (no output)"

        output = f"# Command Output from {serial}\n\n"
        if warning:
            output += f"{warning}\n\n"

        # Check if output is very large and add a note
        if len(result) > 50000:
            output += (
                f"⚠️ Large output detected ({len(result) / 1024:.1f} KB). Consider using more specific filters.\n\n"
            )

        # Wrap the output in a code block
        output += f"```\n{result}\n```"

        return output
    except Exception as e:
        logger.exception("Error executing shell command: %s", e)
        return f"Error executing shell command: {e!s}"

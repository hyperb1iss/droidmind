"""
Log Tools - MCP tools for retrieving logs from Android devices.

This module provides tools for collecting and analyzing various types of logs
from Android devices, including logcat, ANR traces, crash reports, and battery stats.
"""

from enum import Enum
import os
import re
from typing import Any

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger


class LogAction(str, Enum):
    """Defines the available sub-actions for the 'android-log' tool."""

    GET_DEVICE_LOGCAT = "get_device_logcat"
    GET_APP_LOGS = "get_app_logs"
    GET_ANR_LOGS = "get_anr_logs"
    GET_CRASH_LOGS = "get_crash_logs"
    GET_BATTERY_STATS = "get_battery_stats"


async def _get_filtered_logcat(
    device: Any,
    filter_expr: str,
    lines: int = 1000,
    buffer: str = "main",
    format_type: str = "threadtime",
    max_size: int | None = 100000,
) -> str:
    """
    Helper function to get filtered logcat output in a consistent format.

    Args:
        device: Device instance
        filter_expr: Optional filter expression for logcat
        lines: Number of recent lines to fetch
        buffer: Logcat buffer to use (main, system, crash, etc.)
        format_type: Format for logcat output
        max_size: Maximum output size in characters

    Returns:
        Formatted logcat output
    """
    try:
        # Build logcat command
        cmd = ["logcat", "-d", "-v", format_type]

        # Specify buffer if not main
        if buffer != "main":
            cmd.extend(["-b", buffer])

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

        return output
    except Exception as e:
        logger.exception("Error getting logcat output")
        return f"Error retrieving logcat output: {e!s}"


async def _get_device_logcat_impl(
    serial: str,
    ctx: Context,
    lines: int = 1000,
    filter_expr: str = "",
    buffer: str = "main",
    format_type: str = "threadtime",
    max_size: int | None = 100000,
) -> str:
    """
    Get logcat output from a device with flexible filtering options.

    Args:
        serial: Device serial number
        lines: Number of recent lines to fetch (default: 1000)
               Higher values may impact performance and context window limits.
        filter_expr: Optional filter expression (e.g., "ActivityManager:I *:S")
                     Use to focus on specific tags or priority levels
        buffer: Logcat buffer to use (main, system, crash, radio, events, etc.)
        format_type: Format for logcat output (threadtime, brief, tag, process, etc.)
        max_size: Maximum output size in characters (default: 100000)
                  Set to None for unlimited (not recommended)

    Returns:
        Recent logcat entries in markdown format
    """
    device = await get_device_manager().get_device(serial)
    if device is None:
        return f"Error: Device {serial} not found."

    await ctx.info(f"Retrieving logcat from device {serial} (buffer: {buffer})...")

    try:
        output = await _get_filtered_logcat(device, filter_expr, lines, buffer, format_type, max_size)

        # Format the output
        result = ["# Device Logcat Output 📱\n"]
        result.append(f"## Last {lines} Lines from '{buffer}' Buffer")
        if filter_expr:
            result.append(f"\nFilter: `{filter_expr}`")
        result.append("\n```log")
        result.append(output)
        result.append("```")

        return "\n".join(result)

    except Exception as e:
        logger.exception("Error getting logcat output in _get_device_logcat_impl")
        return f"Error retrieving logcat output: {e!s}"


async def _get_anr_logs_impl(serial: str, ctx: Context) -> str:
    """
    Get Application Not Responding (ANR) traces from a device.

    Args:
        serial: Device serial number

    Returns:
        ANR traces in markdown format
    """
    device = await get_device_manager().get_device(serial)
    if device is None:
        return f"Error: Device {serial} not found."

    await ctx.info(f"Retrieving ANR traces from device {serial}...")

    try:
        # Check if ANR directory exists
        anr_dir = "/data/anr"
        dir_check = await device.run_shell(f"ls {anr_dir}")

        if "No such file or directory" in dir_check:
            return f"No ANR directory found at {anr_dir}. The device may not have any ANR traces."

        # Get list of ANR trace files
        files = await device.run_shell(f"find {anr_dir} -type f -name '*.txt' -o -name 'traces*'")
        file_list = [f.strip() for f in files.splitlines() if f.strip()]

        if not file_list:
            return "No ANR trace files found on the device."

        # Prepare the output
        output = []
        output.append("# Application Not Responding (ANR) Traces\n")

        # Get the most recent traces (up to 3)
        recent_files = await device.run_shell(f"ls -lt {anr_dir} | grep -E 'traces|.txt' | head -3")
        recent_file_list = [
            line.split()[-1] for line in recent_files.splitlines() if "traces" in line or ".txt" in line
        ]

        for i, filename in enumerate(recent_file_list):
            if not filename.startswith(anr_dir):
                filename = os.path.join(anr_dir, filename)

            output.append(f"## ANR Trace #{i + 1}: {os.path.basename(filename)}\n")

            # Get file details
            file_stat = await device.run_shell(f"ls -la {filename}")
            output.append(f"**File Info:** `{file_stat.strip()}`\n")

            # Get the content (first 200 lines should be enough for analysis)
            content = await device.run_shell(f"head -200 {filename}")
            output.append("```\n" + content + "\n```\n")

        # Add summary of other trace files if there are more
        if len(file_list) > len(recent_file_list):
            output.append("\n## Additional ANR Traces\n")
            output.append("There are additional ANR trace files that aren't shown above:\n")
            for file in file_list:
                if os.path.basename(file) not in [os.path.basename(f) for f in recent_file_list]:
                    file_stat = await device.run_shell(f"ls -la {file}")
                    output.append(f"- `{file_stat.strip()}`\n")

        return "\n".join(output)
    except Exception as e:
        logger.exception("Error getting ANR traces in _get_anr_logs_impl")
        return f"Error retrieving ANR traces: {e!s}"


async def _get_crash_logs_impl(serial: str, ctx: Context) -> str:
    """
    Get application crash logs from a device.

    Args:
        serial: Device serial number

    Returns:
        Crash logs in markdown format
    """
    device = await get_device_manager().get_device(serial)
    if device is None:
        return f"Error: Device {serial} not found."

    await ctx.info(f"Retrieving crash logs from device {serial}...")

    try:
        # First check the tombstone directory
        tombstone_dir = "/data/tombstones"
        output = []
        output.append("# Android Application Crash Reports\n")

        # Check tombstones
        output.append("## System Tombstones\n")
        tombstones = await device.run_shell(f"ls -la {tombstone_dir}")

        if "No such file or directory" in tombstones or not tombstones.strip():
            output.append("No tombstone files found.\n")
        else:
            tombstone_files = [
                line.split()[-1]
                for line in tombstones.splitlines()
                if line.strip() and not line.startswith("total") and not line.endswith(".")
            ]

            if not tombstone_files:
                output.append("No tombstone files found.\n")
            else:
                output.append("Recent system crash tombstones:\n")
                # Get most recent 3 tombstones
                recent_tombstones = await device.run_shell(f"ls -lt {tombstone_dir} | head -4")
                recent_files = [
                    line.split()[-1]
                    for line in recent_tombstones.splitlines()
                    if not line.startswith("total") and "tombstone" in line
                ]

                for i, filename in enumerate(recent_files[:3]):
                    filepath = os.path.join(tombstone_dir, filename)
                    output.append(f"### Tombstone #{i + 1}: {filename}\n")

                    # Get header of the tombstone (first 30 lines should give the key info)
                    content = await device.run_shell(f"head -30 {filepath}")
                    output.append("```\n" + content + "\n```\n")

        # Now check for dropbox crashes
        output.append("## Dropbox Crash Reports\n")
        dropbox_dir = "/data/system/dropbox"
        dropbox_files = await device.run_shell(f"ls -la {dropbox_dir} | grep crash")

        if "No such file or directory" in dropbox_files or not dropbox_files.strip():
            output.append("No crash reports found in dropbox.\n")
        else:
            crash_files = [
                line.split()[-1] for line in dropbox_files.splitlines() if line.strip() and "crash" in line.lower()
            ]

            if not crash_files:
                output.append("No crash reports found in dropbox.\n")
            else:
                output.append("Recent crash reports from dropbox:\n")
                # Show 3 most recent crash reports
                for i, filename in enumerate(crash_files[:3]):
                    filepath = os.path.join(dropbox_dir, filename)
                    output.append(f"### Crash Report #{i + 1}: {filename}\n")

                    # Get content of the crash report
                    content = await device.run_shell(f"cat {filepath}")
                    # Trim if it's too long
                    if len(content) > 1500:
                        content = content[:1500] + "...\n[Content truncated]"
                    output.append("```\n" + content + "\n```\n")

        # Add logcat crashes too
        output.append("## Recent Crashes in Logcat\n")
        crash_logs = await _get_filtered_logcat(device, "", 100, "crash", "threadtime")

        if not crash_logs.strip():
            output.append("No crash logs found in the crash buffer.\n")
        else:
            output.append("```\n" + crash_logs + "\n```\n")

        return "\n".join(output)
    except Exception as e:
        logger.exception("Error getting crash logs in _get_crash_logs_impl")
        return f"Error retrieving crash logs: {e!s}"


async def _get_battery_stats_impl(serial: str, ctx: Context) -> str:
    """
    Get battery statistics and history from a device.

    Args:
        serial: Device serial number

    Returns:
        Battery statistics in markdown format
    """
    device = await get_device_manager().get_device(serial)
    if device is None:
        return f"Error: Device {serial} not found."

    await ctx.info(f"Retrieving battery statistics from device {serial}...")

    try:
        output = []
        output.append("# Battery Statistics Report 🔋\n")

        # Get current battery status
        output.append("## Current Battery Status\n")
        battery_status = await device.run_shell("dumpsys battery")
        output.append("```\n" + battery_status + "\n```\n")

        # Extract and highlight key metrics
        level_match = re.search(r"level: (\d+)", battery_status)
        level = level_match.group(1) if level_match else "Unknown"

        temp_match = re.search(r"temperature: (\d+)", battery_status)
        temp: float | None = float(temp_match.group(1)) / 10 if temp_match else None
        temp_str = f"{temp}°C" if temp is not None else "Unknown"

        health_match = re.search(r"health: (\d+)", battery_status)
        health_codes = {
            1: "Unknown",
            2: "Good",
            3: "Overheat",
            4: "Dead",
            5: "Over voltage",
            6: "Unspecified failure",
            7: "Cold",
        }
        health = health_codes.get(int(health_match.group(1)), "Unknown") if health_match else "Unknown"

        output.append("### Key Metrics\n")
        output.append(f"- **Battery Level:** {level}%\n")
        output.append(f"- **Temperature:** {temp_str}\n")
        output.append(f"- **Health:** {health}\n")

        # Get battery history and stats
        output.append("## Battery History and Usage\n")
        battery_history = await device.run_shell("dumpsys batterystats --charged")

        # Process the battery history to extract key information
        history_lines = []
        stats_lines = []
        current_section = None

        for line in battery_history.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("Statistics since last charge"):
                current_section = "stats"
            elif line.startswith("Per-app"):
                current_section = "apps"
            elif line.startswith("Discharge step durations"):
                current_section = "history"

            if current_section == "history" and ("step" in line or "Estimated" in line):
                history_lines.append(line)
            elif (
                current_section == "stats"
                and any(x in line for x in ["Capacity:", "Screen", "Bluetooth", "Wifi", "Cellular"])
            ) or (current_section == "apps" and "Uid" in line and "mAh" in line):
                stats_lines.append(line)

        output.append("### Discharge History\n```\n")
        output.extend(history_lines[:20])  # Show last 20 discharge steps
        output.append("\n```\n")

        output.append("### Power Consumption Details\n```\n")
        output.extend(stats_lines[:30])  # Show top 30 power consumption entries
        output.append("\n```\n")

        return "\n".join(output)

    except Exception as e:
        logger.exception("Error getting battery stats in _get_battery_stats_impl")
        return f"Error retrieving battery statistics: {e!s}"


async def _get_app_logs_impl(serial: str, package: str, ctx: Context, lines: int = 1000) -> str:
    """
    Get logs for a specific app from logcat.

    Args:
        serial: Device serial number
        package: Package name of the app to get logs for
        lines: Number of lines to fetch (default: 1000)

    Returns:
        App logs in markdown format
    """
    device = await get_device_manager().get_device(serial)
    if device is None:
        return f"Error: Device {serial} not found."

    await ctx.info(f"Retrieving logs for app {package} from device {serial}...")

    try:
        # Use pid filter for more targeted results
        process_info = await device.run_shell(f"ps -A | grep {package}")

        filter_expr = ""
        if process_info:
            # Try to extract PID for more precise filtering
            process_lines = process_info.strip().split("\n")
            for line in process_lines:
                parts = line.split()
                if len(parts) >= 2 and package in line:
                    pid = parts[1]  # PID is typically the second column
                    filter_expr = f"--pid={pid}"
                    break

        # If we couldn't get the PID, fallback to grep
        output = ""
        if filter_expr:
            # If we have a PID, use direct filtering
            output = await _get_filtered_logcat(device, filter_expr, lines)
        else:
            # Otherwise, get more lines and grep for the package
            raw_logs = await _get_filtered_logcat(device, "", lines * 2)  # Get more lines to account for filtering
            # Extract relevant logs with grep-like filtering
            log_lines = raw_logs.split("\n")
            filtered_lines = [line for line in log_lines if package in line]
            output = "\n".join(filtered_lines[-lines:])  # Take the most recent matching lines

        if not output.strip():
            # Try a broader search if no logs were found
            raw_logs = await _get_filtered_logcat(device, "", lines * 2)
            simplified_package = package.split(".")[-1]  # Get last part of package name
            log_lines = raw_logs.split("\n")
            filtered_lines = [line for line in log_lines if simplified_package in line]
            output = "\n".join(filtered_lines[-lines:])  # Take the most recent matching lines

        result = [f"# Logs for App '{package}' 📱\n"]
        if not output.strip():
            result.append(f"No logs found for package {package}. The app may not be running or not generating logs.")
        else:
            result.append("## Recent Log Entries\n")
            result.append("```log")
            result.append(output)
            result.append("```")

        return "\n".join(result)

    except Exception as e:
        logger.exception("Error getting logs for app %s in _get_app_logs_impl", package)
        return f"Error retrieving app logs: {e!s}"


@mcp.tool(name="android-log")
async def android_log(
    serial: str,
    action: LogAction,
    ctx: Context,
    package: str | None = None,
    lines: int = 1000,
    filter_expr: str = "",
    buffer: str = "main",
    format_type: str = "threadtime",
    max_size: int | None = 100000,
) -> str:
    """
    Perform various log retrieval operations on an Android device.

    This single tool consolidates various log-related actions.
    The 'action' parameter determines the operation.

    Args:
        serial: Device serial number.
        action: The specific log operation to perform.
        ctx: MCP Context for logging and interaction.
        package (Optional[str]): Package name for `get_app_logs` action.
        lines (int): Number of lines to fetch for logcat actions (default: 1000).
        filter_expr (Optional[str]): Logcat filter expression for `get_device_logcat`.
        buffer (Optional[str]): Logcat buffer for `get_device_logcat` (default: "main").
        format_type (Optional[str]): Logcat output format for `get_device_logcat` (default: "threadtime").
        max_size (Optional[int]): Max output size for `get_device_logcat` (default: 100KB).

    Returns:
        A string message containing the requested logs or status.

    ---
    Available Actions and their specific argument usage:

    1.  `action="get_device_logcat"`
        - Optional: `lines`, `filter_expr`, `buffer`, `format_type`, `max_size`.
    2.  `action="get_app_logs"`
        - Requires: `package`.
        - Optional: `lines`.
    3.  `action="get_anr_logs"`
        - No specific arguments beyond `serial` and `ctx`.
    4.  `action="get_crash_logs"`
        - No specific arguments beyond `serial` and `ctx`.
    5.  `action="get_battery_stats"`
        - No specific arguments beyond `serial` and `ctx`.
    ---
    """
    try:
        if action == LogAction.GET_APP_LOGS and package is None:
            return "❌ Error: 'package' is required for action 'get_app_logs'."

        if action == LogAction.GET_DEVICE_LOGCAT:
            return await _get_device_logcat_impl(serial, ctx, lines, filter_expr, buffer, format_type, max_size)
        if action == LogAction.GET_APP_LOGS:
            return await _get_app_logs_impl(serial, package, ctx, lines)  # type: ignore
        if action == LogAction.GET_ANR_LOGS:
            return await _get_anr_logs_impl(serial, ctx)
        if action == LogAction.GET_CRASH_LOGS:
            return await _get_crash_logs_impl(serial, ctx)
        if action == LogAction.GET_BATTERY_STATS:
            return await _get_battery_stats_impl(serial, ctx)

        valid_actions = ", ".join([la.value for la in LogAction])
        logger.error("Invalid log action '%s' received. Valid actions are: %s.", action, valid_actions)
        return f"❌ Error: Unknown log action '{action}'. Valid actions are: {valid_actions}."

    except Exception as e:
        logger.exception("Unexpected error during log operation %s for serial '%s': %s", action, serial, e)
        return f"❌ Error: An unexpected error occurred during '{action.value}': {e!s}"

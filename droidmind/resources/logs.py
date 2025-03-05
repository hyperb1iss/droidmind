"""Log resources for DroidMind."""

import os
import re

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger

# Re-export get_device_manager for test patching
__all__ = ["get_device_manager"]


@mcp.resource("logs://{serial}/anr")
async def device_anr_logs(serial: str) -> str:
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
        logger.exception("Error getting ANR traces")
        return f"Error retrieving ANR traces: {e!s}"


@mcp.resource("logs://{serial}/crashes")
async def device_crash_logs(serial: str) -> str:
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
        crash_logs = await device.run_shell("logcat -d -b crash -v threadtime -t 100")

        if not crash_logs.strip():
            output.append("No crash logs found in the crash buffer.\n")
        else:
            output.append("```\n" + crash_logs + "\n```\n")

        return "\n".join(output)
    except Exception as e:
        logger.exception("Error getting crash logs")
        return f"Error retrieving crash logs: {e!s}"


@mcp.resource("logs://{serial}/battery")
async def device_battery_stats(serial: str) -> str:
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
            elif ((current_section == "stats" and
                   any(x in line for x in ["Capacity:", "Screen", "Bluetooth", "Wifi", "Cellular"])) or
                  (current_section == "apps" and "Uid" in line and "mAh" in line)):
                stats_lines.append(line)

        output.append("### Discharge History\n```\n")
        output.extend(history_lines[:20])  # Show last 20 discharge steps
        output.append("\n```\n")

        output.append("### Power Consumption Details\n```\n")
        output.extend(stats_lines[:30])  # Show top 30 power consumption entries
        output.append("\n```\n")

        return "\n".join(output)

    except Exception as e:
        logger.exception("Error getting battery stats")
        return f"Error retrieving battery statistics: {e!s}"

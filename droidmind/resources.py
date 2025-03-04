"""
DroidMind Resources - Resource implementations for the DroidMind MCP server.

This module provides resource implementations for the DroidMind MCP server,
allowing AI assistants to access device data in a structured way.

Resources are like read-only endpoints that expose data to the AI assistant.
"""

import logging
import os
import re

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.filesystem import DirectoryResource, FileResource

logger = logging.getLogger("droidmind")


# MCP Resource Implementations
@mcp.resource("devices://list")
async def get_devices_list() -> str:
    """
    Get a list of all connected devices as a resource.

    Returns:
        A markdown-formatted list of connected devices
    """
    devices = await get_device_manager().list_devices()

    if not devices:
        return "No devices connected."

    result = "# Connected Devices\n\n"
    for i, device in enumerate(devices, 1):
        model = await device.model
        android_version = await device.android_version
        result += f"## Device {i}: {model}\n"
        result += f"- **Serial**: `{device.serial}`\n"
        result += f"- **Android Version**: {android_version}\n"

    return result


@mcp.resource("fs://{serial}/list/{path}")
async def list_directory(serial: str, path: str) -> str:
    """
    List the contents of a directory on a device.

    Args:
        serial: Device serial number
        path: Directory path to list

    Returns:
        A markdown-formatted directory listing
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not found or not connected."

        # Use the DirectoryResource to list the contents
        dir_resource = DirectoryResource(path, device)
        resources = await dir_resource.list_contents()

        # Format the result in a friendly way
        result = f"# 📁 Directory: {path}\n\n"

        if not resources:
            result += "💔 *No files or directories found*\n"
            return result

        # Add file/folder counts
        n_files = sum(1 for r in resources if isinstance(r, FileResource))
        n_dirs = sum(1 for r in resources if isinstance(r, DirectoryResource))
        result += f"**{n_files}** files, **{n_dirs}** directories\n\n"

        # Create markdown table
        result += "| Type | Name | Size | Permissions |\n"
        result += "|------|------|------|-------------|\n"

        # Sort by directories first, then by name
        resources.sort(key=lambda x: (not isinstance(x, DirectoryResource), x.name))

        for resource in resources:
            if isinstance(resource, DirectoryResource):
                icon = "📁"
                size = "-"
                perms = resource.metadata.get("permissions", "") if hasattr(resource, "metadata") else ""
            else:
                icon = "📄"
                size = resource.metadata.get("size", "0") if hasattr(resource, "metadata") else "0"
                try:
                    size_int = int(size)
                    size = (
                        f"{size_int:,} bytes"
                        if size_int < 1024
                        else f"{size_int / 1024:.1f} KB"
                        if size_int < 1024 * 1024
                        else f"{size_int / (1024 * 1024):.1f} MB"
                    )
                except (ValueError, TypeError):
                    pass
                perms = resource.metadata.get("permissions", "") if hasattr(resource, "metadata") else ""

            result += f"| {icon} | {resource.name} | {size} | {perms} |\n"

        return result

    except Exception as e:
        logger.exception("Error in list_directory resource: %s", e)
        return f"Error listing directory: {e}"


@mcp.resource("fs://{serial}/read/{path}")
async def read_file(serial: str, path: str) -> str:
    """
    Read the contents of a file on a device.

    Args:
        serial: Device serial number
        path: File path to read

    Returns:
        A markdown-formatted file content view
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not found or not connected."

        # Check if the path exists and is a file
        check_cmd = f"[ -f '{path}' ] && echo 'isfile' || ([ -e '{path}' ] && echo 'exists' || echo 'notfound')"
        check_result = await device.run_shell(check_cmd)

        if "notfound" in check_result:
            return f"Error: Path {path} not found on device {serial}."

        if "isfile" not in check_result:
            return f"Error: Path {path} is not a regular file on device {serial}."

        # Check file size
        size_cmd = f"wc -c '{path}'"
        size_result = await device.run_shell(size_cmd)

        try:
            size = int(size_result.split()[0])
            max_size = 100000  # 100KB limit for resources

            if size > max_size:
                return f"""
# ⚠️ File Too Large

The file {path} is {size / 1024:.1f} KB, which exceeds the resource size limit.

Use the `read_file` tool or `pull_file` tool to access this file instead.
"""
        except (ValueError, IndexError):
            # If we can't determine the size, proceed with caution
            pass

        # Read the file
        content = await device.read_file(path)

        # Format the output
        result = f"# File: {path}\n\n"

        # Get file info
        info_cmd = f"ls -la '{path}'"
        info_result = await device.run_shell(info_cmd)
        info_line = info_result.strip().split("\n")[0] if info_result else ""

        if info_line:
            result += f"```\n{info_line}\n```\n\n"

        # Determine if we should use syntax highlighting
        file_ext = os.path.splitext(path)[1].lower()
        code_extensions = {
            ".py": "python",
            ".java": "java",
            ".kt": "kotlin",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "cpp",
            ".xml": "xml",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".sh": "bash",
            ".txt": "",
            ".md": "markdown",
        }

        lang = code_extensions.get(file_ext, "")
        result += f"## Contents\n\n```{lang}\n{content}\n```"

        return result

    except Exception as e:
        logger.exception("Error in read_file resource: %s", e)
        return f"Error reading file: {e}"


@mcp.resource("fs://{serial}/stats/{path}")
# pylint: disable=too-many-locals
async def file_stats(serial: str, path: str) -> str:
    """
    Get detailed information about a file or directory on a device.

    Args:
        serial: Device serial number
        path: Path to the file or directory

    Returns:
        A markdown-formatted file/directory statistics report
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not found or not connected."

        # Check if the path exists
        check_cmd = f"[ -e '{path}' ] && echo 'exists' || echo 'notfound'"
        check_result = await device.run_shell(check_cmd)

        if "notfound" in check_result:
            return f"Error: Path {path} not found on device {serial}."

        # Determine if it's a file or directory
        is_dir_cmd = f"[ -d '{path}' ] && echo 'directory' || echo 'file'"
        is_dir_result = await device.run_shell(is_dir_cmd)
        is_directory = "directory" in is_dir_result

        # Get basic stats
        stat_cmd = f"ls -la '{path}'"
        stat_result = await device.run_shell(stat_cmd)

        # Format the output
        result = f"# {'Directory' if is_directory else 'File'} Statistics: {path}\n\n"

        # Extract basic info from ls output
        if stat_result:
            lines = stat_result.strip().split("\n")
            if lines:
                # For files, the first line contains the info
                # For directories, we need to find the entry for the directory itself
                info_line = ""

                if is_directory:
                    # Find line for .
                    for line in lines:
                        if re.search(r"\s+\.$", line):
                            info_line = line
                            break
                else:
                    info_line = lines[0]

                if info_line:
                    # Parse the line
                    match = re.match(
                        r"^([drwx-]+)\s+(\d+)\s+(\w+)\s+(\w+)\s+(\d+)\s+(\w+\s+\d+\s+[\w:]+)\s+(.+)$", info_line
                    )
                    if match:
                        perms, links, owner, group, size, date, name = match.groups()

                        # Format size
                        try:
                            size_num = int(size)
                            if size_num >= 1024 * 1024:
                                size_str = f"{size_num / (1024 * 1024):.1f} MB"
                            elif size_num >= 1024:
                                size_str = f"{size_num / 1024:.1f} KB"
                            else:
                                size_str = f"{size_num} B"
                        except ValueError:
                            size_str = size

                        result += f"- **Type**: {'Directory' if is_directory else 'File'}\n"
                        result += f"- **Name**: {os.path.basename(path)}\n"
                        result += f"- **Size**: {size_str}\n"
                        result += f"- **Owner**: {owner}:{group}\n"
                        result += f"- **Permissions**: {perms}\n"
                        result += f"- **Modified**: {date}\n"

        # For directories, get additional information
        if is_directory:
            # Count files and subdirectories
            count_cmd = f"find '{path}' -type f | wc -l"
            file_count = await device.run_shell(count_cmd)

            count_cmd = f"find '{path}' -type d | wc -l"
            dir_count = await device.run_shell(count_cmd)

            try:
                file_count_num = int(file_count.strip())
                dir_count_num = int(dir_count.strip()) - 1  # Subtract 1 to exclude the directory itself

                result += f"- **Files**: {file_count_num}\n"
                result += f"- **Subdirectories**: {dir_count_num}\n"
            except ValueError:
                pass

        return result

    except Exception as e:
        logger.exception("Error in file_stats resource: %s", e)
        return f"Error getting file statistics: {e}"

"""
File Operations Tools - MCP tools for managing files on Android devices.

This module provides a unified MCP tool for listing, uploading, downloading, and manipulating
files on connected Android devices using sub-actions.
"""

from enum import Enum
import os
import re
from typing import TYPE_CHECKING, NamedTuple

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.filesystem import DirectoryResource, format_file_size
from droidmind.log import logger

if TYPE_CHECKING:
    from droidmind.devices import Device


class FileAction(str, Enum):
    """Defines the available sub-commands for the 'android-file' tool."""

    LIST_DIRECTORY = "list_directory"
    PUSH_FILE = "push_file"
    PULL_FILE = "pull_file"
    DELETE_FILE = "delete_file"
    CREATE_DIRECTORY = "create_directory"
    FILE_EXISTS = "file_exists"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    FILE_STATS = "file_stats"


class FileInfo(NamedTuple):
    """Information about a file or directory."""

    perms: str
    links: str
    owner: str
    group: str
    size: str
    date: str
    name: str


async def _parse_ls_output(device: "Device", path: str, is_directory: bool) -> FileInfo | None:
    """Parse ls -la output to get file information."""
    stat_cmd = f"ls -la '{path}'"
    stat_result = await device.run_shell(stat_cmd)

    if not stat_result:
        return None

    lines = stat_result.strip().split("\n")
    if not lines:
        return None

    # For files, first line contains info
    # For directories, find the entry for the directory itself
    info_line = ""
    if is_directory:
        for line in lines:
            if re.search(r"\s+\.$", line):
                info_line = line
                break
    else:
        info_line = lines[0]

    if not info_line:
        return None

    # Parse the line
    match = re.match(r"^([drwx-]+)\s+(\d+)\s+(\w+)\s+(\w+)\s+(\d+)\s+(\w+\s+\d+\s+[\w:]+)\s+(.+)$", info_line)
    if not match:
        return None

    return FileInfo(*match.groups())


def _format_size(size: str) -> str:
    """Format file size into human readable format."""
    try:
        size_num = int(size)
        if size_num >= 1024 * 1024:
            return f"{size_num / (1024 * 1024):.1f} MB"
        if size_num >= 1024:
            return f"{size_num / 1024:.1f} KB"
        return f"{size_num} B"
    except ValueError:
        return size


async def _get_directory_counts(device: "Device", path: str) -> tuple[int | None, int | None]:
    """Get file and directory counts for a directory."""
    try:
        # Count files
        count_cmd = f"find '{path}' -type f | wc -l"
        file_count = await device.run_shell(count_cmd)
        file_count_num = int(file_count.strip())

        # Count directories
        count_cmd = f"find '{path}' -type d | wc -l"
        dir_count = await device.run_shell(count_cmd)
        dir_count_num = int(dir_count.strip()) - 1  # Subtract 1 to exclude the directory itself

        return file_count_num, dir_count_num
    except (ValueError, Exception) as e:
        logger.warning("Error getting directory counts: %s", e)
        return None, None


async def _list_directory_impl(device: "Device", path: str, ctx: Context) -> str:
    """Implementation for listing directory contents."""
    if ctx:
        await ctx.info(f"Listing directory {path}...")

    dir_resource = DirectoryResource(path, device)
    contents = await dir_resource.list_contents()

    formatted_output = f"# 📁 Directory: {path}\n\n"
    files = [item for item in contents if item.__class__.__name__ == "FileResource"]
    dirs = [item for item in contents if item.__class__.__name__ == "DirectoryResource"]

    formatted_output += f"**{len(files)} files, {len(dirs)} directories**\n\n"

    if dirs:
        formatted_output += "## Directories\n\n"
        for dir_item in sorted(dirs, key=lambda x: x.name):
            formatted_output += f"📁 `{dir_item.name}`\n"
        formatted_output += "\n"

    if files:
        formatted_output += "## Files\n\n"
        for file_item in sorted(files, key=lambda x: x.name):
            size_str = file_item.to_dict().get("size", "unknown")
            formatted_output += f"📄 `{file_item.name}` ({size_str})\n"

    return formatted_output


async def _push_file_impl(device: "Device", local_path: str, device_path: str, ctx: Context) -> str:
    """Implementation for uploading a file."""
    if not os.path.exists(local_path):
        return f"❌ Error: Local file {local_path} does not exist."

    size = os.path.getsize(local_path)
    size_str = format_file_size(size)

    if ctx:
        await ctx.info(f"Pushing file {os.path.basename(local_path)} ({size_str}) to {device_path}...")

    result = await device.push_file(local_path, device_path)
    return f"""
# ✅ File Uploaded Successfully

The file `{os.path.basename(local_path)}` ({size_str}) has been uploaded to `{device_path}` on device {device.serial}.

**Details**: {result}
"""


async def _pull_file_impl(device: "Device", device_path: str, local_path: str, ctx: Context) -> str:
    """Implementation for downloading a file."""
    local_dir = os.path.dirname(local_path)
    if local_dir and not os.path.exists(local_dir):
        os.makedirs(local_dir, exist_ok=True)

    if ctx:
        await ctx.info(f"Pulling file {device_path} to {local_path}...")

    result = await device.pull_file(device_path, local_path)

    size_str = "unknown size"
    if os.path.exists(local_path):
        size = os.path.getsize(local_path)
        size_str = format_file_size(size)

    return f"""
# ✅ File Downloaded Successfully

The file `{os.path.basename(device_path)}` ({size_str}) has been downloaded from device {device.serial}
to `{local_path}`.

**Details**: {result}
"""


async def _delete_file_impl(device: "Device", path: str, ctx: Context) -> str:
    """Implementation for deleting a file or directory."""
    if ctx:
        await ctx.info(f"Deleting {path}...")
    return await device.delete_file(path)


async def _create_directory_impl(device: "Device", path: str, ctx: Context) -> str:
    """Implementation for creating a directory."""
    if ctx:
        await ctx.info(f"Creating directory {path}...")
    return await device.create_directory(path)


async def _file_exists_impl(
    device: "Device", path: str, ctx: Context
) -> bool:  # ctx is not used here but kept for consistency
    """Implementation for checking if a file exists."""
    return await device.file_exists(path)


async def _read_file_impl(device: "Device", device_path: str, ctx: Context, max_size: int) -> str:
    """Implementation for reading file contents."""
    file_check = await device.run_shell(f"[ -f '{device_path}' ] && echo 'exists' || echo 'not found'")
    if "not found" in file_check:
        return f"❌ Error: File {device_path} not found on device {device.serial}"

    size_check = await device.run_shell(f"wc -c '{device_path}' 2>/dev/null || echo 'unknown'")
    size_str = "unknown size"

    if "unknown" not in size_check:
        try:
            file_size = int(size_check.split()[0])
            if file_size > max_size:
                return f"""
# ⚠️ File Too Large

The file `{device_path}` is {file_size / 1024:.1f} KB, which exceeds the maximum size limit of {max_size / 1024:.1f} KB.

Use `action="pull_file"` to download this file to your local machine instead.
"""
            size_str = f"{file_size / 1024:.1f} KB" if file_size >= 1024 else f"{file_size} bytes"
        except (ValueError, IndexError):
            pass

    if ctx:
        await ctx.info(f"Reading file {device_path} ({size_str})...")

    content = await device.read_file(device_path, max_size)
    code_extensions = [".py", ".java", ".kt", ".c", ".cpp", ".h", ".xml", ".json", ".yaml", ".sh", ".txt", ".md"]
    file_ext = os.path.splitext(device_path)[1].lower()
    result_md = f"# File Contents: {device_path}\n\n"

    if file_ext in code_extensions:
        lang_map = {
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
            ".md": "markdown",
        }
        lang = lang_map.get(file_ext, "")
        result_md += f"```{lang}\n{content}\n```"
    else:
        result_md += f"```\n{content}\n```"
    return result_md


async def _write_file_impl(device: "Device", device_path: str, content: str, ctx: Context) -> str:
    """Implementation for writing text content to a file."""
    parent_dir = os.path.dirname(device_path)
    if parent_dir:
        dir_check = await device.run_shell(f"[ -d '{parent_dir}' ] && echo 'exists' || echo 'not found'")
        if "not found" in dir_check:
            if ctx:
                await ctx.info(f"Creating parent directory {parent_dir}...")
            await device.create_directory(parent_dir)

    content_size = len(content.encode("utf-8"))
    size_str = f"{content_size / 1024:.1f} KB" if content_size >= 1024 else f"{content_size} bytes"

    if ctx:
        await ctx.info(f"Writing {size_str} to {device_path}...")
    await device.write_file(device_path, content)

    return f"""
# ✨ File Written Successfully

- **Path**: {device_path}
- **Size**: {size_str}
- **Device**: {device.serial}

The content has been saved to the file.
"""


async def _file_stats_impl(device: "Device", path: str, ctx: Context) -> str:
    """Implementation for getting file statistics."""
    if ctx:
        await ctx.info(f"Getting statistics for {path}...")

    check_cmd = f"[ -e '{path}' ] && echo 'exists' || echo 'notfound'"
    check_result = await device.run_shell(check_cmd)
    if "notfound" in check_result:
        return f"Error: Path {path} not found on device {device.serial}."

    is_dir_cmd = f"[ -d '{path}' ] && echo 'directory' || echo 'file'"
    is_dir_result = await device.run_shell(is_dir_cmd)
    is_directory = "directory" in is_dir_result

    result = [f"# {'Directory' if is_directory else 'File'} Statistics: {path}\n"]
    file_info = await _parse_ls_output(device, path, is_directory)

    if file_info:
        size_str = _format_size(file_info.size)
        result.extend(
            [
                f"- **Type**: {'Directory' if is_directory else 'File'}\n",
                f"- **Name**: {os.path.basename(path)}\n",
                f"- **Size**: {size_str}\n",
                f"- **Owner**: {file_info.owner}:{file_info.group}\n",
                f"- **Permissions**: {file_info.perms}\n",
                f"- **Modified**: {file_info.date}\n",
            ]
        )

    if is_directory:
        file_count, dir_count = await _get_directory_counts(device, path)
        if file_count is not None:
            result.append(f"- **Files**: {file_count}\n")
        if dir_count is not None:
            result.append(f"- **Subdirectories**: {dir_count}\n")

    return "".join(result)


@mcp.tool(name="android-file")
async def file_operations(
    serial: str,
    action: FileAction,
    ctx: Context,
    path: str | None = None,
    local_path: str | None = None,
    device_path: str | None = None,
    content: str | None = None,
    max_size: int | None = 100000,  # Default from original read_file
) -> str | bool:
    """
    Perform file and directory operations on an Android device.

    This single tool consolidates various file system actions.
    The 'action' parameter determines the operation.

    Args:
        serial: Device serial number.
        action: The specific file operation to perform. See available actions below.
        ctx: MCP Context for logging and interaction.
        path (Optional[str]): General path argument on the device.
                               Used by: list_directory, delete_file, create_directory, file_exists, file_stats.
                               Can also be used by read_file and write_file as an alternative to 'device_path'.
        local_path (Optional[str]): Path on the DroidMind server machine.
                                    Used by: push_file (source), pull_file (destination).
        device_path (Optional[str]): Path on the Android device.
                                     Used by: push_file (destination), pull_file (source), read_file (source),
                                     write_file (destination).
                                     If 'path' is also provided for read/write, 'device_path' takes precedence.
        content (Optional[str]): Text content to write.
                                 Used by: write_file.
        max_size (Optional[int]): Maximum file size in bytes for read_file (default: 100KB).
                                  Used by: read_file.

    Returns:
        Union[str, bool]: A string message indicating the result or status for most actions.
                          Returns a boolean for the 'file_exists' action.

    ---
    Available Actions and their specific argument usage:

    1.  `action="list_directory"`: Lists contents of a directory.
        - Requires: `path` (directory path on device).
        - Returns: Formatted string of directory contents.

    2.  `action="push_file"`: Uploads a file from the local server to the device.
        - Requires: `local_path` (source on server), `device_path` (destination on device).
        - Returns: String message confirming upload.

    3.  `action="pull_file"`: Downloads a file from the device to the local server.
        - Requires: `device_path` (source on device), `local_path` (destination on server).
        - Returns: String message confirming download.

    4.  `action="delete_file"`: Deletes a file or directory from the device.
        - Requires: `path` (path to delete on device).
        - Returns: String message confirming deletion.

    5.  `action="create_directory"`: Creates a directory on the device.
        - Requires: `path` (directory path to create on device).
        - Returns: String message confirming creation.

    6.  `action="file_exists"`: Checks if a file or directory exists on the device.
        - Requires: `path` (path to check on device).
        - Returns: `True` if exists, `False` otherwise.

    7.  `action="read_file"`: Reads the contents of a file from the device.
        - Requires: `device_path` (or `path`) for the file on device.
        - Optional: `max_size` (defaults to 100KB).
        - Returns: String containing file contents or error message.

    8.  `action="write_file"`: Writes text content to a file on the device.
        - Requires: `device_path` (or `path`) for the file on device, `content` (text to write).
        - Returns: String message confirming write.

    9.  `action="file_stats"`: Gets detailed statistics for a file or directory.
        - Requires: `path` (path on device).
        - Returns: Markdown-formatted string of file/directory statistics.
    ---
    """
    # Declare here so it's always bound for exception logging
    _effective_device_path: str | None = None
    try:
        # Initialize _effective_device_path early for robust logging
        _effective_device_path = device_path if device_path is not None else path

        device = await get_device_manager().get_device(serial)
        if not device:
            if action == FileAction.FILE_EXISTS:
                logger.warning("Device %s not found for file_exists check.", serial)
                return False
            return f"❌ Error: Device {serial} not found or not connected."

        # Use device_path if provided, otherwise fall back to path for relevant actions
        # _effective_device_path assignment moved above

        if action == FileAction.LIST_DIRECTORY:
            if path is None:
                return "❌ Error: 'path' is required for list_directory."
            return await _list_directory_impl(device, path, ctx)
        if action == FileAction.PUSH_FILE:
            if local_path is None or device_path is None:
                return "❌ Error: 'local_path' and 'device_path' are required for push_file."
            return await _push_file_impl(device, local_path, device_path, ctx)
        if action == FileAction.PULL_FILE:
            if device_path is None or local_path is None:
                return "❌ Error: 'device_path' and 'local_path' are required for pull_file."
            return await _pull_file_impl(device, device_path, local_path, ctx)
        if action == FileAction.DELETE_FILE:
            if path is None:
                return "❌ Error: 'path' is required for delete_file."
            return await _delete_file_impl(device, path, ctx)
        if action == FileAction.CREATE_DIRECTORY:
            if path is None:
                return "❌ Error: 'path' is required for create_directory."
            return await _create_directory_impl(device, path, ctx)
        if action == FileAction.FILE_EXISTS:
            if path is None:
                return "❌ Error: 'path' is required for file_exists."
            return await _file_exists_impl(device, path, ctx)
        if action == FileAction.READ_FILE:
            if _effective_device_path is None:
                return "❌ Error: 'device_path' or 'path' is required for read_file."
            return await _read_file_impl(device, _effective_device_path, ctx, max_size or 100000)
        if action == FileAction.WRITE_FILE:
            if _effective_device_path is None or content is None:
                return "❌ Error: ('device_path' or 'path') and 'content' are required for write_file."
            return await _write_file_impl(device, _effective_device_path, content, ctx)
        if action == FileAction.FILE_STATS:
            if path is None:
                return "❌ Error: 'path' is required for file_stats."
            return await _file_stats_impl(device, path, ctx)

        # Default case for invalid actions
        valid_actions = ", ".join([act.value for act in FileAction])
        logger.error("Invalid file action '%s' received. Valid actions are: %s", action, valid_actions)
        return f"❌ Error: Unknown file action '{action}'. Valid actions are: {valid_actions}."

    except ValueError as ve:
        logger.warning("ValueError during file operation %s for device %s: %s", action, serial, ve)
        if action == FileAction.FILE_EXISTS:
            return False
        return f"❌ Error: {ve}"
    except Exception as e:
        # Log with a fallback for _effective_device_path if necessary
        log_path_info = _effective_device_path if _effective_device_path is not None else "[path not determinable]"
        logger.exception(
            "Unexpected error during file operation %s on %s with path/device_path '%s': %s",
            action,
            serial,
            log_path_info,
            e,
        )
        if action == FileAction.FILE_EXISTS:
            return False
        return f"❌ Error: An unexpected error occurred: {e!s}"

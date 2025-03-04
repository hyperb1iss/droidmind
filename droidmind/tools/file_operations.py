"""
File Operations Tools - MCP tools for managing files on Android devices.

This module provides MCP tools for listing, uploading, downloading, and manipulating
files on connected Android devices.
"""

import logging
import os

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.filesystem import DirectoryResource, format_file_size

logger = logging.getLogger("droidmind")


@mcp.tool()
async def list_directory(serial: str, path: str, ctx: Context) -> str:
    """
    List contents of a directory on the device.

    Args:
        serial: Device serial number
        path: Directory path to list

    Returns:
        Directory listing
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            return f"Error: Device {serial} not found"

        # Log progress if ctx is available
        if ctx:
            await ctx.info(f"Listing directory {path}...")

        # Use DirectoryResource to get structured directory contents
        dir_resource = DirectoryResource(path, device)
        contents = await dir_resource.list_contents()

        # Format the output
        formatted_output = f"# 📁 Directory: {path}\n\n"

        # Count files and directories
        files = [item for item in contents if item.__class__.__name__ == "FileResource"]
        dirs = [item for item in contents if item.__class__.__name__ == "DirectoryResource"]

        formatted_output += f"**{len(files)} files, {len(dirs)} directories**\n\n"

        # List directories first
        if dirs:
            formatted_output += "## Directories\n\n"
            for dir_item in sorted(dirs, key=lambda x: x.name):
                formatted_output += f"📁 `{dir_item.name}`\n"
            formatted_output += "\n"

        # Then list files
        if files:
            formatted_output += "## Files\n\n"
            for file_item in sorted(files, key=lambda x: x.name):
                size_str = file_item.to_dict().get("size", "unknown")
                formatted_output += f"📄 `{file_item.name}` ({size_str})\n"

        return formatted_output
    except Exception as e:
        logger.exception("Error listing directory: %s", e)
        return f"Error listing directory: {e!s}"


@mcp.tool()
async def push_file(serial: str, local_path: str, device_path: str, ctx: Context) -> str:
    """
    Upload a file to the device.

    Args:
        serial: Device serial number
        local_path: Path to the local file
        device_path: Destination path on the device

    Returns:
        Upload result message
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            raise ValueError(f"Device {serial} not found")

        # Check if the local file exists
        if not os.path.exists(local_path):
            return f"❌ Error: Local file {local_path} does not exist."

        # Get file size for progress reporting
        size = os.path.getsize(local_path)
        size_str = format_file_size(size)

        # Log progress if ctx is available
        if ctx:
            await ctx.info(f"Pushing file {os.path.basename(local_path)} ({size_str}) to {device_path}...")

        # Push the file
        result = await device.push_file(local_path, device_path)

        # Format the result
        return f"""
# ✅ File Uploaded Successfully

The file `{os.path.basename(local_path)}` ({size_str}) has been uploaded to `{device_path}` on device {serial}.

**Details**: {result}
"""

    except ValueError:
        # Re-raise ValueError to ensure it propagates to the caller for testing
        raise
    except Exception as e:
        logger.exception("Error pushing file: %s", e)
        return f"❌ Error pushing file: {e}"


@mcp.tool()
async def pull_file(serial: str, device_path: str, local_path: str, ctx: Context) -> str:
    """
    Download a file from the device to the local machine.

    Args:
        serial: Device serial number
        device_path: Path to the file on the device
        local_path: Destination path on the local machine

    Returns:
        Download result message
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            raise ValueError(f"Device {serial} not found")

        # Check if the directory exists
        local_dir = os.path.dirname(local_path)
        if local_dir and not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        # Log progress if ctx is available
        if ctx:
            await ctx.info(f"Pulling file {device_path} to {local_path}...")

        # Pull the file
        result = await device.pull_file(device_path, local_path)

        # Get file size for reporting
        if os.path.exists(local_path):
            size = os.path.getsize(local_path)
            size_str = format_file_size(size)
        else:
            size_str = "unknown size"

        # Format the result
        return f"""
# ✅ File Downloaded Successfully

The file `{os.path.basename(device_path)}` ({size_str}) has been downloaded from device {serial} to `{local_path}`.

**Details**: {result}
"""

    except Exception as e:
        logger.exception("Error pulling file: %s", e)
        return f"❌ Error pulling file: {e}"


@mcp.tool()
async def delete_file(serial: str, path: str, ctx: Context) -> str:
    """
    Delete a file or directory from the device.

    Args:
        serial: Device serial number
        path: Path to the file or directory to delete

    Returns:
        Deletion result message
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            raise ValueError(f"Device {serial} not found")

        # Log progress if ctx is available
        if ctx:
            await ctx.info(f"Deleting {path}...")

        # Delete the file
        return await device.delete_file(path)

    except Exception as e:
        logger.exception("Error deleting file: %s", e)
        return f"❌ Error deleting file: {e}"


@mcp.tool()
async def create_directory(serial: str, path: str, ctx: Context) -> str:
    """
    Create a directory on the device.

    Args:
        serial: Device serial number
        path: Path to the directory to create

    Returns:
        Result message
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            raise ValueError(f"Device {serial} not found")

        # Log progress if ctx is available
        if ctx:
            await ctx.info(f"Creating directory {path}...")

        # Create the directory
        return await device.create_directory(path)

    except Exception as e:
        logger.exception("Error creating directory: %s", e)
        return f"❌ Error creating directory: {e}"


@mcp.tool()
async def file_exists(serial: str, path: str, ctx: Context) -> bool:
    """
    Check if a file exists on the device.

    Args:
        serial: Device serial number
        path: Path to the file on the device

    Returns:
        True if the file exists, False otherwise
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            raise ValueError(f"Device {serial} not found")

        # Check if the file exists
        return await device.file_exists(path)

    except Exception as e:
        logger.exception("Error checking if file exists: %s", e)
        return False


@mcp.tool()
async def read_file(serial: str, device_path: str, ctx: Context, max_size: int = 100000) -> str:
    """
    Read the contents of a file on the device.

    Args:
        serial: Device serial number
        device_path: Path to the file on device
        max_size: Maximum file size to read in bytes (default: 100KB)
                  Files larger than this will return an error message instead

    Returns:
        File contents as text or error message
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            return f"❌ Error: Device {serial} not connected or not found."

        # Check file existence
        file_check = await device.run_shell(f"[ -f '{device_path}' ] && echo 'exists' || echo 'not found'")
        if "not found" in file_check:
            return f"❌ Error: File {device_path} not found on device {serial}"

        # Check file size
        size_check = await device.run_shell(f"wc -c '{device_path}' 2>/dev/null || echo 'unknown'")
        size_str = "unknown size"

        if "unknown" not in size_check:
            try:
                file_size = int(size_check.split()[0])
                if file_size > max_size:
                    return f"""
# ⚠️ File Too Large

The file `{device_path}` is {file_size / 1024:.1f} KB, which exceeds the maximum size limit of {max_size / 1024:.1f} KB.

Use `pull_file` to download this file to your local machine instead.
"""
                size_str = f"{file_size / 1024:.1f} KB" if file_size >= 1024 else f"{file_size} bytes"
            except (ValueError, IndexError):
                # Continue with reading if we can't parse the size
                pass

        # Log progress if ctx is available
        if ctx:
            await ctx.info(f"Reading file {device_path} ({size_str})...")

        # Read the file
        content = await device.read_file(device_path, max_size)

        # Determine if we should show the content in a code block based on the file extension
        code_extensions = [".py", ".java", ".kt", ".c", ".cpp", ".h", ".xml", ".json", ".yaml", ".sh", ".txt", ".md"]
        file_ext = os.path.splitext(device_path)[1].lower()

        result = f"# File Contents: {device_path}\n\n"

        if file_ext in code_extensions:
            # Try to guess the language for syntax highlighting
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
            result += f"```{lang}\n{content}\n```"
        else:
            # For binary or unknown files, just use a plain code block
            result += f"```\n{content}\n```"

        return result

    except Exception as e:
        logger.exception("Error reading file: %s", e)
        return f"❌ Error reading file: {e!s}"


@mcp.tool()
async def write_file(serial: str, device_path: str, content: str, ctx: Context) -> str:
    """
    Write text content to a file on the device.

    Args:
        serial: Device serial number
        device_path: Path to the file on device
        content: Text content to write to the file

    Returns:
        Writing result message
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            return f"❌ Error: Device {serial} not connected or not found."

        # Check if the parent directory exists
        parent_dir = os.path.dirname(device_path)
        if parent_dir:
            dir_check = await device.run_shell(f"[ -d '{parent_dir}' ] && echo 'exists' || echo 'not found'")
            if "not found" in dir_check:
                # Create parent directory
                await ctx.info(f"Creating parent directory {parent_dir}...")
                await device.create_directory(parent_dir)

        # Write to the file
        content_size = len(content.encode("utf-8"))
        size_str = f"{content_size / 1024:.1f} KB" if content_size >= 1024 else f"{content_size} bytes"

        await ctx.info(f"Writing {size_str} to {device_path}...")
        await device.write_file(device_path, content)

        return f"""
# ✨ File Written Successfully

- **Path**: {device_path}
- **Size**: {size_str}
- **Device**: {serial}

The content has been saved to the file.
"""
    except Exception as e:
        logger.exception("Error writing file: %s", e)
        return f"❌ Error writing file: {e!s}"

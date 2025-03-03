"""
Device abstractions for Android device management.

This module provides high-level abstractions for interacting with Android devices
through ADB. It defines two primary classes:

1. Device: Represents a single Android device and provides methods for
   interacting with it.
2. DeviceManager: Manages device discovery and connection.
"""

import contextlib
import logging
import os
import re
import tempfile

import aiofiles

from droidmind.adb import ADBWrapper

logger = logging.getLogger("droidmind")


# pylint: disable=too-many-public-methods
class Device:
    """High-level representation of an Android device.

    This class encapsulates device-specific operations and properties
    to provide a more convenient API for interacting with Android devices.
    """

    def __init__(self, serial: str, *, adb: ADBWrapper) -> None:
        """Initialize a Device instance.

        Args:
            serial: The device serial number or connection string (e.g., "ip:port")
            adb: Optional ADBWrapper instance to use directly
        """
        self._serial = serial
        self._adb = adb

        self._properties_cache: dict[str, str] = {}

    @property
    def serial(self) -> str:
        """Get the device serial number."""
        return self._serial

    async def get_properties(self) -> dict[str, str]:
        """Get all device properties.

        Returns:
            Dictionary of device properties
        """
        if not self._properties_cache:
            self._properties_cache = await self._adb.get_device_properties(self._serial)
        return self._properties_cache

    async def get_property(self, name: str) -> str:
        """Get a specific device property.

        Args:
            name: Property name

        Returns:
            Property value or empty string if not found
        """
        properties = await self.get_properties()
        return properties.get(name, "")

    @property
    async def model(self) -> str:
        """Get the device model."""
        props = await self.get_properties()
        return props.get("ro.product.model", "Unknown")

    @property
    async def brand(self) -> str:
        """Get the device brand."""
        props = await self.get_properties()
        return props.get("ro.product.brand", "Unknown")

    @property
    async def android_version(self) -> str:
        """Get the Android version."""
        props = await self.get_properties()
        return props.get("ro.build.version.release", "Unknown")

    @property
    async def sdk_level(self) -> str:
        """Get the SDK level."""
        props = await self.get_properties()
        return props.get("ro.build.version.sdk", "Unknown")

    @property
    async def build_number(self) -> str:
        """Get the build number."""
        props = await self.get_properties()
        return props.get("ro.build.display.id", "Unknown")

    async def get_logcat(self, lines: int = 1000, filter_expr: str | None = None) -> str:
        """Get the most recent lines from logcat.

        Args:
            lines: Number of lines to retrieve (default: 1000)
            filter_expr: Optional filter expression (e.g., "ActivityManager:I *:S")

        Returns:
            Recent logcat output
        """
        cmd = "logcat -d"

        # Apply line limit
        if lines > 0:
            cmd += f" -t {lines}"

        # Apply filter if provided
        if filter_expr and filter_expr.strip():
            # Sanitize filter expression to prevent command injection
            safe_filter = re.sub(r"[;&|<>$]", "", filter_expr)
            cmd += f" {safe_filter}"

        # Get raw logcat
        output = await self._adb.shell(self._serial, cmd)

        # If the output is extremely large, summarize by log level
        if len(output) > 50000:
            # Still return the full output, but add a summary at the beginning
            log_levels = {
                "V": 0,  # Verbose
                "D": 0,  # Debug
                "I": 0,  # Info
                "W": 0,  # Warning
                "E": 0,  # Error
                "F": 0,  # Fatal
            }

            # Count occurrences of each log level
            for line in output.splitlines():
                for level in log_levels:
                    if f"/{level} " in line:
                        log_levels[level] += 1
                        break

            # Create a summary
            total_lines = sum(log_levels.values())
            summary_lines = [
                "## Logcat Summary",
                f"Total lines: {total_lines}",
                "",
                "| Level | Count | Percentage |",
                "|-------|-------|------------|",
            ]

            for level, count in log_levels.items():
                level_name = {"V": "Verbose", "D": "Debug", "I": "Info", "W": "Warning", "E": "Error", "F": "Fatal"}[
                    level
                ]

                percentage = (count / total_lines * 100) if total_lines > 0 else 0
                summary_lines.append(f"| {level_name} | {count} | {percentage:.1f}% |")

            summary_lines.extend(
                [
                    "",
                    "To reduce output size, try filtering with a specific tag or level:",
                    'Example: `device_logcat(serial, filter_expr="ActivityManager:I *:S")`',
                    "",
                    "## Full Logcat Output",
                    "",
                ]
            )

            # Add summary to beginning of output
            output = "\n".join(summary_lines) + "\n" + output

        return output

    async def list_directory(self, path: str) -> str:
        """List the contents of a directory on the device.

        Args:
            path: Directory path to list

        Returns:
            Directory listing
        """
        return await self._adb.shell(self._serial, f"ls -la {path}")

    async def run_shell(self, command: str, max_lines: int | None = 1000, max_size: int | None = 100000) -> str:
        """Run a shell command on the device.

        Args:
            command: Shell command to run
            max_lines: Maximum number of output lines to return
                      Use positive numbers for first N lines, negative for last N lines
                      Set to None for unlimited (not recommended for large outputs)
            max_size: Maximum output size in characters (default: 100000)
                      Limits total response size regardless of line count

        Returns:
            Command output with optional truncation summary
        """
        # Handle special case where max_lines or max_size is 0 or negative
        if max_lines is not None and max_lines <= 0:
            max_lines = None
        if max_size is not None and max_size <= 0:
            max_size = None

        # Check if the command is likely to produce large output
        large_output_patterns = [
            r"\bcat\s+",  # cat command
            r"\bgrep\s+.+\s+-r",  # recursive grep
            r"\bfind\s+.+",  # find commands
            r"\bls\s+-[RalL]",  # recursive ls or with many options
            r"\bdumpsys\b",  # dumpsys commands
            r"\bpm\s+list\b",  # package list
        ]

        is_large_output_likely = any(re.search(pattern, command) for pattern in large_output_patterns)

        # Add automatic paging for commands likely to produce large output
        if is_large_output_likely and not command.endswith(("| head", "| tail", "| grep", "| wc")):
            # Default to showing beginning of output for likely large commands
            if max_lines is None or max_lines > 500:
                max_lines = 500

        # Execute the command with appropriate line limiting if specified
        if max_lines is None:
            output = await self._adb.shell(self._serial, command)
        else:
            # For positive max_lines, use head to get first N lines
            # For negative max_lines, use tail to get last N lines
            if max_lines > 0:
                piped_command = f"{command} | head -n {max_lines}"
            else:
                piped_command = f"{command} | tail -n {abs(max_lines)}"

            output = await self._adb.shell(self._serial, piped_command)

        # Limit total output size if needed
        if max_size and len(output) > max_size:
            output_lines = output.splitlines()
            total_lines = len(output_lines)

            if total_lines <= 10:
                # If we have very few lines but huge content (like a binary dump)
                # Just truncate with a message
                output = output[:max_size] + f"\n\n... Output truncated! Total size: {len(output)} characters."
            else:
                # Calculate how many lines to keep from beginning and end
                keep_lines = min(max_lines or total_lines, total_lines)
                keep_from_start = keep_lines // 2
                keep_from_end = keep_lines - keep_from_start

                truncated_output = "\n".join(output_lines[:keep_from_start])
                truncated_output += f"\n\n... {total_lines - keep_from_start - keep_from_end} lines omitted ...\n\n"
                truncated_output += "\n".join(output_lines[-keep_from_end:])

                # Add summary info
                truncated_output += f"\n\n[Output truncated: {len(output)} chars, {total_lines} lines]"
                output = truncated_output

        # Add warning for large outputs that were truncated
        original_line_count = output.count("\n") + 1
        if original_line_count >= (max_lines or 1000) or (max_size and len(output) >= max_size):
            # Calculate size info for summary
            size_in_kb = len(output) / 1024
            if size_in_kb < 1:
                size_info = f"{len(output)} bytes"
            else:
                size_info = f"{size_in_kb:.1f} KB"

            # Add a separator and summary line
            if not output.endswith("\n"):
                output += "\n"
            output += f"\n[Command output truncated: {original_line_count} lines, {size_info}]"

        return output

    async def reboot(self, mode: str = "normal") -> str:
        """Reboot the device.

        Args:
            mode: Reboot mode - "normal", "recovery", or "bootloader"

        Returns:
            Command output
        """
        return await self._adb.reboot_device(self._serial, mode)

    async def take_screenshot(self) -> bytes:
        """Take a screenshot of the device.

        Returns:
            Screenshot data as bytes
        """
        # Create a temporary file for the screenshot
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
            screenshot_path = temp.name

        try:
            # Take screenshot on device and save to /sdcard/
            await self._adb.shell(self._serial, "screencap -p /sdcard/screenshot.png")

            # Pull the file from the device
            await self._adb.pull_file(self._serial, "/sdcard/screenshot.png", screenshot_path)

            # Clean up the file on the device
            await self._adb.shell(self._serial, "rm /sdcard/screenshot.png")

            # Read the screenshot file
            async with aiofiles.open(screenshot_path, "rb") as f:
                screenshot_data = await f.read()

            # Clean up the temporary file
            try:
                os.unlink(screenshot_path)
            except OSError:
                logger.warning("Failed to remove temporary screenshot file: %s", screenshot_path)

            return screenshot_data

        except Exception as e:
            logger.exception("Error capturing screenshot: %s", e)
            # Clean up in case of error
            with contextlib.suppress(OSError):
                os.unlink(screenshot_path)
            raise

    async def install_app(self, apk_path: str, reinstall: bool = False, grant_permissions: bool = True) -> str:
        """Install an APK on the device.

        Args:
            apk_path: Path to the APK file
            reinstall: Whether to reinstall if app exists
            grant_permissions: Whether to grant all requested permissions

        Returns:
            Installation result
        """
        return await self._adb.install_app(self._serial, apk_path, reinstall, grant_permissions)

    async def push_file(self, local_path: str, device_path: str) -> str:
        """Push a file to the device.

        Args:
            local_path: Path to the local file
            device_path: Destination path on the device

        Returns:
            Result message
        """
        return await self._adb.push_file(self._serial, local_path, device_path)

    async def pull_file(self, device_path: str, local_path: str) -> str:
        """Pull a file from the device.

        Args:
            device_path: Path to the file on the device
            local_path: Destination path on the local machine

        Returns:
            Result message
        """
        return await self._adb.pull_file(self._serial, device_path, local_path)

    async def delete_file(self, device_path: str) -> str:
        """Delete a file or directory on the device.

        Args:
            device_path: Path to the file or directory on the device

        Returns:
            Result message
        """
        # For directories, use rm -rf, for files use rm
        # First check if it's a directory
        result = await self._adb.shell(self._serial, f"[ -d '{device_path}' ] && echo 'directory' || echo 'file'")

        if result.strip() == "directory":
            cmd = f"rm -rf '{device_path}'"
        else:
            cmd = f"rm '{device_path}'"

        await self._adb.shell(self._serial, cmd)
        return f"Successfully deleted {device_path}"

    async def create_directory(self, device_path: str) -> str:
        """Create a directory on the device.

        Args:
            device_path: Path to the directory to create

        Returns:
            Result message
        """
        # Use mkdir -p to create parent directories if needed
        await self._adb.shell(self._serial, f"mkdir -p '{device_path}'")
        return f"Successfully created directory {device_path}"

    async def file_exists(self, device_path: str) -> bool:
        """Check if a file exists on the device.

        Args:
            device_path: Path to the file on the device

        Returns:
            True if the file exists, False otherwise
        """
        # Use test -e to check if file exists, return exit code
        result = await self._adb.shell(self._serial, f"[ -e '{device_path}' ] && echo 0 || echo 1")
        # Convert to boolean (0 = exists, 1 = does not exist)
        return result.strip() == "0"

    async def read_file(self, device_path: str, max_size: int = 100000) -> str:
        """Read a file from the device.

        Args:
            device_path: Path to the file on the device
            max_size: Maximum file size to read in bytes

        Returns:
            File content as string
        """
        # Check file size first
        size_check = await self._adb.shell(self._serial, f"wc -c '{device_path}'")

        try:
            size = int(size_check.split()[0])
        except (ValueError, IndexError):
            # If we can't get size, assume it's within limits
            size = 0

        if size > max_size > 0:
            return (
                f"File is too large ({size} bytes) to read entirely. "
                f"Max size is {max_size} bytes. Use pull_file instead."
            )

        # Read the file
        return await self._adb.shell(self._serial, f"cat '{device_path}'")

    async def write_file(self, device_path: str, content: str) -> str:
        """Write content to a file on the device.

        Args:
            device_path: Path to the file on the device
            content: Content to write

        Returns:
            Result message
        """
        # Create a temporary file locally
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
            temp.write(content)
            temp_path = temp.name

        try:
            # Push the temporary file to the device
            await self.push_file(temp_path, device_path)
            return f"Successfully wrote to {device_path}"
        finally:
            # Clean up the temporary file
            with contextlib.suppress(OSError):
                os.unlink(temp_path)


class DeviceManager:
    """Manages Android device connections and discovery.

    This class provides methods for listing devices, connecting to devices,
    and retrieving device instances.
    """

    def __init__(self, adb_path: str | None = None):
        """Initialize the DeviceManager with the given ADB wrapper.

        Args:
            adb: The ADBWrapper instance to use for device operations
        """
        self._adb = ADBWrapper(adb_path=adb_path)

    async def list_devices(self) -> list[Device]:
        """List all connected Android devices.

        Returns:
            List of Device instances
        """
        devices_info = await self._adb.get_devices()

        devices = []
        for device_info in devices_info:
            serial = device_info["serial"]
            device = Device(serial, adb=self._adb)
            devices.append(device)

        return devices

    async def get_device(self, serial: str) -> Device | None:
        """Get a Device instance by serial number.

        Args:
            serial: Device serial number

        Returns:
            Device instance or None if not found
        """
        devices_info = await self._adb.get_devices()

        device_exists = any(device["serial"] == serial for device in devices_info)
        if not device_exists:
            return None

        return Device(serial, adb=self._adb)

    async def connect(self, ip_address: str, port: int = 5555) -> Device | None:
        """Connect to a device over TCP/IP.

        Args:
            ip_address: Device IP address
            port: TCP port (default: 5555)

        Returns:
            Device instance if successful, None otherwise
        """
        # Validate IP address using regex
        ip_pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
        if not re.match(ip_pattern, ip_address):
            logger.error("Invalid IP address: %s", ip_address)
            return None

        # Try to connect
        result = await self._adb.connect_device_tcp(ip_address, port)

        # Check if connection was successful
        if "connected" in result.lower() or f"{ip_address}:{port}" in result:
            # Return a new device instance
            serial = f"{ip_address}:{port}"
            return Device(serial, adb=self._adb)

        logger.error("Failed to connect to device at %s:%s: %s", ip_address, port, result)
        return None

    async def disconnect(self, serial: str) -> bool:
        """Disconnect from a device.

        Args:
            serial: Device serial number

        Returns:
            True if successful, False otherwise
        """
        return await self._adb.disconnect_device(serial)


# Module-level variable for the singleton DeviceManager instance
_device_manager_instance: DeviceManager | None = None


def set_device_manager(device_manager: DeviceManager) -> None:
    """Set the global device manager instance.

    Args:
        device_manager: The DeviceManager instance to use
    """
    global _device_manager_instance  # pylint: disable=global-statement
    _device_manager_instance = device_manager
    logger.debug("Global device manager instance set")


def get_device_manager() -> DeviceManager:
    """Get the global device manager instance.

    Returns:
        The global DeviceManager instance

    Raises:
        RuntimeError: If the device manager instance hasn't been set
    """
    if _device_manager_instance is None:
        raise RuntimeError("DeviceManager instance hasn't been initialized")
    return _device_manager_instance

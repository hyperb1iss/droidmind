"""
Device abstractions for Android device management.

This module provides high-level abstractions for interacting with Android devices
through ADB. It defines two primary classes:

1. Device: Represents a single Android device and provides methods for
   interacting with it.
2. DeviceManager: Manages device discovery and connection.
"""

import contextlib
import os
import random
import re
import string
import tempfile
import time
from urllib.parse import unquote

import aiofiles

from droidmind.adb import ADBWrapper
from droidmind.log import logger
from droidmind.packages import parse_package_list
from droidmind.security import log_command_execution, sanitize_shell_command


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
        # Sanitize and validate the shell command
        try:
            sanitized_command = sanitize_shell_command(command)
            # Log command execution with appropriate risk level
            log_command_execution(command)
        except ValueError as e:
            logger.error("Security validation failed for shell command: %s", e)
            return f"Error: Command rejected for security reasons: {e}"

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
            output = await self._adb.shell(self._serial, sanitized_command)
        else:
            # For positive max_lines, use head to get first N lines
            # For negative max_lines, use tail to get last N lines
            if max_lines > 0:
                piped_command = f"{sanitized_command} | head -n {max_lines}"
            else:
                piped_command = f"{sanitized_command} | tail -n {abs(max_lines)}"

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
            # Generate a unique filename with timestamp and random component
            timestamp = int(time.time())
            random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))  # noqa: S311
            device_filename = f"/.screenshot_{timestamp}_{random_suffix}.png"

            # Take screenshot on device and save to a hidden file
            await self._adb.shell(self._serial, f"screencap -p {device_filename}")

            # Pull the file from the device
            await self._adb.pull_file(self._serial, device_filename, screenshot_path)

            # Clean up the file on the device
            await self._adb.shell(self._serial, f"rm {device_filename}")

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

    async def uninstall_app(self, package: str, keep_data: bool = False) -> str:
        """
        Uninstall an app from the device.

        Args:
            package: Package name to uninstall
            keep_data: Whether to keep app data and cache directories

        Returns:
            Uninstallation result message
        """
        log_command_execution(f"Uninstalling package {package} from {self._serial}")

        cmd = ["pm", "uninstall"]
        if keep_data:
            cmd.append("-k")
        cmd.append(package)

        result = await self.run_shell(" ".join(cmd))
        return result.strip()

    async def start_app(self, package: str, activity: str = "") -> str:
        """
        Start an app on the device.

        Args:
            package: Package name to start
            activity: Optional activity name to start (if empty, launches the default activity)

        Returns:
            Result message
        """
        log_command_execution(f"Starting package {package} on {self._serial}")

        if activity:
            if not activity.startswith(".") and "." not in activity:
                activity = f".{activity}"

            if not activity.startswith(".") and "." in activity and not activity.startswith(package):
                # Fully qualified activity name
                return await self.start_activity(
                    activity.split("/")[0], activity.split("/", 1)[1] if "/" in activity else activity
                )

            # Relative activity name
            return await self.start_activity(package, activity)

        # Start main activity
        cmd = f"monkey -p {package} -c android.intent.category.LAUNCHER 1"
        result = await self.run_shell(cmd)

        if "No activities found" in result:
            return f"Error: No launchable activities found for {package}"

        return f"Started package {package}"

    async def stop_app(self, package: str) -> str:
        """
        Force stop an app on the device.

        Args:
            package: Package name to stop

        Returns:
            Result message
        """
        log_command_execution(f"Stopping package {package} on {self._serial}")

        cmd = f"am force-stop {package}"
        await self.run_shell(cmd)

        return f"Stopped package {package}"

    async def clear_app_data(self, package: str) -> str:
        """
        Clear app data and cache for the specified package.

        Args:
            package: Package name to clear data for

        Returns:
            Result message
        """
        log_command_execution(f"Clearing data for package {package} on {self._serial}")

        cmd = f"pm clear {package}"
        result = await self.run_shell(cmd)

        if "Success" in result:
            return f"Successfully cleared data for package {package}"

        return f"Failed to clear data for package {package}: {result}"

    async def get_app_list(self, include_system_apps: bool = False) -> list[dict[str, str]]:
        """Get a list of installed applications.

        Args:
            include_system_apps: Whether to include system apps in the result

        Returns:
            List of dicts with package information
        """
        cmd = ["pm", "list", "packages", "-f"]  # -f to get APK paths
        if not include_system_apps:
            cmd.append("-3")  # Only third-party apps

        result = await self.run_shell(" ".join(cmd))

        return parse_package_list(result)

    async def get_app_info(self, package: str) -> dict[str, str]:
        """Get detailed information about an installed app.
        This method provides comprehensive details about a specific package.
        For a simple list of installed packages, use ADBWrapper.list_apps() instead.

        Args:
            package: Package name to get information for

        Returns:
            Dictionary with detailed app information including:
            - version: App version name
            - install_path: Installation path
            - first_install: First installation timestamp
            - user_id: App's user ID
            - permissions: Comma-separated list of requested permissions
            - raw_dump: Complete dumpsys output
        """
        cmd = f"dumpsys package {package}"
        # Set max_lines to None to retrieve the complete dumpsys output
        result = await self.run_shell(cmd, max_lines=None)

        if f"Unable to find package: {package}" in result:
            return {"error": f"Package {package} not found"}

        info = {"raw_dump": result}

        # Extract version info
        version_match = re.search(r"versionName=([^\s]+)", result)
        if version_match:
            info["version"] = version_match.group(1)

        # Extract installation path
        path_match = re.search(r"codePath=([^\s]+)", result)
        if path_match:
            info["install_path"] = path_match.group(1)

        # Extract first install time
        time_match = re.search(r"firstInstallTime=([^\s]+)", result)
        if time_match:
            info["first_install"] = time_match.group(1)

        # Extract user ID
        uid_match = re.search(r"userId=(\d+)", result)
        if uid_match:
            info["user_id"] = uid_match.group(1)

        # Extract requested permissions
        permissions = []
        perm_section = False
        for line in result.splitlines():
            if "requested permissions:" in line:
                perm_section = True
                continue
            if perm_section:
                if not line.strip() or not line.startswith(" "):
                    perm_section = False
                    continue
                permissions.append(line.strip())

        # Join permissions into a comma-separated string
        if permissions:
            info["permissions"] = ", ".join(permissions)

        return info

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
            content: Text content to write to the file

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

    # UI Automation Methods
    async def tap(self, x: int, y: int) -> str:
        """Simulate a tap at the specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Result message
        """
        command = f"input tap {x} {y}"
        return await self._adb.shell(self.serial, command)

    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 300) -> str:
        """Simulate a swipe gesture from one point to another.

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration_ms: Duration of the swipe in milliseconds

        Returns:
            Result message
        """
        command = f"input swipe {start_x} {start_y} {end_x} {end_y} {duration_ms}"
        return await self._adb.shell(self.serial, command)

    async def input_text(self, text: str) -> str:
        """Input text on the device.

        Args:
            text: Text to input

        Returns:
            Result message
        """
        # Escape special characters that could cause issues in shell
        safe_text = text.replace("'", "\\'").replace('"', '\\"')
        command = f"input text '{safe_text}'"
        return await self._adb.shell(self.serial, command)

    async def press_key(self, keycode: int) -> str:
        """Simulate pressing a key by its keycode.

        Common keycodes:
        - 3: HOME
        - 4: BACK
        - 24: VOLUME UP
        - 25: VOLUME DOWN
        - 26: POWER
        - 82: MENU

        Args:
            keycode: Android keycode to press

        Returns:
            Result message
        """
        command = f"input keyevent {keycode}"
        return await self._adb.shell(self.serial, command)

    async def start_activity(self, package: str, activity: str, extras: dict[str, str] | None = None) -> str:
        """Start an activity using an intent.

        Args:
            package: Package name
            activity: Activity name
            extras: Optional intent extras as key-value pairs

        Returns:
            Result message
        """
        command = f"am start -n {package}/{activity}"

        if extras:
            for key, value in extras.items():
                # Escape values that could cause issues in shell
                safe_value = value.replace("'", "\\'").replace('"', '\\"')
                command += f" -e {key} '{safe_value}'"

        return await self._adb.shell(self.serial, command)


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
            serial: Device serial number (URL-encoded if from resource path)

        Returns:
            Device instance or None if not found
        """
        # Decode URL-encoded serial (handles colons in TCP/IP addresses)
        decoded_serial = unquote(serial)

        devices_info = await self._adb.get_devices()

        device_exists = any(device["serial"] == decoded_serial for device in devices_info)
        if not device_exists:
            return None

        return Device(decoded_serial, adb=self._adb)

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

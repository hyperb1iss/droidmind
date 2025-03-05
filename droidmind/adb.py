"""
ADB Wrapper for DroidMind.

This module provides a wrapper around the system's ADB binary to interact with Android devices.
"""

import asyncio
from contextlib import AsyncExitStack
import os
import re
import shlex

from droidmind.log import logger
from droidmind.packages import parse_package_list
from droidmind.security import log_command_execution, validate_adb_command


class ADBWrapper:
    """A wrapper around the system ADB binary to interact with Android devices."""

    def __init__(
        self,
        adb_path: str | None = None,
        connection_timeout: float = 10.0,
        auth_timeout: float = 1.0,
    ):
        """Initialize the ADB wrapper.

        Args:
            adb_path: Path to ADB binary (defaults to 'adb' in PATH)
            connection_timeout: Timeout for ADB connection in seconds
            auth_timeout: Timeout for ADB authentication in seconds
        """
        self.adb_path = adb_path or "adb"
        self.connection_timeout = connection_timeout
        self.auth_timeout = auth_timeout

        # Track connected devices (cached)
        self._devices_cache: list[dict[str, str]] = []
        self._cache_time: float = 0.0

        logger.debug("ADBWrapper initialized with binary path: %s", self.adb_path)

    async def _run_adb_command(
        self, args: list[str], timeout_seconds: float | None = None, check: bool = True
    ) -> tuple[str, str]:
        """Run an ADB command and return stdout and stderr.

        Args:
            args: List of arguments to pass to ADB
            timeout_seconds: Command timeout in seconds (None for no timeout)
            check: Whether to check return code and raise exception

        Returns:
            Tuple of (stdout, stderr) as strings

        Raises:
            RuntimeError: If command fails and check=True
        """
        # Validate the ADB command for security
        try:
            await validate_adb_command(args)
        except ValueError as e:
            logger.error("Security validation failed for ADB command: %s", e)
            raise RuntimeError(f"Security validation failed: {e}") from e

        cmd = [self.adb_path, *args]
        logger.debug("Using ADB path for command: %s", self.adb_path)
        cmd_str = " ".join(shlex.quote(arg) for arg in cmd)

        # Log command execution
        log_command_execution(" ".join(args))
        logger.debug("Running ADB command: %s", cmd_str)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async with AsyncExitStack() as stack:
                if timeout_seconds is not None:
                    # Use asyncio.timeout() for Python 3.11+
                    # For earlier versions, we'd use asyncio.wait_for directly
                    await stack.enter_async_context(asyncio.timeout(timeout_seconds))

                stdout_bytes, stderr_bytes = await process.communicate()

            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()

            if check and process.returncode != 0:
                error_msg = f"ADB command failed with code {process.returncode}: {stderr or stdout}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            return stdout, stderr

        except TimeoutError as exc:
            logger.exception("ADB command timed out after %ss: %s", timeout_seconds, cmd_str)
            raise RuntimeError(f"ADB command timed out: {cmd_str}") from exc

        except Exception as e:
            logger.exception("Error executing ADB command: %s", e)
            # Provide more specific error messages based on exception type
            if isinstance(e, FileNotFoundError):
                error_msg = (
                    f"ADB binary not found at path: {self.adb_path}. Please ensure ADB is installed and in your PATH."
                )
                logger.exception(error_msg)
                raise FileNotFoundError(error_msg) from e
            if isinstance(e, PermissionError):
                error_msg = f"Permission denied when executing ADB command: {cmd_str}. Check file permissions."
                logger.exception(error_msg)
                raise PermissionError(error_msg) from e
            if isinstance(e, OSError):
                error_msg = f"OS error when executing ADB command: {cmd_str}. Error: {e}"
                logger.exception(error_msg)
                raise OSError(error_msg) from e
            # For other exceptions, re-raise with more context
            raise RuntimeError(f"Failed to execute ADB command: {cmd_str}. Error: {e}") from e

    async def _run_adb_device_command(
        self, serial: str, args: list[str], timeout_seconds: float | None = None, check: bool = True
    ) -> tuple[str, str]:
        """Run an ADB command for a specific device.

        Args:
            serial: Device serial number
            args: List of arguments to pass to ADB
            timeout_seconds: Command timeout in seconds
            check: Whether to check return code

        Returns:
            Tuple of (stdout, stderr)
        """
        return await self._run_adb_command(["-s", serial, *args], timeout_seconds, check)

    async def connect_device_tcp(self, host: str, port: int = 5555) -> str:
        """Connect to a device over TCP/IP.

        Args:
            host: IP address or hostname of the device
            port: TCP port to connect to

        Returns:
            Device serial number (in the format host:port)

        Raises:
            RuntimeError: If connection fails
        """
        serial = f"{host}:{port}"

        # Check if already connected
        devices = await self.get_devices()
        if any(d["serial"] == serial for d in devices):
            logger.info("Device %s is already connected", serial)
            return serial

        # Connect to the device
        logger.info("Connecting to device at %s:%s", host, port)
        stdout, _ = await self._run_adb_command(["connect", serial], timeout_seconds=self.connection_timeout)

        if "connected" not in stdout.lower():
            error_msg = f"Failed to connect to {serial}: {stdout}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info("Successfully connected to device %s", serial)

        # Clear the device cache to force a refresh
        self._devices_cache = []

        return serial

    async def connect_device_usb(self) -> str | None:
        """Connect to a USB device.

        Returns:
            The serial number of the connected device, or None if connection failed.
        """
        try:
            # List USB devices
            devices = await self.get_devices()
            usb_devices = [d for d in devices if ":" not in d["serial"]]

            if not usb_devices:
                logger.warning("No USB devices found")
                return None

            return usb_devices[0]["serial"]

        except (RuntimeError, OSError, TimeoutError) as e:
            logger.exception("Failed to connect to USB device due to system error: %s", e)
            return None
        except Exception as e:  # noqa: BLE001 - Need to handle any device-specific errors
            logger.exception("Failed to connect to USB device: %s", e)
            return None

    async def disconnect_device(self, serial: str) -> bool:
        """Disconnect from a device.

        Args:
            serial: The device serial number.

        Returns:
            True if disconnected, False if device wasn't connected.
        """
        try:
            # Only TCP devices can be disconnected
            if ":" not in serial:
                logger.warning("Cannot disconnect USB device %s", serial)
                return False

            stdout, _ = await self._run_adb_command(
                ["disconnect", serial],
                check=False,  # Don't raise exception for disconnection
            )

            # Clear cache
            self._devices_cache = []

            if "disconnected" in stdout.lower():
                logger.info("Disconnected from %s", serial)
                return True
            logger.warning("Device %s was not connected", serial)
            return False

        except (RuntimeError, OSError, TimeoutError) as e:
            logger.exception("System error disconnecting from %s: %s", serial, e)
            return False
        except Exception as e:  # noqa: BLE001 - Must handle any device-specific errors for clean disconnect
            logger.exception("Error disconnecting from %s: %s", serial, e)
            return False

    async def get_devices(self) -> list[dict[str, str]]:
        """Get a list of connected devices.

        Returns:
            A list of dictionaries containing device information.
        """
        result = []

        try:
            stdout, _ = await self._run_adb_command(["devices", "-l"])

            # Parse the output
            lines = stdout.splitlines()
            if len(lines) <= 1:
                logger.info("No devices connected")
                return []

            for line in lines[1:]:  # Skip the "List of devices attached" header
                if not line.strip():
                    continue

                parts = line.split()
                if not parts:
                    continue

                serial = parts[0]
                status = parts[1] if len(parts) > 1 else "unknown"

                if status != "device":
                    # Skip unauthorized or offline devices
                    logger.warning("Device %s is %s, skipping", serial, status)
                    continue

                # Create basic device info
                device_info = {
                    "serial": serial,
                    "status": status,
                }

                # Extract model from device info line if available
                model_match = re.search(r"model:(\S+)", line)
                if model_match:
                    device_info["model"] = model_match.group(1)

                # Get more device details if we have a connected device
                if status == "device":
                    try:
                        # Get additional device properties directly without using get_device_property
                        # to avoid potential infinite recursion
                        model_stdout, _ = await self._run_adb_device_command(
                            serial, ["shell", "getprop ro.product.model"], check=False
                        )
                        if model_stdout.strip():
                            device_info["model"] = model_stdout.strip()

                        version_stdout, _ = await self._run_adb_device_command(
                            serial, ["shell", "getprop ro.build.version.release"], check=False
                        )
                        if version_stdout.strip():
                            device_info["android_version"] = version_stdout.strip()
                    except (TimeoutError, RuntimeError, OSError) as e:
                        # Continue even if we can't get all properties
                        logger.debug("Could not get all device properties for %s: %s", serial, e)

                result.append(device_info)

            # Update cache
            self._devices_cache = result
            self._cache_time = asyncio.get_event_loop().time()

            return result

        except Exception as e:  # noqa: BLE001 - Top-level device list handler needs to catch all errors
            logger.exception("Error getting device list: %s", e)
            # Check for specific error types to provide more helpful messages
            if isinstance(e, RuntimeError) and "ADB command failed" in str(e):
                logger.exception("ADB command failed. Is ADB installed and in your PATH?")
            elif isinstance(e, FileNotFoundError):
                logger.exception("ADB binary not found at path: %s", self.adb_path)
            elif isinstance(e, TimeoutError):
                logger.exception("ADB command timed out. Device may be unresponsive.")
            elif isinstance(e, OSError):
                logger.exception("OS error when running ADB. Check permissions and connectivity.")

            # Return cached devices if available, otherwise empty list
            if self._devices_cache:
                logger.info("Returning %d cached devices", len(self._devices_cache))
                return self._devices_cache
            return []

    async def shell(self, serial: str, command: str) -> str:
        """Run a shell command on the device.

        Args:
            serial: The device serial number.
            command: The shell command to run.

        Returns:
            The command output as a string.

        Raises:
            ValueError: If device is not connected.
            RuntimeError: If command execution fails.
        """
        try:
            # Use cached device list to avoid infinite recursion
            # Only fetch devices if cache is empty
            if not self._devices_cache:
                # Direct ADB command to check if device exists without recursion
                stdout, _ = await self._run_adb_command(["devices"], check=False)
                if serial not in stdout:
                    raise ValueError(f"Device {serial} not connected")
            else:
                device_serials = [d["serial"] for d in self._devices_cache]
                if serial not in device_serials:
                    raise ValueError(f"Device {serial} not connected")

            # Execute shell command
            stdout, _ = await self._run_adb_device_command(serial, ["shell", command])

            return stdout

        except ValueError:
            raise  # Re-raise ValueError for not connected

        except Exception as e:
            logger.exception("Error executing command on %s: %s", serial, e)
            raise RuntimeError(f"Command execution failed: {e!s}") from e

    async def get_device_properties(self, serial: str) -> dict[str, str]:
        """Get all properties from a device.

        Args:
            serial: The device serial number.

        Returns:
            Dictionary of device properties.

        Raises:
            ValueError: If device is not connected.
        """
        # Direct shell command without checking device list to avoid recursion
        try:
            result = await self.shell(serial, "getprop")

            # Parse the getprop output into a dictionary
            properties = {}
            for line in result.splitlines():
                match = re.match(r"\[(.+?)\]: \[(.+?)\]", line)
                if match:
                    key, value = match.groups()
                    properties[key] = value

            return properties
        except ValueError:
            # Re-raise if device not connected
            raise
        except (RuntimeError, OSError, TimeoutError) as e:
            logger.exception("System error getting properties from %s: %s", serial, e)
            return {}
        except Exception as e:  # noqa: BLE001 - Must handle any device-specific property errors
            logger.exception("Error getting properties from %s: %s", serial, e)
            return {}

    async def get_device_property(self, serial: str, prop_name: str) -> str | None:
        """Get a specific property from a device.

        Args:
            serial: The device serial number.
            prop_name: The property name to get.

        Returns:
            The property value or None if not found.

        Raises:
            ValueError: If device is not connected.
        """
        try:
            # Direct shell command to avoid potential recursion
            stdout, _ = await self._run_adb_device_command(serial, ["shell", f"getprop {prop_name}"], check=False)
            return stdout.strip() if stdout else None
        except (RuntimeError, OSError, TimeoutError) as e:
            logger.exception("System error getting property %s from %s: %s", prop_name, serial, e)
            return None
        except Exception as e:  # noqa: BLE001 - Must handle any device-specific property errors
            logger.exception("Error getting property %s from %s: %s", prop_name, serial, e)
            return None

    async def install_app(
        self, serial: str, apk_path: str, reinstall: bool = False, grant_permissions: bool = True
    ) -> str:
        """Install an APK on the device.

        Args:
            serial: The device serial number.
            apk_path: Path to the APK file.
            reinstall: Whether to reinstall if app already exists.
            grant_permissions: Whether to automatically grant permissions.

        Returns:
            Installation result message.

        Raises:
            ValueError: If device is not connected or APK doesn't exist.
        """
        if not os.path.exists(apk_path):
            raise ValueError(f"APK file not found: {apk_path}")

        # Check if device is connected
        devices = await self.get_devices()
        device_serials = [d["serial"] for d in devices]

        if serial not in device_serials:
            raise ValueError(f"Device {serial} not connected")

        # Build install command args
        install_args = ["install"]
        if reinstall:
            install_args.append("-r")
        if grant_permissions:
            install_args.append("-g")
        install_args.append(apk_path)

        # Execute installation
        try:
            stdout, stderr = await self._run_adb_device_command(
                serial,
                install_args,
                timeout_seconds=120,  # Longer timeout for installation
            )

            if "success" in stdout.lower():
                return f"Successfully installed {os.path.basename(apk_path)}"
            return f"Installation failed: {stdout or stderr}"

        except Exception as e:
            logger.exception("Error installing app: %s", e)
            raise RuntimeError(f"Installation failed: {e!s}") from e

    async def push_file(self, serial: str, local_path: str, device_path: str) -> str:
        """Push a file to the device.

        Args:
            serial: The device serial number.
            local_path: Path to the local file.
            device_path: Destination path on the device.

        Returns:
            Result message.

        Raises:
            ValueError: If device is not connected or local file doesn't exist.
        """
        if not os.path.exists(local_path):
            raise ValueError(f"Local file not found: {local_path}")

        # Check if device is connected
        devices = await self.get_devices()
        device_serials = [d["serial"] for d in devices]

        if serial not in device_serials:
            raise ValueError(f"Device {serial} not connected")

        try:
            # Execute push command
            logger.info("Pushing %s to %s on %s", local_path, device_path, serial)
            stdout, _ = await self._run_adb_device_command(
                serial,
                ["push", local_path, device_path],
                timeout_seconds=60,  # Longer timeout for file transfer
            )

            return f"Successfully pushed {os.path.basename(local_path)} to {device_path}"

        except Exception as e:
            logger.exception("Error pushing file to %s: %s", serial, e)
            raise RuntimeError(f"File push failed: {e!s}") from e

    async def pull_file(self, serial: str, device_path: str, local_path: str) -> str:
        """Pull a file from the device.

        Args:
            serial: The device serial number.
            device_path: Path to the file on the device.
            local_path: Destination path on the local machine.

        Returns:
            Result message.

        Raises:
            ValueError: If device is not connected.
        """
        # Check if device is connected
        devices = await self.get_devices()
        device_serials = [d["serial"] for d in devices]

        if serial not in device_serials:
            raise ValueError(f"Device {serial} not connected")

        try:
            # Create directory if it doesn't exist
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)

            # Execute pull command
            logger.info("Pulling %s from %s to %s", device_path, serial, local_path)
            stdout, _ = await self._run_adb_device_command(
                serial,
                ["pull", device_path, local_path],
                timeout_seconds=60,  # Longer timeout for file transfer
            )

            return f"Successfully pulled {device_path} to {os.path.basename(local_path)}"

        except Exception as e:
            logger.exception("Error pulling file from %s: %s", serial, e)
            raise RuntimeError(f"File pull failed: {e!s}") from e

    async def reboot_device(self, serial: str, mode: str = "normal") -> str:
        """Reboot the device.

        Args:
            serial: The device serial number.
            mode: Reboot mode - "normal", "recovery", or "bootloader".

        Returns:
            Result message.

        Raises:
            ValueError: If device is not connected or mode is invalid.
        """
        # Check if device is connected
        devices = await self.get_devices()
        device_serials = [d["serial"] for d in devices]

        if serial not in device_serials:
            raise ValueError(f"Device {serial} not connected")

        # Validate reboot mode
        valid_modes = ["normal", "recovery", "bootloader"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid reboot mode. Must be one of: {', '.join(valid_modes)}")

        try:
            # Execute reboot command
            logger.info("Rebooting %s into %s mode", serial, mode)

            if mode == "normal":
                await self._run_adb_device_command(serial, ["reboot"])
            else:
                await self._run_adb_device_command(serial, ["reboot", mode])

            # Device will disconnect after reboot
            # Clear our device cache
            self._devices_cache = [d for d in self._devices_cache if d["serial"] != serial]

            return f"Device {serial} rebooting into {mode} mode"

        except Exception as e:
            logger.exception("Error rebooting %s: %s", serial, e)
            raise RuntimeError(f"Reboot failed: {e!s}") from e

    async def capture_screenshot(self, serial: str, local_path: str | None = None) -> str:
        """Capture a screenshot from the device.

        Args:
            serial: The device serial number.
            local_path: Path to save the screenshot (optional).

        Returns:
            Path to the saved screenshot.

        Raises:
            ValueError: If device is not connected.
        """
        # Check if device is connected
        devices = await self.get_devices()
        device_serials = [d["serial"] for d in devices]

        if serial not in device_serials:
            raise ValueError(f"Device {serial} not connected")

        # Generate default path if not provided
        if not local_path:
            timestamp = asyncio.get_event_loop().time()
            local_path = f"screenshot_{serial.replace(':', '_')}_{int(timestamp)}.png"

        # Temp path on device
        device_path = "/sdcard/screenshot.png"

        try:
            # Take screenshot using screencap command
            logger.info("Taking screenshot on %s", serial)
            await self.shell(serial, f"screencap -p {device_path}")

            # Pull screenshot to local machine
            await self.pull_file(serial, device_path, local_path)

            # Clean up on device
            await self.shell(serial, f"rm {device_path}")

            return local_path

        except Exception as e:
            logger.exception("Error capturing screenshot from %s: %s", serial, e)
            raise RuntimeError(f"Screenshot capture failed: {e!s}") from e

    async def list_apps(self, serial: str, include_system_apps: bool = False) -> list[dict[str, str]]:
        """List basic information about installed applications on the device.
        For detailed app information, use Device.get_app_info() instead.

        Args:
            serial: Device serial number
            include_system_apps: Whether to include system apps

        Returns:
            List of dicts containing basic package info (package name and installation path)
        """
        cmd = ["pm", "list", "packages", "-f"]
        if not include_system_apps:
            cmd.append("-3")

        stdout = await self.shell(serial, " ".join(cmd))
        return parse_package_list(stdout)

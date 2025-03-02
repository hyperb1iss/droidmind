"""
ADB Wrapper for DroidMind.

This module provides a wrapper around the adb_shell library to interact with Android devices.
"""

import asyncio
import logging
import os
from pathlib import Path
import re

from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.exceptions import (
    AdbCommandFailureException,
)

logger = logging.getLogger(__name__)


class ADBWrapper:
    """A wrapper around adb_shell to interact with Android devices."""

    def __init__(
        self,
        adb_key_path: str | None = None,
        connection_timeout: float = 10.0,
        auth_timeout: float = 1.0,
    ):
        """Initialize the ADB wrapper.

        Args:
            adb_key_path: Path to ADB key (defaults to ~/.android/adbkey)
            connection_timeout: Timeout for ADB connection in seconds
            auth_timeout: Timeout for ADB authentication in seconds
        """
        self.adb_key_path = adb_key_path or self._get_default_adb_key_path()
        self.connection_timeout = connection_timeout
        self.auth_timeout = auth_timeout

        # Ensure ADB key exists
        self._ensure_adb_key_exists()

        # Dict to store connected devices keyed by serial number
        self._devices: dict[str, AdbDeviceTcp | AdbDeviceUsb] = {}

        logger.debug(f"ADBWrapper initialized with key: {self.adb_key_path}")

    def _get_default_adb_key_path(self) -> str:
        """Get the default ADB key path."""
        return os.path.expanduser("~/.android/adbkey")

    def _ensure_adb_key_exists(self) -> None:
        """Ensure ADB key exists, generating it if needed."""
        key_path = Path(self.adb_key_path)
        pub_key_path = Path(f"{self.adb_key_path}.pub")

        if not key_path.exists() or not pub_key_path.exists():
            # Create parent directories if they don't exist
            key_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Generating ADB key pair at {self.adb_key_path}")
            keygen(self.adb_key_path)

    def _load_signer(self) -> PythonRSASigner:
        """Load ADB key signer."""
        try:
            return PythonRSASigner.from_file(
                self.adb_key_path,
                f"{self.adb_key_path}.pub",
            )
        except Exception as e:
            logger.exception(f"Failed to load ADB key: {e}")
            raise

    async def connect_device_tcp(self, host: str, port: int = 5555) -> str:
        """Connect to a device over TCP/IP.

        Args:
            host: IP address or hostname of the device
            port: TCP port to connect to

        Returns:
            Device serial number (in the format host:port)

        Raises:
            AdbConnectionError: If connection fails
        """
        # Normalize hostname for use as serial
        serial = f"{host}:{port}"

        # Check if already connected
        if serial in self._devices and self._devices[serial].available:
            logger.info(f"Device {serial} is already connected")
            return serial

        # Create a new ADB device
        logger.debug(f"Connecting to device at {host}:{port}")
        device = AdbDeviceTcp(host=host, port=port, default_timeout_s=self.connection_timeout)

        try:
            # Connect to the device
            signer = self._load_signer()
            await asyncio.to_thread(device.connect, rsa_keys=[signer], auth_timeout_s=self.auth_timeout)

            # Store the connected device
            self._devices[serial] = device
            logger.info(f"Successfully connected to device {serial}")

            return serial

        except Exception as e:
            logger.exception(f"Failed to connect to device {host}:{port}: {e}")
            raise

    async def connect_device_usb(self) -> str | None:
        """Connect to a USB device.

        Returns:
            The device serial number or None if no device found.

        Raises:
            AdbConnectionError: If connection fails.
        """
        device = AdbDeviceUsb(default_transport_timeout_s=self.connection_timeout)

        try:
            # Get USB device info first
            device_info = await asyncio.to_thread(device.get_serial_number)
            serial = device_info

            if serial in self._devices:
                logger.info(f"Device {serial} already connected")
                return serial

            logger.info(f"Connecting to USB device {serial}...")
            await asyncio.to_thread(device.connect, rsa_keys=[self._load_signer()], auth_timeout_s=self.auth_timeout)

            self._devices[serial] = device
            logger.info(f"Connected to USB device {serial}")
            return serial

        except Exception as e:
            logger.exception(f"Failed to connect to USB device: {e}")
            return None

    async def disconnect_device(self, serial: str) -> bool:
        """Disconnect from a device.

        Args:
            serial: The device serial number.

        Returns:
            True if disconnected, False if device wasn't connected.
        """
        if serial not in self._devices:
            logger.warning(f"Device {serial} not connected")
            return False

        try:
            device = self._devices[serial]
            await asyncio.to_thread(device.close)
            del self._devices[serial]
            logger.info(f"Disconnected from {serial}")
            return True

        except Exception as e:
            logger.exception(f"Error disconnecting from {serial}: {e}")
            return False

    async def get_devices(self) -> list[dict[str, str]]:
        """Get a list of connected devices.

        Returns:
            A list of dictionaries containing device information.
        """
        result = []

        for serial, device in self._devices.items():
            try:
                # Check if device is still connected
                if not device.available:
                    logger.warning(f"Device {serial} no longer available")
                    continue

                # Get basic device info
                device_info = {
                    "serial": serial,
                    "status": "device",  # We only track connected devices
                }

                # Get model if possible
                try:
                    model = await self.get_device_property(serial, "ro.product.model")
                    if model:
                        device_info["model"] = model
                except Exception:
                    pass

                # Get Android version if possible
                try:
                    android_version = await self.get_device_property(serial, "ro.build.version.release")
                    if android_version:
                        device_info["android_version"] = android_version
                except Exception:
                    pass

                result.append(device_info)

            except Exception as e:
                logger.exception(f"Error getting info for device {serial}: {e}")

        return result

    async def shell(self, serial: str, command: str) -> str:
        """Run a shell command on the device.

        Args:
            serial: The device serial number.
            command: The shell command to run.

        Returns:
            The command output as a string.

        Raises:
            ValueError: If device is not connected.
            AdbCommandFailureException: If command execution fails.
        """
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")

        device = self._devices[serial]

        try:
            logger.debug(f"Running shell command on {serial}: {command}")
            return await asyncio.to_thread(device.shell, command)

        except AdbCommandFailureException as e:
            logger.exception(f"Command failed on {serial}: {e}")
            raise

        except Exception as e:
            logger.exception(f"Error executing command on {serial}: {e}")
            raise

    async def get_device_properties(self, serial: str) -> dict[str, str]:
        """Get all properties from a device.

        Args:
            serial: The device serial number.

        Returns:
            Dictionary of device properties.

        Raises:
            ValueError: If device is not connected.
        """
        result = await self.shell(serial, "getprop")

        # Parse the getprop output into a dictionary
        properties = {}
        for line in result.splitlines():
            match = re.match(r"\[(.+?)\]: \[(.+?)\]", line)
            if match:
                key, value = match.groups()
                properties[key] = value

        return properties

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
            result = await self.shell(serial, f"getprop {prop_name}")
            return result.strip() if result else None
        except Exception as e:
            logger.exception(f"Error getting property {prop_name} from {serial}: {e}")
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
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")

        if not os.path.exists(apk_path):
            raise ValueError(f"APK file not found: {apk_path}")

        # Build install command
        cmd = ["pm", "install"]
        if reinstall:
            cmd.append("-r")
        if grant_permissions:
            cmd.append("-g")
        cmd.append(f'"{apk_path}"')

        # Execute installation command
        result = await self.shell(serial, " ".join(cmd))

        if "Success" in result:
            return f"Successfully installed {os.path.basename(apk_path)}"
        else:
            return f"Installation failed: {result}"

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
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")

        if not os.path.exists(local_path):
            raise ValueError(f"Local file not found: {local_path}")

        device = self._devices[serial]

        try:
            # Read file content
            with open(local_path, "rb") as f:
                f.read()

            # Push to device
            logger.info(f"Pushing {local_path} to {device_path} on {serial}")
            await asyncio.to_thread(device.push, local_path, device_path)

            return f"Successfully pushed {os.path.basename(local_path)} to {device_path}"

        except Exception as e:
            logger.exception(f"Error pushing file to {serial}: {e}")
            raise

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
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")

        device = self._devices[serial]

        try:
            # Create directory if it doesn't exist
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)

            # Pull from device
            logger.info(f"Pulling {device_path} from {serial} to {local_path}")
            await asyncio.to_thread(device.pull, device_path, local_path)

            return f"Successfully pulled {device_path} to {os.path.basename(local_path)}"

        except Exception as e:
            logger.exception(f"Error pulling file from {serial}: {e}")
            raise

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
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")

        valid_modes = ["normal", "recovery", "bootloader"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid reboot mode. Must be one of: {', '.join(valid_modes)}")

        device = self._devices[serial]

        try:
            logger.info(f"Rebooting {serial} into {mode} mode")

            if mode == "normal":
                await asyncio.to_thread(device.reboot)
            else:
                await asyncio.to_thread(device.shell, f"reboot {mode}")

            # Device will disconnect after reboot
            if serial in self._devices:
                del self._devices[serial]

            return f"Device {serial} rebooting into {mode} mode"

        except Exception as e:
            logger.exception(f"Error rebooting {serial}: {e}")
            raise

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
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")

        # Generate default path if not provided
        if not local_path:
            timestamp = asyncio.get_event_loop().time()
            local_path = f"screenshot_{serial.replace(':', '_')}_{int(timestamp)}.png"

        # Temp path on device
        device_path = "/sdcard/screenshot.png"

        try:
            # Take screenshot on device
            logger.info(f"Taking screenshot on {serial}")
            await self.shell(serial, "screencap -p " + device_path)

            # Pull screenshot to local machine
            await self.pull_file(serial, device_path, local_path)

            # Clean up on device
            await self.shell(serial, f"rm {device_path}")

            return local_path

        except Exception as e:
            logger.exception(f"Error capturing screenshot from {serial}: {e}")
            raise

    async def list_apps(self, serial: str, system_apps: bool = False) -> list[dict[str, str]]:
        """List installed apps on the device.

        Args:
            serial: The device serial number.
            system_apps: Whether to include system apps.

        Returns:
            List of dictionaries with app information.

        Raises:
            ValueError: If device is not connected.
        """
        if serial not in self._devices:
            raise ValueError(f"Device {serial} not connected")

        flags = "-3" if not system_apps else ""
        result = await self.shell(serial, f"pm list packages {flags} -f")

        apps = []
        for line in result.splitlines():
            if not line.startswith("package:"):
                continue

            # Parse package info
            # Format: package:/data/app/com.example.app-hash=.../base.apk=com.example.app
            parts = line[8:].split("=")
            if len(parts) < 2:
                continue

            apk_path = parts[0]
            package_name = parts[-1]

            # Get app label if possible
            try:
                label_result = await self.shell(
                    serial,
                    f'dumpsys package {package_name} | grep "applicationInfo" | grep "labelRes"',
                )
                label = "Unknown"
                if label_result:
                    label_match = re.search(r"label=(.*?)\s", label_result)
                    if label_match:
                        label = label_match.group(1)
            except Exception:
                label = "Unknown"

            apps.append(
                {
                    "package": package_name,
                    "path": apk_path,
                    "label": label,
                }
            )

        return apps

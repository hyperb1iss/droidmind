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

    async def get_logcat(self, lines: int = 100) -> str:
        """Get the most recent lines from logcat.

        Args:
            lines: Number of lines to retrieve

        Returns:
            Recent logcat output
        """
        return await self._adb.shell(self._serial, f"logcat -d -t {lines}")

    async def list_directory(self, path: str) -> str:
        """List the contents of a directory on the device.

        Args:
            path: Directory path to list

        Returns:
            Directory listing
        """
        return await self._adb.shell(self._serial, f"ls -la {path}")

    async def run_shell(self, command: str) -> str:
        """Run a shell command on the device.

        Args:
            command: Shell command to run

        Returns:
            Command output
        """
        return await self._adb.shell(self._serial, command)

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
    global _device_manager_instance # pylint: disable=global-statement
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

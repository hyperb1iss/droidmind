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

from droidmind.adb.service import ADBService

logger = logging.getLogger("droidmind")


class Device:
    """High-level representation of an Android device.

    This class encapsulates device-specific operations and properties
    to provide a more convenient API for interacting with Android devices.
    """

    def __init__(self, serial: str, adb_service: ADBService | None = None) -> None:
        """Initialize a Device instance.

        Args:
            serial: The device serial number or connection string (e.g., "ip:port")
            adb_service: Optional ADBService instance to use. If not provided,
                         one will be obtained when needed.
        """
        self._serial = serial
        self._adb_service = adb_service
        self._properties_cache: dict[str, str] = {}

    @property
    def serial(self) -> str:
        """Get the device serial number."""
        return self._serial

    async def _get_adb_service(self) -> ADBService:
        """Get the ADBService instance, creating one if needed."""
        if self._adb_service is None:
            self._adb_service = await ADBService.get_instance()
        return self._adb_service

    async def get_properties(self) -> dict[str, str]:
        """Get all device properties.

        Returns:
            Dictionary of device properties
        """
        if not self._properties_cache:
            adb_service = await self._get_adb_service()
            self._properties_cache = await adb_service.get_device_properties(self._serial)
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
        adb_service = await self._get_adb_service()
        return await adb_service.shell(self._serial, f"logcat -d -t {lines}")

    async def list_directory(self, path: str) -> str:
        """List the contents of a directory on the device.

        Args:
            path: Directory path to list

        Returns:
            Directory listing
        """
        adb_service = await self._get_adb_service()
        return await adb_service.shell(self._serial, f"ls -la {path}")

    async def run_shell(self, command: str) -> str:
        """Run a shell command on the device.

        Args:
            command: Shell command to run

        Returns:
            Command output
        """
        adb_service = await self._get_adb_service()
        return await adb_service.shell(self._serial, command)

    async def reboot(self, mode: str = "normal") -> str:
        """Reboot the device.

        Args:
            mode: Reboot mode - "normal", "recovery", or "bootloader"

        Returns:
            Command output
        """
        adb_service = await self._get_adb_service()
        return await adb_service.reboot_device(self._serial, mode)

    async def take_screenshot(self) -> bytes:
        """Take a screenshot of the device.

        Returns:
            Screenshot data as bytes
        """
        adb_service = await self._get_adb_service()

        # Create a temporary file for the screenshot
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
            screenshot_path = temp.name

        try:
            # Take screenshot on device and save to /sdcard/
            await adb_service.shell(self._serial, "screencap -p /sdcard/screenshot.png")

            # Pull the file from the device
            await adb_service.pull_file(self._serial, "/sdcard/screenshot.png", screenshot_path)

            # Clean up the file on the device
            await adb_service.shell(self._serial, "rm /sdcard/screenshot.png")

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
        adb_service = await self._get_adb_service()
        return await adb_service.install_app(self._serial, apk_path, reinstall, grant_permissions)


class DeviceManager:
    """Manages Android device connections and discovery.

    This class provides static methods for listing devices, connecting to devices,
    and retrieving device instances.
    """

    @staticmethod
    async def list_devices() -> list[Device]:
        """List all connected Android devices.

        Returns:
            List of Device instances
        """
        adb_service = await ADBService.get_instance()
        devices_info = await adb_service.get_devices()

        devices = []
        for device_info in devices_info:
            serial = device_info["serial"]
            device = Device(serial, adb_service)
            devices.append(device)

        return devices

    @staticmethod
    async def get_device(serial: str) -> Device | None:
        """Get a Device instance by serial number.

        Args:
            serial: Device serial number

        Returns:
            Device instance or None if not found
        """
        adb_service = await ADBService.get_instance()
        devices_info = await adb_service.get_devices()

        device_exists = any(device["serial"] == serial for device in devices_info)
        if not device_exists:
            return None

        return Device(serial, adb_service)

    @staticmethod
    async def connect(ip_address: str, port: int = 5555) -> Device | None:
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
        adb_service = await ADBService.get_instance()
        result = await adb_service.connect_device_tcp(ip_address, port)

        # Check if connection was successful
        if "connected" in result.lower() or f"{ip_address}:{port}" in result:
            # Return a new device instance
            serial = f"{ip_address}:{port}"
            return Device(serial, adb_service)

        logger.error("Failed to connect to device at %s:%s: %s", ip_address, port, result)
        return None

    @staticmethod
    async def disconnect(serial: str) -> bool:
        """Disconnect from a device.

        Args:
            serial: Device serial number

        Returns:
            True if successful, False otherwise
        """
        adb_service = await ADBService.get_instance()
        return await adb_service.disconnect_device(serial)

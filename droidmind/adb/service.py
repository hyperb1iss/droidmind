"""
ADB Service - Service for ADB wrapper management.

This module provides a service for managing the ADB wrapper instance.
"""

import asyncio
import logging
from typing import Optional

from droidmind.adb.wrapper import ADBWrapper

logger = logging.getLogger("droidmind")


class ADBService:
    """Service for managing ADB wrapper instance."""

    _instance: Optional["ADBService"] = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        """Initialize the ADB service."""
        self.adb = ADBWrapper()
        self._temp_dir: str | None = None
        logger.debug("ADBService initialized")

    @classmethod
    async def get_instance(cls) -> "ADBService":
        """Get the singleton instance of the ADB service.

        Returns:
            The ADB service instance
        """
        async with cls._lock:
            if cls._instance is None:
                cls._instance = ADBService()
                logger.debug("Created new ADBService instance")
            return cls._instance

    def set_temp_dir(self, temp_dir: str) -> None:
        """Set the temporary directory for file operations.

        Args:
            temp_dir: Path to temporary directory
        """
        self._temp_dir = temp_dir
        logger.debug("Set temp directory to %s", temp_dir)

    @property
    def temp_dir(self) -> str | None:
        """Get the temporary directory path.

        Returns:
            Temporary directory path or None if not set
        """
        return self._temp_dir

    async def cleanup(self) -> None:
        """Clean up the ADB service resources."""
        # Skip disconnecting devices during shutdown
        logger.debug("Skipping ADB device disconnections during shutdown.")
        logger.debug("ADBService cleanup complete")

    # Delegation methods to expose ADB functionality via the service
    async def get_devices(self) -> list[dict[str, str]]:
        return await self.adb.get_devices()

    async def shell(self, serial: str, command: str) -> str:
        return await self.adb.shell(serial, command)

    async def connect_device_tcp(self, host: str, port: int = 5555) -> str:
        return await self.adb.connect_device_tcp(host, port)

    async def disconnect_device(self, serial: str) -> bool:
        return await self.adb.disconnect_device(serial)

    async def get_device_properties(self, serial: str) -> dict[str, str]:
        return await self.adb.get_device_properties(serial)

    async def push_file(self, serial: str, local_path: str, device_path: str) -> str:
        return await self.adb.push_file(serial, local_path, device_path)

    async def pull_file(self, serial: str, device_path: str, local_path: str) -> str:
        return await self.adb.pull_file(serial, device_path, local_path)

    async def install_app(
        self, serial: str, apk_path: str, reinstall: bool = False, grant_permissions: bool = True
    ) -> str:
        return await self.adb.install_app(serial, apk_path, reinstall, grant_permissions)

    async def reboot_device(self, serial: str, mode: str = "normal") -> str:
        return await self.adb.reboot_device(serial, mode)


# Added get_adb function
async def get_adb() -> ADBWrapper:
    """Return the ADBWrapper instance from the ADBService singleton."""
    service = await ADBService.get_instance()
    return service.adb

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
        # Disconnect all devices
        try:
            devices = await self.adb.get_devices()
            for device in devices:
                serial = device["serial"]
                await self.adb.disconnect_device(serial)
                logger.debug("Disconnected device %s", serial)
        except Exception as e:
            logger.exception("Error disconnecting devices: %s", e)

        logger.debug("ADBService cleanup complete")


# Convenience function to get the ADB wrapper
async def get_adb() -> ADBWrapper:
    """Get the ADB wrapper instance.

    Returns:
        The ADB wrapper instance
    """
    service = await ADBService.get_instance()
    return service.adb


# Convenience function to get the temp directory
async def get_temp_dir() -> str | None:
    """Get the temporary directory path.

    Returns:
        Temporary directory path or None if not set
    """
    service = await ADBService.get_instance()
    return service.temp_dir

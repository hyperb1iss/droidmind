"""
DroidMind Filesystem - Classes for managing device filesystem resources.

This module provides object-oriented abstractions for interacting with the
Android device filesystem, allowing for structured access to files and directories.
"""

import logging
import os
from typing import Any, Union

from droidmind.devices import Device

logger = logging.getLogger("droidmind")


class FileSystemResource:
    """Base class for file system resources."""

    def __init__(self, path: str, device: Device) -> None:
        """
        Initialize a FileSystemResource.

        Args:
            path: Path to the resource on the device
            device: Device instance this resource belongs to
        """
        self.path = path
        self._device = device
        self.name = os.path.basename(path) or path
        self.pretty_path = path

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the resource to a dictionary representation.

        Returns:
            Dict with resource information
        """
        return {"name": self.name, "path": self.path, "pretty_path": self.pretty_path, "resource_type": "filesystem"}


class DirectoryResource(FileSystemResource):
    """Directory resource on a device."""

    async def list_contents(self) -> list[Union["DirectoryResource", "FileResource"]]:
        """
        List the contents of the directory.

        Returns:
            List of FileResource and DirectoryResource objects
        """
        # Get the directory listing from the device
        directory_listing = await self._device.list_directory(self.path)

        logger.debug("Parsing directory listing: %s", directory_listing)

        # Parse entries from the ls -la output
        entries: list[dict[str, str]] = []

        # Parse the text format (ls -la output)
        for line in directory_listing.splitlines():
            if not line.strip() or line.startswith("total "):
                continue

            # Parse ls -la output format
            parts = line.split()
            if len(parts) >= 8:
                permissions = parts[0]
                size = parts[4]
                name = " ".join(parts[8:])

                # Skip . and .. entries
                if name in [".", ".."]:
                    continue

                entry_type = "directory" if permissions.startswith("d") else "file"

                entries.append({"name": name, "type": entry_type, "size": size, "permissions": permissions})

        results: list[DirectoryResource | FileResource] = []

        # Create resource objects for each entry
        for entry in entries:
            entry_name = entry.get("name", "")

            # Skip . and .. entries
            if entry_name in [".", ".."]:
                continue

            if not entry_name:
                continue

            entry_path = os.path.join(self.path, entry_name)

            if entry.get("type") == "directory":
                dir_resource = DirectoryResource(entry_path, device=self._device)
                results.append(dir_resource)
            else:
                file_resource = FileResource(
                    entry_path,
                    device=self._device,
                    metadata={"size": entry.get("size", "0"), "permissions": entry.get("permissions", "")},
                )
                results.append(file_resource)

        return results

    async def create_subdirectory(self, name: str) -> "DirectoryResource":
        """
        Create a subdirectory within this directory.

        Args:
            name: Name of the subdirectory to create

        Returns:
            DirectoryResource for the new subdirectory
        """
        path = os.path.join(self.path, name)
        await self._device.create_directory(path)
        return DirectoryResource(path, device=self._device)

    async def to_dict_with_contents(self) -> dict[str, Any]:
        """
        Convert the directory and its contents to a dictionary.

        Returns:
            Dict with directory information and contents
        """
        base_dict = self.to_dict()
        base_dict["resource_type"] = "directory"

        contents = await self.list_contents()
        base_dict["contents"] = [res.to_dict() for res in contents]

        return base_dict


class FileResource(FileSystemResource):
    """File resource on a device."""

    def __init__(self, path: str, device: Device, metadata: dict[str, str] | None = None) -> None:
        """
        Initialize a FileResource.

        Args:
            path: Path to the file on the device
            device: Device instance this resource belongs to
            metadata: Optional metadata about the file
        """
        super().__init__(path, device)
        self.metadata = metadata or {}

    async def read_content(self) -> str:
        """
        Read the content of the file.

        Returns:
            File content as a string
        """
        return await self._device.read_file(self.path)

    async def exists(self) -> bool:
        """
        Check if the file exists.

        Returns:
            True if the file exists, False otherwise
        """
        return await self._device.file_exists(self.path)

    async def delete(self) -> bool:
        """
        Delete the file.

        Returns:
            True if deletion was successful
        """
        await self._device.delete_file(self.path)
        return True

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the file to a dictionary representation.

        Returns:
            Dict with file information
        """
        base_dict = super().to_dict()
        base_dict["resource_type"] = "file"
        base_dict["metadata"] = self.metadata
        return base_dict

    @classmethod
    def create_from_entry(cls, parent_path: str, entry: dict[str, str], device: Device) -> "FileResource":
        """
        Create a FileResource from a directory entry.

        Args:
            parent_path: Path of the parent directory
            entry: Directory entry information
            device: Device instance

        Returns:
            FileResource instance
        """
        path = os.path.join(parent_path, entry["name"])
        metadata = {"size": entry.get("size", "0"), "permissions": entry.get("permissions", "")}
        return cls(path, device=device, metadata=metadata)


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to a human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

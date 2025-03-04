"""Tests for the file system resources module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from droidmind.devices import Device
from droidmind.filesystem import (
    DirectoryResource,
    FileResource,
    FileSystemResource,
)


class TestFileSystemResource:
    """Tests for the FileSystemResource base class."""

    @pytest.fixture
    def resource(self):
        """Create a FileSystemResource instance with a mocked device."""
        # Create a mock Device
        mock_device = AsyncMock(spec=Device)
        mock_device.serial = "device1"

        # Create the resource
        resource = FileSystemResource("/sdcard/path", device=mock_device)

        return resource

    def test_initialization(self, resource):
        """Test initialization of the FileSystemResource."""
        assert resource.path == "/sdcard/path"
        assert resource._device.serial == "device1"
        assert resource.name == "path"
        assert resource.pretty_path == "/sdcard/path"

    def test_to_dict(self, resource):
        """Test the to_dict method."""
        # Call the method
        result = resource.to_dict()

        # Verify the result
        assert result["name"] == "path"
        assert result["path"] == "/sdcard/path"
        assert result["pretty_path"] == "/sdcard/path"
        assert result["resource_type"] == "filesystem"


@pytest.mark.asyncio
class TestDirectoryResource:
    """Tests for the DirectoryResource class."""

    @pytest.fixture
    async def directory_resource(self):
        """Create a DirectoryResource instance with a mocked device."""
        # Create a mock Device
        mock_device = AsyncMock(spec=Device)
        mock_device.serial = "device1"

        # Mock the list_directory method
        mock_device.list_directory = AsyncMock(
            return_value="""total 16
drwxr-xr-x 4 root root 4096 Jan 1 12:00 .
drwxr-xr-x 4 root root 4096 Jan 1 12:00 ..
-rw-r--r-- 1 root root 1024 Jan 1 12:00 file.txt
drwxr-xr-x 2 root root 4096 Jan 1 12:00 folder"""
        )

        mock_device.create_directory = AsyncMock(return_value=True)

        # Create the resource
        directory = DirectoryResource("/sdcard/dir", device=mock_device)

        return directory

    async def test_list_contents(self, directory_resource):
        """Test listing directory contents."""
        # Call the method
        contents = await directory_resource.list_contents()

        # Verify the result
        assert len(contents) == 2  # Should not include . and ..

        # Check for both file and directory resources
        file_found = False
        dir_found = False

        for resource in contents:
            if isinstance(resource, FileResource) and resource.name == "file.txt":
                file_found = True
            elif isinstance(resource, DirectoryResource) and resource.name == "folder":
                dir_found = True

        assert file_found
        assert dir_found

        # Verify that the device's list_directory method was called
        directory_resource._device.list_directory.assert_called_once_with("/sdcard/dir")

    async def test_create_subdirectory(self, directory_resource):
        """Test creating a subdirectory."""
        # Call the method
        result = await directory_resource.create_subdirectory("new_folder")

        # Verify the result
        assert isinstance(result, DirectoryResource)
        assert result.path == "/sdcard/dir/new_folder"

        # Verify that the device's create_directory method was called
        directory_resource._device.create_directory.assert_called_once_with("/sdcard/dir/new_folder")

    async def test_to_dict_with_contents(self, directory_resource):
        """Test the to_dict method with contents."""
        # Call the method
        result = await directory_resource.to_dict_with_contents()

        # Verify the result
        assert result["name"] == "dir"
        assert result["path"] == "/sdcard/dir"
        assert result["resource_type"] == "directory"
        assert "contents" in result
        assert len(result["contents"]) == 2  # Should not include . and ..


@pytest.mark.asyncio
class TestFileResource:
    """Tests for the FileResource class."""

    @pytest.fixture
    async def file_resource(self):
        """Create a FileResource instance with a mocked device."""
        # Create a mock Device
        mock_device = AsyncMock(spec=Device)
        mock_device.serial = "device1"

        # Mock the file methods
        mock_device.read_file = AsyncMock(return_value="This is the file content")
        mock_device.file_exists = AsyncMock(return_value=True)
        mock_device.delete_file = AsyncMock(return_value=True)

        # Create the resource
        file = FileResource(
            "/sdcard/file.txt", device=mock_device, metadata={"size": "1024", "permissions": "-rw-r--r--"}
        )

        return file

    async def test_read_content(self, file_resource):
        """Test reading file content."""
        # Call the method
        content = await file_resource.read_content()

        # Verify the result
        assert content == "This is the file content"

        # Verify that the device's read_file method was called
        file_resource._device.read_file.assert_called_once_with("/sdcard/file.txt")

    async def test_exists(self, file_resource):
        """Test checking if a file exists."""
        # Call the method
        exists = await file_resource.exists()

        # Verify the result
        assert exists is True

        # Verify that the device's file_exists method was called
        file_resource._device.file_exists.assert_called_once_with("/sdcard/file.txt")

    async def test_delete(self, file_resource):
        """Test deleting a file."""
        # Call the method
        result = await file_resource.delete()

        # Verify the result
        assert result is True

        # Verify that the device's delete_file method was called
        file_resource._device.delete_file.assert_called_once_with("/sdcard/file.txt")

    async def test_to_dict(self, file_resource):
        """Test the to_dict method."""
        # Call the method
        result = file_resource.to_dict()

        # Verify the result
        assert result["name"] == "file.txt"
        assert result["path"] == "/sdcard/file.txt"
        assert result["resource_type"] == "file"
        assert result["metadata"]["size"] == "1024"
        assert result["metadata"]["permissions"] == "-rw-r--r--"

    async def test_create_from_entry(self):
        """Test creating a FileResource from a directory entry."""
        # Create a mock Device
        mock_device = MagicMock(spec=Device)
        mock_device.serial = "device1"

        # Create a directory entry
        entry = {"name": "test.txt", "type": "file", "size": "2048", "permissions": "-rw-r--r--"}

        # Create the resource
        file = FileResource.create_from_entry(parent_path="/sdcard", entry=entry, device=mock_device)

        # Verify the result
        assert file.path == "/sdcard/test.txt"
        assert file.name == "test.txt"
        assert file.metadata["size"] == "2048"
        assert file.metadata["permissions"] == "-rw-r--r--"

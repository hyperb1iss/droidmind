"""Tests for the file system tools module."""

import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from droidmind.devices import Device
from droidmind.tools import (
    create_directory,
    delete_file,
    file_exists,
    list_directory,
    pull_file,
    push_file,
    read_file,
)


@pytest.mark.asyncio
class TestFileTools:
    """Tests for file system tools."""

    @pytest.fixture
    async def mock_device(self):
        """Create a mocked Device instance."""
        with patch("droidmind.devices.Device"):
            # Set up the mock device
            mock_device = AsyncMock(spec=Device)
            mock_device.serial = "device1"

            # Mock all the file operation methods
            mock_device.push_file = AsyncMock(return_value="1 file pushed")
            mock_device.pull_file = AsyncMock(return_value="1 file pulled")
            mock_device.read_file = AsyncMock(return_value="File content")
            mock_device.run_shell = AsyncMock(
                side_effect=lambda cmd: "exists" if "[ -f" in cmd else "1024" if "wc -c" in cmd else ""
            )
            mock_device.list_directory = AsyncMock(
                return_value="""total 16
drwxr-xr-x 4 root root 4096 Jan 1 12:00 .
drwxr-xr-x 4 root root 4096 Jan 1 12:00 ..
-rw-r--r-- 1 root root 1024 Jan 1 12:00 file.txt
drwxr-xr-x 2 root root 4096 Jan 1 12:00 folder"""
            )
            mock_device.create_directory = AsyncMock(return_value="Successfully created directory /sdcard/new_folder")
            mock_device.delete_file = AsyncMock(return_value="Successfully deleted /sdcard/file.txt")
            mock_device.file_exists = AsyncMock(return_value=True)

            # Set up the get_device_manager().get_device() chain to return our mock
            with patch("droidmind.tools.get_device_manager") as mock_get_manager:
                mock_manager = AsyncMock()
                mock_manager.get_device = AsyncMock(return_value=mock_device)
                mock_get_manager.return_value = mock_manager

                yield mock_device

    async def test_push_file(self, mock_device):
        """Test the push_file tool."""
        # Create a temporary file to push
        with tempfile.NamedTemporaryFile() as temp_file:
            # Call the tool
            result = await push_file(
                serial="device1", local_path=temp_file.name, device_path="/sdcard/file.txt", ctx=None
            )

            # Verify the result
            assert "success" in result.lower()
            assert "1 file pushed" in result

            # Check that the device's push_file method was called
            mock_device.push_file.assert_called_once_with(temp_file.name, "/sdcard/file.txt")

    async def test_pull_file(self, mock_device):
        """Test the pull_file tool."""
        # Create a temporary file to receive the pulled file
        with tempfile.NamedTemporaryFile() as temp_file:
            # Call the tool
            result = await pull_file(
                serial="device1", device_path="/sdcard/file.txt", local_path=temp_file.name, ctx=None
            )

            # Verify the result
            assert "success" in result.lower()
            assert "1 file pulled" in result

            # Check that the device's pull_file method was called
            mock_device.pull_file.assert_called_once_with("/sdcard/file.txt", temp_file.name)

    async def test_read_file(self, mock_device):
        """Test the read_file tool."""
        # Call the tool
        result = await read_file(serial="device1", device_path="/sdcard/file.txt", ctx=None)

        # Verify the result contains the file content
        assert "File content" in result

        # Check that the device's read_file method was called
        mock_device.read_file.assert_called_once_with("/sdcard/file.txt", 100000)

    async def test_list_directory(self, mock_device):
        """Test the list_directory tool."""
        # Call the tool
        result = await list_directory(serial="device1", path="/sdcard", ctx=None)

        # Verify the result
        assert "file.txt" in result
        assert "folder" in result

        # Check that the device's list_directory method was called
        mock_device.list_directory.assert_called_once_with("/sdcard")

    async def test_create_directory(self, mock_device):
        """Test the create_directory tool."""
        # Call the tool
        result = await create_directory(serial="device1", path="/sdcard/new_folder", ctx=None)

        # Verify the result
        assert "success" in result.lower()

        # Check that the device's create_directory method was called
        mock_device.create_directory.assert_called_once_with("/sdcard/new_folder")

    async def test_delete_file(self, mock_device):
        """Test the delete_file tool."""
        # Call the tool
        result = await delete_file(serial="device1", path="/sdcard/file.txt", ctx=None)

        # Verify the result
        assert "success" in result.lower()

        # Check that the device's delete_file method was called
        mock_device.delete_file.assert_called_once_with("/sdcard/file.txt")

    async def test_file_exists(self, mock_device):
        """Test the file_exists tool."""
        # Set up the mock to return True
        mock_device.file_exists.return_value = True

        # Call the tool
        result = await file_exists(serial="device1", path="/sdcard/file.txt", ctx=None)

        # Verify the result
        assert result is True

        # Check that the device's file_exists method was called
        mock_device.file_exists.assert_called_once_with("/sdcard/file.txt")

        # Reset the mock
        mock_device.file_exists.reset_mock()
        mock_device.file_exists.return_value = False

        # Call the tool again with a non-existent file
        result = await file_exists(serial="device1", path="/sdcard/nonexistent.txt", ctx=None)

        # Verify the result
        assert result is False

        # Check that the device's file_exists method was called
        mock_device.file_exists.assert_called_once_with("/sdcard/nonexistent.txt")

    async def test_device_not_found(self):
        """Test tool behavior when device is not found."""
        # Set up the get_device method to return None
        from droidmind.tools import get_device_manager

        get_device_manager().get_device = AsyncMock(return_value=None)

        # Call the push_file tool
        with pytest.raises(ValueError, match="Device device1 not found"):
            await push_file(
                serial="device1", local_path="/local/path/file.txt", device_path="/sdcard/file.txt", ctx=None
            )

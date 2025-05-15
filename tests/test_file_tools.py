"""Tests for the file system tools module."""

import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from droidmind.devices import Device
from droidmind.tools import file_operations
from droidmind.tools.file_operations import FileAction  # Import the enum for actions


@pytest.mark.asyncio
class TestFileTools:
    """Tests for the file system tools."""

    @pytest.fixture
    async def mock_device(self):
        """Create a mock device for testing."""
        mock_device = AsyncMock(spec=Device)
        mock_device.serial = "device1"

        # Set up the push_file method
        mock_device.push_file = AsyncMock(return_value="1 file pushed")

        # Set up the pull_file method
        mock_device.pull_file = AsyncMock(return_value="1 file pulled")

        # Set up the read_file method
        mock_device.read_file = AsyncMock(return_value="file contents")

        # Set up the list_directory method
        mock_device.list_directory = AsyncMock(
            return_value="""total 8
drwxr-xr-x 4 root root 4096 Jan 1 12:00 .
drwxr-xr-x 4 root root 4096 Jan 1 12:00 ..
-rw-r--r-- 1 root root 1024 Jan 1 12:00 test.txt
drwxr-xr-x 2 root root 4096 Jan 1 12:00 test_dir"""
        )

        # Set up the create_directory method
        mock_device.create_directory = AsyncMock(return_value="Directory created")

        # Set up the delete_file method
        mock_device.delete_file = AsyncMock(return_value="File deleted")

        # Set up the file_exists method
        mock_device.file_exists = AsyncMock(return_value=True)

        # Set up the run_shell method for file existence check
        mock_device.run_shell = AsyncMock(side_effect=lambda cmd, *args, **kwargs: "exists" if "[ -f" in cmd else "")

        # Set up the get_device_manager().get_device() chain to return our mock
        with patch("droidmind.tools.file_operations.get_device_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.get_device = AsyncMock(return_value=mock_device)
            mock_get_manager.return_value = mock_manager

            yield mock_device

    async def test_push_file(self, mock_device):
        """Test the push_file action."""
        # Create a temporary file to push
        with tempfile.NamedTemporaryFile() as temp_file:
            # Call the tool with push_file action
            result = await file_operations(
                serial="device1",
                action=FileAction.PUSH_FILE,
                local_path=temp_file.name,
                device_path="/sdcard/file.txt",
                ctx=None,
            )

            # Verify the result
            assert "success" in result.lower()
            assert "1 file pushed" in result

    async def test_pull_file(self, mock_device):
        """Test the pull_file action."""
        # Create a temporary file to pull to
        with tempfile.NamedTemporaryFile() as temp_file:
            # Call the tool with pull_file action
            result = await file_operations(
                serial="device1",
                action=FileAction.PULL_FILE,
                device_path="/sdcard/file.txt",
                local_path=temp_file.name,
                ctx=None,
            )

            # Verify the result
            assert "success" in result.lower()
            assert "1 file pulled" in result

    async def test_read_file(self, mock_device):
        """Test the read_file action."""
        # Call the tool with read_file action
        result = await file_operations(
            serial="device1", action=FileAction.READ_FILE, device_path="/sdcard/file.txt", ctx=None
        )

        # Verify the result
        assert "file contents" in result.lower()

    async def test_list_directory(self, mock_device):
        """Test the list_directory action."""
        # Call the tool with list_directory action
        result = await file_operations(serial="device1", action=FileAction.LIST_DIRECTORY, path="/sdcard", ctx=None)

        # Verify the result
        assert "directory" in result.lower()

    async def test_create_directory(self, mock_device):
        """Test the create_directory action."""
        # Call the tool with create_directory action
        result = await file_operations(
            serial="device1", action=FileAction.CREATE_DIRECTORY, path="/sdcard/test", ctx=None
        )

        # Verify the result
        assert "directory created" in result.lower()

    async def test_delete_file(self, mock_device):
        """Test the delete_file action."""
        # Call the tool with delete_file action
        result = await file_operations(
            serial="device1", action=FileAction.DELETE_FILE, path="/sdcard/file.txt", ctx=None
        )

        # Verify the result
        assert "file deleted" in result.lower()

    async def test_file_exists(self, mock_device):
        """Test the file_exists action."""
        # Call the tool with file_exists action
        result = await file_operations(
            serial="device1", action=FileAction.FILE_EXISTS, path="/sdcard/file.txt", ctx=None
        )

        # Verify the result
        assert result is True

        # Test with a non-existent file
        mock_device.file_exists.return_value = False
        result = await file_operations(
            serial="device1", action=FileAction.FILE_EXISTS, path="/sdcard/nonexistent.txt", ctx=None
        )

        # Verify the result
        assert result is False

    @patch("droidmind.tools.file_operations.get_device_manager")
    async def test_device_not_found(self, mock_get_manager):
        """Test handling of device not found."""
        # Set up the mock to return None for get_device
        mock_manager = AsyncMock()
        mock_manager.get_device = AsyncMock(return_value=None)
        mock_get_manager.return_value = mock_manager

        # Test with a non-existent device
        result = await file_operations(
            serial="nonexistent", action=FileAction.FILE_EXISTS, path="/sdcard/file.txt", ctx=None
        )

        # Verify the result
        assert result is False

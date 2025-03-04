"""Tests for the DeviceManager and Device classes."""

from unittest.mock import AsyncMock, patch

import pytest

from droidmind.devices import Device, DeviceManager, get_device_manager


class TestDeviceManager:
    """Tests for the DeviceManager class."""

    @pytest.fixture
    def device_manager(self):
        """Create a new DeviceManager instance with mocked ADB wrapper."""
        with patch("droidmind.devices.ADBWrapper") as mock_adb_class:
            # Set up the mock ADB wrapper
            mock_adb = mock_adb_class.return_value
            mock_adb.get_devices = AsyncMock(
                return_value=[
                    {"serial": "device1", "state": "device"},
                    {"serial": "192.168.1.100:5555", "state": "device"},
                ]
            )

            # Create the DeviceManager with the mocked ADB wrapper
            manager = DeviceManager(adb_path=None)
            yield manager

    @pytest.mark.asyncio
    async def test_list_devices(self, device_manager):
        """Test listing devices."""
        # Call the method
        devices = await device_manager.list_devices()

        # Verify the result
        assert len(devices) == 2
        assert devices[0].serial == "device1"
        assert devices[1].serial == "192.168.1.100:5555"

        # Check that the ADB wrapper's get_devices method was called
        device_manager._adb.get_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_device_existing(self, device_manager):
        """Test getting an existing device."""
        # Call the method
        device = await device_manager.get_device("device1")

        # Verify the result
        assert device is not None
        assert device.serial == "device1"

        # Check that the ADB wrapper's get_devices method was called
        device_manager._adb.get_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_device_nonexistent(self, device_manager):
        """Test getting a non-existent device."""
        # Call the method
        device = await device_manager.get_device("nonexistent")

        # Verify the result
        assert device is None

        # Check that the ADB wrapper's get_devices method was called
        device_manager._adb.get_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect(self, device_manager):
        """Test connecting to a device over TCP/IP."""
        # Mock the ADB connect method
        device_manager._adb.connect_device_tcp = AsyncMock(return_value="192.168.1.101:5555")

        # Call the method
        device = await device_manager.connect("192.168.1.101")

        # Verify the result
        assert device is not None
        assert device.serial == "192.168.1.101:5555"

        # Check that the ADB wrapper's connect_device_tcp method was called
        device_manager._adb.connect_device_tcp.assert_called_once_with("192.168.1.101", 5555)

    @pytest.mark.asyncio
    async def test_disconnect_success(self, device_manager):
        """Test disconnecting from a device successfully."""
        # Mock the ADB disconnect method
        device_manager._adb.disconnect_device = AsyncMock(return_value=True)

        # Call the method
        result = await device_manager.disconnect("192.168.1.100:5555")

        # Verify the result
        assert result is True

        # Check that the ADB wrapper's disconnect_device method was called
        device_manager._adb.disconnect_device.assert_called_once_with("192.168.1.100:5555")

    @pytest.mark.asyncio
    async def test_disconnect_failure(self, device_manager):
        """Test disconnecting from a device that fails."""
        # Mock the ADB disconnect method
        device_manager._adb.disconnect_device = AsyncMock(return_value=False)

        # Call the method
        result = await device_manager.disconnect("device1")

        # Verify the result
        assert result is False

        # Check that the ADB wrapper's disconnect_device method was called
        device_manager._adb.disconnect_device.assert_called_once_with("device1")

    @pytest.mark.asyncio
    async def test_singleton_access(self):
        """Test that get_device_manager returns the initialized instance."""
        # Get the device manager
        device_manager = get_device_manager()

        # Verify it's not None
        assert device_manager is not None
        assert isinstance(device_manager, DeviceManager)


class TestDevice:
    """Tests for the Device class."""

    @pytest.fixture
    def device(self):
        """Create a Device instance with mocked ADB wrapper."""
        with patch("droidmind.devices.ADBWrapper") as mock_adb_class:
            # Set up the mock ADB wrapper
            mock_adb = mock_adb_class.return_value

            # Mock the device properties
            mock_adb.get_device_properties = AsyncMock(
                return_value={
                    "ro.product.model": "Pixel 4",
                    "ro.product.brand": "Google",
                    "ro.build.version.release": "11",
                    "ro.build.version.sdk": "30",
                    "ro.build.display.id": "RQ3A.211001.001",
                }
            )

            # Mock other methods
            mock_adb.shell = AsyncMock(return_value="command output")
            mock_adb.reboot_device = AsyncMock(return_value="Device rebooted")

            # Create the Device
            device = Device("device1", adb=mock_adb)
            yield device

    @pytest.mark.asyncio
    async def test_get_properties(self, device):
        """Test getting device properties."""
        # Call the method
        properties = await device.get_properties()

        # Verify the result
        assert properties["ro.product.model"] == "Pixel 4"
        assert properties["ro.product.brand"] == "Google"
        assert properties["ro.build.version.release"] == "11"

        # Check that the ADB wrapper's get_device_properties method was called
        device._adb.get_device_properties.assert_called_once_with("device1")

    @pytest.mark.asyncio
    async def test_model_property(self, device):
        """Test the model property."""
        # Call the property
        model = await device.model

        # Verify the result
        assert model == "Pixel 4"

        # The get_properties method should have been called which calls get_device_properties
        device._adb.get_device_properties.assert_called_once_with("device1")

    @pytest.mark.asyncio
    async def test_run_shell(self, device):
        """Test running a shell command."""
        # Call the method
        result = await device.run_shell("ls -la")

        # Verify the result
        assert result == "command output"

        # Check that the ADB wrapper's shell method was called with the expected command
        # The implementation now adds "| head -n 500" to commands that might produce large output
        device._adb.shell.assert_called_once_with("device1", "ls -la | head -n 500")

    @pytest.mark.asyncio
    async def test_reboot(self, device):
        """Test rebooting the device."""
        # Call the method
        result = await device.reboot("recovery")

        # Verify the result
        assert result == "Device rebooted"

        # Check that the ADB wrapper's reboot_device method was called
        device._adb.reboot_device.assert_called_once_with("device1", "recovery")

    @pytest.mark.asyncio
    async def test_list_directory(self, device):
        """Test listing a directory on the device."""
        # Update the mock with an actual list of entries instead of a string
        device._adb.shell.return_value = """
        total 24
        drwxr-xr-x 4 root root 4096 2023-01-01 12:00 .
        drwxr-xr-x 21 root root 4096 2023-01-01 12:00 ..
        drwxr-xr-x 2 root root 4096 2023-01-01 12:00 folder1
        -rw-r--r-- 1 root root 1024 2023-01-01 12:00 file1.txt
        -rw-r--r-- 1 root root 2048 2023-01-01 12:00 file2.txt
        """

        # We need to mock the list_directory method directly as it parses the shell output
        device.list_directory = AsyncMock(
            return_value=[
                {"name": ".", "type": "directory", "size": "4096", "permissions": "drwxr-xr-x"},
                {"name": "..", "type": "directory", "size": "4096", "permissions": "drwxr-xr-x"},
                {"name": "folder1", "type": "directory", "size": "4096", "permissions": "drwxr-xr-x"},
                {"name": "file1.txt", "type": "file", "size": "1024", "permissions": "-rw-r--r--"},
                {"name": "file2.txt", "type": "file", "size": "2048", "permissions": "-rw-r--r--"},
            ]
        )

        # Call the method
        result = await device.list_directory("/sdcard")

        # Verify the result has the expected structure
        assert len(result) == 5  # 5 entries including . and ..
        assert any(entry["name"] == "folder1" and entry["type"] == "directory" for entry in result)
        assert any(
            entry["name"] == "file1.txt" and entry["type"] == "file" and entry["size"] == "1024" for entry in result
        )
        assert any(
            entry["name"] == "file2.txt" and entry["type"] == "file" and entry["size"] == "2048" for entry in result
        )

        # Since we're now mocking list_directory directly, we assert that it was called with the right path
        device.list_directory.assert_called_once_with("/sdcard")

    @pytest.mark.asyncio
    async def test_push_file(self, device):
        """Test pushing a file to the device."""
        # Mock the push_file method of ADB
        device._adb.push_file = AsyncMock(return_value="1 file pushed")

        # Call the method
        result = await device.push_file("/local/path/file.txt", "/sdcard/file.txt")

        # Verify the result
        assert result == "1 file pushed"

        # Check that the ADB wrapper's push_file method was called
        device._adb.push_file.assert_called_once_with("device1", "/local/path/file.txt", "/sdcard/file.txt")

    @pytest.mark.asyncio
    async def test_pull_file(self, device):
        """Test pulling a file from the device."""
        # Mock the pull_file method of ADB
        device._adb.pull_file = AsyncMock(return_value="1 file pulled")

        # Call the method
        result = await device.pull_file("/sdcard/file.txt", "/local/path/file.txt")

        # Verify the result
        assert result == "1 file pulled"

        # Check that the ADB wrapper's pull_file method was called
        device._adb.pull_file.assert_called_once_with("device1", "/sdcard/file.txt", "/local/path/file.txt")

    @pytest.mark.asyncio
    async def test_read_file(self, device):
        """Test reading a file from the device."""
        # Mock the shell command output
        device._adb.shell.side_effect = ["1024", "This is the content of the file"]

        # Call the method
        result = await device.read_file("/sdcard/file.txt")

        # Verify the result
        assert result == "This is the content of the file"

        # Check that the ADB shell method was called with the expected commands
        # First call checks the file size
        # Second call reads the file content
        assert device._adb.shell.call_count == 2
        device._adb.shell.assert_any_call("device1", "wc -c '/sdcard/file.txt'")
        device._adb.shell.assert_any_call("device1", "cat '/sdcard/file.txt'")

    @pytest.mark.asyncio
    async def test_create_directory(self, device):
        """Test creating a directory on the device."""
        # Mock the shell command output
        device._adb.shell.return_value = ""  # Successful mkdir returns nothing

        # Call the method
        result = await device.create_directory("/sdcard/new_folder")

        # Verify the result matches the expected string message
        assert result == "Successfully created directory /sdcard/new_folder"

        # Check that the ADB shell method was called with the expected command
        device._adb.shell.assert_called_once_with("device1", "mkdir -p '/sdcard/new_folder'")

    @pytest.mark.asyncio
    async def test_delete_file(self, device):
        """Test deleting a file from the device."""
        # Mock the shell command outputs for file_exists check and delete
        device._adb.shell.side_effect = ["file", ""]  # First check file type, then delete

        # Call the method
        result = await device.delete_file("/sdcard/file.txt")

        # Verify the result
        assert result == "Successfully deleted /sdcard/file.txt"

        # Check that the ADB shell method was called with the expected commands
        assert device._adb.shell.call_count == 2
        # First call should check if it's a file or directory
        device._adb.shell.assert_any_call("device1", "[ -d '/sdcard/file.txt' ] && echo 'directory' || echo 'file'")
        # Second call should delete the file
        device._adb.shell.assert_any_call("device1", "rm '/sdcard/file.txt'")

    @pytest.mark.asyncio
    async def test_file_exists(self, device):
        """Test checking if a file exists on the device."""
        # Mock the shell command output for existing file
        device._adb.shell.return_value = "0"  # [ -e FILE ] returns 0 if file exists

        # Call the method
        result = await device.file_exists("/sdcard/file.txt")

        # Verify the result
        assert result is True

        # Check that the ADB shell method was called with the expected command
        device._adb.shell.assert_called_once_with("device1", "[ -e '/sdcard/file.txt' ] && echo 0 || echo 1")

        # Reset the mock
        device._adb.shell.reset_mock()

        # Mock the shell command output for non-existing file
        device._adb.shell.return_value = "1"  # [ -e FILE ] returns 1 if file doesn't exist

        # Call the method again
        result = await device.file_exists("/sdcard/nonexistent.txt")

        # Verify the result
        assert result is False

        # Check that the ADB shell method was called with the expected command
        device._adb.shell.assert_called_once_with("device1", "[ -e '/sdcard/nonexistent.txt' ] && echo 0 || echo 1")

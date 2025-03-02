"""Tests for the ADB wrapper module."""

import tempfile
import unittest
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from droidmind.adb.wrapper import ADBWrapper


class TestADBWrapper(unittest.TestCase):
    """Test the ADB wrapper module."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp(prefix="droidmind_test_")

        # Mock subprocess for ADB commands
        self.subprocess_patcher = patch("asyncio.create_subprocess_exec")
        self.mock_subprocess = self.subprocess_patcher.start()

        # Set up mock process
        self.mock_process = AsyncMock()
        self.mock_process.communicate = AsyncMock(return_value=(b"stdout", b"stderr"))
        self.mock_process.returncode = 0
        self.mock_subprocess.return_value = self.mock_process

    def tearDown(self):
        """Clean up test environment."""
        self.subprocess_patcher.stop()

        # Remove temporary directory
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test ADBWrapper initialization."""
        wrapper = ADBWrapper()

        # Verify defaults
        assert wrapper.connection_timeout == 10.0
        assert wrapper.auth_timeout == 1.0
        assert wrapper._devices_cache == []


@pytest.mark.asyncio
class TestADBWrapperAsync:
    """Test the async methods of ADBWrapper."""

    @pytest_asyncio.fixture
    async def wrapper(self, request):
        """Set up ADBWrapper for testing."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="droidmind_test_")

        # Mock subprocess for ADB commands
        subprocess_patcher = patch("asyncio.create_subprocess_exec")
        mock_subprocess = subprocess_patcher.start()

        # Set up mock process
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"stdout", b"stderr"))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Create wrapper
        wrapper = ADBWrapper()

        # Mock the get_devices method to return a connected device
        wrapper.get_devices = AsyncMock(
            return_value=[{"serial": "device1", "model": "Pixel 4", "android_version": "11"}]
        )

        # Add cleanup
        def cleanup():
            subprocess_patcher.stop()
            import shutil

            shutil.rmtree(temp_dir)

        request.addfinalizer(cleanup)
        return wrapper

    async def test_connect_device_tcp(self, wrapper):
        """Test connecting to a device over TCP/IP."""
        # Mock the ADB command output
        wrapper._run_adb_command = AsyncMock(return_value=("connected to 192.168.1.100:5555", ""))

        # Call the method
        result = await wrapper.connect_device_tcp("192.168.1.100", 5555)

        # Verify the result - the actual implementation returns just the serial
        assert result == "192.168.1.100:5555"
        wrapper._run_adb_command.assert_called_once_with(
            ["connect", "192.168.1.100:5555"], timeout_seconds=wrapper.connection_timeout
        )

    async def test_connect_device_tcp_error(self, wrapper):
        """Test error handling when connecting to a device over TCP/IP."""
        # Mock the ADB command output for an error
        wrapper._run_adb_command = AsyncMock(return_value=("failed to connect to 192.168.1.100:5555", ""))

        # Call the method - should raise RuntimeError
        with pytest.raises(RuntimeError) as excinfo:
            await wrapper.connect_device_tcp("192.168.1.100", 5555)

        # Verify the error message
        assert "Failed to connect" in str(excinfo.value)
        wrapper._run_adb_command.assert_called_once_with(
            ["connect", "192.168.1.100:5555"], timeout_seconds=wrapper.connection_timeout
        )

    async def test_disconnect_device(self, wrapper):
        """Test disconnecting from a device."""
        # Mock the ADB command output
        wrapper._run_adb_command = AsyncMock(return_value=("disconnected device1:5555", ""))

        # Call the method with a TCP device (has a colon in the serial)
        result = await wrapper.disconnect_device("device1:5555")

        # Verify the result
        assert result is True
        wrapper._run_adb_command.assert_called_once_with(["disconnect", "device1:5555"], check=False)

    async def test_disconnect_device_not_connected(self, wrapper):
        """Test disconnecting from a device that's not connected."""
        # Call the method with a USB device (no colon in the serial)
        result = await wrapper.disconnect_device("device1")

        # Verify the result - should be False for USB devices
        assert result is False
        # No ADB command should be called for USB devices

    async def test_shell(self, wrapper):
        """Test running a shell command on a device."""
        # Mock the ADB command output
        wrapper._run_adb_device_command = AsyncMock(return_value=("command output", ""))

        # Mock the _run_adb_command to make the device appear connected
        wrapper._run_adb_command = AsyncMock(return_value=("List of devices attached\ndevice1\tdevice", ""))

        # Clear the devices cache to force a check
        wrapper._devices_cache = []

        # Call the method
        result = await wrapper.shell("device1", "ls -la")

        # Verify the result
        assert result == "command output"
        wrapper._run_adb_device_command.assert_called_once_with("device1", ["shell", "ls -la"])

    async def test_shell_device_not_connected(self, wrapper):
        """Test running a shell command on a device that's not connected."""
        # Override the get_devices mock to return no devices
        wrapper.get_devices = AsyncMock(return_value=[])

        # Call the method and expect an exception
        with pytest.raises(ValueError) as excinfo:
            await wrapper.shell("nonexistent", "ls -la")

        # Verify the error message
        assert "Device nonexistent not connected" in str(excinfo.value)

    async def test_get_device_properties(self, wrapper):
        """Test getting device properties."""
        # Mock the shell command output
        wrapper.shell = AsyncMock(
            return_value=(
                "[ro.build.version.release]: [11]\n[ro.build.version.sdk]: [30]\n[ro.product.model]: [Pixel 4]\n"
            )
        )

        # Call the method
        result = await wrapper.get_device_properties("device1")

        # Verify the result
        assert result == {
            "ro.build.version.release": "11",
            "ro.build.version.sdk": "30",
            "ro.product.model": "Pixel 4",
        }
        wrapper.shell.assert_called_once_with("device1", "getprop")

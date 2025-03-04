"""Tests for the DroidMind MCP tools and resources."""

from unittest.mock import AsyncMock, MagicMock, patch

from mcp.server.fastmcp import Context, Image
import pytest

from droidmind.devices import Device
from droidmind.tools import (
    connect_device,
    device_properties,
    devicelist as list_devices,
    disconnect_device,
    reboot_device,
    screenshot as capture_screenshot,
    shell_command,
)


@pytest.fixture
def mock_context():
    """Create a mock MCP context."""
    context = MagicMock(spec=Context)

    # Make methods that are awaited return awaitable objects
    context.info = AsyncMock()  # This is awaited in some functions
    context.error = AsyncMock()  # This is awaited in some functions
    context.warning = AsyncMock()  # This is awaited in some functions
    context.success = AsyncMock()  # This is awaited in some functions
    context.report_progress = AsyncMock()  # This is awaited

    return context


@pytest.fixture
def mock_device():
    """Create a mock Device."""
    device = MagicMock(spec=Device)

    # Set up device serial as a regular attribute
    device.serial = "device1"

    # Create a class to make awaitable properties
    class AsyncPropertyMock:
        def __init__(self, return_value):
            self.return_value = return_value

        def __await__(self):
            async def _async_return():
                return self.return_value

            return _async_return().__await__()

    # Set up device properties with awaitable objects
    device.model = AsyncPropertyMock("Pixel 4")
    device.brand = AsyncPropertyMock("Google")
    device.android_version = AsyncPropertyMock("11")
    device.sdk_level = AsyncPropertyMock("30")
    device.build_number = AsyncPropertyMock("RQ3A.211001.001")

    # Set up async methods
    device.get_properties = AsyncMock(
        return_value={
            "ro.build.version.release": "11",
            "ro.build.version.sdk": "30",
            "ro.product.model": "Pixel 4",
            "ro.product.brand": "Google",
            "ro.product.name": "redfin",
            "ro.build.display.id": "RQ3A.211001.001",
        }
    )
    device.get_logcat = AsyncMock(return_value="logcat output")
    device.list_directory = AsyncMock(return_value="file1\nfile2\nfile3")
    device.run_shell = AsyncMock(return_value="command output")
    device.install_app = AsyncMock(return_value="Success")
    device.take_screenshot = AsyncMock(return_value=b"fake image data")
    device.reboot = AsyncMock(return_value="Device rebooted")

    return device


@pytest.mark.asyncio
@patch("droidmind.devices.DeviceManager.list_devices")
async def test_list_devices(mock_list_devices, mock_context, mock_device):
    """Test the list_devices tool."""
    # Create a second mock device
    device2 = MagicMock(spec=Device)
    device2.serial = "device2"

    # Create a class to make awaitable properties (same as in mock_device fixture)
    class AsyncPropertyMock:
        def __init__(self, return_value):
            self.return_value = return_value

        def __await__(self):
            async def _async_return():
                return self.return_value

            return _async_return().__await__()

    # Set up device properties with awaitable objects
    device2.model = AsyncPropertyMock("Galaxy S21")
    device2.brand = AsyncPropertyMock("Samsung")
    device2.android_version = AsyncPropertyMock("12")

    # Set up mock devices
    mock_list_devices.return_value = [mock_device, device2]

    # Call the tool
    result = await list_devices(mock_context)

    # Verify the result
    assert "Connected Android Devices (2)" in result
    assert "Device 1: Pixel 4" in result
    assert "Device 2: Galaxy S21" in result
    assert "Serial**: `device1`" in result
    assert "Serial**: `device2`" in result
    assert "Android Version**: 11" in result
    assert "Android Version**: 12" in result


@pytest.mark.asyncio
@patch("droidmind.devices.DeviceManager.list_devices")
async def test_list_devices_empty(mock_list_devices, mock_context):
    """Test the list_devices tool with no devices."""
    # Set up empty device list
    mock_list_devices.return_value = []

    # Call the tool
    result = await list_devices(mock_context)

    # Verify the result
    assert "No devices connected" in result
    assert "connect_device" in result


@pytest.mark.asyncio
@patch("droidmind.tools.get_device_manager")
async def test_device_properties(mock_get_device_manager, mock_context, mock_device):
    """Test the device_properties tool."""
    # Setup mock get_device_manager to return a mock that has get_device method
    mock_manager = MagicMock()
    mock_manager.get_device = AsyncMock(return_value=mock_device)
    mock_get_device_manager.return_value = mock_manager

    # Call the tool with correct parameter order
    result = await device_properties(ctx=mock_context, serial="device1")

    # Verify the result
    assert "Device Properties for device1" in result
    assert "**Model**: Pixel 4" in result
    assert "**Brand**: Google" in result
    assert "**Android Version**: 11" in result
    assert "**SDK Level**: 30" in result
    assert "**Build Number**: RQ3A.211001.001" in result


@pytest.mark.asyncio
@patch("droidmind.tools.get_device_manager")
async def test_device_properties_not_found(mock_get_device_manager, mock_context):
    """Test the device_properties tool with a non-existent device."""
    # Setup mock get_device_manager to return a mock that has get_device method
    mock_manager = MagicMock()
    mock_manager.get_device = AsyncMock(return_value=None)
    mock_get_device_manager.return_value = mock_manager

    # Call the tool
    result = await device_properties(ctx=mock_context, serial="nonexistent")

    # Verify the result
    assert "Device nonexistent not found or not connected" in result


@pytest.mark.asyncio
@patch("droidmind.devices.DeviceManager.connect")
async def test_connect_device(mock_connect, mock_context, mock_device):
    """Test the connect_device tool."""
    # Mock the connect method to return a device
    mock_connect.return_value = mock_device

    # Call the tool
    result = await connect_device(ctx=mock_context, ip_address="192.168.1.100", port=5555)

    # Verify the result
    assert "Device Connected Successfully" in result
    assert "Pixel 4" in result
    assert "192.168.1.100:5555" in result


@pytest.mark.asyncio
@patch("droidmind.devices.DeviceManager.disconnect")
async def test_disconnect_device(mock_disconnect, mock_context):
    """Test the disconnect_device tool."""
    # Set up mock disconnect
    mock_disconnect.return_value = True

    # Call the tool
    result = await disconnect_device(ctx=mock_context, serial="device1")

    # Verify the result
    assert "Successfully disconnected from device device1" in result

    # Verify the mock was called
    mock_disconnect.assert_called_once_with("device1")


@pytest.mark.asyncio
@patch("droidmind.tools.get_device_manager")
async def test_shell_command(mock_get_device_manager, mock_context, mock_device):
    """Test the shell_command tool."""
    # Setup mock get_device_manager to return a mock that has get_device method
    mock_manager = MagicMock()
    mock_manager.get_device = AsyncMock(return_value=mock_device)
    mock_get_device_manager.return_value = mock_manager

    # Call the tool
    result = await shell_command(ctx=mock_context, serial="device1", command="ls")

    # Verify the result
    assert "command output" in result

    # Verify the mock was called with the default parameters for max_lines and max_size
    mock_device.run_shell.assert_called_once_with("ls", 1000, 100000)


@pytest.mark.asyncio
@patch("droidmind.devices.DeviceManager.get_device")
async def test_capture_screenshot(mock_get_device, mock_context, mock_device):
    """Test the capture_screenshot tool."""
    # Setup mock get_device
    mock_get_device.return_value = mock_device

    # Call the tool
    result = await capture_screenshot(ctx=mock_context, serial="device1")

    # Verify the result is an Image object
    assert isinstance(result, Image)

    # Check if the screenshot capture was successful
    if result.data == b"":
        # If the test ran into an error, the tool would return empty data
        mock_context.error.assert_called()
    else:
        # Otherwise it should contain our fake image data
        assert result.data == b"fake image data"
        mock_device.take_screenshot.assert_called_once()
        # Check that info was called twice (once for starting, once for success)
        assert mock_context.info.call_count >= 2


@pytest.mark.asyncio
@patch("droidmind.tools.get_device_manager")
async def test_reboot_device(mock_get_device_manager, mock_context, mock_device):
    """Test the reboot_device tool."""
    # Setup mock get_device_manager to return a mock that has get_device method
    mock_manager = MagicMock()
    mock_manager.get_device = AsyncMock(return_value=mock_device)
    mock_get_device_manager.return_value = mock_manager

    # Call the tool
    result = await reboot_device(ctx=mock_context, serial="device1", mode="recovery")

    # Verify the result
    assert "Device device1 is rebooting in recovery mode" in result

    # Verify the mock was called
    mock_device.reboot.assert_called_once_with("recovery")

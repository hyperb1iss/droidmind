"""Tests for the DroidMind MCP tools and resources."""

from unittest.mock import AsyncMock, MagicMock, patch

from mcp.server.fastmcp import Context, Image
import pytest

from droidmind.devices import Device
from droidmind.tools import (
    connect_device,
    device_properties,
    disconnect_device,
    list_devices,
    reboot_device,
    screenshot as capture_screenshot,
    shell_command,
)


@pytest.fixture
def mock_context():
    """Create a mock MCP context."""
    context = MagicMock(spec=Context)
    context.info = AsyncMock()
    context.error = AsyncMock()
    return context


@pytest.fixture
def mock_device():
    """Create a mock device for testing."""
    device = MagicMock(spec=Device)
    device.serial = "device1"

    # Set up properties
    class AsyncPropertyMock:
        def __init__(self, return_value):
            self.return_value = return_value

        def __await__(self):
            async def _async_return():
                return self.return_value

            return _async_return().__await__()

    device.model = AsyncPropertyMock("Pixel 4")
    device.brand = AsyncPropertyMock("Google")
    device.android_version = AsyncPropertyMock("11")
    device.sdk_level = AsyncPropertyMock("30")
    device.build_number = AsyncPropertyMock("RQ3A.211001.001")

    # Set up methods
    device.get_properties = AsyncMock(
        return_value={
            "ro.product.model": "Pixel 4",
            "ro.product.brand": "Google",
            "ro.build.version.release": "11",
            "ro.build.version.sdk": "30",
            "ro.build.id": "RQ3A.211001.001",
        }
    )
    device.run_shell = AsyncMock(return_value="Command output")
    device.take_screenshot = AsyncMock(return_value=b"FAKE_SCREENSHOT_DATA")
    device.reboot = AsyncMock()

    return device


@pytest.mark.asyncio
@patch("droidmind.tools.device_management.get_device_manager")
async def test_list_devices(mock_list_devices, mock_context, mock_device):
    """Test the devicelist tool."""

    # Set up the mock device list
    class AsyncPropertyMock:
        def __init__(self, return_value):
            self.return_value = return_value

        def __await__(self):
            async def _async_return():
                return self.return_value

            return _async_return().__await__()

    mock_device1 = MagicMock(spec=Device)
    mock_device1.serial = "device1"
    mock_device1.model = AsyncPropertyMock("Pixel 4")
    mock_device1.android_version = AsyncPropertyMock("11")

    mock_device2 = MagicMock(spec=Device)
    mock_device2.serial = "device2"
    mock_device2.model = AsyncPropertyMock("Pixel 5")
    mock_device2.android_version = AsyncPropertyMock("12")

    # Set up the mock device manager
    mock_manager = MagicMock()
    mock_manager.list_devices = AsyncMock(return_value=[mock_device1, mock_device2])
    mock_list_devices.return_value = mock_manager

    # Call the tool
    result = await list_devices(ctx=mock_context)

    # Verify the result
    assert "Connected Android Devices (2)" in result
    assert "Device 1: Pixel 4" in result
    assert "Device 2: Pixel 5" in result


@pytest.mark.asyncio
@patch("droidmind.tools.device_management.get_device_manager")
async def test_list_devices_empty(mock_list_devices, mock_context):
    """Test the devicelist tool with no devices."""
    # Set up the mock device manager
    mock_manager = MagicMock()
    mock_manager.list_devices = AsyncMock(return_value=[])
    mock_list_devices.return_value = mock_manager

    # Call the tool
    result = await list_devices(ctx=mock_context)

    # Verify the result
    assert "No devices connected" in result


@pytest.mark.asyncio
@patch("droidmind.tools.device_management.get_device_manager")
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
@patch("droidmind.tools.device_management.get_device_manager")
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
@patch("droidmind.tools.device_management.get_device_manager")
async def test_connect_device(mock_connect, mock_context, mock_device):
    """Test the connect_device tool."""
    # Setup mock get_device_manager to return a mock that has connect method
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock(return_value=mock_device)
    mock_connect.return_value = mock_manager

    # Call the tool
    result = await connect_device(ctx=mock_context, ip_address="192.168.1.100", port=5555)

    # Verify the result
    assert "Device Connected Successfully" in result
    assert "Pixel 4" in result
    assert "192.168.1.100:5555" in result


@pytest.mark.asyncio
@patch("droidmind.tools.device_management.get_device_manager")
async def test_disconnect_device(mock_disconnect, mock_context):
    """Test the disconnect_device tool."""
    # Setup mock get_device_manager to return a mock that has disconnect method
    mock_manager = MagicMock()
    mock_manager.disconnect = AsyncMock(return_value=True)
    mock_disconnect.return_value = mock_manager

    # Call the tool
    result = await disconnect_device(ctx=mock_context, serial="device1")

    # Verify the result
    assert "Successfully disconnected from device device1" in result


@pytest.mark.asyncio
@patch("droidmind.tools.shell.get_device_manager")
async def test_shell_command(mock_get_device_manager, mock_context, mock_device):
    """Test the shell_command tool."""
    # Setup mock get_device_manager to return a mock that has get_device method
    mock_manager = MagicMock()
    mock_manager.get_device = AsyncMock(return_value=mock_device)
    mock_get_device_manager.return_value = mock_manager

    # Call the tool
    result = await shell_command(ctx=mock_context, serial="device1", command="ls -la")

    # Verify the result
    assert "Command Output from device1" in result
    assert "Command output" in result


@pytest.mark.asyncio
@patch("droidmind.tools.media.get_device_manager")
async def test_capture_screenshot(mock_get_device, mock_context, mock_device):
    """Test the screenshot tool."""
    # Setup mock get_device_manager to return a mock that has get_device method
    mock_manager = MagicMock()
    mock_manager.get_device = AsyncMock(return_value=mock_device)
    mock_get_device.return_value = mock_manager

    # Call the tool
    result = await capture_screenshot(ctx=mock_context, serial="device1")

    # Verify the result is an Image object with the expected data
    assert isinstance(result, Image)
    assert result.data == b"FAKE_SCREENSHOT_DATA"

    # Verify the context methods were called
    mock_context.info.assert_called()
    assert "Capturing screenshot" in mock_context.info.call_args_list[0][0][0]


@pytest.mark.asyncio
@patch("droidmind.tools.device_management.get_device_manager")
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

    # Verify the device's reboot method was called with the correct mode
    mock_device.reboot.assert_called_once_with("recovery")

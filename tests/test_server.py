"""Tests for the DroidMind MCP tools and resources."""

import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from mcp.server.fastmcp import Context, Image
import pytest

from droidmind.adb.wrapper import ADBWrapper
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
    context.report_progress = AsyncMock()  # This is awaited

    return context


@pytest.fixture
def mock_adb():
    """Create a mock ADB wrapper."""
    adb = MagicMock(spec=ADBWrapper)
    return adb


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
async def test_list_devices(mock_get_adb, mock_context, mock_adb):
    """Test the list_devices tool."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
        {"serial": "device2", "model": "Galaxy S21", "android_version": "12"},
    ]
    mock_adb.get_devices = AsyncMock(return_value=mock_devices)
    mock_get_adb.return_value = mock_adb

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
@patch("droidmind.tools.get_adb")
async def test_list_devices_empty(mock_get_adb, mock_context, mock_adb):
    """Test the list_devices tool with no devices."""
    # Set up empty device list
    mock_adb.get_devices = AsyncMock(return_value=[])
    mock_get_adb.return_value = mock_adb

    # Call the tool
    result = await list_devices(mock_context)

    # Verify the result
    assert "No devices connected" in result
    assert "connect_device" in result


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
async def test_device_properties(mock_get_adb, mock_context, mock_adb):
    """Test the device_properties tool."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_adb.get_devices = AsyncMock(return_value=mock_devices)

    # Set up mock properties
    mock_properties = {
        "ro.build.version.release": "11",
        "ro.build.version.sdk": "30",
        "ro.product.model": "Pixel 4",
        "ro.product.brand": "Google",
        "ro.product.name": "redfin",
        "ro.build.display.id": "RQ3A.211001.001",
        "ro.build.type": "user",
        "ro.build.date": "Mon Oct 1 12:00:00 UTC 2021",
        "ro.hardware": "redfin",
        "ro.product.cpu.abi": "arm64-v8a",
        "ro.sf.lcd_density": "440",
    }
    mock_adb.get_device_properties = AsyncMock(return_value=mock_properties)
    mock_get_adb.return_value = mock_adb

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
@patch("droidmind.tools.get_adb")
async def test_device_properties_not_found(mock_get_adb, mock_context, mock_adb):
    """Test the device_properties tool with a non-existent device."""
    # Set up empty device list
    mock_adb.get_devices = AsyncMock(return_value=[])
    # Return empty dict for properties
    mock_adb.get_device_properties = AsyncMock(return_value={})
    mock_get_adb.return_value = mock_adb

    # Call the tool
    result = await device_properties(ctx=mock_context, serial="nonexistent")

    # Verify the result
    assert "No properties found for device nonexistent" in result


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
async def test_connect_device(mock_get_adb, mock_context, mock_adb):
    """Test the connect_device tool."""
    # Set up mock devices
    mock_devices = [
        {"serial": "192.168.1.100:5555", "model": "Pixel 4", "android_version": "11"},
    ]

    # Mock the connect_device_tcp method to return a successful result
    mock_adb.connect_device_tcp = AsyncMock(return_value="192.168.1.100:5555")

    # Mock get_devices to return the connected device
    mock_adb.get_devices = AsyncMock(return_value=mock_devices)

    mock_get_adb.return_value = mock_adb

    # Call the tool
    result = await connect_device(ctx=mock_context, ip_address="192.168.1.100", port=5555)

    # Verify the result
    assert "Device Connected Successfully" in result
    assert "Pixel 4" in result


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
async def test_disconnect_device(mock_get_adb, mock_context, mock_adb):
    """Test the disconnect_device tool."""
    # Set up mock disconnect
    mock_adb.disconnect_device = AsyncMock(return_value=True)
    mock_get_adb.return_value = mock_adb

    # Call the tool
    result = await disconnect_device(ctx=mock_context, serial="device1")

    # Verify the result
    assert "Successfully disconnected from device device1" in result

    # Verify the mock was called
    mock_adb.disconnect_device.assert_called_once_with("device1")


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
async def test_shell_command(mock_get_adb, mock_context, mock_adb):
    """Test the shell_command tool."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_adb.get_devices = AsyncMock(return_value=mock_devices)

    # Set up mock shell command
    mock_adb.shell = AsyncMock(return_value="command output")
    mock_get_adb.return_value = mock_adb

    # Call the tool
    result = await shell_command(ctx=mock_context, serial="device1", command="ls")

    # Verify the result
    assert "command output" in result

    # Verify the mock was called
    mock_adb.shell.assert_called_once_with("device1", "ls")


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
@patch("droidmind.tools.get_temp_dir")
@patch("droidmind.tools.aiofiles.open")
async def test_capture_screenshot(mock_aiofiles_open, mock_get_temp_dir, mock_get_adb, mock_context, mock_adb):
    """Test the capture_screenshot tool."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_adb.get_devices = AsyncMock(return_value=mock_devices)

    # Set up mock shell commands
    mock_adb.shell = AsyncMock(return_value="")
    mock_adb.pull_file = AsyncMock(return_value="")

    # Set up mock temp dir - use tempfile.gettempdir() for security
    mock_get_temp_dir.return_value = tempfile.gettempdir()

    # Set up mock file read - properly mock the async context manager
    mock_file = AsyncMock()
    mock_file.read = AsyncMock(return_value=b"fake image data")

    # Create a context manager that returns the mock file
    class AsyncContextManagerMock:
        async def __aenter__(self):
            return mock_file

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Make the mock return our async context manager
    mock_aiofiles_open.return_value = AsyncContextManagerMock()

    mock_get_adb.return_value = mock_adb

    # Call the tool
    result = await capture_screenshot(ctx=mock_context, serial="device1")

    # Verify the result is an Image object
    assert isinstance(result, Image)
    assert result.data == b"fake image data"


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
async def test_reboot_device(mock_get_adb, mock_context, mock_adb):
    """Test the reboot_device tool."""
    # Set up mock reboot
    mock_adb.reboot_device = AsyncMock(return_value="Rebooting device1")
    mock_get_adb.return_value = mock_adb

    # Call the tool
    result = await reboot_device(ctx=mock_context, serial="device1")

    # Verify the result
    assert "Rebooting device1" in result

    # Verify the mock was called
    mock_adb.reboot_device.assert_called_once_with("device1", "normal")

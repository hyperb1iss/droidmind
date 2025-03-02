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
    context.info = MagicMock()  # This is just called, not awaited
    context.error = MagicMock()  # This is just called, not awaited
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
    """Test the device_properties tool with a device that doesn't exist."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_adb.get_devices = AsyncMock(return_value=mock_devices)
    mock_get_adb.return_value = mock_adb

    # Call the tool with correct parameter order
    result = await device_properties(ctx=mock_context, serial="nonexistent")

    # Verify the result
    assert "Error: Device nonexistent not connected or not found" in result


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
async def test_connect_device(mock_get_adb, mock_context, mock_adb):
    """Test the connect_device tool."""
    # Set up mock connection
    mock_adb.connect_device = AsyncMock(return_value="connected to 192.168.1.100:5555")

    # Set up mock device info
    mock_devices = [
        {"serial": "192.168.1.100:5555", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_adb.get_devices = AsyncMock(return_value=mock_devices)
    mock_get_adb.return_value = mock_adb

    # Call the tool
    result = await connect_device(ctx=mock_context, ip_address="192.168.1.100")

    # Verify the result
    assert "Device Connected Successfully" in result
    assert "192.168.1.100" in result


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
async def test_disconnect_device(mock_get_adb, mock_context, mock_adb):
    """Test the disconnect_device tool."""
    # Set up mock devices to make the device appear connected
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_adb.get_devices = AsyncMock(return_value=mock_devices)

    # Set up mock disconnection
    mock_adb.disconnect_device = AsyncMock(return_value=True)
    mock_get_adb.return_value = mock_adb

    # Call the tool with named parameters
    result = await disconnect_device(ctx=mock_context, serial="device1")

    # Verify the result - adjust based on your new output format
    assert "device1" in result


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

    # Call the tool with named parameters
    result = await shell_command(ctx=mock_context, serial="device1", command="ls -la")

    # Verify the result - adjust based on your new output format
    assert "command output" in result


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
@patch("droidmind.tools.get_temp_dir")
async def test_capture_screenshot(mock_get_temp_dir, mock_get_adb, mock_context, mock_adb):
    """Test the screenshot tool."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_adb.get_devices = AsyncMock(return_value=mock_devices)

    # Set up temp dir
    temp_dir = tempfile.mkdtemp(prefix="droidmind_test_")
    mock_get_temp_dir.return_value = temp_dir

    # Set up mock screenshot capture
    mock_adb.shell = AsyncMock()
    mock_adb.pull_file = AsyncMock()
    mock_get_adb.return_value = mock_adb

    # Mock file operations
    with patch("builtins.open", create=True) as mock_open, patch("os.unlink"):
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.read.return_value = b"mock image data"

        # Call the tool with named parameters
        result = await capture_screenshot(ctx=mock_context, serial="device1")

        # Verify the result
        assert isinstance(result, Image)
        assert result.data == b"mock image data"
        # The Image class doesn't have a format attribute in the actual implementation
        # So we don't check for it


@pytest.mark.asyncio
@patch("droidmind.tools.get_adb")
async def test_reboot_device(mock_get_adb, mock_context, mock_adb):
    """Test the reboot_device tool."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_adb.get_devices = AsyncMock(return_value=mock_devices)

    # Set up mock reboot
    mock_adb.reboot_device = AsyncMock(return_value="Device device1 rebooting into normal mode")
    mock_get_adb.return_value = mock_adb

    # Call the tool with named parameters
    result = await reboot_device(ctx=mock_context, serial="device1")

    # Verify the result - adjust based on your new output format
    assert "device1" in result

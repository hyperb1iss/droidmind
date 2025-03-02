"""Tests for the MCP server implementation."""

import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import Context, Image

from droidmind.adb.wrapper import ADBWrapper
from droidmind.server import (
    _device_properties_impl as device_properties,
)
from droidmind.server import (
    _list_devices_impl as list_devices,
)
from droidmind.server import (
    capture_screenshot,
    connect_device,
    disconnect_device,
    reboot_device,
    shell_command,
)


@pytest.fixture
def mock_context():
    """Create a mock MCP context with an ADB wrapper."""
    context = MagicMock(spec=Context)
    adb = MagicMock(spec=ADBWrapper)
    context.lifespan_context = MagicMock()
    context.lifespan_context.adb = adb
    context.lifespan_context.temp_dir = tempfile.mkdtemp(prefix="droidmind_test_")

    # Make methods that are awaited return awaitable objects
    context.info = MagicMock()  # This is just called, not awaited
    context.error = MagicMock()  # This is just called, not awaited
    context.report_progress = AsyncMock()  # This is awaited

    return context


@pytest.mark.asyncio
async def test_list_devices(mock_context):
    """Test the list_devices resource."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
        {"serial": "device2", "model": "Galaxy S21", "android_version": "12"},
    ]
    mock_context.lifespan_context.adb.get_devices = AsyncMock(return_value=mock_devices)

    # Call the resource
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
async def test_list_devices_empty(mock_context):
    """Test the list_devices resource with no devices."""
    # Set up empty device list
    mock_context.lifespan_context.adb.get_devices = AsyncMock(return_value=[])

    # Call the resource
    result = await list_devices(mock_context)

    # Verify the result
    assert "No devices connected" in result
    assert "connect_device" in result


@pytest.mark.asyncio
async def test_device_properties(mock_context):
    """Test the device_properties resource."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_context.lifespan_context.adb.get_devices = AsyncMock(return_value=mock_devices)

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
    mock_context.lifespan_context.adb.get_device_properties = AsyncMock(
        return_value=mock_properties
    )

    # Call the resource
    result = await device_properties("device1", mock_context)

    # Verify the result
    assert "Device Properties for device1" in result
    assert "**Model**: Pixel 4" in result
    assert "**Brand**: Google" in result
    assert "**Android Version**: 11" in result
    assert "**SDK Level**: 30" in result
    assert "**Build Number**: RQ3A.211001.001" in result


@pytest.mark.asyncio
async def test_device_properties_not_found(mock_context):
    """Test the device_properties resource with a device that doesn't exist."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_context.lifespan_context.adb.get_devices = AsyncMock(return_value=mock_devices)

    # Call the resource with a non-existent device
    result = await device_properties("nonexistent", mock_context)

    # Verify the result
    assert "Error: Device nonexistent not connected or not found" in result


@pytest.mark.asyncio
async def test_connect_device(mock_context):
    """Test the connect_device tool."""
    # Set up mock connection
    mock_context.lifespan_context.adb.connect_device_tcp = AsyncMock(
        return_value="192.168.1.100:5555"
    )

    # Set up mock device info
    mock_devices = [
        {"serial": "192.168.1.100:5555", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_context.lifespan_context.adb.get_devices = AsyncMock(return_value=mock_devices)

    # Call the tool
    result = await connect_device("192.168.1.100", mock_context)

    # Verify the result
    assert "Successfully connected to Pixel 4 (Android 11)" in result
    assert "192.168.1.100:5555" in result


@pytest.mark.asyncio
async def test_disconnect_device(mock_context):
    """Test the disconnect_device tool."""
    # Set up mock disconnection
    mock_context.lifespan_context.adb.disconnect_device = AsyncMock(return_value=True)

    # Call the tool
    result = await disconnect_device("device1", mock_context)

    # Verify the result
    assert "Successfully disconnected from device device1" in result


@pytest.mark.asyncio
async def test_shell_command(mock_context):
    """Test the shell_command tool."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_context.lifespan_context.adb.get_devices = AsyncMock(return_value=mock_devices)

    # Set up mock shell command
    mock_context.lifespan_context.adb.shell = AsyncMock(return_value="command output")

    # Call the tool
    result = await shell_command("device1", "ls -la", mock_context)

    # Verify the result
    assert "Command output from device1" in result
    assert "command output" in result


@pytest.mark.asyncio
async def test_capture_screenshot(mock_context):
    """Test the capture_screenshot tool."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_context.lifespan_context.adb.get_devices = AsyncMock(return_value=mock_devices)

    # Set up mock screenshot capture
    mock_context.lifespan_context.adb.shell = AsyncMock()
    mock_context.lifespan_context.adb.pull_file = AsyncMock()

    # Mock file operations
    with patch("builtins.open", create=True) as mock_open, patch("os.unlink"):
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.read.return_value = b"mock image data"

        # Call the tool
        result = await capture_screenshot("device1", mock_context)

        # Verify the result
        assert isinstance(result, Image)
        assert result.data == b"mock image data"
        assert result.format == "png"


@pytest.mark.asyncio
async def test_reboot_device(mock_context):
    """Test the reboot_device tool."""
    # Set up mock devices
    mock_devices = [
        {"serial": "device1", "model": "Pixel 4", "android_version": "11"},
    ]
    mock_context.lifespan_context.adb.get_devices = AsyncMock(return_value=mock_devices)

    # Set up mock reboot
    mock_context.lifespan_context.adb.reboot_device = AsyncMock(
        return_value="Device device1 rebooting into normal mode"
    )

    # Call the tool
    result = await reboot_device("device1", mock_context)

    # Verify the result
    assert "Device device1 rebooting into normal mode" in result

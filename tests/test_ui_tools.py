# pylint: disable=duplicate-code
"""Tests for UI automation tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from droidmind.devices import Device
from droidmind.tools.ui import input_text, press_key, start_intent, swipe, tap


@pytest.fixture
def mock_context():
    """Create a mock Context object."""
    ctx = MagicMock()
    ctx.info = AsyncMock()
    ctx.error = AsyncMock()
    return ctx


@pytest.fixture
def mock_device():
    """Create a mock Device object."""
    device = AsyncMock(spec=Device)
    device.serial = "test_serial"
    device.tap = AsyncMock(return_value="tap_success")
    device.swipe = AsyncMock(return_value="swipe_success")
    device.input_text = AsyncMock(return_value="input_text_success")
    device.press_key = AsyncMock(return_value="press_key_success")
    device.start_activity = AsyncMock(return_value="start_activity_success")
    return device


@pytest.fixture
def mock_device_manager(mock_device):
    """Create a mock DeviceManager that returns the mock device."""
    with patch("droidmind.tools.ui.get_device_manager") as mock_get_manager:
        manager = MagicMock()
        manager.get_device = AsyncMock(return_value=mock_device)
        mock_get_manager.return_value = manager
        yield manager


async def test_tap(mock_context, mock_device, mock_device_manager):
    """Test the tap tool."""
    result = await tap("test_serial", 100, 200, mock_context)

    # Assert context methods were called
    mock_context.info.assert_called()

    # Assert device methods were called with correct params
    mock_device.tap.assert_called_once_with(100, 200)

    # Assert result is correct
    assert "Successfully" in result


async def test_swipe(mock_context, mock_device, mock_device_manager):
    """Test the swipe tool."""
    result = await swipe("test_serial", 100, 200, 300, 400, mock_context, 500)

    # Assert context methods were called
    mock_context.info.assert_called()

    # Assert device methods were called with correct params
    mock_device.swipe.assert_called_once_with(100, 200, 300, 400, 500)

    # Assert result is correct
    assert "Successfully" in result


async def test_input_text(mock_context, mock_device, mock_device_manager):
    """Test the input_text tool."""
    result = await input_text("test_serial", "Hello World", mock_context)

    # Assert context methods were called
    mock_context.info.assert_called()

    # Assert device methods were called with correct params
    mock_device.input_text.assert_called_once_with("Hello World")

    # Assert result is correct
    assert "Successfully" in result


async def test_press_key(mock_context, mock_device, mock_device_manager):
    """Test the press_key tool."""
    result = await press_key("test_serial", 4, mock_context)  # BACK key

    # Assert context methods were called
    mock_context.info.assert_called()

    # Assert device methods were called with correct params
    mock_device.press_key.assert_called_once_with(4)

    # Assert result is correct
    assert "Successfully" in result


async def test_start_intent(mock_context, mock_device, mock_device_manager):
    """Test the start_intent tool."""
    result = await start_intent(
        "test_serial", "com.android.settings", ".Settings", mock_context, {"extra_key": "extra_value"}
    )

    # Assert context methods were called
    mock_context.info.assert_called()

    # Assert device methods were called with correct params
    mock_device.start_activity.assert_called_once_with(
        "com.android.settings", ".Settings", {"extra_key": "extra_value"}
    )

    # Assert result is correct
    assert "Successfully" in result


async def test_device_not_found(mock_context, mock_device_manager):
    """Test error handling when device is not found."""
    # Simulate device not found
    mock_device_manager.get_device = AsyncMock(return_value=None)

    result = await tap("nonexistent_serial", 100, 200, mock_context)

    # Assert error was logged
    mock_context.error.assert_called_once()

    # Assert error message is returned
    assert "Error" in result
    assert "not connected" in result

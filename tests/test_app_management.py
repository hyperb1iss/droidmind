"""Tests for app management functionality in DroidMind."""

from unittest.mock import AsyncMock, patch

import pytest

from droidmind.devices import Device, DeviceManager
from droidmind.tools.app_management import AppAction, app_operations
from droidmind.tools.logs import LogAction, android_log as logs_tool


@pytest.fixture
def mock_device():
    """Create a mock device for testing."""
    device = AsyncMock(spec=Device)
    device.serial = "test_device"

    # Set up method responses
    device.uninstall_app.return_value = "Success"
    device.start_app.return_value = "Started package com.example.app"
    device.stop_app.return_value = "Stopped package com.example.app"
    device.clear_app_data.return_value = "Successfully cleared data for package com.example.app"
    device.get_app_list.return_value = [{"package": "com.example.app", "path": "/data/app/com.example.app.apk"}]
    device.get_app_info.return_value = {
        "version": "1.0",
        "install_path": "/data/app/com.example.app",
        "first_install": "2023-01-01",
        "user_id": "10001",
        "permissions": ["android.permission.INTERNET", "android.permission.CAMERA"],
    }

    # Run shell returns for various commands
    async def mock_run_shell(cmd, max_lines=None):
        if "pm path" in cmd:
            return "package:/data/app/com.example.app.apk"
        if "aapt" in cmd or "aapt2" in cmd:
            return "Mock AndroidManifest content"
        if "ls" in cmd and "shared_prefs" in cmd:
            return "-rw------- 1 u0_a123 u0_a123 1234 2023-01-01 12:00 prefs.xml"
        if "cat" in cmd and "shared_prefs" in cmd:
            return '<map><string name="key">value</string></map>'
        if "logcat" in cmd:
            return "01-01 12:00:00.000 1234 5678 I App: This is a log message"
        if "ps -A | grep" in cmd:
            return "u0_a123    1234  123 1234567 123456 0 0 S com.example.app"
        if "which su" in cmd:
            return "/system/bin/su"
        if "su -c" in cmd:
            return "Mock root command output"
        if "dumpsys package" in cmd:
            return """
            Package [com.example.app]
            userId=10001
            versionCode=1
            versionName=1.0
            """
        return "Generic command output"

    device.run_shell.side_effect = mock_run_shell

    return device


@pytest.fixture
def mock_device_manager(mock_device):
    """Create a mock device manager for testing."""
    manager = AsyncMock(spec=DeviceManager)
    manager.get_device.return_value = mock_device
    return manager


@pytest.fixture
def mock_context():
    """Create a mock MCP context."""
    context = AsyncMock()
    context.info = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_uninstall_app(mock_device_manager, mock_context):
    """Test the uninstall_app action via app_operations."""
    with patch("droidmind.tools.app_management.get_device_manager", return_value=mock_device_manager):
        result = await app_operations(
            serial="test_device",
            action=AppAction.UNINSTALL_APP,
            package="com.example.app",
            ctx=mock_context,
            keep_data=False,
        )

    assert "Successfully uninstalled" in result
    mock_device_manager.get_device.assert_called_once_with("test_device")
    mock_device = mock_device_manager.get_device.return_value
    mock_device.uninstall_app.assert_called_once_with("com.example.app", False)


@pytest.mark.asyncio
async def test_start_app(mock_device_manager, mock_context):
    """Test the start_app action via app_operations."""
    with patch("droidmind.tools.app_management.get_device_manager", return_value=mock_device_manager):
        result = await app_operations(
            serial="test_device",
            action=AppAction.START_APP,
            package="com.example.app",
            ctx=mock_context,
        )

    assert "Started package" in result
    mock_device_manager.get_device.assert_called_once_with("test_device")
    mock_device = mock_device_manager.get_device.return_value
    mock_device.start_app.assert_called_once_with("com.example.app", "")


@pytest.mark.asyncio
async def test_stop_app(mock_device_manager, mock_context):
    """Test the stop_app action via app_operations."""
    with patch("droidmind.tools.app_management.get_device_manager", return_value=mock_device_manager):
        result = await app_operations(
            serial="test_device",
            action=AppAction.STOP_APP,
            package="com.example.app",
            ctx=mock_context,
        )

    assert "Stopped package" in result
    mock_device_manager.get_device.assert_called_once_with("test_device")
    mock_device = mock_device_manager.get_device.return_value
    mock_device.stop_app.assert_called_once_with("com.example.app")


@pytest.mark.asyncio
async def test_clear_app_data(mock_device_manager, mock_context):
    """Test the clear_app_data action via app_operations."""
    with patch("droidmind.tools.app_management.get_device_manager", return_value=mock_device_manager):
        result = await app_operations(
            serial="test_device",
            action=AppAction.CLEAR_APP_DATA,
            package="com.example.app",
            ctx=mock_context,
        )

    assert "Successfully" in result
    mock_device_manager.get_device.assert_called_once_with("test_device")
    mock_device = mock_device_manager.get_device.return_value
    mock_device.clear_app_data.assert_called_once_with("com.example.app")


@pytest.mark.asyncio
async def test_list_packages(mock_device_manager, mock_context):
    """Test the list_packages action via app_operations."""
    with patch("droidmind.tools.app_management.get_device_manager", return_value=mock_device_manager):
        result = await app_operations(
            serial="test_device",
            action=AppAction.LIST_PACKAGES,
            ctx=mock_context,
            include_system_apps=False,
        )

    assert "Installed Packages" in result
    assert "com.example.app" in result
    mock_device_manager.get_device.assert_called_once_with("test_device")
    mock_device = mock_device_manager.get_device.return_value
    mock_device.get_app_list.assert_called_once_with(False)


@pytest.mark.asyncio
async def test_get_app_manifest(mock_device_manager, mock_context):
    """Test the get_app_manifest action via app_operations."""
    with patch("droidmind.tools.app_management.get_device_manager", return_value=mock_device_manager):
        result = await app_operations(
            serial="test_device",
            action=AppAction.GET_APP_MANIFEST,
            package="com.example.app",
            ctx=mock_context,
        )

    assert "App Manifest for" in result
    mock_device_manager.get_device.assert_called_once_with("test_device")
    mock_device = mock_device_manager.get_device.return_value
    mock_device.run_shell.assert_any_call("dumpsys package com.example.app", max_lines=None)


@pytest.mark.asyncio
async def test_app_logs_tool(mock_device_manager, mock_context):
    """Test the get_app_logs action via android_log tool."""
    with patch("droidmind.tools.logs.get_device_manager", return_value=mock_device_manager):
        result = await logs_tool(
            serial="test_device", action=LogAction.GET_APP_LOGS, package="com.example.app", ctx=mock_context
        )

    assert "Logs for App" in result
    assert "This is a log message" in result
    mock_device_manager.get_device.assert_called_once_with("test_device")
    mock_device = mock_device_manager.get_device.return_value
    mock_device.run_shell.assert_any_call("ps -A | grep com.example.app")


@pytest.mark.asyncio
async def test_install_app(mock_device_manager, mock_context):
    """Test the install_app action via app_operations."""
    mock_device = mock_device_manager.get_device.return_value
    mock_device.install_app.return_value = "Success"
    apk_path = "/fake/path/to/app.apk"

    with (
        patch("droidmind.tools.app_management.get_device_manager", return_value=mock_device_manager),
        patch("os.path.isfile", return_value=True),
    ):
        result = await app_operations(
            serial="test_device",
            action=AppAction.INSTALL_APP,
            apk_path=apk_path,
            reinstall=False,
            grant_permissions=True,
            ctx=mock_context,
        )

    assert "Successfully installed APK" in result
    mock_device_manager.get_device.assert_called_once_with("test_device")
    mock_device.install_app.assert_called_once_with(apk_path, False, True)

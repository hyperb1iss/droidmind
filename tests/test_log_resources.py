"""Tests for the log resources in the DroidMind MCP server."""

from unittest.mock import AsyncMock, patch

import pytest

from droidmind.devices import Device, DeviceManager
from droidmind.resources.logs import device_anr_logs, device_battery_stats, device_crash_logs


@pytest.mark.asyncio
class TestANRResource:
    """Tests for the logs://{serial}/anr resource."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock Device."""
        mock_device = AsyncMock(spec=Device)
        mock_device.serial = "test_device"
        mock_device._adb = AsyncMock()
        mock_device.run_shell = AsyncMock()
        mock_device.run_shell.side_effect = lambda cmd: {
            # ls /data/anr
            "ls /data/anr": "traces.txt\ntraces_1.txt",
            # find command
            "find /data/anr -type f -name '*.txt' -o -name 'traces*'": "/data/anr/traces.txt\n/data/anr/traces_1.txt",
            # ls -lt command
            "ls -lt /data/anr | grep -E 'traces|.txt' | head -3": "-rw-r--r-- root root 12345 2023-01-01 12:00 traces.txt\n-rw-r--r-- root root 12345 2023-01-01 12:00 traces_1.txt",
            # ls -la for file details
            "ls -la /data/anr/traces.txt": "-rw-r--r-- root root 12345 2023-01-01 12:00 traces.txt",
            "ls -la /data/anr/traces_1.txt": "-rw-r--r-- root root 12345 2023-01-01 12:00 traces_1.txt",
            # head -200 for content
            "head -200 /data/anr/traces.txt": "Sample ANR trace content",
            "head -200 /data/anr/traces_1.txt": "Another ANR trace content",
        }[cmd]
        return mock_device

    @pytest.fixture
    def mock_device_manager(self, mock_device):
        """Create a mock DeviceManager that returns our mock device."""
        mock_dm = AsyncMock(spec=DeviceManager)
        mock_dm.get_device.return_value = mock_device
        return mock_dm

    async def test_anr_logs_basic(self, mock_device, mock_device_manager):
        """Test basic ANR logs functionality."""
        # Patch the device manager to return our mock
        with patch("droidmind.resources.logs.get_device_manager", return_value=mock_device_manager):
            # Call the resource
            result = await device_anr_logs("test_device")

            # Verify results
            assert "# Application Not Responding (ANR) Traces" in result
            assert "Sample ANR trace content" in result
            assert "Another ANR trace content" in result


@pytest.mark.asyncio
class TestCrashLogsResource:
    """Tests for the logs://{serial}/crashes resource."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock Device."""
        mock_device = AsyncMock(spec=Device)
        mock_device.serial = "test_device"
        mock_device._adb = AsyncMock()
        mock_device.run_shell = AsyncMock()
        mock_device.run_shell.side_effect = lambda cmd: {
            # Tombstone directory
            "ls -la /data/tombstones": "drwxr-xr-x root root 4096 2023-01-01 12:00 .\n-rw-r--r-- root root 12345 2023-01-01 12:00 tombstone_01",
            "ls -lt /data/tombstones | head -4": "-rw-r--r-- root root 12345 2023-01-01 12:00 tombstone_01",
            "head -30 /data/tombstones/tombstone_01": "Sample tombstone content",
            # Dropbox directory
            "ls -la /data/system/dropbox | grep crash": "-rw-r--r-- root root 12345 2023-01-01 12:00 crash_01.txt",
            "cat /data/system/dropbox/crash_01.txt": "Sample crash report content",
            # Logcat crash buffer
            "logcat -d -b crash -v threadtime -t 100": "Sample crash log from logcat buffer",
        }[cmd]
        return mock_device

    @pytest.fixture
    def mock_device_manager(self, mock_device):
        """Create a mock DeviceManager that returns our mock device."""
        mock_dm = AsyncMock(spec=DeviceManager)
        mock_dm.get_device.return_value = mock_device
        return mock_dm

    async def test_crash_logs_basic(self, mock_device, mock_device_manager):
        """Test basic crash logs functionality."""
        # Patch the device manager to return our mock
        with patch("droidmind.resources.logs.get_device_manager", return_value=mock_device_manager):
            # Call the resource
            result = await device_crash_logs("test_device")

            # Verify results
            assert "# Android Application Crash Reports" in result
            assert "## System Tombstones" in result
            assert "Sample tombstone content" in result
            assert "## Dropbox Crash Reports" in result
            assert "Sample crash report content" in result
            assert "## Recent Crashes in Logcat" in result
            assert "Sample crash log from logcat buffer" in result


@pytest.mark.asyncio
class TestBatteryStatsResource:
    """Tests for the logs://{serial}/battery resource."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock Device."""
        mock_device = AsyncMock(spec=Device)
        mock_device.serial = "test_device"
        mock_device._adb = AsyncMock()
        mock_device.run_shell = AsyncMock()
        mock_device.run_shell.side_effect = lambda cmd: {
            # Battery status
            "dumpsys battery": "Current Battery Service state:\n  level: 85\n  temperature: 350\n  health: 2",
            # Battery history and stats
            "dumpsys batterystats --charged": """
Discharge step durations:
  #0: +1m30s092ms to 85 (screen-off)
  #1: +1m30s019ms to 86 (screen-off)
  #2: +1m29s982ms to 87 (screen-off)
Estimated discharge time remaining: +3h45m20s
Estimated screen off time: 5h 15m 30s

Statistics since last charge:
  System starts: 0, currently on battery: true
  Time on battery: 2h 15m 30s
  Time on battery screen off: 1h 45m 20s
  Screen on: 30m 10s (22.3%) 25x
  Screen brightnesses:
    dark 2m 10s (7.2%)
    dim 20m 15s (67.1%)
    medium 5m 25s (17.9%)
    bright 2m 20s (7.8%)

  Cellular Statistics:
    Cellular active time: 15m 30s
  Wifi Statistics:
    Wifi active time: 2h 10m 15s
  Bluetooth Statistics:
    Bluetooth scan time: 1h 30m 45s
"""
        }[cmd]
        return mock_device

    @pytest.fixture
    def mock_device_manager(self, mock_device):
        """Create a mock DeviceManager that returns our mock device."""
        mock_dm = AsyncMock(spec=DeviceManager)
        mock_dm.get_device.return_value = mock_device
        return mock_dm

    async def test_battery_stats_basic(self, mock_device, mock_device_manager):
        """Test basic battery stats functionality."""
        # Patch the device manager to return our mock
        with patch("droidmind.resources.logs.get_device_manager", return_value=mock_device_manager):
            # Call the resource
            result = await device_battery_stats("test_device")

            # Verify results
            assert "# Battery Statistics Report 🔋" in result
            assert "## Current Battery Status" in result
            assert "### Key Metrics" in result
            assert "**Battery Level:** 85%" in result
            assert "**Temperature:** 35.0°C" in result
            assert "**Health:** Good" in result
            assert "## Battery History and Usage" in result
            assert "### Discharge History" in result
            assert "### Power Consumption Details" in result
            assert "Estimated discharge time remaining" in result
            assert "Screen brightnesses" in result
            assert "Cellular Statistics" in result
            assert "Wifi Statistics" in result
            assert "Bluetooth Statistics" in result

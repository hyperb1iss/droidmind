"""Tests for the log resources in the DroidMind MCP server."""

from unittest.mock import AsyncMock, patch

import pytest

from droidmind.devices import Device, DeviceManager
from droidmind.resources import device_anr_logs, device_battery_stats, device_crash_logs


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
        with patch("droidmind.resources.get_device_manager", return_value=mock_device_manager):
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
        with patch("droidmind.resources.get_device_manager", return_value=mock_device_manager):
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
            # Battery history
            "dumpsys batterystats --charged | head -200": "Battery History (1% used, 99% free):\n...",
            # Battery usage by app
            "dumpsys batterystats --list": "App usage:\nPackage1: 10%\nPackage2: 5%",
            # Battery stats checkin format
            "dumpsys batterystats --checkin": "9,0,i,vers,12,116,s84\n9,0,i,uid,10008,com.android.app1\n9,0,i,uid,10009,com.android.app2",
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
        with patch("droidmind.resources.get_device_manager", return_value=mock_device_manager):
            # Call the resource
            result = await device_battery_stats("test_device")

            # Verify results
            assert "# Battery Statistics Report 🔋" in result
            assert "## Current Battery Status" in result
            assert "### Key Metrics" in result
            assert "**Battery Level:** 85%" in result
            assert "**Temperature:** 35.0°C" in result
            assert "**Health:** Good" in result
            assert "## Battery History" in result
            assert "## Battery Usage by App" in result
            assert "## Power Usage Summary" in result

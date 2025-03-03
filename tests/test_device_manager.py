"""Tests for the DeviceManager and Device classes."""

from unittest.mock import AsyncMock, patch

import pytest

from droidmind.devices import Device, DeviceManager, get_device_manager


class TestDeviceManager:
    """Tests for the DeviceManager class."""

    @pytest.fixture
    def device_manager(self):
        """Create a new DeviceManager instance with mocked ADB wrapper."""
        with patch("droidmind.devices.ADBWrapper") as mock_adb_class:
            # Set up the mock ADB wrapper
            mock_adb = mock_adb_class.return_value
            mock_adb.get_devices = AsyncMock(
                return_value=[
                    {"serial": "device1", "state": "device"},
                    {"serial": "192.168.1.100:5555", "state": "device"},
                ]
            )

            # Create the DeviceManager with the mocked ADB wrapper
            manager = DeviceManager(adb_path=None)
            yield manager

    @pytest.mark.asyncio
    async def test_list_devices(self, device_manager):
        """Test listing devices."""
        # Call the method
        devices = await device_manager.list_devices()

        # Verify the result
        assert len(devices) == 2
        assert devices[0].serial == "device1"
        assert devices[1].serial == "192.168.1.100:5555"

        # Check that the ADB wrapper's get_devices method was called
        device_manager._adb.get_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_device_existing(self, device_manager):
        """Test getting an existing device."""
        # Call the method
        device = await device_manager.get_device("device1")

        # Verify the result
        assert device is not None
        assert device.serial == "device1"

        # Check that the ADB wrapper's get_devices method was called
        device_manager._adb.get_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_device_nonexistent(self, device_manager):
        """Test getting a non-existent device."""
        # Call the method
        device = await device_manager.get_device("nonexistent")

        # Verify the result
        assert device is None

        # Check that the ADB wrapper's get_devices method was called
        device_manager._adb.get_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect(self, device_manager):
        """Test connecting to a device over TCP/IP."""
        # Mock the ADB connect method
        device_manager._adb.connect_device_tcp = AsyncMock(return_value="192.168.1.101:5555")

        # Call the method
        device = await device_manager.connect("192.168.1.101")

        # Verify the result
        assert device is not None
        assert device.serial == "192.168.1.101:5555"

        # Check that the ADB wrapper's connect_device_tcp method was called
        device_manager._adb.connect_device_tcp.assert_called_once_with("192.168.1.101", 5555)

    @pytest.mark.asyncio
    async def test_disconnect_success(self, device_manager):
        """Test disconnecting from a device successfully."""
        # Mock the ADB disconnect method
        device_manager._adb.disconnect_device = AsyncMock(return_value=True)

        # Call the method
        result = await device_manager.disconnect("192.168.1.100:5555")

        # Verify the result
        assert result is True

        # Check that the ADB wrapper's disconnect_device method was called
        device_manager._adb.disconnect_device.assert_called_once_with("192.168.1.100:5555")

    @pytest.mark.asyncio
    async def test_disconnect_failure(self, device_manager):
        """Test disconnecting from a device that fails."""
        # Mock the ADB disconnect method
        device_manager._adb.disconnect_device = AsyncMock(return_value=False)

        # Call the method
        result = await device_manager.disconnect("device1")

        # Verify the result
        assert result is False

        # Check that the ADB wrapper's disconnect_device method was called
        device_manager._adb.disconnect_device.assert_called_once_with("device1")

    @pytest.mark.asyncio
    async def test_singleton_access(self):
        """Test that get_device_manager returns the initialized instance."""
        # Get the device manager
        device_manager = get_device_manager()

        # Verify it's not None
        assert device_manager is not None
        assert isinstance(device_manager, DeviceManager)


class TestDevice:
    """Tests for the Device class."""

    @pytest.fixture
    def device(self):
        """Create a Device instance with mocked ADB wrapper."""
        with patch("droidmind.devices.ADBWrapper") as mock_adb_class:
            # Set up the mock ADB wrapper
            mock_adb = mock_adb_class.return_value

            # Mock the device properties
            mock_adb.get_device_properties = AsyncMock(
                return_value={
                    "ro.product.model": "Pixel 4",
                    "ro.product.brand": "Google",
                    "ro.build.version.release": "11",
                    "ro.build.version.sdk": "30",
                    "ro.build.display.id": "RQ3A.211001.001",
                }
            )

            # Mock other methods
            mock_adb.shell = AsyncMock(return_value="command output")
            mock_adb.reboot_device = AsyncMock(return_value="Device rebooted")

            # Create the Device
            device = Device("device1", adb=mock_adb)
            yield device

    @pytest.mark.asyncio
    async def test_get_properties(self, device):
        """Test getting device properties."""
        # Call the method
        properties = await device.get_properties()

        # Verify the result
        assert properties["ro.product.model"] == "Pixel 4"
        assert properties["ro.product.brand"] == "Google"
        assert properties["ro.build.version.release"] == "11"

        # Check that the ADB wrapper's get_device_properties method was called
        device._adb.get_device_properties.assert_called_once_with("device1")

    @pytest.mark.asyncio
    async def test_model_property(self, device):
        """Test the model property."""
        # Call the property
        model = await device.model

        # Verify the result
        assert model == "Pixel 4"

        # The get_properties method should have been called which calls get_device_properties
        device._adb.get_device_properties.assert_called_once_with("device1")

    @pytest.mark.asyncio
    async def test_run_shell(self, device):
        """Test running a shell command."""
        # Call the method
        result = await device.run_shell("ls -la")

        # Verify the result
        assert result == "command output"

        # Check that the ADB wrapper's shell method was called
        device._adb.shell.assert_called_once_with("device1", "ls -la")

    @pytest.mark.asyncio
    async def test_reboot(self, device):
        """Test rebooting the device."""
        # Call the method
        result = await device.reboot("recovery")

        # Verify the result
        assert result == "Device rebooted"

        # Check that the ADB wrapper's reboot_device method was called
        device._adb.reboot_device.assert_called_once_with("device1", "recovery")

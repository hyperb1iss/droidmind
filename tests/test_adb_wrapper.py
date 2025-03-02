"""Tests for the ADB wrapper module."""

import os
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from adb_shell.exceptions import AdbConnectionError
import pytest
import pytest_asyncio

from droidmind.adb.wrapper import ADBWrapper


class TestADBWrapper(unittest.TestCase):
    """Test the ADB wrapper module."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for the ADB key
        self.temp_dir = tempfile.mkdtemp(prefix="droidmind_test_")
        self.adb_key_path = os.path.join(self.temp_dir, "adbkey")

        # Patch the key generation and loading
        self.keygen_patcher = patch("droidmind.adb.wrapper.keygen")
        self.mock_keygen = self.keygen_patcher.start()

        self.signer_patcher = patch("droidmind.adb.wrapper.PythonRSASigner")
        self.mock_signer = self.signer_patcher.start()
        self.mock_signer.return_value = MagicMock()

        # Create empty key files
        with open(self.adb_key_path, "w") as f:
            f.write("mock_private_key")
        with open(f"{self.adb_key_path}.pub", "w") as f:
            f.write("mock_public_key")

    def tearDown(self):
        """Clean up test environment."""
        self.keygen_patcher.stop()
        self.signer_patcher.stop()

        # Remove temporary directory
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test ADBWrapper initialization."""
        wrapper = ADBWrapper(adb_key_path=self.adb_key_path)

        # Verify key loading
        assert wrapper.adb_key_path == self.adb_key_path
        self.mock_signer.assert_called_once_with("mock_public_key", "mock_private_key")

        # Verify defaults
        assert wrapper.connection_timeout == 10.0
        assert wrapper.auth_timeout == 1.0
        assert wrapper._devices == {}

    def test_ensure_adb_key_exists(self):
        """Test ADB key generation if it doesn't exist."""
        # Remove existing key
        os.remove(self.adb_key_path)
        os.remove(f"{self.adb_key_path}.pub")

        # Mock the key generation to actually create the files
        def mock_keygen_impl(path):
            with open(path, "w") as f:
                f.write("generated_private_key")
            with open(f"{path}.pub", "w") as f:
                f.write("generated_public_key")

        self.mock_keygen.side_effect = mock_keygen_impl

        # Initialize wrapper, should trigger key generation
        ADBWrapper(adb_key_path=self.adb_key_path)

        # Verify key generation
        self.mock_keygen.assert_called_once_with(self.adb_key_path)


@pytest.mark.asyncio
class TestADBWrapperAsync:
    """Test the async methods of ADBWrapper."""

    @pytest_asyncio.fixture
    async def wrapper(self, request):
        """Set up ADBWrapper for testing."""
        with (
            patch("droidmind.adb.wrapper.keygen"),
            patch("droidmind.adb.wrapper.PythonRSASigner") as mock_signer,
        ):
            mock_signer.return_value = MagicMock()

            # Create a temporary directory for the ADB key
            temp_dir = tempfile.mkdtemp(prefix="droidmind_test_")
            adb_key_path = os.path.join(temp_dir, "adbkey")

            # Create empty key files
            os.makedirs(os.path.dirname(adb_key_path), exist_ok=True)
            with open(adb_key_path, "w") as f:
                f.write("mock_private_key")
            with open(f"{adb_key_path}.pub", "w") as f:
                f.write("mock_public_key")

            wrapper = ADBWrapper(adb_key_path=adb_key_path)

            # Add finalizer for cleanup
            def cleanup():
                import shutil

                shutil.rmtree(temp_dir)

            request.addfinalizer(cleanup)

            return wrapper

    async def test_connect_device_tcp(self, wrapper):
        """Test connecting to a device over TCP/IP."""
        device_mock = MagicMock()

        with (
            patch("droidmind.adb.wrapper.AdbDeviceTcp") as mock_device_class,
            patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
        ):
            mock_device_class.return_value = device_mock

            # Test successful connection
            serial = await wrapper.connect_device_tcp("192.168.1.100")

            # Verify the AdbDeviceTcp was created correctly
            mock_device_class.assert_called_once_with("192.168.1.100", 5555, default_transport_timeout_s=10.0)

            # Verify connect was called with the right parameters
            mock_to_thread.assert_called_once_with(device_mock.connect, rsa_keys=[wrapper.signer], auth_timeout_s=1.0)

            # Verify the device was added to the connected devices
            assert serial == "192.168.1.100:5555"
            assert serial in wrapper._devices
            assert wrapper._devices[serial] == device_mock

    async def test_connect_device_tcp_error(self, wrapper):
        """Test error handling when connecting to a device."""
        with (
            patch("droidmind.adb.wrapper.AdbDeviceTcp") as mock_device_class,
            patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
        ):
            device_mock = MagicMock()
            mock_device_class.return_value = device_mock

            # Simulate connection error
            mock_to_thread.side_effect = AdbConnectionError("Connection failed")

            # Test connection failure
            with pytest.raises(AdbConnectionError):
                await wrapper.connect_device_tcp("192.168.1.100")

            # Verify the device was not added
            assert wrapper._devices == {}

    async def test_disconnect_device(self, wrapper):
        """Test disconnecting from a device."""
        # Set up mock device
        device_mock = MagicMock()
        wrapper._devices = {"192.168.1.100:5555": device_mock}

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            # Test successful disconnection
            success = await wrapper.disconnect_device("192.168.1.100:5555")

            # Verify disconnect was called
            mock_to_thread.assert_called_once_with(device_mock.close)

            # Verify the device was removed
            assert success is True
            assert wrapper._devices == {}

    async def test_disconnect_device_not_connected(self, wrapper):
        """Test disconnecting from a device that is not connected."""
        # Test disconnecting a device that doesn't exist
        success = await wrapper.disconnect_device("nonexistent:5555")

        # Verify the result
        assert success is False

    async def test_shell(self, wrapper):
        """Test running a shell command on a device."""
        # Set up mock device
        device_mock = MagicMock()
        device_mock.shell = AsyncMock(return_value="command output")
        wrapper._devices = {"192.168.1.100:5555": device_mock}

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = "command output"

            # Test running a shell command
            output = await wrapper.shell("192.168.1.100:5555", "ls -la")

            # Verify shell was called with the right command
            mock_to_thread.assert_called_once_with(device_mock.shell, "ls -la")

            # Verify the output
            assert output == "command output"

    async def test_shell_device_not_connected(self, wrapper):
        """Test running a shell command on a device that is not connected."""
        # Test running a command on a device that doesn't exist
        with pytest.raises(ValueError):
            await wrapper.shell("nonexistent:5555", "ls -la")

    async def test_get_device_properties(self, wrapper):
        """Test getting device properties."""
        # Set up mock device
        device_mock = MagicMock()
        wrapper._devices = {"192.168.1.100:5555": device_mock}

        # Mock getprop output
        getprop_output = """
[ro.build.version.release]: [11]
[ro.build.version.sdk]: [30]
[ro.product.model]: [Pixel 4]
"""

        with patch.object(wrapper, "shell", new_callable=AsyncMock) as mock_shell:
            mock_shell.return_value = getprop_output

            # Test getting device properties
            properties = await wrapper.get_device_properties("192.168.1.100:5555")

            # Verify shell was called with getprop
            mock_shell.assert_called_once_with("192.168.1.100:5555", "getprop")

            # Verify the properties were parsed correctly
            assert len(properties) == 3
            assert properties["ro.build.version.release"] == "11"
            assert properties["ro.build.version.sdk"] == "30"
            assert properties["ro.product.model"] == "Pixel 4"

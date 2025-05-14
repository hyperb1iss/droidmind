"""Pytest configuration and fixtures for DroidMind tests."""

from unittest.mock import patch

import pytest

from droidmind.devices import DeviceManager, set_device_manager


@pytest.fixture(scope="session", autouse=True)
def _initialize_device_manager():
    """Initialize the DeviceManager singleton before tests run.

    This fixture runs automatically at the start of the test session and
    ensures the DeviceManager is properly initialized.
    """
    # Initialize the DeviceManager with a mock ADB path
    device_manager = DeviceManager(adb_path=None)

    # Patch get_device_manager to return our instance
    with patch("droidmind.devices.get_device_manager", return_value=device_manager):
        # Also set it via the normal method to ensure both access patterns work
        set_device_manager(device_manager)
        yield

    # Clean up can be done here if needed

"""Device information resources for DroidMind."""

from droidmind.context import mcp
from droidmind.devices import get_device_manager


@mcp.resource("devices://list")
async def get_devices_list() -> str:
    """
    Get a list of all connected devices as a resource.

    Returns:
        A markdown-formatted list of connected devices
    """
    devices = await get_device_manager().list_devices()

    if not devices:
        return "No devices connected."

    result = "# Connected Devices\n\n"
    for i, device in enumerate(devices, 1):
        model = await device.model
        android_version = await device.android_version
        result += f"## Device {i}: {model}\n"
        result += f"- **Serial**: `{device.serial}`\n"
        result += f"- **Android Version**: {android_version}\n"

    return result

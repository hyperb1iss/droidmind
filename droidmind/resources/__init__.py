"""
DroidMind Resources - Resource implementations for the DroidMind MCP server.

This module provides resource implementations for the DroidMind MCP server,
allowing AI assistants to access device data in a structured way.

Resources are like read-only endpoints that expose data to the AI assistant.
"""

from droidmind.devices import get_device_manager
from droidmind.resources.app_resources import (
    app_logs,
    app_manifest,
)
from droidmind.resources.device_info import get_devices_list
from droidmind.resources.logs import device_anr_logs, device_battery_stats, device_crash_logs

__all__ = [
    "app_logs",
    "app_manifest",
    "device_anr_logs",
    "device_battery_stats",
    "device_crash_logs",
    "get_devices_list",
]

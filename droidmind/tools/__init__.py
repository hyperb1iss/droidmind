"""
DroidMind Tools Package - MCP tools for controlling Android devices.

This package provides MCP tools for controlling Android devices via ADB.
Tools are organized by functionality into separate modules.
"""

import logging

from droidmind.devices import get_device_manager
from droidmind.tools.app_management import (
    clear_app_data,
    get_app_activities,
    get_app_info,
    get_app_manifest,
    get_app_permissions,
    install_app,
    list_packages,
    start_app,
    stop_app,
    uninstall_app,
)

# Re-export all tool functions for backward compatibility
from droidmind.tools.device_management import (
    connect_device,
    device_properties,
    disconnect_device,
    list_devices,
    reboot_device,
)
from droidmind.tools.diagnostics import (
    capture_bugreport,
    dump_heap,
)
from droidmind.tools.file_operations import file_operations
from droidmind.tools.logs import (
    app_logs,
    device_anr_logs,
    device_battery_stats,
    device_crash_logs,
    device_logcat,
)
from droidmind.tools.media import (
    screenshot,
)
from droidmind.tools.shell import (
    shell_command,
)
from droidmind.tools.ui import (
    input_text,
    press_key,
    start_intent,
    swipe,
    tap,
)

# Re-export get_device_manager for backward compatibility
__all__ = [
    "app_logs",
    "capture_bugreport",
    "clear_app_data",
    "connect_device",
    "device_anr_logs",
    "device_battery_stats",
    "device_crash_logs",
    "device_logcat",
    "device_properties",
    "disconnect_device",
    "dump_heap",
    "file_operations",
    "get_app_activities",
    "get_app_info",
    "get_app_manifest",
    "get_app_permissions",
    "get_device_manager",
    "input_text",
    "install_app",
    "list_devices",
    "list_packages",
    "press_key",
    "reboot_device",
    "screenshot",
    "shell_command",
    "start_app",
    "start_intent",
    "stop_app",
    "swipe",
    "tap",
    "uninstall_app",
]

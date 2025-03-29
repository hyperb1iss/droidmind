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
from droidmind.tools.file_operations import (
    create_directory,
    delete_file,
    file_exists,
    file_stats,
    list_directory,
    pull_file,
    push_file,
    read_file,
    write_file,
)
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
    # App logs and diagnostics
    "app_logs",
    # Diagnostics
    "capture_bugreport",
    # App management
    "clear_app_data",
    # Device management
    "connect_device",
    "create_directory",
    "delete_file",
    "device_anr_logs",
    "device_battery_stats",
    "device_crash_logs",
    "device_logcat",
    "device_properties",
    "disconnect_device",
    "dump_heap",
    "file_exists",
    # File operations
    "file_stats",
    # App management
    "get_app_activities",
    "get_app_info",
    "get_app_manifest",
    "get_app_permissions",
    # Utilities
    "get_device_manager",
    # UI automation
    "input_text",
    # App management
    "install_app",
    "list_devices",
    # File operations
    "list_directory",
    "list_packages",
    "press_key",
    "pull_file",
    "push_file",
    "read_file",
    "reboot_device",
    # Media
    "screenshot",
    # Shell
    "shell_command",
    "start_app",
    "start_intent",
    "stop_app",
    "swipe",
    "tap",
    "uninstall_app",
    "write_file",
]

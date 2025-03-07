"""
DroidMind Tools Package - MCP tools for controlling Android devices.

This package provides MCP tools for controlling Android devices via ADB.
Tools are organized by functionality into separate modules.
"""

import logging

from droidmind.devices import get_device_manager
from droidmind.tools.app_management import (
    clear_app_data,
    install_app,
    list_packages,
    start_app,
    stop_app,
    uninstall_app,
)
from droidmind.tools.device_info import (
    device_properties,
)

# Re-export all tool functions for backward compatibility
from droidmind.tools.device_management import (
    connect_device,
    devicelist,
    disconnect_device,
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
    list_directory,
    pull_file,
    push_file,
    read_file,
    write_file,
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
    # Diagnostics
    "capture_bugreport",
    # Device management
    "connect_device",
    "create_directory",
    "delete_file",
    # Device info
    "device_properties",
    # Device management
    "devicelist",
    "disconnect_device",
    "dump_heap",
    "file_exists",
    # Utilities
    "get_device_manager",
    # UI automation
    "input_text",
    # App management
    "install_app",
    # File operations
    "list_directory",
    "press_key",
    "pull_file",
    "push_file",
    "read_file",
    "reboot_device",
    # Media
    "screenshot",
    # Shell
    "shell_command",
    "start_intent",
    "swipe",
    "tap",
    "write_file",
]

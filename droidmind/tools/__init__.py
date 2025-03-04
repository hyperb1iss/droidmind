"""
DroidMind Tools Package - MCP tools for controlling Android devices.

This package provides MCP tools for controlling Android devices via ADB.
Tools are organized by functionality into separate modules.
"""

import logging

from mcp.server.fastmcp import Context

from droidmind.devices import DeviceManager, get_device_manager
from droidmind.tools.app_management import (
    install_app,
)
from droidmind.tools.device_info import (
    device_logcat,
    device_properties,
)

# Re-export all tool functions for backward compatibility
from droidmind.tools.device_management import (
    connect_device,
    devicelist,
    disconnect_device,
    reboot_device,
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
    "connect_device",
    "create_directory",
    "delete_file",
    "device_logcat",
    # Device info
    "device_properties",
    # Device management
    "devicelist",
    "disconnect_device",
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

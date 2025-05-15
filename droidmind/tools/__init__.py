"""
DroidMind Tools Package - MCP tools for controlling Android devices.

This package provides MCP tools for controlling Android devices via ADB.
Tools are organized by functionality into separate modules.
"""

import logging

from droidmind.devices import get_device_manager
from droidmind.tools.app_management import (
    app_operations,
)

# Re-export all tool functions for backward compatibility
from droidmind.tools.device_management import (
    android_device,
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
    "android_device",
    "app_logs",
    "app_operations",
    "capture_bugreport",
    "device_anr_logs",
    "device_battery_stats",
    "device_crash_logs",
    "device_logcat",
    "dump_heap",
    "file_operations",
    "get_device_manager",
    "input_text",
    "press_key",
    "screenshot",
    "shell_command",
    "start_intent",
    "swipe",
    "tap",
]

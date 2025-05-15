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
    android_diag,
)
from droidmind.tools.file_operations import file_operations
from droidmind.tools.logs import (
    android_log,
)
from droidmind.tools.media import (
    screenshot,
)
from droidmind.tools.shell import (
    shell_command,
)
from droidmind.tools.ui import (
    android_ui,
)

# Re-export get_device_manager for backward compatibility
__all__ = [
    "android_device",
    "android_diag",
    "android_log",
    "android_ui",
    "app_operations",
    "file_operations",
    "get_device_manager",
    "screenshot",
    "shell_command",
]

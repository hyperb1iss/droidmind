"""
DroidMind Prompts - Prompt implementations for the DroidMind MCP server.

This module provides all the prompt templates for the DroidMind MCP server,
allowing AI assistants to have pre-defined interaction patterns.
"""

import logging

from droidmind.core import mcp

logger = logging.getLogger("droidmind")


@mcp.prompt()
def debug_app_crash(app_package: str) -> str:
    """
    Generate a prompt to debug an app crash.

    Args:
        app_package: The package name of the crashed app
    """
    return f"""I need help debugging a crash in my Android app with package name '{app_package}'.

Can you help me:
1. Capture the relevant logcat output for this app
2. Analyze the stack trace and error messages
3. Identify the root cause of the crash
4. Suggest potential fixes

Please include specific code or configuration changes that might solve the issue.
"""


@mcp.prompt()
def analyze_battery_usage() -> str:
    """Generate a prompt to analyze battery usage on a device."""
    return """I need help analyzing battery usage on my Android device.

Can you:
1. Capture battery stats and analyze which apps or services are consuming the most power
2. Identify any wakelocks or processes preventing the device from entering deep sleep
3. Suggest optimizations to improve battery life
4. Recommend settings changes or apps that could help monitor or reduce battery consumption

Please include both immediate actions I can take and long-term strategies for battery optimization.
"""

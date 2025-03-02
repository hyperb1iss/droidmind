"""
DroidMind Resources - Resource implementations for the DroidMind MCP server.

This module provides resource implementations for the DroidMind MCP server,
allowing AI assistants to access device data in a structured way.

Resources are like read-only endpoints that expose data to the AI assistant.
"""

import logging

logger = logging.getLogger("droidmind")


# Example resource implementation (commented out for future use)
# @mcp.resource("devices://list")
# async def get_devices_list(ctx: Context) -> str:
#     """
#     Get a list of all connected devices as a resource.
#
#     Returns:
#         A markdown-formatted list of connected devices
#     """
#     adb = ctx.request_context.lifespan_context.adb
#     devices = await adb.get_devices()
#
#     if not devices:
#         return "No devices connected."
#
#     result = "# Connected Devices\n\n"
#     for device in devices:
#         result += f"- **{device.get('model', 'Unknown')}** (`{device.get('serial', 'Unknown')}`)\n"
#
#     return result

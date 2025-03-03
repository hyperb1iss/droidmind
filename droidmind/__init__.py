"""
DroidMind - Control Android devices with AI via Model Context Protocol.

This package provides a server that implements the Model Context Protocol (MCP)
to allow AI assistants to control and interact with Android devices.
"""

# Import core modules to register resources and tools
from droidmind.context import mcp
import droidmind.resources  # Imported for side effects
import droidmind.tools  # Imported for side effects

__version__ = "0.1.0"
__all__ = ["adb", "core", "prompts", "resources", "server", "tools", "utils"]

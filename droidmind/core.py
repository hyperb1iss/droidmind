"""
DroidMind Core - Core functionality for the DroidMind MCP server.

This module provides the core classes and functionality for the DroidMind
MCP server, including context management and server lifecycle.
"""

import logging

from droidmind.mcp_instance import mcp  # Imported for side effects # noqa: F401

# We don't need to import resources here, as they will register themselves
# when imported elsewhere (like in __init__.py)

logger = logging.getLogger("droidmind")

"""
DroidMind Core - Core functionality for the DroidMind MCP server.

This module provides the core classes and functionality for the DroidMind
MCP server, including context management and server lifecycle.
"""

from dataclasses import dataclass
import logging

from mcp.server.fastmcp import FastMCP

from droidmind.adb.wrapper import ADBWrapper

logger = logging.getLogger("droidmind")


@dataclass
class DroidMindContext:
    """Context for DroidMind server.

    This class stores the context for the DroidMind server, including
    the ADB wrapper and temporary directory for file operations.
    """

    adb: ADBWrapper
    temp_dir: str


# Create the MCP server
mcp = FastMCP(
    "DroidMind",
    description="Control Android devices with MCP",
    dependencies=["rich>=13.9.4"],
)

# Import tools and resources to register them with the MCP server
# These imports must come after the mcp server creation to avoid circular imports

"""
DroidMind MCP Instance.

This module provides the MCP server instance for the DroidMind application.
It's separated to avoid cyclic imports between core.py and tools.py.
"""

from mcp.server.fastmcp import FastMCP

# Create the MCP server with lifespan
mcp = FastMCP(
    "DroidMind",
    instructions="Control Android devices with MCP",
    dependencies=["rich>=13.9.4"],
)

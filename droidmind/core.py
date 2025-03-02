"""
DroidMind Core - Core functionality for the DroidMind MCP server.

This module provides the core classes and functionality for the DroidMind
MCP server, including context management and server lifecycle.
"""

import logging
import os
import shutil
import tempfile
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

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


@asynccontextmanager
async def droidmind_lifespan(server: FastMCP) -> AsyncIterator[DroidMindContext]:
    """Initialize and clean up DroidMind resources.

    Args:
        server: The FastMCP server instance

    Yields:
        DroidMindContext: The context for the DroidMind server
    """
    # Don't print banner here - it's already printed at server startup
    logger.info("Initializing DroidMind session...")

    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="droidmind_")
    logger.info(f"Created temporary directory: {temp_dir}")

    # Initialize ADB wrapper
    adb = ADBWrapper()

    try:
        # Yield context to the server
        yield DroidMindContext(adb=adb, temp_dir=temp_dir)

    finally:
        # Clean up
        logger.info("Shutting down DroidMind session...")

        # Disconnect all devices
        devices = await adb.get_devices()
        for device in devices:
            serial = device["serial"]
            await adb.disconnect_device(serial)

        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Removed temporary directory: {temp_dir}")


# Create the MCP server
mcp = FastMCP(
    "DroidMind",
    description="Control Android devices with MCP",
    lifespan=droidmind_lifespan,
    dependencies=["adb-shell>=0.4.4", "rich>=13.9.4"],
)

"""
DroidMind MCP Instance.

This module provides the MCP server instance for the DroidMind application.
It's separated to avoid cyclic imports between core.py and tools.py.
"""

from collections.abc import AsyncGenerator
import contextlib
from dataclasses import dataclass
import logging
import shutil
import tempfile

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


# Create a lifespan function for the MCP server
@contextlib.asynccontextmanager
async def mcp_lifespan(_server: FastMCP) -> AsyncGenerator[DroidMindContext]:
    """Lifespan context manager for the MCP server.

    This sets up the ADB service and temporary directory for the server.
    """
    # Avoid circular import
    from droidmind.adb.service import ADBService

    # Create a temporary directory for file operations
    temp_dir = tempfile.mkdtemp(prefix="droidmind_")
    logger.debug("Created temporary directory: %s", temp_dir)

    # Set up the ADB service with the temp directory
    adb_service = await ADBService.get_instance()
    adb_service.set_temp_dir(temp_dir)
    logger.debug("ADB service initialized with temp directory")

    # Create the context object
    context = DroidMindContext(adb=adb_service.adb, temp_dir=temp_dir)

    try:
        # Yield the context to the server
        yield context
    finally:
        # Clean up ADB service
        try:
            await adb_service.cleanup()
            logger.debug("ADB service cleaned up")
        except Exception:
            # We need to catch all exceptions during cleanup to ensure resources are released
            logger.exception("Error cleaning up ADB service")

        # Remove temporary directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug("Removed temporary directory: %s", temp_dir)
        except Exception:
            # We need to catch all exceptions during cleanup to ensure resources are released
            logger.exception("Error removing temporary directory")


# Create the MCP server with lifespan
mcp = FastMCP(
    "DroidMind",
    description="Control Android devices with MCP",
    dependencies=["rich>=13.9.4"],
    lifespan=mcp_lifespan,
)

"""
DroidMind Core - Core functionality for the DroidMind MCP server.

This module provides the core classes and functionality for the DroidMind
MCP server, including context management and server lifecycle.
"""

from collections.abc import AsyncGenerator
import contextlib
from dataclasses import dataclass
import logging
import tempfile

from mcp.server.fastmcp import FastMCP

from droidmind.adb.service import ADBService
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
async def mcp_lifespan(server: object) -> AsyncGenerator[DroidMindContext]:
    """Lifespan context manager for the MCP server.

    This sets up the ADB service and temporary directory for the server.
    """
    # Create a temporary directory for file operations
    temp_dir = tempfile.mkdtemp(prefix="droidmind_")
    logger.debug(f"Created temporary directory: {temp_dir}")

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
        except Exception as e:
            logger.error(f"Error cleaning up ADB service: {e}")

        # Remove temporary directory
        try:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug(f"Removed temporary directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Error removing temporary directory: {e}")


# Create the MCP server
mcp = FastMCP(
    "DroidMind",
    description="Control Android devices with MCP",
    dependencies=["rich>=13.9.4"],
    lifespan=mcp_lifespan,
)

# Import tools and resources to register them with the MCP server
# These imports must come after the mcp server creation to avoid circular imports


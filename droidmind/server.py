"""
DroidMind MCP Server.

This module implements the command-line interface and server startup for DroidMind.
It delegates core functionality to specialized modules.
"""

import ipaddress
import logging
import signal
import sys
from typing import Any, cast

# Third-party imports
import anyio
import click
from mcp.server.stdio import stdio_server

# First-party imports (DroidMind modules)
from droidmind.core import mcp
from droidmind.networking import setup_sse_server
from droidmind.utils import console

# Defer logging configuration until after command line parsing
logger = logging.getLogger("droidmind")


# Main entrypoint
@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the server to (use 0.0.0.0 for all interfaces)",
)
@click.option("--port", default=8000, type=int, help="Port to listen on for network connections")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type to use (stdio for terminal, sse for network)",
)
@click.option("--debug/--no-debug", default=False, help="Enable debug mode for more verbose logging")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set the logging level",
)
def main(host: str, port: int, transport: str, debug: bool, log_level: str) -> None:
    """
    DroidMind MCP Server - Control Android devices with AI assistants.

    This server implements the Model Context Protocol (MCP) to allow AI assistants
    to control and interact with Android devices via ADB.
    """
    # Start visual elements before configuring logging
    # Display the banner right away
    console.print_banner()

    # Prepare server configuration info
    config: dict[str, Any] = {
        "transport": transport.upper(),
        "host": host,
        "port": port,
        "debug": debug,
        "log_level": log_level if not debug else "DEBUG",
    }

    # Validate host before showing config
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if host != "localhost":
            config["host"] = "127.0.0.1"
            config["host_note"] = f"(Changed from {host} - invalid address)"

    # Display beautiful configuration with NeonGlam aesthetic
    console.display_system_info(config)

    # Configure logging using our ultimate NeonGlam config from console.py
    handler = console.create_custom_handler()

    # Configure basic logging with our custom handler
    logging.basicConfig(
        level=getattr(logging, str(config["log_level"])),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler],
        force=True,  # Make sure we override any existing configuration
    )
    logger.setLevel(logging.DEBUG if debug else getattr(logging, log_level))
    logger.handlers = [handler]
    logger.propagate = False

    # Also configure Uvicorn loggers with our custom handler
    for uv_logger in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        uvicorn_logger = logging.getLogger(uv_logger)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False

    # Set up signal handlers
    def handle_exit(signum: int, _: object = None) -> None:
        logger.info("Received signal %s, shutting down gracefully...", signal.Signals(signum).name)
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Start appropriate server based on transport mode
    if transport == "sse":
        # Launch the SSE server - no need to display connection info again
        setup_sse_server(
            cast(str, config["host"]),
            cast(int, config["port"]),
            mcp,
            debug
        )
    else:
        # Use stdio transport for terminal use
        logger.info("Using stdio transport for terminal interaction")

        # Launch the stdio server
        async def arun() -> None:
            async with stdio_server() as streams:
                # Log that we're ready to accept commands
                console.startup_complete()

                # Use the public FastMCP run method
                await mcp.run(
                    streams[0],
                    streams[1],
                )

        anyio.run(arun)


if __name__ == "__main__":
    main(host="127.0.0.1", port=8000, transport="stdio", debug=False, log_level="INFO")

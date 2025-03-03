"""
DroidMind MCP Server.

This module implements the command-line interface and server startup for DroidMind.
It delegates core functionality to specialized modules.
"""

import ipaddress
import logging
from typing import Any, cast

import anyio
import click
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.routing import Mount, Route
import uvicorn

from droidmind.mcp_instance import mcp
from droidmind.utils import console

logger = logging.getLogger("droidmind")


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
    logging.basicConfig(
        level=getattr(logging, str(config["log_level"])),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler],
        force=True,
    )
    logger.setLevel(logging.DEBUG if debug else getattr(logging, log_level))
    logger.handlers = [handler]
    logger.propagate = False

    # Also configure Uvicorn loggers with our custom handler
    for uv_logger in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        uvicorn_logger = logging.getLogger(uv_logger)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False

    if transport == "sse":
        # Set up SSE transport
        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Request) -> None:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await mcp._mcp_server.run(
                    streams[0],
                    streams[1],
                    mcp._mcp_server.create_initialization_options(),
                )

        # Create Starlette app with CORS middleware
        app = Starlette(
            debug=debug,
            middleware=[
                Middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_methods=["GET", "POST"],
                    allow_headers=["*"],
                )
            ],
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        # Run the server
        uvicorn.run(app, host=cast(str, config["host"]), port=cast(int, config["port"]), log_config=None)
    else:
        # Use stdio transport for terminal use
        logger.info("Using stdio transport for terminal interaction")
        from mcp.server.stdio import stdio_server

        async def arun() -> None:
            async with stdio_server() as streams:
                # Log that we're ready to accept commands
                console.startup_complete()
                await mcp._mcp_server.run(
                    streams[0],
                    streams[1],
                    mcp._mcp_server.create_initialization_options(),
                )

        anyio.run(arun)


if __name__ == "__main__":
    main(
        host="127.0.0.1",
        port=8000,
        transport="stdio",
        debug=False,
        log_level="INFO"
    )

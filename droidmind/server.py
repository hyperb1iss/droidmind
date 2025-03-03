"""
DroidMind MCP Server.

This module implements the command-line interface and server startup for DroidMind.
It delegates core functionality to specialized modules.
"""

import asyncio
import ipaddress
import logging
from typing import Any, cast

import anyio
import click
from mcp.server.sse import SseServerTransport
from rich.logging import RichHandler
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.routing import Mount, Route
import uvicorn

from droidmind.context import mcp
from droidmind.devices import DeviceManager, set_device_manager

from . import console

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
@click.option(
    "--adb-path",
    type=str,
    default=None,
    help="Path to the ADB binary (uses auto-detection if not specified)",
)
def main(host: str, port: int, transport: str, debug: bool, log_level: str, adb_path: str | None) -> None:
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
        "adb_path": adb_path or "auto-detected",
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

    # Configure logging using Rich
    handler = RichHandler(console=console.console, rich_tracebacks=True)
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

    # Initialize the global device manager with the specified ADB path
    set_device_manager(DeviceManager(adb_path=adb_path))
    logger.debug("Global device manager initialized with ADB path: %s", adb_path or "auto-detected")

    if transport == "sse":
        # Define middleware to suppress 'NoneType object is not callable' errors during shutdown
        class SuppressNoneTypeErrorMiddleware:
            def __init__(self, app: Any) -> None:
                self.app = app

            async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
                try:
                    await self.app(scope, receive, send)
                except TypeError as e:
                    if "NoneType" in str(e) and "not callable" in str(e):
                        pass
                    else:
                        raise

        # Set up SSE transport
        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Request) -> None:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                try:
                    await mcp._mcp_server.run(
                        streams[0],
                        streams[1],
                        mcp._mcp_server.create_initialization_options(),
                    )
                except asyncio.CancelledError:
                    logger.debug("ASGI connection cancelled, shutting down quietly.")
                except Exception as e:  # noqa: BLE001
                    logger.debug("ASGI connection ended with exception: %s", e)

        # Create Starlette app with custom middleware including our suppressor and CORS
        app = Starlette(
            debug=debug,
            middleware=[
                Middleware(SuppressNoneTypeErrorMiddleware),
                Middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_methods=["GET", "POST"],
                    allow_headers=["*"],
                ),
            ],
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        # Create a custom Uvicorn config with our shutdown handler
        uvicorn_config = uvicorn.Config(
            app,
            host=cast(str, config["host"]),
            port=cast(int, config["port"]),
            log_config=None,
            timeout_graceful_shutdown=0,  # Shutdown immediately
        )
        # Create server with the Config object
        server = uvicorn.Server(uvicorn_config)

        try:
            asyncio.run(server.serve())
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, shutting down gracefully.")
        except Exception as e:
            logger.exception("Server encountered exception during shutdown: %s", e)

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
    main(host="127.0.0.1", port=8000, transport="stdio", debug=False, log_level="INFO", adb_path="adb")

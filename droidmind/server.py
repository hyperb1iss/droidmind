"""
DroidMind MCP Server.

This module implements the command-line interface and server startup for DroidMind.
It delegates core functionality to specialized modules.
"""

import asyncio
import ipaddress
import sys
import traceback
from types import TracebackType
from typing import Any, cast

import anyio
import click
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from rich.logging import RichHandler
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.types import ASGIApp, Receive, Scope, Send
import uvicorn

# Annotated modules with MCP prompts and tools
from droidmind import (  # noqa: F401
    console,
    prompts,
    tools,
)
from droidmind.context import mcp
from droidmind.devices import DeviceManager, set_device_manager
from droidmind.log import logger, setup_logging


# Custom exception handler for TaskGroup exceptions
def handle_taskgroup_exception(exc: BaseException) -> None:
    """Handle TaskGroup exceptions by extracting and logging all nested exceptions.

    Args:
        exc: The exception to handle
    """
    # Log the main exception
    logger.error("TaskGroup exception occurred: %s", exc)

    # Extract and log all nested exceptions
    if isinstance(exc, BaseExceptionGroup):
        for i, e in enumerate(exc.exceptions):
            logger.error("TaskGroup sub-exception %d: %s", i + 1, e)
            logger.error("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    # Check for __context__ attribute (chained exceptions)
    if hasattr(exc, "__context__") and exc.__context__ is not None:
        logger.error("Chained exception: %s", exc.__context__)
        logger.error(
            "".join(traceback.format_exception(type(exc.__context__), exc.__context__, exc.__context__.__traceback__))
        )


def setup_asyncio_exception_handler() -> None:
    """Set up the asyncio exception handler."""

    # Set up asyncio exception handler
    def asyncio_exception_handler(_loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
        # Extract exception
        exception = context.get("exception")
        if exception:
            logger.error("Unhandled asyncio exception: %s", exception)
            handle_taskgroup_exception(exception)
        else:
            logger.error("Unhandled asyncio error: %s", context["message"])

    # Get the current event loop and set the exception handler
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(asyncio_exception_handler)


def setup_global_exception_handler() -> None:
    """Set up the global exception handler."""

    def global_exception_handler(
        exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            # Let KeyboardInterrupt pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # For all other exceptions, log them with our custom handler
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        # Also handle TaskGroup exceptions
        handle_taskgroup_exception(exc_value)

    # Install the global exception handler
    sys.excepthook = global_exception_handler


def run_sse_server(config: dict[str, Any]) -> None:
    """Run the server with SSE transport.

    Args:
        config: Server configuration
    """

    # Define middleware to suppress 'NoneType object is not callable' errors during shutdown
    class SuppressNoneTypeErrorMiddleware:
        def __init__(self, app: ASGIApp) -> None:
            self.app = app

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
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
            except Exception as e:  # noqa: BLE001 - Top-level ASGI connection handler must catch all errors
                logger.exception("ASGI connection ended with exception: %s", e)
                # Use our custom exception handler for detailed logging
                handle_taskgroup_exception(e)

    # Create Starlette app with custom middleware including our suppressor and CORS
    app = Starlette(
        debug=config.get("debug", False),
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
    except Exception as e:  # noqa: BLE001 - Top-level server shutdown handler must catch all errors
        logger.exception("Server encountered exception during shutdown: %s", e)


def run_stdio_server(config: dict[str, Any]) -> None:
    """Run the server with stdio transport.

    Args:
        config: Server configuration
    """
    # Use stdio transport for terminal use
    logger.info("Using stdio transport for terminal interaction")

    # Determine if we should show startup message (only if log_file is specified)
    bool(config.get("log_file") and config["log_file"] != "console")

    async def arun() -> None:
        async with stdio_server() as streams:
            # Log that we're ready to accept commands
            console.startup_complete()
            # Add device listing on startup
            await mcp._mcp_server.run(
                streams[0],
                streams[1],
                mcp._mcp_server.create_initialization_options(),
            )

    anyio.run(arun)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the server to (use 0.0.0.0 for all interfaces)",
)
@click.option(
    "--port",
    default=4256,  # h.a.l.o
    type=int,
    help="Port to listen on for network connections",
)
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
    "--log-file",
    "-l",
    type=str,
    default=None,
    help="Path to log file (if not specified, logs go to console in SSE mode or nowhere in stdio mode)",
)
@click.option(
    "--adb-path",
    type=str,
    default=None,
    help="Path to the ADB binary (uses auto-detection if not specified)",
)
def main(
    host: str, port: int, transport: str, debug: bool, log_level: str, log_file: str | None, adb_path: str | None
) -> None:
    """
    DroidMind MCP Server - Control Android devices with AI assistants.

    This server implements the Model Context Protocol (MCP) to allow AI assistants
    to control and interact with Android devices via ADB.
    """
    # Set up global exception handler
    setup_global_exception_handler()

    # Start visual elements before configuring logging - ONLY for SSE mode
    if transport == "sse":
        console.print_banner()

    # Prepare server configuration info
    config: dict[str, Any] = {
        "transport": transport.upper(),
        "host": host,
        "port": port,
        "debug": debug,
        "log_level": log_level if not debug else "DEBUG",
        "adb_path": adb_path or "auto-detected",
        "log_file": log_file or "console",
    }

    # Validate host before showing config
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if host != "localhost":
            config["host"] = "127.0.0.1"
            config["host_note"] = f"(Changed from {host} - invalid address)"

    # Configure logging differently based on transport and log_file
    if transport == "stdio":
        # In stdio mode we don't use Rich console logging unless log_file is specified
        # Also disable all console logging if no log file is specified
        disable_console_logging = not log_file
        setup_logging(
            config["log_level"], debug, handler=None, log_file=log_file, disable_console_logging=disable_console_logging
        )
    else:
        # In SSE mode we use Rich console logging + optional file logging
        handler = RichHandler(console=console.console, rich_tracebacks=True)
        setup_logging(config["log_level"], debug, handler=handler, log_file=log_file, disable_console_logging=False)

    # Display beautiful configuration with NeonGlam aesthetic
    # Only in SSE mode
    if transport == "sse":
        console.display_system_info(config)

    # Set up asyncio exception handler
    setup_asyncio_exception_handler()

    # Initialize the global device manager with the specified ADB path
    set_device_manager(DeviceManager(adb_path=adb_path))
    logger.debug("Global device manager initialized with ADB path: %s", adb_path or "auto-detected")

    # Run the appropriate server based on transport
    if transport == "sse":
        run_sse_server(config)
    else:
        run_stdio_server(config)


if __name__ == "__main__":
    main(host="127.0.0.1", port=4256, transport="sse", debug=False, log_level="INFO", log_file=None, adb_path="adb")

# pylint: disable=too-many-statements

"""
DroidMind Networking - Network utilities for the DroidMind MCP server.

This module provides networking utilities for the DroidMind MCP server,
including SSE (Server-Sent Events) server setup and interface detection.
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging
import os
import signal
import threading
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Mount, Route
import uvicorn

from droidmind.utils import console

logger = logging.getLogger("droidmind")


def setup_sse_server(host: str, port: int, mcp_server: FastMCP, debug: bool = False) -> None:
    """
    Set up the SSE server using Starlette and uvicorn.

    Args:
        host: Host to bind the server to
        port: Port to listen on
        mcp_server: The FastMCP server instance
        debug: Whether to enable debug mode
    """
    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    # Track active connections for proper cleanup
    active_connections: set[int] = set()

    async def handle_sse(request: Request) -> None:
        """Handle SSE connection."""
        # Note: Using _send is required by the SSE implementation
        # ruff: noqa: SLF001
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            # Add connection to active set
            connection_id = id(streams)
            active_connections.add(connection_id)
            try:
                # The run method expects a transport type, not the streams directly
                # ruff: noqa: SLF001
                await mcp_server._mcp_server.run(
                    streams[0],
                    streams[1],
                    mcp_server._mcp_server.create_initialization_options(),
                )
            except Exception:
                # Log the full exception with traceback
                logger.exception("Error in SSE connection")
                # Re-raise to let the framework handle it
                raise
            finally:
                # Remove connection from active set when done
                if connection_id in active_connections:
                    active_connections.remove(connection_id)

    async def handle_index(request: Request) -> HTMLResponse:
        """Serve the index page with server info."""
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DroidMind MCP Server</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #121212;
                    color: #e0e0e0;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    min-height: 100vh;
                    line-height: 1.6;
                }}
                header {{
                    background-color: #1f1f1f;
                    width: 100%;
                    text-align: center;
                    padding: 2rem 0;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
                }}
                h1 {{
                    font-size: 2.5rem;
                    margin: 0;
                    color: #a4c639; /* Android green */
                }}
                h2 {{
                    font-size: 1.5rem;
                    color: #a4c639;
                    margin-top: 2rem;
                }}
                .container {{
                    max-width: 800px;
                    width: 90%;
                    margin: 2rem auto;
                    padding: 1.5rem;
                    background-color: #1f1f1f;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                }}
                .info {{
                    margin-bottom: 1.5rem;
                    padding: 1rem;
                    background-color: #2c2c2c;
                    border-radius: 6px;
                }}
                .endpoints {{
                    background-color: #2c2c2c;
                    padding: 1rem;
                    border-radius: 6px;
                    margin-bottom: 1.5rem;
                }}
                pre {{
                    background-color: #262626;
                    padding: 1rem;
                    border-radius: 4px;
                    overflow-x: auto;
                    font-family: 'Courier New', monospace;
                }}
                code {{
                    font-family: 'Courier New', monospace;
                    background-color: #262626;
                    padding: 0.2rem 0.4rem;
                    border-radius: 3px;
                }}
                .label {{
                    font-weight: bold;
                    color: #a4c639;
                    margin-right: 0.5rem;
                }}
                footer {{
                    margin-top: auto;
                    padding: 1rem;
                    text-align: center;
                    font-size: 0.9rem;
                    color: #888;
                    width: 100%;
                    background-color: #1a1a1a;
                }}
                a {{
                    color: #a4c639;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <header>
                <h1>DroidMind MCP Server</h1>
                <p>Control Android devices with AI assistants using the Model Context Protocol</p>
            </header>

            <div class="container">
                <div class="info">
                    <h2>Server Information</h2>
                    <p><span class="label">Status:</span> Active</p>
                    <p><span class="label">Host:</span> {host}</p>
                    <p><span class="label">Port:</span> {port}</p>
                    <p><span class="label">Server URL:</span> <a href="{base_url}" target="_blank">{base_url}</a></p>
                </div>

                <div class="endpoints">
                    <h2>API Endpoints</h2>
                    <p><span class="label">SSE Connection:</span> <code>{base_url}/sse</code></p>
                    <p><span class="label">Messages:</span> <code>{base_url}/messages/</code></p>
                </div>

                <div class="info">
                    <h2>Getting Started</h2>
                    <p>To connect an AI assistant to this server, use the SSE transport with the following
                    connection URL:</p>
                    <pre>sse://{host}:{port}/sse</pre>
                    <p>You can configure Claude/ChatGPT to use this server with the Model Context Protocol.</p>
                </div>
            </div>

            <footer>
                <p>DroidMind &copy; 2023-2024 |
                <a href="https://github.com/hyperbliss/droidmind" target="_blank">GitHub</a></p>
            </footer>
        </body>
        </html>
        """
        return HTMLResponse(html)

    async def handle_info(_request: Request) -> JSONResponse:
        """Return JSON info about the server."""
        return JSONResponse(
            {
                "name": "DroidMind MCP Server",
                "version": "0.1.0",
                "endpoints": {"sse": "/sse", "messages": "/messages/"},
                "host": host,
                "port": port,
            }
        )

    # Create Starlette app with CORS middleware and lifespan
    @asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncGenerator:  # type: ignore
        """Handle application lifespan events."""
        # Setup - nothing to do here now as MCP server handles ADB setup
        yield

        # Cleanup on shutdown
        logger.info("Cleaning up resources...")

        # Clear active connections to prevent hanging
        active_connections.clear()
        logger.debug("Cleared active connections")

        # Give tasks a moment to clean up
        await asyncio.sleep(0.5)

    # CORS middleware
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
    ]

    app = Starlette(
        debug=debug,
        middleware=middleware,
        routes=[
            Route("/", endpoint=handle_index),
            Route("/info", endpoint=handle_info),
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        lifespan=lifespan,
    )

    # Display listen address info
    if host == "0.0.0.0":  # noqa: S104 - Intentional binding to all interfaces
        # When binding to all interfaces, show a simple message
        console.header("Listen Addresses")
        console.success(f"Server listening on all interfaces at port {port}")
        console.success(f"Connect to the server using: sse://YOUR_IP:{port}/sse")
    else:
        # Show the specific address we're listening on
        console.header("Listen Address")
        console.success(f"Server listening on {host}:{port}")
        console.success(f"Connect to the server using: sse://{host}:{port}/sse")

    # Create a server instance that we can access for shutdown
    config = uvicorn.Config(app, host=host, port=port, log_level="debug" if debug else "info", log_config=None)
    server = uvicorn.Server(config)

    # Configure graceful shutdown
    # Set up signal handlers for graceful shutdown
    def handle_exit(signum: int, _frame: Any) -> None:
        """Handle exit signals for graceful shutdown."""
        logger.info("Received signal %s, initiating graceful shutdown with task debug...", signal.Signals(signum).name)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        async def debug_tasks() -> None:
            """Debug and log active tasks during shutdown."""
            for i in range(5):  # print active tasks for 5 seconds
                logger.info("[DEBUG TASKS] Snapshot %d - Active tasks:", i + 1)
                tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task(loop)]
                if not tasks:
                    logger.info("[DEBUG TASKS] No active tasks found.")
                for t in tasks:
                    try:
                        task_name = t.get_name()
                    except AttributeError:
                        task_name = str(t)
                    logger.info("Task: %s, Done: %s", task_name, t.done())
                    stack = t.get_stack(limit=3)
                    if stack:
                        for stack_frame in stack:
                            logger.info("  at %s:%d", stack_frame.f_code.co_filename, stack_frame.f_lineno)
                    else:
                        logger.info("  No stack available.")
                await asyncio.sleep(1)

        # Store reference to the task and use it to prevent it from being garbage collected
        # ruff: noqa: RUF006
        loop.create_task(debug_tasks())
        # Delay shutdown to allow debug_tasks to run for 5 seconds
        loop.call_later(5, lambda: setattr(server, "should_exit", True))

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)  # Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit)  # Termination request

    # Start the server with graceful shutdown support
    logger.info("Press Ctrl+C to exit")
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, exiting...")
    finally:
        # Make sure we clean up
        logger.info("Cleaning up resources...")

        # Force exit if we're still hanging after 3 seconds
        def force_exit() -> None:
            """Force exit if shutdown takes too long."""
            logger.warning("Server shutdown taking too long, forcing exit...")
            os._exit(0)

        # Schedule force exit after 3 seconds
        force_timer = threading.Timer(3.0, force_exit)
        force_timer.daemon = True
        force_timer.start()

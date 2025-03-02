"""
DroidMind MCP Server.

This module implements the command-line interface and server startup for DroidMind.
It delegates core functionality to specialized modules.
"""

import ipaddress
import logging
import signal
import sys

import click
from rich import print as rprint
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.panel import Panel

# Import tools and prompts to register them
# Import DroidMind modules
from droidmind.core import mcp
from droidmind.networking import setup_sse_server
from droidmind.utils import console

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
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
def main(host: str, port: int, transport: str, debug: bool, log_level: str):
    """
    DroidMind MCP Server - Control Android devices with AI assistants.

    This server implements the Model Context Protocol (MCP) to allow AI assistants
    to control and interact with Android devices via ADB.
    """
    # Configure logging level - debug takes precedence over log_level
    if debug:
        logging.getLogger("droidmind").setLevel(logging.DEBUG)
        logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
        logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)
        log_level = "DEBUG"  # Override log_level for display purposes
    else:
        logging.getLogger("droidmind").setLevel(getattr(logging, log_level))

    # Display beautiful welcome message with server info
    console.print_banner()
    logger.info("Starting DroidMind MCP server...")

    # Validate host
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if host != "localhost":
            logger.warning(f"Invalid host address: {host}. Using localhost instead.")
            host = "127.0.0.1"

    # Display server configuration
    config_table = Panel(
        Markdown(f"""
        # Server Configuration

        * **Transport**: {transport.upper()}
        * **Host**: {host}
        * **Port**: {port}
        * **Debug Mode**: {"Enabled" if debug else "Disabled"}
        * **Log Level**: {log_level}
        """),
        title="[cyan]DroidMind Configuration[/cyan]",
        border_style="cyan",
    )
    rprint(config_table)

    # Set up signal handlers for stdio mode
    def handle_stdio_exit(signum, frame):
        logger.info(f"Received signal {signal.Signals(signum).name}, shutting down gracefully...")
        # Exit normally
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_stdio_exit)
    signal.signal(signal.SIGTERM, handle_stdio_exit)

    # Start server based on transport mode
    if transport == "sse":
        # Start SSE server
        logger.info(f"Starting DroidMind with SSE transport on {host}:{port}")
        setup_sse_server(host, port, mcp, debug)
    else:
        # Use stdio transport for terminal use
        logger.info("Starting DroidMind with stdio transport")
        import anyio
        from mcp.server.stdio import stdio_server

        logger.info("Press Ctrl+C to exit")

        async def arun():
            async with stdio_server() as streams:
                await mcp._mcp_server.run(
                    streams[0],
                    streams[1],
                    mcp._mcp_server.create_initialization_options(),
                )

        anyio.run(arun)


if __name__ == "__main__":
    main()

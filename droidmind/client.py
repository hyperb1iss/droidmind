"""
DroidMind Client - Beautiful SSE client for interacting with DroidMind servers.

This module provides a command-line interface for interacting with DroidMind
servers over SSE transport, with a focus on beautiful visualization and
intuitive command structure.
"""

import asyncio
import functools
import json
import sys
from typing import Any

import click
from mcp import ClientSession
from mcp.client.sse import sse_client
from rich import box
from rich.align import Align
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

# Constants for styling
CYBER_MAGENTA = "#FF00FF"
ELECTRIC_CYAN = "#00FFFF"
NEON_VIOLET = "#9D00FF"
MINT_GREEN = "#39FF14"
ELECTRIC_YELLOW = "#FFE744"
AMBER = "#FFBF00"
HOT_PINK = "#FF69B4"
CRIMSON = "#DC143C"
COOL_BLUE = "#00BFFF"
LAVENDER = "#E6E6FA"
HOLO_SILVER = "#F0F0F0"
NEON_PEACH = "#FF9E80"

# Set up console for pretty output
console = Console()


# Client class to handle MCP communication and operations
class DroidMindClient:
    """Client for interacting with DroidMind servers through MCP."""

    def __init__(self, server_url: str, verbose: int = 0):
        """Initialize the client with the server URL."""
        self.server_url = server_url
        self.verbose = verbose
        self.session: ClientSession | None = None
        self._connection = None  # Store the connection context manager

    async def connect(self) -> None:
        """Establish connection to the server using MCP client."""
        try:
            if self.verbose:
                console.print(f"[dim {NEON_PEACH}]Connecting to DroidMind server at {self.server_url}...[/]")

            # Create SSE client connection using async with context manager
            self._connection = sse_client(
                self.server_url,
                headers=None,  # Optional headers if needed
                timeout=5,  # Default connection timeout
                sse_read_timeout=300,  # Default read timeout (5 minutes)
            )

            # Use the connection as an async context manager
            connection = await self._connection.__aenter__()
            read, write = connection

            if self.verbose >= 2:
                console.print(f"[dim {NEON_PEACH}]Got read/write connection pair[/]")

            # Create MCP client session
            self.session = ClientSession(
                read,
                write,
                sampling_callback=None,  # We don't need to handle model sampling
            )

            if self.verbose >= 2:
                console.print(f"[dim {NEON_PEACH}]Created ClientSession, initializing...[/]")

            # Initialize the session with timeout
            try:
                init_task = self.session.initialize()
                await asyncio.wait_for(init_task, timeout=10.0)

                if self.verbose >= 2:
                    console.print(f"[dim {NEON_PEACH}]Session initialized successfully[/]")

                # Try listing available tools and resources if verbosity is high
                if self.verbose >= 3:
                    try:
                        tools = await self.session.list_tools()
                        console.print(f"[dim {NEON_PEACH}]Available tools: {len(tools)} found[/]")

                        resources = await self.session.list_resources()
                        console.print(f"[dim {NEON_PEACH}]Available resources: {len(resources)} found[/]")
                    except Exception as e:
                        console.print(f"[dim {NEON_PEACH}]Could not list tools/resources: {e}[/]")
            except TimeoutError:
                raise Exception("Timed out waiting for server initialization")

            if self.verbose:
                console.print(f"[bold {MINT_GREEN}]Successfully connected to DroidMind server![/]")

        except Exception as e:
            console.print(f"[bold {CRIMSON}]Failed to connect to server: {e}[/]")
            if self.verbose >= 2:
                import traceback

                console.print(f"[dim {NEON_PEACH}]Error details: {traceback.format_exc()}[/]")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the server."""
        try:
            if self.session:
                try:
                    await self.session.aclose()
                except Exception as e:
                    if self.verbose >= 2:
                        console.print(f"[dim {AMBER}]Session close error: {e}[/]")
                self.session = None

            # Clean up the connection context manager if it exists
            if self._connection:
                try:
                    await self._connection.__aexit__(None, None, None)
                except Exception as e:
                    if self.verbose >= 2:
                        console.print(f"[dim {AMBER}]Connection close error: {e}[/]")
                self._connection = None
        except Exception as e:
            if self.verbose:
                console.print(f"[dim {NEON_PEACH}]Disconnect issue: {e}[/]")

    # API methods to interact with the server
    async def _direct_api_call(self, method: str, params: dict, timeout: float = 10.0) -> Any:
        """Make a direct JSON-RPC call to the server bypassing normal MCP methods.

        This is a fallback for when standard methods don't work properly.
        """
        if not self.session or not hasattr(self.session, "_writer"):
            raise Exception("Not connected to server or session missing writer")

        try:
            # Create request ID
            request_id = getattr(self, "_next_request_id", 0)
            self._next_request_id = request_id + 1

            # Build request
            request = {"jsonrpc": "2.0", "method": method, "params": params, "id": request_id}

            if self.verbose >= 3:
                console.print(f"[dim {NEON_PEACH}]Direct API call: {request}[/]")

            # Send request
            await self.session._writer(json.dumps(request))

            # Wait for response with timeout
            start_time = asyncio.get_event_loop().time()
            while True:
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError

                # Try to get response
                try:
                    message = await asyncio.wait_for(self.session._reader(), timeout=1.0)
                    if not message:
                        await asyncio.sleep(0.1)
                        continue
                except TimeoutError:
                    await asyncio.sleep(0.1)
                    continue

                # Parse response
                try:
                    response = json.loads(message)

                    if self.verbose >= 3:
                        console.print(f"[dim {NEON_PEACH}]Direct API response: {response}[/]")

                    # Check if this is the response to our request
                    if "id" in response and response["id"] == request_id:
                        if "error" in response:
                            raise Exception(f"API error: {response['error']}")
                        return response.get("result")
                except json.JSONDecodeError:
                    if self.verbose >= 2:
                        console.print(f"[dim {AMBER}]Invalid JSON response: {message}[/]")
                    continue

        except Exception as e:
            if self.verbose >= 2:
                console.print(f"[dim {CRIMSON}]Direct API call failed: {e}[/]")
            raise

    async def get_connected_devices(self) -> list[dict[str, Any]]:
        """Get a list of connected devices using direct API call.

        This is a fallback for when read_resource doesn't work.
        """
        try:
            # Try the specific MCP tool name we found from the API docs
            result = await self._direct_api_call(
                "callTool",
                {
                    "name": "mcp__devicelist",  # Using the exact tool name from the API
                    "arguments": {"random_string": "default"},
                },
            )

            if self.verbose >= 2:
                console.print(f"[dim {NEON_PEACH}]Direct mcp__devicelist call result: {result}[/]")

            if isinstance(result, str):
                return {"text": result}
            return result
        except Exception as e:
            # Try the alternate name if the first one failed
            if self.verbose >= 2:
                console.print(f"[dim {AMBER}]First tool call failed: {e}, trying alternate name...[/]")

            try:
                result = await self._direct_api_call(
                    "callTool",
                    {
                        "name": "mcp__deviceslist",  # Alternate possible name
                        "arguments": {"random_string": "default"},
                    },
                )

                if self.verbose >= 2:
                    console.print(f"[dim {NEON_PEACH}]Direct mcp__deviceslist call result: {result}[/]")

                if isinstance(result, str):
                    return {"text": result}
                return result
            except Exception as e2:
                if self.verbose >= 2:
                    console.print(f"[dim {AMBER}]Alternate tool call failed: {e2}, trying generic devicelist...[/]")

                # Try one more fallback to a generic name
                try:
                    result = await self._direct_api_call("callTool", {"name": "devicelist", "arguments": {}})

                    if self.verbose >= 2:
                        console.print(f"[dim {NEON_PEACH}]Direct devicelist call result: {result}[/]")

                    if isinstance(result, str):
                        return {"text": result}
                    return result
                except Exception as e3:
                    if self.verbose >= 2:
                        console.print(f"[dim {CRIMSON}]All direct tool calls failed")
                    return {"error": f"Failed to list devices after multiple attempts: {e3}"}

    async def list_devices(self) -> str:
        """List connected Android devices."""
        with console.status(f"[bold {CYBER_MAGENTA}]Scanning for connected devices...", spinner="moon"):
            if not self.session:
                return "Error: Not connected to server"

            try:
                # Phase 1: Try standard MCP resource reading
                if self.verbose >= 2:
                    console.print(f"[dim {NEON_PEACH}]Attempting to read resource: devices://list[/]")

                try:
                    content_task = self.session.read_resource("devices://list")
                    content, mime_type = await asyncio.wait_for(content_task, timeout=10.0)

                    if self.verbose >= 2:
                        console.print(f"[dim {NEON_PEACH}]Received response of type {mime_type}[/]")

                    return content.decode("utf-8") if isinstance(content, bytes) else content
                except TimeoutError:
                    if self.verbose:
                        console.print(
                            f"[dim {AMBER}]Timed out waiting for device list, trying alternative methods...[/]"
                        )
                except Exception as e:
                    if self.verbose >= 2:
                        console.print(f"[dim {AMBER}]Resource reading failed: {e}, trying alternatives...[/]")

                # Phase 2: Try direct tool call to devicelist
                if self.verbose >= 2:
                    console.print(f"[dim {NEON_PEACH}]Attempting direct tool call to devicelist[/]")

                try:
                    result = await self.session.call_tool("devicelist", arguments={})
                    if result:
                        return result
                except Exception as e:
                    if self.verbose >= 2:
                        console.print(f"[dim {AMBER}]Tool call failed: {e}, trying direct API...[/]")

                # Phase 3: Try direct API call
                if self.verbose >= 2:
                    console.print(f"[dim {NEON_PEACH}]Attempting direct API call[/]")

                result = await self.get_connected_devices()
                if isinstance(result, dict):
                    if "text" in result:
                        return result["text"]
                    elif "error" in result:
                        return f"Error listing devices: {result['error']}"
                    else:
                        return f"Unknown response format: {result}"
                else:
                    return "No devices found or unexpected response format"

            except Exception as e:
                error_msg = f"Error listing devices: {e!s}"
                if self.verbose >= 2:
                    import traceback

                    console.print(f"[dim {NEON_PEACH}]Error details: {traceback.format_exc()}[/]")
                return error_msg

    async def get_device_properties(self, serial: str) -> str:
        """Get detailed properties of a device."""
        with console.status(f"[bold {CYBER_MAGENTA}]Reading device properties...", spinner="point"):
            if not self.session:
                return "Error: Not connected to server"

            try:
                return await self.session.call_tool("device_properties", arguments={"serial": serial})
            except Exception as e:
                return f"Error getting device properties: {e!s}"

    async def connect_device(self, ip_address: str, port: int = 5555) -> str:
        """Connect to an Android device over TCP/IP."""
        with console.status(f"[bold {CYBER_MAGENTA}]Establishing connection to device...", spinner="arc"):
            if not self.session:
                return "Error: Not connected to server"

            try:
                return await self.session.call_tool(
                    "connect_device", arguments={"ip_address": ip_address, "port": port}
                )
            except Exception as e:
                return f"Error connecting to device: {e!s}"

    async def run_shell_command(self, serial: str, command: str) -> str:
        """Run a shell command on the device."""
        with console.status(f"[bold {CYBER_MAGENTA}]Executing command on device...", spinner="line"):
            if not self.session:
                return "Error: Not connected to server"

            try:
                return await self.session.call_tool("shell_command", arguments={"serial": serial, "command": command})
            except Exception as e:
                return f"Error running command: {e!s}"

    async def disconnect_device(self, serial: str) -> str:
        """Disconnect from an Android device."""
        with console.status(f"[bold {CYBER_MAGENTA}]Disconnecting device...", spinner="dots"):
            if not self.session:
                return "Error: Not connected to server"

            try:
                return await self.session.call_tool("disconnect_device", arguments={"serial": serial})
            except Exception as e:
                return f"Error disconnecting device: {e!s}"

    async def list_directory(self, serial: str, path: str) -> str:
        """List contents of a directory on the device."""
        with console.status(f"[bold {CYBER_MAGENTA}]Reading directory contents...", spinner="aesthetic"):
            if not self.session:
                return "Error: Not connected to server"

            try:
                return await self.session.call_tool("list_directory", arguments={"serial": serial, "path": path})
            except Exception as e:
                return f"Error listing directory: {e!s}"

    async def get_device_logcat(self, serial: str) -> str:
        """Get recent logcat output from a device."""
        with console.status(f"[bold {CYBER_MAGENTA}]Reading device logs...", spinner="dots12"):
            if not self.session:
                return "Error: Not connected to server"

            try:
                return await self.session.call_tool("device_logcat", arguments={"serial": serial})
            except Exception as e:
                return f"Error getting logcat: {e!s}"

    async def capture_screenshot(self, serial: str) -> dict[str, Any]:
        """Capture a screenshot from the device."""
        with console.status(f"[bold {CYBER_MAGENTA}]Capturing device screenshot...", spinner="aesthetic"):
            if not self.session:
                return {"error": "Not connected to server"}

            try:
                return await self.session.call_tool("capture_screenshot", arguments={"serial": serial})
            except Exception as e:
                console.print(f"[bold {CRIMSON}]Error capturing screenshot: {e}[/]")
                return {"error": str(e)}

    async def reboot_device(self, serial: str, mode: str = "normal") -> str:
        """Reboot the device."""
        with console.status(f"[bold {CYBER_MAGENTA}]Rebooting device...", spinner="dots"):
            if not self.session:
                return "Error: Not connected to server"

            try:
                return await self.session.call_tool("reboot_device", arguments={"serial": serial, "mode": mode})
            except Exception as e:
                return f"Error rebooting device: {e!s}"

    async def list_available_tools(self) -> list[dict[str, Any]]:
        """List all available tools from the server."""
        if not self.session:
            return []

        try:
            return await self.session.list_tools()
        except Exception as e:
            console.print(f"[bold {CRIMSON}]Failed to list tools: {e}[/]")
            return []

    async def list_available_resources(self) -> list[dict[str, Any]]:
        """List all available resources from the server."""
        if not self.session:
            return []

        try:
            return await self.session.list_resources()
        except Exception as e:
            console.print(f"[bold {CRIMSON}]Failed to list resources: {e}[/]")
            return []


# Helper for displaying results
def display_result(result: str, title: str = "Result") -> None:
    """Display a result in a nicely formatted panel."""
    if result.startswith("#"):
        # This is markdown, render it as such
        console.print(Panel(Markdown(result), title=title, border_style=ELECTRIC_CYAN, box=box.ROUNDED))
    else:
        # Plain text
        console.print(Panel(result, title=title, border_style=ELECTRIC_CYAN, box=box.ROUNDED))


def print_banner() -> None:
    """Print the DroidMind banner."""
    # Create a bold gradient text for the title
    title = Text("DroidMind", style="bold")
    title.stylize("magenta", 0, 5)
    title.stylize("cyan", 5, 9)

    subtitle = Text("Control Android Devices with AI", style=f"italic {NEON_PEACH}")

    # Create a panel with the banner
    banner = Panel(
        Align.center(
            Text.assemble(title, "\n", subtitle, "\n", Text("✨ Client Edition ✨", style=f"bold {NEON_VIOLET}"))
        ),
        border_style=CYBER_MAGENTA,
        box=box.ROUNDED,
    )

    console.print(banner)
    console.print(Rule(style=ELECTRIC_CYAN))


# Helper for running async Click commands
def async_command(f):
    """Decorator to allow Click commands to be async."""

    @click.pass_context
    @functools.wraps(f)
    def wrapper(ctx, *args, **kwargs):
        return asyncio.run(f(ctx, *args, **kwargs))

    return wrapper


# Click group for command-line interface
@click.group()
@click.option("--server", default="http://localhost:8000", help="DroidMind server URL")
@click.option("--verbose", count=True, help="Enable verbose output (use multiple times for more detail)")
@click.option("--debug", is_flag=True, help="Enable debug mode with exception tracebacks")
@click.pass_context
def cli(ctx: click.Context, server: str, verbose: int, debug: bool) -> None:
    """
    ✨ DroidMind Client - Control Android devices with AI ✨

    Connect to a DroidMind server and control Android devices.
    """
    # Print the banner
    print_banner()

    # Create a client to use in subcommands
    ctx.ensure_object(dict)
    ctx.obj["client"] = DroidMindClient(server, verbose)
    ctx.obj["server_url"] = server
    ctx.obj["debug"] = debug


@cli.command("devices")
@async_command
async def list_devices(ctx: click.Context) -> None:
    """List all connected Android devices."""
    client: DroidMindClient = ctx.obj["client"]

    try:
        await client.connect()
        result = await client.list_devices()
        display_result(result, "Connected Devices")
    finally:
        await client.disconnect()


@cli.command("connect")
@click.argument("ip_address")
@click.option("--port", default=5555, help="Port to connect to (default: 5555)")
@async_command
async def connect_device(ctx: click.Context, ip_address: str, port: int) -> None:
    """Connect to an Android device over TCP/IP."""
    client: DroidMindClient = ctx.obj["client"]

    try:
        await client.connect()
        result = await client.connect_device(ip_address, port)
        display_result(result, "Device Connection")
    finally:
        await client.disconnect()


@cli.command("disconnect")
@click.argument("serial")
@async_command
async def disconnect_device(ctx: click.Context, serial: str) -> None:
    """Disconnect from an Android device."""
    client: DroidMindClient = ctx.obj["client"]

    try:
        await client.connect()
        result = await client.disconnect_device(serial)
        display_result(result, "Device Disconnection")
    finally:
        await client.disconnect()


@cli.command("properties")
@click.argument("serial")
@async_command
async def get_properties(ctx: click.Context, serial: str) -> None:
    """Get detailed properties of a device."""
    client: DroidMindClient = ctx.obj["client"]

    try:
        await client.connect()
        result = await client.get_device_properties(serial)
        display_result(result, f"Device Properties: {serial}")
    finally:
        await client.disconnect()


@cli.command("shell")
@click.argument("serial")
@click.argument("command")
@async_command
async def run_shell(ctx: click.Context, serial: str, command: str) -> None:
    """Run a shell command on the device."""
    client: DroidMindClient = ctx.obj["client"]

    try:
        await client.connect()
        result = await client.run_shell_command(serial, command)
        display_result(result, f"Shell Command: {command}")
    finally:
        await client.disconnect()


@cli.command("ls")
@click.argument("serial")
@click.argument("path", default="/")
@async_command
async def list_dir(ctx: click.Context, serial: str, path: str) -> None:
    """List contents of a directory on the device."""
    client: DroidMindClient = ctx.obj["client"]

    try:
        await client.connect()
        result = await client.list_directory(serial, path)
        display_result(result, f"Directory Listing: {path}")
    finally:
        await client.disconnect()


@cli.command("logcat")
@click.argument("serial")
@async_command
async def get_logcat(ctx: click.Context, serial: str) -> None:
    """Get recent logcat output from a device."""
    client: DroidMindClient = ctx.obj["client"]

    try:
        await client.connect()
        result = await client.get_device_logcat(serial)
        display_result(result, f"Logcat: {serial}")
    finally:
        await client.disconnect()


@cli.command("screenshot")
@click.argument("serial")
@click.option("--output", "-o", help="Output file path (PNG format)")
@async_command
async def capture_screenshot(ctx: click.Context, serial: str, output: str | None) -> None:
    """Capture a screenshot from the device."""
    client: DroidMindClient = ctx.obj["client"]

    try:
        await client.connect()
        result = await client.capture_screenshot(serial)

        if isinstance(result, dict) and "error" in result:
            console.print(f"[bold {CRIMSON}]Error: {result['error']}[/]")
            return

        if "base64_data" in result:
            import base64

            image_data = base64.b64decode(result["base64_data"])

            # Default output name if not specified
            if not output:
                output = f"{serial.replace(':', '_')}_screenshot.png"

            with open(output, "wb") as f:
                f.write(image_data)

            console.print(f"[bold {MINT_GREEN}]Screenshot saved to:[/] [bold white]{output}[/]")
        else:
            console.print(f"[bold {CRIMSON}]Error: unexpected response format[/]")
    finally:
        await client.disconnect()


@cli.command("reboot")
@click.argument("serial")
@click.option(
    "--mode",
    type=click.Choice(["normal", "recovery", "bootloader"]),
    default="normal",
    help="Reboot mode (default: normal)",
)
@async_command
async def reboot_device(ctx: click.Context, serial: str, mode: str) -> None:
    """Reboot the device."""
    client: DroidMindClient = ctx.obj["client"]

    try:
        await client.connect()
        result = await client.reboot_device(serial, mode)
        display_result(result, f"Reboot ({mode})")
    finally:
        await client.disconnect()


@cli.command("info")
@async_command
async def server_info(ctx: click.Context) -> None:
    """Display information about available tools and resources."""
    client: DroidMindClient = ctx.obj["client"]

    try:
        await client.connect()

        # Get available tools
        tools = await client.list_available_tools()

        console.print(f"[bold {CYBER_MAGENTA}]Available Tools:[/]")
        if tools:
            # Create a table for tools
            table = Table(box=box.ROUNDED)
            table.add_column("Tool Name", style=f"bold {ELECTRIC_CYAN}")
            table.add_column("Description", style=COOL_BLUE)
            table.add_column("Arguments", style=NEON_PEACH)

            for tool in tools:
                name = tool.get("name", "")
                description = tool.get("description", "")
                args = ", ".join([arg.get("name", "") for arg in tool.get("arguments", [])])
                table.add_row(name, description, args)

            console.print(table)
        else:
            console.print("[dim]No tools available[/]")

        # Get available resources
        resources = await client.list_available_resources()

        console.print(f"\n[bold {CYBER_MAGENTA}]Available Resources:[/]")
        if resources:
            # Create a table for resources
            table = Table(box=box.ROUNDED)
            table.add_column("Resource URI", style=f"bold {ELECTRIC_CYAN}")
            table.add_column("Description", style=COOL_BLUE)

            for resource in resources:
                uri = resource.get("uri", "")
                description = resource.get("description", "")
                table.add_row(uri, description)

            console.print(table)
        else:
            console.print("[dim]No resources available[/]")

    finally:
        await client.disconnect()


@cli.command("test")
@async_command
async def test_connection(ctx: click.Context) -> None:
    """Test the connection to the server and list available tools."""
    client: DroidMindClient = ctx.obj["client"]

    console.print(f"[bold {CYBER_MAGENTA}]Testing connection to[/] [bold {ELECTRIC_CYAN}]{client.server_url}[/]")

    try:
        start_time = asyncio.get_event_loop().time()

        # Show a spinner while connecting
        with console.status(f"[bold {CYBER_MAGENTA}]Establishing connection...", spinner="dots") as status:
            # Step 1: Try to establish connection only
            try:
                # Create SSE client connection using async with context manager
                client._connection = sse_client(client.server_url, headers=None, timeout=5, sse_read_timeout=300)

                # Use the connection as an async context manager
                connection = await client._connection.__aenter__()
                read, write = connection

                console.print(f"[bold {MINT_GREEN}]✓[/] SSE connection established")
                elapsed = asyncio.get_event_loop().time() - start_time
                console.print(f"[dim {NEON_PEACH}]Time: {elapsed:.2f}s[/]")

                # Step 2: Create MCP client session
                status.update(f"[bold {CYBER_MAGENTA}]Creating MCP session...")
                client.session = ClientSession(read, write, sampling_callback=None)
                console.print(f"[bold {MINT_GREEN}]✓[/] Client session created")

                # Step 3: Low-level monitoring of SSE events during initialization
                status.update(f"[bold {CYBER_MAGENTA}]Monitoring SSE events during initialization...")

                # Create a task for the normal initialization process
                init_task = asyncio.create_task(client.session.initialize())

                # At the same time, monitor raw SSE events
                try:
                    message_count = 0
                    max_attempts = 10

                    for attempt in range(max_attempts):
                        console.print(f"[{NEON_PEACH}]Waiting for SSE events (attempt {attempt + 1}/{max_attempts})[/]")

                        # Try to read a message directly
                        try:
                            # Use a much shorter timeout for each read attempt
                            raw_message = await asyncio.wait_for(read.__anext__(), timeout=1.0)
                            message_count += 1

                            console.print(f"[bold {MINT_GREEN}]✓[/] Received SSE message #{message_count}:")

                            # Try to parse and display message data
                            try:
                                if isinstance(raw_message, dict):
                                    message_type = raw_message.get("type", "unknown")
                                    message_data = raw_message.get("data", "")

                                    console.print(f"[{ELECTRIC_CYAN}]  Type:[/] {message_type}")

                                    # Try to parse JSON data if it exists
                                    if message_data:
                                        try:
                                            if isinstance(message_data, str):
                                                # Some implementations might send JSON as a string
                                                json_data = json.loads(message_data)
                                                console.print(
                                                    f"[{ELECTRIC_CYAN}]  Data:[/] {json.dumps(json_data, indent=2)}"
                                                )
                                            else:
                                                # Or it might already be a parsed object
                                                console.print(
                                                    f"[{ELECTRIC_CYAN}]  Data:[/] {json.dumps(message_data, indent=2)}"
                                                )
                                        except json.JSONDecodeError:
                                            # Not valid JSON, just print as-is
                                            console.print(f"[{ELECTRIC_CYAN}]  Data:[/] {message_data}")
                                else:
                                    console.print(f"[{ELECTRIC_CYAN}]  Raw message:[/] {raw_message}")
                            except Exception as e:
                                console.print(f"[{AMBER}]  Error parsing message: {e}[/]")
                                console.print(f"[{AMBER}]  Raw message: {raw_message}[/]")

                        except TimeoutError:
                            console.print(f"[{AMBER}]No SSE message received in this attempt[/]")

                        except StopAsyncIteration:
                            console.print(f"[bold {CRIMSON}]SSE stream ended unexpectedly[/]")
                            break

                        except Exception as e:
                            console.print(f"[{AMBER}]Error reading SSE message: {e}[/]")

                        # Check if initialization has completed
                        if init_task.done():
                            console.print(f"[bold {MINT_GREEN}]Initialization task completed during monitoring[/]")
                            break

                    if message_count > 0:
                        console.print(
                            f"[bold {MINT_GREEN}]✓[/] Received {message_count} SSE messages during monitoring"
                        )
                    else:
                        console.print(f"[bold {CRIMSON}]✗[/] No SSE messages received during monitoring")

                except Exception as e:
                    console.print(f"[bold {CRIMSON}]Error during SSE monitoring: {e}[/]")

                # Check the status of the initialization task
                try:
                    # Wait for initialization with timeout
                    await asyncio.wait_for(init_task, timeout=2.0)  # Short timeout since we've already waited
                    console.print(f"[bold {MINT_GREEN}]✓[/] Session initialized successfully")

                    # Step 4: List tools if session was initialized
                    await _list_tools_and_resources(client, status)

                except TimeoutError:
                    console.print(f"[bold {CRIMSON}]✗[/] Session initialization timed out")
                    # Check if we can cancel the task safely
                    if not init_task.done():
                        init_task.cancel()
                except Exception as e:
                    console.print(f"[bold {CRIMSON}]✗[/] Session initialization failed: {e}[/]")
                    if client.verbose >= 2:
                        import traceback

                        console.print(f"[dim {NEON_PEACH}]Error details: {traceback.format_exc()}[/]")

            except Exception as e:
                console.print(f"[bold {CRIMSON}]Connection test failed: {e}[/]")
                if client.verbose >= 2:
                    import traceback

                    console.print(f"[dim {NEON_PEACH}]Error details: {traceback.format_exc()}[/]")
    finally:
        # Clean up
        try:
            await client.disconnect()
            console.print(f"[dim {NEON_PEACH}]Connection closed[/]")
        except Exception as e:
            console.print(f"[bold {CRIMSON}]Error during cleanup: {e}[/]")


async def _list_tools_and_resources(client, status):
    """Helper function to list tools and resources."""
    # List tools
    status.update(f"[bold {CYBER_MAGENTA}]Listing available tools...")
    try:
        tools_start = asyncio.get_event_loop().time()
        tools = await asyncio.wait_for(client.session.list_tools(), timeout=5.0)
        tools_elapsed = asyncio.get_event_loop().time() - tools_start

        console.print(f"[bold {MINT_GREEN}]✓[/] Retrieved {len(tools)} tools (took {tools_elapsed:.2f}s)")

        if tools:
            # Create a table for tools
            table = Table(box=box.ROUNDED)
            table.add_column("Tool Name", style=f"bold {ELECTRIC_CYAN}")
            table.add_column("Description", style=COOL_BLUE)

            for tool in tools:
                name = tool.get("name", "")
                description = tool.get("description", "")
                table.add_row(name, description)

            console.print(table)
    except Exception as e:
        console.print(f"[bold {CRIMSON}]✗[/] Failed to list tools: {e}")

    # List resources
    status.update(f"[bold {CYBER_MAGENTA}]Listing available resources...")
    try:
        resources_start = asyncio.get_event_loop().time()
        resources = await asyncio.wait_for(client.session.list_resources(), timeout=5.0)
        resources_elapsed = asyncio.get_event_loop().time() - resources_start

        console.print(f"[bold {MINT_GREEN}]✓[/] Retrieved {len(resources)} resources (took {resources_elapsed:.2f}s)")

        if resources:
            # Create a table for resources
            table = Table(box=box.ROUNDED)
            table.add_column("Resource URI", style=f"bold {ELECTRIC_CYAN}")
            table.add_column("Description", style=COOL_BLUE)

            for resource in resources:
                uri = resource.get("uri", "")
                description = resource.get("description", "")
                table.add_row(uri, description)

            console.print(table)
    except Exception as e:
        console.print(f"[bold {CRIMSON}]✗[/] Failed to list resources: {e}")


def main() -> None:
    """Run the CLI."""
    try:
        cli()
    except Exception as e:
        console.print(f"[bold {CRIMSON}]Unexpected error: {e!s}[/]")
        if any(arg.startswith("--verbose") for arg in sys.argv) or any(arg == "--debug" for arg in sys.argv):
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()

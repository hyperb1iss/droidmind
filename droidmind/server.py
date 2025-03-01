"""
DroidMind MCP Server.

This module implements the Model Context Protocol server for Android devices.
"""

import os
import asyncio
import logging
import tempfile
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional, Any, Union
import ipaddress
import socket

import click
from rich.logging import RichHandler
from rich import print as rprint
from rich.panel import Panel
from rich.markdown import Markdown
from sse_starlette.sse import EventSourceResponse

from mcp.server.fastmcp import FastMCP, Context, Image

from droidmind.adb.wrapper import ADBWrapper
from droidmind.utils import console


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("droidmind")


@dataclass
class DroidMindContext:
    """Context for DroidMind server."""
    adb: ADBWrapper
    temp_dir: str


@asynccontextmanager
async def droidmind_lifespan(server: FastMCP) -> AsyncIterator[DroidMindContext]:
    """Initialize and clean up DroidMind resources."""
    # Don't print banner here - it's already printed at server startup
    console.info("Initializing DroidMind session...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="droidmind_")
    console.info(f"Created temporary directory: {temp_dir}")
    
    # Initialize ADB wrapper
    adb = ADBWrapper()
    
    try:
        # Yield context to the server
        yield DroidMindContext(adb=adb, temp_dir=temp_dir)
        
    finally:
        # Clean up
        console.info("Shutting down DroidMind session...")
        
        # Disconnect all devices
        devices = await adb.get_devices()
        for device in devices:
            serial = device["serial"]
            await adb.disconnect_device(serial)
        
        # Clean up temporary directory
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            console.info(f"Removed temporary directory: {temp_dir}")


# Create the MCP server
mcp = FastMCP(
    "DroidMind", 
    description="Control Android devices with MCP",
    lifespan=droidmind_lifespan,
    dependencies=["adb-shell>=0.4.4", "rich>=13.9.4"],
)


# ======== Resources ========

@mcp.resource("device://list")
async def list_devices() -> str:
    """
    List all connected Android devices.
    
    Returns:
        A formatted list of connected devices with their basic information.
    """
    from mcp.server.fastmcp import get_request_context
    ctx = get_request_context()
    return await _list_devices_impl(ctx)

async def _list_devices_impl(ctx: Context) -> str:
    """Implementation function for list_devices that can be called directly by tests."""
    adb = ctx.lifespan_context.adb
    
    devices = await adb.get_devices()
    
    if not devices:
        return "No devices connected.\n\nUse the `connect_device` tool to connect to a device."
    
    # Format the output
    result = f"# Connected Android Devices ({len(devices)})\n\n"
    
    for i, device in enumerate(devices, 1):
        serial = device.get("serial", "Unknown")
        model = device.get("model", "Unknown model")
        android_version = device.get("android_version", "Unknown version")
        
        result += f"## Device {i}: {model}\n"
        result += f"- **Serial**: `{serial}`\n"
        result += f"- **Status**: Connected\n"
        result += f"- **Android Version**: {android_version}\n\n"
    
    return result


@mcp.resource("device://{serial}/properties")
async def device_properties(serial: str) -> str:
    """
    Get detailed properties of a specific device.
    
    Args:
        serial: Device serial number
        
    Returns:
        Formatted device properties as text
    """
    from mcp.server.fastmcp import get_request_context
    ctx = get_request_context()
    return await _device_properties_impl(serial, ctx)

async def _device_properties_impl(serial: str, ctx: Context) -> str:
    """Implementation function for device_properties that can be called directly by tests."""
    adb = ctx.lifespan_context.adb
    
    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]
    
    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."
    
    # Get all properties
    try:
        properties = await adb.get_device_properties(serial)
    except Exception as e:
        return f"Error retrieving device properties: {str(e)}"
    
    # Extract key information
    android_version = properties.get("ro.build.version.release", "Unknown")
    sdk_version = properties.get("ro.build.version.sdk", "Unknown")
    device_model = properties.get("ro.product.model", "Unknown")
    device_brand = properties.get("ro.product.brand", "Unknown")
    device_name = properties.get("ro.product.name", "Unknown")
    
    # Format output in a structured way
    result = f"""
# Device Properties for {serial}

## Basic Information
- **Model**: {device_model}
- **Brand**: {device_brand}
- **Name**: {device_name}
- **Android Version**: {android_version}
- **SDK Level**: {sdk_version}

## Build Details
- **Build Number**: {properties.get("ro.build.display.id", "Unknown")}
- **Build Type**: {properties.get("ro.build.type", "Unknown")}
- **Build Time**: {properties.get("ro.build.date", "Unknown")}

## Hardware
- **Chipset**: {properties.get("ro.hardware", "Unknown")}
- **Architecture**: {properties.get("ro.product.cpu.abi", "Unknown")}
- **Screen Density**: {properties.get("ro.sf.lcd_density", "Unknown")}
- **RAM**: {properties.get("ro.product.ram", "Unknown")}
"""
    
    # Include a selection of other interesting properties
    interesting_props = [
        "ro.product.cpu.abilist",
        "ro.build.fingerprint",
        "ro.build.characteristics",
        "ro.build.tags",
        "ro.product.manufacturer",
        "ro.product.locale",
        "ro.config.bluetooth_max_connected",
        "ro.crypto.state",
        "ro.boot.hardware.revision",
    ]
    
    result += "\n## Other Properties\n"
    for prop in interesting_props:
        if prop in properties:
            result += f"- **{prop}**: {properties[prop]}\n"
    
    return result


@mcp.resource("logs://{serial}/logcat")
async def device_logcat(serial: str) -> str:
    """
    Get recent logcat output from a device.
    
    Args:
        serial: Device serial number
        
    Returns:
        Recent logcat entries
    """
    from mcp.server.fastmcp import get_request_context
    ctx = get_request_context()
    return await _device_logcat_impl(serial, ctx)

async def _device_logcat_impl(serial: str, ctx: Context) -> str:
    """Implementation function for device_logcat that can be called directly by tests."""
    adb = ctx.lifespan_context.adb
    
    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]
    
    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."
    
    try:
        # Get recent logs (limited to last 200 lines for performance)
        logcat = await adb.shell(serial, "logcat -d -v time -T 200")
        
        if not logcat.strip():
            return "No logcat entries found."
        
        return f"# Logcat for device {serial}\n\n```\n{logcat}\n```"
        
    except Exception as e:
        return f"Error retrieving logcat: {str(e)}"


@mcp.resource("fs://{serial}/list/{path}")
async def list_directory(serial: str, path: str) -> str:
    """
    List contents of a directory on the device.
    
    Args:
        serial: Device serial number
        path: Directory path to list
        
    Returns:
        Directory listing
    """
    from mcp.server.fastmcp import get_request_context
    ctx = get_request_context()
    return await _list_directory_impl(serial, path, ctx)

async def _list_directory_impl(serial: str, path: str, ctx: Context) -> str:
    """Implementation function for list_directory that can be called directly by tests."""
    adb = ctx.lifespan_context.adb
    
    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]
    
    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."
    
    try:
        # Sanitize path
        path = path.replace("//", "/")
        if not path.startswith("/"):
            path = f"/{path}"
            
        # List directory contents
        output = await adb.shell(serial, f"ls -la {path}")
        
        if "No such file or directory" in output:
            return f"Error: Path {path} does not exist on device {serial}."
        
        return f"# Directory listing for {path} on device {serial}\n\n```\n{output}\n```"
        
    except Exception as e:
        return f"Error listing directory: {str(e)}"


# ======== Tools ========

@mcp.tool()
async def connect_device(
    host: str,
    ctx: Context,
    port: int = 5555
) -> str:
    """
    Connect to an Android device via TCP/IP.
    
    Args:
        host: IP address or hostname of the device
        port: Port to connect to (default: 5555)
        
    Returns:
        Connection result message
    """
    adb = ctx.lifespan_context.adb
    
    try:
        # Try to connect to the device
        await ctx.report_progress(0, 2)
        
        ctx.info(f"Connecting to device at {host}:{port}...")
        serial = await adb.connect_device_tcp(host, port)
        
        await ctx.report_progress(1, 2)
        
        # Get basic device info
        devices = await adb.get_devices()
        device_info = next((d for d in devices if d["serial"] == serial), {})
        
        model = device_info.get("model", "Unknown model")
        android_version = device_info.get("android_version", "Unknown version")
        
        await ctx.report_progress(2, 2)
        
        return f"Successfully connected to {model} (Android {android_version}) at {serial}"
        
    except Exception as e:
        return f"Failed to connect to device: {str(e)}"


@mcp.tool()
async def disconnect_device(
    serial: str,
    ctx: Context
) -> str:
    """
    Disconnect from an Android device.
    
    Args:
        serial: Device serial number
        
    Returns:
        Disconnection result message
    """
    adb = ctx.lifespan_context.adb
    
    try:
        # Try to disconnect from the device
        ctx.info(f"Disconnecting from device {serial}...")
        success = await adb.disconnect_device(serial)
        
        if success:
            return f"Successfully disconnected from device {serial}"
        else:
            return f"Device {serial} was not connected"
        
    except Exception as e:
        return f"Error disconnecting from device: {str(e)}"


@mcp.tool()
async def shell_command(
    serial: str,
    command: str,
    ctx: Context
) -> str:
    """
    Run a shell command on the device.
    
    Args:
        serial: Device serial number
        command: Shell command to run
        
    Returns:
        Command output
    """
    adb = ctx.lifespan_context.adb
    
    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]
    
    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."
    
    try:
        # Run the command
        ctx.info(f"Running command on {serial}: {command}")
        output = await adb.shell(serial, command)
        
        return f"Command output from {serial}:\n\n```\n{output}\n```"
        
    except Exception as e:
        return f"Error running command: {str(e)}"


@mcp.tool()
async def install_app(
    serial: str,
    apk_path: str,
    ctx: Context,
    reinstall: bool = False,
    grant_permissions: bool = True
) -> str:
    """
    Install an APK on the device.
    
    Args:
        serial: Device serial number
        apk_path: Path to the APK file (local to the server)
        reinstall: Whether to reinstall if app exists
        grant_permissions: Whether to grant all requested permissions
        
    Returns:
        Installation result message
    """
    adb = ctx.lifespan_context.adb
    
    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]
    
    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."
    
    try:
        # Check if APK exists
        if not os.path.exists(apk_path):
            return f"Error: APK file not found at {apk_path}"
        
        # Install the app
        ctx.info(f"Installing APK: {os.path.basename(apk_path)}")
        await ctx.report_progress(0, 2)
        
        # Push APK to device first
        device_apk_path = f"/data/local/tmp/{os.path.basename(apk_path)}"
        await adb.push_file(serial, apk_path, device_apk_path)
        
        await ctx.report_progress(1, 2)
        
        # Install from the pushed file
        result = await adb.install_app(serial, device_apk_path, reinstall, grant_permissions)
        
        # Clean up
        await adb.shell(serial, f"rm {device_apk_path}")
        
        await ctx.report_progress(2, 2)
        
        return result
        
    except Exception as e:
        return f"Error installing app: {str(e)}"


@mcp.tool()
async def capture_screenshot(
    serial: str,
    ctx: Context
) -> Image:
    """
    Capture a screenshot from the device.
    
    Args:
        serial: Device serial number
        
    Returns:
        Device screenshot as an image
    """
    adb = ctx.lifespan_context.adb
    temp_dir = ctx.lifespan_context.temp_dir
    
    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]
    
    if serial not in device_serials:
        raise ValueError(f"Device {serial} not connected or not found.")
    
    try:
        # Create a temporary file path
        screenshot_path = os.path.join(temp_dir, f"{serial.replace(':', '_')}_screenshot.png")
        
        # Capture the screenshot
        ctx.info(f"Capturing screenshot from {serial}...")
        await ctx.report_progress(0, 3)
        
        # Take screenshot on device
        await adb.shell(serial, "screencap -p /sdcard/screenshot.png")
        await ctx.report_progress(1, 3)
        
        # Pull screenshot to local machine
        await adb.pull_file(serial, "/sdcard/screenshot.png", screenshot_path)
        await ctx.report_progress(2, 3)
        
        # Clean up on device
        await adb.shell(serial, "rm /sdcard/screenshot.png")
        await ctx.report_progress(3, 3)
        
        # Read the image and return it
        with open(screenshot_path, "rb") as f:
            image_data = f.read()
        
        ctx.info(f"Screenshot captured successfully ({len(image_data)} bytes)")
        
        # Clean up local temp file after reading
        try:
            os.unlink(screenshot_path)
        except Exception:
            pass
            
        # Create Image object with format attribute - this is needed for tests
        image = Image(data=image_data)
        image.format = "png"  # Ensure format is set for test compatibility
        return image
        
    except Exception as e:
        ctx.error(f"Error capturing screenshot: {str(e)}")
        raise


@mcp.tool()
async def reboot_device(
    serial: str,
    ctx: Context,
    mode: str = "normal"
) -> str:
    """
    Reboot the device.
    
    Args:
        serial: Device serial number
        mode: Reboot mode - "normal", "recovery", or "bootloader"
        
    Returns:
        Reboot result message
    """
    adb = ctx.lifespan_context.adb
    
    # Check if device is connected
    devices = await adb.get_devices()
    device_serials = [d["serial"] for d in devices]
    
    if serial not in device_serials:
        return f"Error: Device {serial} not connected or not found."
    
    valid_modes = ["normal", "recovery", "bootloader"]
    if mode not in valid_modes:
        return f"Error: Invalid reboot mode. Must be one of: {', '.join(valid_modes)}"
    
    try:
        # Reboot the device
        ctx.info(f"Rebooting device {serial} into {mode} mode...")
        result = await adb.reboot_device(serial, mode)
        
        return result
        
    except Exception as e:
        return f"Error rebooting device: {str(e)}"


# ======== Prompts ========

@mcp.prompt()
def debug_app_crash(app_package: str) -> str:
    """
    Generate a prompt to debug an app crash.
    
    Args:
        app_package: The package name of the crashed app
    """
    return f"""I need help debugging a crash in my Android app with package name '{app_package}'.

Can you help me:
1. Capture the relevant logcat output for this app
2. Analyze the stack trace and error messages
3. Identify the root cause of the crash
4. Suggest potential fixes

Please include specific code or configuration changes that might solve the issue.
"""


@mcp.prompt()
def analyze_battery_usage() -> str:
    """Generate a prompt to analyze battery usage on a device."""
    return """I need help analyzing battery usage on my Android device.

Can you:
1. Capture battery stats and analyze which apps or services are consuming the most power
2. Identify any wakelocks or processes preventing the device from entering deep sleep
3. Suggest optimizations to improve battery life
4. Recommend settings changes or apps that could help monitor or reduce battery consumption

Please include both immediate actions I can take and long-term strategies for battery optimization.
"""

# ======== SSE Server Setup ========

def get_available_interfaces():
    """Get available network interfaces with their IP addresses."""
    interfaces = []
    
    try:
        import socket
        import netifaces
        
        # Get all network interfaces using netifaces
        for interface in netifaces.interfaces():
            try:
                # Get the IP address for this interface
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        # Skip loopback addresses unless it's the only one
                        if not ip.startswith('127.') or interface == 'lo':
                            interfaces.append((interface, ip))
            except (OSError, ValueError):
                continue
    except ImportError:
        # Fallback method if netifaces is not available
        try:
            # Get hostname and IP
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip and not ip.startswith('127.'):
                interfaces.append(("default", ip))
        except (socket.error, OSError):
            pass
    
    # Always include localhost
    if not any(ip == "127.0.0.1" for _, ip in interfaces):
        interfaces.append(("localhost", "127.0.0.1"))
        
    return interfaces


def setup_sse_server(host: str, port: int, debug: bool = False):
    """Set up the SSE server using Starlette and uvicorn."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    from starlette.responses import JSONResponse, HTMLResponse
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    import uvicorn
    
    # Set up SSE transport
    sse = SseServerTransport("/messages/")
    
    async def handle_sse(request):
        """Handle SSE connection."""
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            # The run method expects a transport type, not the streams directly
            await mcp._mcp_server.run(
                streams[0],
                streams[1],
                mcp._mcp_server.create_initialization_options(),
            )
    
    async def handle_index(request):
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
                    <p>To connect an AI assistant to this server, use the SSE transport with the following connection URL:</p>
                    <pre>sse://{host}:{port}/sse</pre>
                    <p>You can configure Claude/ChatGPT to use this server with the Model Context Protocol.</p>
                </div>
            </div>
            
            <footer>
                <p>DroidMind &copy; 2023-2024 | <a href="https://github.com/hyperbliss/droidmind" target="_blank">GitHub</a></p>
            </footer>
        </body>
        </html>
        """
        return HTMLResponse(html)
    
    async def handle_info(request):
        """Return JSON info about the server."""
        return JSONResponse({
            "name": "DroidMind MCP Server",
            "version": "0.1.0",
            "endpoints": {
                "sse": "/sse",
                "messages": "/messages/"
            },
            "host": host,
            "port": port
        })
    
    # Create Starlette app with CORS middleware
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
    )
    
    # Display server information
    interfaces = get_available_interfaces()
    
    console.info("Server is ready! 🚀")
    console.header("Network Information")
    
    if host == "0.0.0.0":
        # When binding to all interfaces, show all non-loopback interfaces
        for name, ip in interfaces:
            if not ip.startswith("127."):
                url = f"http://{ip}:{port}"
                console.success(f"Interface {name}: {url}")
        
        # Also show localhost for local connections
        console.info(f"Local access: http://localhost:{port}")
        
        # Show MCP URL for AI assistants
        console.header("MCP Connection URL")
        console.info("Use this URL to connect AI assistants:")
        for name, ip in interfaces:
            if not ip.startswith("127."):
                mcp_url = f"sse://{ip}:{port}/sse"
                console.success(f"MCP URL ({name}): {mcp_url}")
        console.info(f"Local MCP URL: sse://localhost:{port}/sse")
    else:
        # When binding to a specific interface, just show that one
        url = f"http://{host}:{port}"
        console.success(f"Server running at: {url}")
        
        # Show MCP URL for AI assistants
        console.header("MCP Connection URL")
        console.info("Use this URL to connect AI assistants:")
        mcp_url = f"sse://{host}:{port}/sse"
        console.success(f"MCP URL: {mcp_url}")
    
    # Start the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="debug" if debug else "info"
    )


# Main entrypoint
@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the server to (use 0.0.0.0 for all interfaces)"
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Port to listen on for network connections"
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type to use (stdio for terminal, sse for network)"
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable debug mode for more verbose logging"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set the logging level"
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
        log_level = "DEBUG"  # Override log_level for display purposes
    else:
        logging.getLogger("droidmind").setLevel(getattr(logging, log_level))
    
    # Display beautiful welcome message with server info
    console.print_banner()
    console.info("Starting DroidMind MCP server...")
    
    # Validate host
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if host != "localhost":
            console.warning(f"Invalid host address: {host}. Using localhost instead.")
            host = "127.0.0.1"
    
    # Display server configuration
    config_table = Panel(
        Markdown(f"""
        # Server Configuration
        
        * **Transport**: {transport.upper()}
        * **Host**: {host}
        * **Port**: {port}
        * **Debug Mode**: {'Enabled' if debug else 'Disabled'}
        * **Log Level**: {log_level}
        """),
        title="[cyan]DroidMind Configuration[/cyan]",
        border_style="cyan"
    )
    rprint(config_table)
    
    # Start server based on transport mode
    if transport == "sse":
        # Start SSE server
        console.info(f"Starting DroidMind with SSE transport on {host}:{port}")
        setup_sse_server(host, port, debug)
    else:
        # Use stdio transport for terminal use
        console.info("Starting DroidMind with stdio transport")
        import anyio
        from mcp.server.stdio import stdio_server
        
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
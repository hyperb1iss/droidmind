"""
Console utilities for DroidMind using the rich library for beautiful terminal output.

This module provides a standardized way to format output for DroidMind. It works by:
1. Using the 'rich' library for beautiful terminal output
2. Routing all log messages through the proper Python logger
3. Maintaining a consistent visual style across the application

USAGE:
    - For basic logging, use the provided functions like info(), warning(), error(), debug()
      Examples:
         console.info("Connected to device")  
         console.error("Failed to connect")
    
    - For tables and other rich content, the functions will:
      a) Display rich content to the console for user-friendly visualization
      b) Also log a plain text message about the action via the logger
      
    - For the banner and purely visual elements, direct console printing is used

IMPORTANT NOTE:
    This module provides custom formatting methods not available in standard Python loggers 
    (like header(), success(), etc). When making changes:
    
    - Use console.* for any custom formatted output (header, success, tables, etc)
    - Use logger.* directly for standard log levels (info, warning, error, debug)
    - NEVER try to call custom methods on the standard logger (e.g., logger.header() will fail!)

The module uses a configured logger with a RichHandler, so all output will be 
properly formatted, time-stamped, and can be filtered by log level.
"""

import logging
from typing import Any, Optional, List, Dict, Union

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich.style import Style
from rich.tree import Tree
from rich.live import Live

# Create a console with a custom theme for DroidMind - for direct console operations
console = Console(
    highlight=True,
    theme=None,  # Default theme works well
)

# Get the configured logger
logger = logging.getLogger("droidmind")

# Define styles for different types of messages
styles = {
    "info": Style(color="cyan"),
    "success": Style(color="green"),
    "warning": Style(color="yellow"),
    "error": Style(color="red", bold=True),
    "debug": Style(color="magenta", dim=True),
    "header": Style(color="blue", bold=True),
    "android": Style(color="#a4c639", bold=True),  # Android green
    "device": Style(color="bright_cyan"),
    "command": Style(color="bright_green"),
    "property": Style(color="bright_yellow"),
}

def print_banner() -> None:
    """Display the DroidMind banner."""
    banner = r"""
    ██████╗ ██████╗  ██████╗ ██╗██████╗ ███╗   ███╗██╗███╗   ██╗██████╗ 
    ██╔══██╗██╔══██╗██╔═══██╗██║██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗
    ██║  ██║██████╔╝██║   ██║██║██║  ██║██╔████╔██║██║██╔██╗ ██║██║  ██║
    ██║  ██║██╔══██╗██║   ██║██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║██║  ██║
    ██████╔╝██║  ██║╚██████╔╝██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ 
    """
    android_txt = Text("Connect AI assistants to Android with MCP", style=styles["android"])
    
    # This is a special case where we want visual output directly to console
    # rather than through the logger for the banner
    console.print()
    console.print(Text(banner, style=styles["android"]))
    console.print(Panel(android_txt, border_style=styles["android"]))
    console.print()
    
    # Log that the banner was displayed at INFO level
    logger.info("DroidMind server initialized")

def info(message: str) -> None:
    """Log an info message."""
    logger.info(f"[i] {message}")

def success(message: str) -> None:
    """Log a success message."""
    logger.info(f"[✓] {message}")

def warning(message: str) -> None:
    """Log a warning message."""
    logger.warning(f"[!] {message}")

def error(message: str) -> None:
    """Log an error message."""
    logger.error(f"[✗] {message}")

def debug(message: str) -> None:
    """Log a debug message."""
    logger.debug(f"[DEBUG] {message}")

def header(message: str) -> None:
    """Log a section header."""
    logger.info(f"\n{message}")
    logger.info("=" * len(message))

def device_table(devices: List[Dict[str, str]]) -> None:
    """Print a table of connected devices."""
    if not devices:
        warning("No devices connected.")
        return
    
    table = Table(title="Connected Android Devices")
    table.add_column("Serial", style=styles["device"])
    table.add_column("Status", style=styles["info"])
    table.add_column("Model", style=styles["property"])
    table.add_column("Android Version", style=styles["property"])
    
    for device in devices:
        table.add_row(
            device.get("serial", "unknown"),
            device.get("status", "unknown"),
            device.get("model", "unknown"),
            device.get("android_version", "unknown")
        )
    
    # For tables and other rich content, we still want to use console.print
    # for direct visualization, but also log that the table was displayed
    console.print(table)
    logger.info(f"Displayed device table with {len(devices)} device(s)")

def property_table(properties: Dict[str, str], title: str = "Device Properties") -> None:
    """Print a table of device properties."""
    if not properties:
        warning("No properties available.")
        return
    
    table = Table(title=title)
    table.add_column("Property", style=styles["property"])
    table.add_column("Value", style=styles["info"])
    
    for key, value in properties.items():
        table.add_row(key, value)
    
    # For tables and other rich content, we still want to use console.print
    # for direct visualization, but also log that the table was displayed
    console.print(table)
    logger.info(f"Displayed property table with {len(properties)} properties")

def command_output(command: str, output: str) -> None:
    """Print command and its output."""
    # Log the command execution
    logger.info(f"Executed command: {command}")
    
    # For command output visualization, use console directly
    console.print(f"$ {command}", style=styles["command"])
    console.print(output)

def progress_context(description: str = "Processing..."):
    """Context manager for showing progress during operations."""
    # Log the start of a progress operation
    logger.debug(f"Starting progress operation: {description}")
    
    # Return the progress context for visualization
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )

def create_device_tree(device_info: Dict[str, Any]) -> Tree:
    """Create a rich Tree showing device information in a hierarchical view."""
    serial = device_info.get("serial", "unknown")
    tree = Tree(f"[bold cyan]{serial}[/bold cyan]")
    
    # Basic info
    basic = tree.add("Basic Info", style="blue")
    for key in ["model", "status", "android_version"]:
        if key in device_info:
            basic.add(f"{key.replace('_', ' ').title()}: [yellow]{device_info[key]}[/yellow]")
    
    # Properties
    if "properties" in device_info and device_info["properties"]:
        props = tree.add("Properties", style="blue")
        for key, value in device_info["properties"].items():
            props.add(f"{key}: [yellow]{value}[/yellow]")
    
    # Features
    if "features" in device_info and device_info["features"]:
        feats = tree.add("Features", style="blue")
        for feature in device_info["features"]:
            feats.add(f"[green]{feature}[/green]")
    
    # Log that we created a device tree
    logger.debug(f"Created device tree for {serial}")
    
    return tree 
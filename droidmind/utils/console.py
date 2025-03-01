"""
Console utilities for DroidMind using the rich library for beautiful terminal output.
"""

from typing import Any, Optional, List, Dict, Union

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich.style import Style
from rich.tree import Tree
from rich.live import Live

# Create a console with a custom theme for DroidMind
console = Console(
    highlight=True,
    theme=None,  # Default theme works well
)

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
    
    console.print()
    console.print(Text(banner, style=styles["android"]))
    console.print(Panel(android_txt, border_style=styles["android"]))
    console.print()

def info(message: str) -> None:
    """Print an info message."""
    console.print(f"[i] {message}", style=styles["info"])

def success(message: str) -> None:
    """Print a success message."""
    console.print(f"[✓] {message}", style=styles["success"])

def warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[!] {message}", style=styles["warning"])

def error(message: str) -> None:
    """Print an error message."""
    console.print(f"[✗] {message}", style=styles["error"])

def debug(message: str) -> None:
    """Print a debug message."""
    console.print(f"[DEBUG] {message}", style=styles["debug"])

def header(message: str) -> None:
    """Print a section header."""
    console.print(f"\n{message}", style=styles["header"])
    console.print("=" * len(message), style=styles["header"])

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
    
    console.print(table)

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
    
    console.print(table)

def command_output(command: str, output: str) -> None:
    """Print command and its output."""
    console.print(f"$ {command}", style=styles["command"])
    console.print(output)

def progress_context(description: str = "Processing..."):
    """Context manager for showing progress during operations."""
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
    
    return tree 
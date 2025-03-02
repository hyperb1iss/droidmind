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
from typing import Any

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

# Create a console with a custom theme for DroidMind - for direct console operations
console = Console(
    highlight=True,
    theme=None,  # Default theme works well
)

# Get the configured logger
logger = logging.getLogger("droidmind")

# NeonGlam color palette aligned with our aesthetic guidelines
COLORS = {
    # Primary colors
    "cyber_magenta": "#FF00FF",
    "electric_cyan": "#00FFFF",
    # Success colors
    "neon_violet": "#9D00FF",
    "mint_green": "#39FF14",
    # Warning colors
    "electric_yellow": "#FFE744",
    "amber": "#FFBF00",
    # Error colors
    "hot_pink": "#FF69B4",
    "crimson": "#DC143C",
    # Info colors
    "cool_blue": "#00BFFF",
    "lavender": "#E6E6FA",
    # Accent colors
    "holo_silver": "#F0F0F0",
    "neon_peach": "#FF9E80",
}

# Define styles for different types of messages using our NeonGlam palette
styles = {
    "info": Style(color=COLORS["cool_blue"]),
    "success": Style(color=COLORS["mint_green"]),
    "warning": Style(color=COLORS["amber"]),
    "error": Style(color=COLORS["hot_pink"], bold=True),
    "debug": Style(color=COLORS["lavender"], dim=True),
    "header": Style(color=COLORS["neon_violet"], bold=True),
    "android": Style(color=COLORS["mint_green"], bold=True),
    "device": Style(color=COLORS["electric_cyan"]),
    "command": Style(color=COLORS["neon_violet"]),
    "property": Style(color=COLORS["electric_yellow"]),
    "banner": Style(color=COLORS["cyber_magenta"]),
    "panel_border": Style(color=COLORS["cyber_magenta"]),
    "panel_title": Style(color=COLORS["electric_cyan"], bold=True),
}


def print_banner() -> None:
    """Display the DroidMind banner with NeonGlam aesthetics and simulated gradient."""
    # Create a more dramatic, blocky DROIDMIND logo with horizontal gradient
    console.print()
    console.print()  # Extra spacing before logo

    # Define gradient colors for a cyberpunk feel - horizontal gradient
    gradient_colors = [
        COLORS["cyber_magenta"],
        COLORS["hot_pink"],
        COLORS["neon_peach"],
        COLORS["electric_yellow"],
        COLORS["mint_green"],
        COLORS["electric_cyan"],
        COLORS["cool_blue"],
        COLORS["neon_violet"],
    ]

    # ASCII art for a more dramatic, blocky logo
    logo_lines = [
        "██████╗ ██████╗  ██████╗ ██╗██████╗ ███╗   ███╗██╗███╗   ██╗██████╗ ",
        "██╔══██╗██╔══██╗██╔═══██╗██║██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗",
        "██║  ██║██████╔╝██║   ██║██║██║  ██║██╔████╔██║██║██╔██╗ ██║██║  ██║",
        "██║  ██║██╔══██╗██║   ██║██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║██║  ██║",
        "██████╔╝██║  ██║╚██████╔╝██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██████╔╝",
        "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ ",
    ]

    # Apply horizontal gradient effect to the entire logo
    for line in logo_lines:
        gradient_line = Text()
        char_count = len(line)
        for i, char in enumerate(line):
            # Calculate color index based on character position for horizontal gradient
            color_index = min(int((i / char_count) * len(gradient_colors)), len(gradient_colors) - 1)
            gradient_line.append(char, Style(color=gradient_colors[color_index]))
        # Center the logo
        console.print(gradient_line, justify="center")

    # Add a more impactful tagline with sparkles - properly centered
    console.print()  # Add space
    tagline = Text("✧ NEURAL-POWERED ANDROID CONTROL SYSTEM ✧", style=f"bold {COLORS['electric_cyan']}")

    # Print the tagline centered without a panel
    console.print(tagline, justify="center")
    console.print()
    console.print()  # Extra spacing after logo


def display_system_info(config: dict[str, Any]) -> None:
    """Display all server configuration and connection information in a single cohesive panel."""
    # Create a styled table for all system information - no box border and wider spacing
    info_table = Table(box=None, show_header=False, padding=(0, 2), show_edge=False)
    info_table.add_column("Category", style=f"bold {COLORS['cyber_magenta']}", width=10)
    info_table.add_column("Key", style=f"bold {COLORS['electric_cyan']}", width=12)
    info_table.add_column("Value", style=f"bold {COLORS['mint_green']}")

    # Add horizontal separator
    console.print(Text("━" * console.width, style=Style(color=COLORS["cyber_magenta"])))

    # Centered title for the system info
    title = Text("✧ DROIDMIND SYSTEM STATUS ✧", style=f"bold {COLORS['electric_cyan']}")
    console.print(title, justify="center")

    # Another horizontal separator
    console.print(Text("━" * console.width, style=Style(color=COLORS["cyber_magenta"])))

    # System configuration section
    info_table.add_row("SYSTEM", "Transport", config["transport"])
    info_table.add_row("", "Host", f"{config['host']} {config.get('host_note', '')}")
    info_table.add_row("", "Port", str(config["port"]))
    info_table.add_row("", "Debug Mode", "✨ Enabled" if config["debug"] else "Disabled")
    info_table.add_row("", "Log Level", config["log_level"])

    # Connection info section - in the same table
    server_url = f"http://{config['host']}:{config['port']}"
    mcp_url = f"sse://{config['host']}:{config['port']}/sse"

    info_table.add_row("", "", "")  # Add a small visual separator
    info_table.add_row("NETWORK", "Server URL", server_url)
    info_table.add_row("", "MCP URL", mcp_url)
    info_table.add_row("", "Status", "✨ ONLINE")
    info_table.add_row("", "Exit", "Press Ctrl+C to exit")

    # Display the unified information table without a panel
    console.print(info_table)

    # Final horizontal separator
    console.print(Text("━" * console.width, style=Style(color=COLORS["cyber_magenta"])))
    console.print()

    # No need to log these messages through the standard logger anymore
    # They are already displayed in the table and are redundant


# Keep these functions for backward compatibility, but make them call the unified function
def display_server_info(config: dict[str, Any]) -> None:
    """Legacy function that now uses the unified display_system_info."""
    display_system_info(config)


def display_connection_info(host: str, port: int) -> None:
    """Legacy function that's now redundant with display_system_info."""
    # This function now does nothing as the information is displayed by display_system_info
    # Only kept for backward compatibility


def startup_complete() -> None:
    """Print a visual indicator that startup is complete."""
    msg = Text("✧ NEURAL INTERFACE ACTIVATED ✧", style=f"bold {COLORS['mint_green']}")
    console.print(Panel(msg, box=ROUNDED, border_style=styles["panel_border"], padding=(0, 2), expand=False))
    console.print()


def info(message: str) -> None:
    """Log an info message."""
    logger.info(f"[i] {message}")


def success(message: str) -> None:
    """Log a success message."""
    logger.info(f"✨ {message}")


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
    """Log a section header with a more visually appealing style."""
    # Create a sleek header text with our color
    header_text = Text(f" {message} ", style=f"bold {COLORS['cyber_magenta']}")

    # For headers, use console directly for better visual appeal
    console.print()
    console.print(header_text)

    # Also log it through the normal logger
    logger.info(message)


def config_panel(title: str, content: str, border_style: str = "panel_border") -> Panel:
    """Create a styled panel with the NeonGlam aesthetic."""
    styled_title = Text(title, style=styles["panel_title"])

    return Panel(
        content,
        title=styled_title,
        border_style=styles[border_style],
        box=ROUNDED,
        padding=(0, 1),
    )


def device_table(devices: list[dict[str, str]]) -> None:
    """Print a table of connected devices."""
    if not devices:
        warning("No devices connected.")
        return

    table = Table(title="Connected Android Devices", box=ROUNDED)
    table.border_style = styles["panel_border"].color
    table.title_style = styles["panel_title"]

    table.add_column("Serial", style=styles["device"])
    table.add_column("Status", style=styles["info"])
    table.add_column("Model", style=styles["property"])
    table.add_column("Android Version", style=styles["property"])

    for device in devices:
        table.add_row(
            device.get("serial", "unknown"),
            device.get("status", "unknown"),
            device.get("model", "unknown"),
            device.get("android_version", "unknown"),
        )

    # For tables and other rich content, we still want to use console.print
    # for direct visualization, but also log that the table was displayed
    console.print(table)
    logger.info(f"Displayed device table with {len(devices)} device(s)")


def property_table(properties: dict[str, str], title: str = "Device Properties") -> None:
    """Print a table of device properties."""
    if not properties:
        warning("No properties available.")
        return

    table = Table(title=title, box=ROUNDED)
    table.border_style = styles["panel_border"].color
    table.title_style = styles["panel_title"]

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
    command_text = Text(f"$ {command}", style=styles["command"])
    console.print(command_text)
    console.print(output)


def progress_context(description: str = "Processing...") -> Progress:
    """Context manager for showing progress during operations with NeonGlam style."""
    # Log the start of a progress operation
    logger.debug(f"Starting progress operation: {description}")

    # Return the progress context for visualization with cyberpunk styling
    return Progress(
        SpinnerColumn(spinner_name="dots2"),  # More cyberpunk-looking spinner
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style=COLORS["neon_violet"]),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    )


def create_device_tree(device_info: dict[str, Any]) -> Tree:
    """Create a rich Tree showing device information in a hierarchical view."""
    serial = device_info.get("serial", "unknown")
    tree = Tree(f"[bold {COLORS['electric_cyan']}]{serial}[/]")

    # Basic info
    basic = tree.add("Basic Info", style=COLORS["neon_violet"])
    for key in ["model", "status", "android_version"]:
        if key in device_info:
            basic.add(f"{key.replace('_', ' ').title()}: [{COLORS['electric_yellow']}]{device_info[key]}[/]")

    # Properties
    if device_info.get("properties"):
        props = tree.add("Properties", style=COLORS["neon_violet"])
        for key, value in device_info["properties"].items():
            props.add(f"{key}: [{COLORS['electric_yellow']}]{value}[/]")

    # Features
    if device_info.get("features"):
        feats = tree.add("Features", style=COLORS["neon_violet"])
        for feature in device_info["features"]:
            feats.add(f"[{COLORS['mint_green']}]{feature}[/]")

    # Log that we created a device tree
    logger.debug(f"Created device tree for {serial}")

    return tree


def create_custom_handler() -> logging.Handler:
    """Create a custom Rich logging handler that uses our styling."""
    from rich.logging import RichHandler

    class NeonGlamHandler(RichHandler):
        """Custom handler with NeonGlam styling."""

        def emit(self, record: logging.LogRecord) -> None:
            """Emit a log record with custom styling based on level."""
            # Skip recording redundant messages about server URLs that we already display
            if any(
                skip in record.msg
                for skip in [
                    "Server running at:",
                    "MCP URL:",
                    "Press Ctrl+C to exit",
                    "Server is ready!",
                    "Uvicorn running on",
                ]
            ):
                return

            super().emit(record)

    return NeonGlamHandler(rich_tracebacks=True, markup=True)

"""
Console utilities for DroidMind using the rich library for beautiful terminal output.
"""

from typing import Any

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from droidmind.log import logger

# Create a console with a custom theme for DroidMind - for direct console operations
console = Console(
    highlight=True,
    theme=None,  # Default theme works well
)

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


def startup_complete() -> None:
    """Print a visual indicator that startup is complete."""
    msg = Text("✧ NEURAL INTERFACE ACTIVATED ✧", style=f"bold {COLORS['mint_green']}")
    console.print(Panel(msg, box=ROUNDED, border_style=styles["panel_border"], padding=(0, 2), expand=False))
    console.print()


def header(message: str) -> None:
    """Log a section header with a more visually appealing style."""
    # Create a sleek header text with our color
    header_text = Text(f" {message} ", style=f"bold {COLORS['cyber_magenta']}")

    # For headers, use console directly for better visual appeal
    console.print()
    console.print(header_text)

    # Also log it through the normal logger
    logger.info(message)

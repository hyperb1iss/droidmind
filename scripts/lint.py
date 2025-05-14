#!/usr/bin/env python3

"""Lint script for the DroidMind project."""

# ruff: noqa: S603

import subprocess
import sys

from rich.console import Console
from rich.text import Text

from droidmind.console import COLORS

# Create console with NeonGlam aesthetic
console = Console()


def print_header(message: str) -> None:
    """Print a stylized header."""
    text = Text(message)
    text.stylize(f"bold {COLORS['cyber_magenta']}")
    console.print()
    console.print(text)
    console.print("━" * console.width, style=COLORS["electric_cyan"])


def run_lint() -> bool:
    """Run linting checks on the project using ruff, pylint, and mypy.

    Returns:
        bool: True if all checks passed, False otherwise
    """
    print_header("✨ DROIDMIND LINT CHECK ✨")
    checks: list[tuple[str, list[str], str]] = [
        (
            "Ruff",
            ["uv", "run", "ruff", "check"],
            "Primary linter check",
        ),
        (
            "Pylint",
            ["uv", "run", "pylint", "droidmind", "tests", "scripts"],
            "Secondary linter for complex checks",
        ),
        (
            "MyPy",
            ["uv", "run", "mypy", "droidmind"],
            "Type checking verification",
        ),
    ]
    all_passed = True
    for tool_name, command, description in checks:
        # Print what we're about to run
        console.print(f"Running {tool_name} ({description})...", style=COLORS["electric_cyan"])

        # Run the command directly, letting output flow to the terminal with original colors
        result = subprocess.run(command, check=False)

        # Check if it passed or failed
        success = result.returncode == 0
        if not success:
            all_passed = False

        # Print status after the command output
        status = "✨ PASSED" if success else "❌ FAILED"
        color = COLORS["mint_green"] if success else COLORS["hot_pink"]
        status_text = Text(f"{tool_name}: {status}")
        status_text.stylize(f"bold {color}")
        console.print(status_text)
        console.print()  # Add blank line after each tool
    # Final summary with a separator
    console.print("━" * console.width, style=COLORS["cyber_magenta"])
    if all_passed:
        console.print("✨ All checks passed!", style=f"bold {COLORS['mint_green']}")
    else:
        console.print("❌ Some checks failed.", style=f"bold {COLORS['hot_pink']}")
    return all_passed


if __name__ == "__main__":
    success = run_lint()
    sys.exit(0 if success else 1)

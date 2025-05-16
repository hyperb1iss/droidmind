#!/usr/bin/env python3
"""Release management script for DroidMind."""

# ruff: noqa: E501, T201, S603, S607, BLE001
# pylint: disable=broad-exception-caught

import collections.abc
import os
import re
import shutil
import subprocess
import sys

from colorama import Style, init
from rich.console import Console
import tomlkit
from tomlkit import exceptions as tomlkit_exceptions
from wcwidth import wcswidth

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Create a console for styled output
console = Console()

# Constants
PROJECT_NAME = "DroidMind"
REPO_NAME = "hyperb1iss/droidmind"
PROJECT_LINK = f"https://github.com/{REPO_NAME}"
ISSUE_TRACKER = f"{PROJECT_LINK}/issues"

# ANSI Color Constants - using COLORS from droidmind.console
COLOR_RESET = Style.RESET_ALL
# Map the hex colors to ANSI sequences for direct terminal printing
COLOR_BORDER = "\033[38;2;255;0;255m"  # Cyber Magenta
COLOR_STAR = "\033[38;2;255;182;193m"  # Light pink
COLOR_ERROR = f"\033[38;2;{255};{105};{180}m"  # Hot pink
COLOR_SUCCESS = f"\033[38;2;{57};{255};{20}m"  # Mint Green
COLOR_BUILD_SUCCESS = f"\033[38;2;{0};{255};{255}m"  # Electric Cyan
COLOR_VERSION_PROMPT = f"\033[38;2;{157};{0};{255}m"  # Neon Violet
COLOR_STEP = f"\033[38;2;{255};{0};{255}m"  # Cyber Magenta
COLOR_WARNING = f"\033[38;2;{255};{191};{0}m"  # Amber

# Gradient colors for the banner (NeonGlam scheme from COLORS)
GRADIENT_COLORS = [
    (255, 0, 255),  # Cyber Magenta
    (157, 0, 255),  # Neon Violet
    (0, 255, 255),  # Electric Cyan
    (57, 255, 20),  # Mint Green
    (255, 191, 0),  # Amber
]


def print_colored(message: str, color: str) -> None:
    """Print a message with a specific color."""
    print(f"{color}{message}{COLOR_RESET}")


def print_step(step: str) -> None:
    """Print a step in the process with a specific color."""
    print_colored(f"\n✨ {step}", COLOR_STEP)


def print_error(message: str) -> None:
    """Print an error message with a specific color."""
    print_colored(f"❌ Error: {message}", COLOR_ERROR)


def print_success(message: str) -> None:
    """Print a success message with a specific color."""
    print_colored(f"✅ {message}", COLOR_SUCCESS)


def print_warning(message: str) -> None:
    """Print a warning message with a specific color."""
    print_colored(f"⚠️  {message}", COLOR_WARNING)


def _load_pyproject_data() -> tuple[tomlkit.TOMLDocument, collections.abc.MutableMapping]:
    """Loads and validates the pyproject.toml file, returning the document and project table."""
    try:
        with open("pyproject.toml", encoding="utf-8") as f:
            pyproject_doc = tomlkit.parse(f.read())
    except FileNotFoundError:
        print_error("pyproject.toml not found. Please ensure it exists in the project root directory.")
        sys.exit(1)
    except tomlkit_exceptions.TOMLKitError as e:
        print_error(f"Error parsing pyproject.toml: {e!s}")
        sys.exit(1)

    project_item = pyproject_doc.get("project")
    if project_item is None:
        print_error("Invalid pyproject.toml: The [project] table is missing.")
        sys.exit(1)
    if not isinstance(project_item, collections.abc.MutableMapping):
        print_error(
            f"Invalid pyproject.toml: The 'project' key is of type '{type(project_item).__name__}', but it should be a modifiable mapping (like a TOML table)."
        )
        sys.exit(1)
    return pyproject_doc, project_item


def generate_gradient(colors: list[tuple[int, int, int]], steps: int) -> list[str]:
    """Generate a list of color codes for a smooth multi-color gradient."""
    gradient = []
    segments = len(colors) - 1
    steps_per_segment = max(1, steps // segments)

    for i in range(segments):
        start_color = colors[i]
        end_color = colors[i + 1]
        for j in range(steps_per_segment):
            t = j / steps_per_segment
            r = int(start_color[0] * (1 - t) + end_color[0] * t)
            g = int(start_color[1] * (1 - t) + end_color[1] * t)
            b = int(start_color[2] * (1 - t) + end_color[2] * t)
            gradient.append(f"\033[38;2;{r};{g};{b}m")

    return gradient


def strip_ansi(text: str) -> str:
    """Remove ANSI color codes from a string."""
    ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", text)


def apply_gradient(text: str, gradient: list[str], line_number: int) -> str:
    """Apply gradient colors diagonally to text."""
    return "".join(f"{gradient[(i + line_number) % len(gradient)]}{char}" for i, char in enumerate(text))


def center_text(text: str, width: int) -> str:
    """Center text, accounting for ANSI color codes and Unicode widths."""
    visible_length = wcswidth(strip_ansi(text))
    padding = (width - visible_length) // 2
    return f"{' ' * padding}{text}{' ' * (width - padding - visible_length)}"


def center_block(block: list[str], width: int) -> list[str]:
    """Center a block of text within a given width."""
    return [center_text(line, width) for line in block]


def create_banner() -> str:
    """Create a FULL RGB banner with diagonal gradient."""
    banner_width = 80
    content_width = banner_width - 4  # Accounting for border characters
    cosmic_gradient = generate_gradient(GRADIENT_COLORS, banner_width)

    logo = [
        "██████╗ ██████╗  ██████╗ ██╗██████╗ ███╗   ███╗██╗███╗   ██╗██████╗ ",
        "██╔══██╗██╔══██╗██╔═══██╗██║██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗",
        "██║  ██║██████╔╝██║   ██║██║██║  ██║██╔████╔██║██║██╔██╗ ██║██║  ██║",
        "██║  ██║██╔══██╗██║   ██║██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║██║  ██║",
        "██████╔╝██║  ██║╚██████╔╝██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██████╔╝",
        "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ ",
        center_text("✧ NEURAL-POWERED ANDROID CONTROL SYSTEM ✧", content_width),
    ]

    centered_logo = center_block(logo, content_width)

    banner = [
        center_text(f"{COLOR_STAR}･ ｡ ☆ ∴｡　　･ﾟ*｡★･ ∴｡　　･ﾟ*｡☆ ･ ｡ ☆ ∴｡", banner_width),
        f"{COLOR_BORDER}╭{'─' * (banner_width - 2)}╮",
    ]

    for line_number, line in enumerate(centered_logo):
        gradient_line = apply_gradient(line, cosmic_gradient, line_number)
        banner.append(f"{COLOR_BORDER}│ {gradient_line} {COLOR_BORDER}│")

    release_manager_text = COLOR_STEP + "Release Manager"

    banner.extend(
        [
            f"{COLOR_BORDER}╰{'─' * (banner_width - 2)}╯",
            center_text(
                f"{COLOR_STAR}∴｡　　･ﾟ*｡☆ {release_manager_text}{COLOR_STAR} ☆｡*ﾟ･　 ｡∴",
                banner_width,
            ),
            center_text(f"{COLOR_STAR}･ ｡ ☆ ∴｡　　･ﾟ*｡★･ ∴｡　　･ﾟ*｡☆ ･ ｡ ☆ ∴｡", banner_width),
        ]
    )

    return "\n".join(banner)


def print_logo() -> None:
    """Print the banner/logo for the release manager."""
    print(create_banner())


def check_tool_installed(tool_name: str) -> None:
    """Check if a tool is installed."""
    if shutil.which(tool_name) is None:
        print_error(f"{tool_name} is not installed. Please install it and try again.")
        sys.exit(1)


def check_branch() -> None:
    """Ensure we're on the main branch."""
    current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
    if current_branch != "main":
        print_error("You must be on the main branch to release.")
        sys.exit(1)


def check_uncommitted_changes() -> None:
    """Check for uncommitted changes."""
    result = subprocess.run(
        ["git", "diff-index", "--quiet", "HEAD", "--"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print_error("You have uncommitted changes. Please commit or stash them before releasing.")
        sys.exit(1)


def get_current_version() -> str:
    """Get the current version from pyproject.toml."""
    _pyproject_doc, project_table = _load_pyproject_data()

    version_item = project_table.get("version")
    if version_item is None:
        print_error("Invalid pyproject.toml: The 'version' key is missing from the [project] table.")
        sys.exit(1)

    if not isinstance(version_item, str):
        print_warning(
            f"Warning: 'version' in pyproject.toml is of type '{type(version_item).__name__}', not a string. Attempting to use it as a string."
        )
    return str(version_item)


def update_version(new_version: str) -> None:
    """Update the version in pyproject.toml."""
    pyproject_doc, project_table = _load_pyproject_data()

    project_table["version"] = new_version

    with open("pyproject.toml", "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(pyproject_doc))

    print_success(f"Updated version in pyproject.toml to {new_version}")


def update_docs_version(current_version: str, new_version: str) -> None:
    """Update documentation version."""
    docs_paths = ["README.md", "docs/index.md"]
    for docs_path in docs_paths:
        if os.path.exists(docs_path):
            with open(docs_path, encoding="utf-8") as f:
                content = f.read()
            # Try different version patterns
            patterns = [
                f"version {current_version}",
                f"v{current_version}",
                f"Version: {current_version}",
            ]
            updated_content = content
            for pattern in patterns:
                replacement = pattern.replace(current_version, new_version)
                updated_content = updated_content.replace(pattern, replacement)
            # Only write if changes were made
            if updated_content != content:
                with open(docs_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                print_success(f"Updated version in {docs_path} to {new_version}")
            else:
                print_warning(f"No version string found in {docs_path}. Manual update may be needed.")
        else:
            print_warning(f"{docs_path} not found. Skipping documentation version update.")


def show_changes() -> bool:
    """Show changes and ask for confirmation."""
    print_warning("The following files will be modified:")
    subprocess.run(["git", "status", "--porcelain"], check=True)
    confirmation = input(
        f"{COLOR_VERSION_PROMPT}Do you want to proceed with these changes? (y/N): {COLOR_RESET}"
    ).lower()
    return confirmation == "y"


def commit_and_push(version: str) -> None:
    """Commit and push changes to the repository."""
    print_step("Committing and pushing changes")
    try:
        subprocess.run(["git", "add", "pyproject.toml", "README.md", "docs"], check=True)
        subprocess.run(["git", "commit", "-m", f"✨ Release version {version}"], check=True)
        subprocess.run(["git", "push"], check=True)
        subprocess.run(["git", "tag", f"v{version}"], check=True)
        subprocess.run(["git", "push", "--tags"], check=True)
        print_success(f"Changes committed and pushed for version {version}")
    except subprocess.CalledProcessError as e:
        print_error(f"Git operations failed: {e!s}")
        sys.exit(1)


def is_valid_version(version: str) -> bool:
    """Validate version format."""
    return re.match(r"^\d+\.\d+\.\d+$", version) is not None


def run_tests() -> bool:
    """Run tests to ensure everything works before release."""
    print_step("Running tests")
    try:
        result = subprocess.run(["pytest"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print_success("All tests passed!")
            return True
        print_error("Tests failed. Please fix the tests before releasing.")
        print(result.stdout)
        print(result.stderr)
        return False
    except Exception as e:
        print_error(f"Error running tests: {e!s}")
        return False


def main() -> None:
    """Main function to handle the release process."""
    print_logo()
    print_step(f"Starting release process for {PROJECT_NAME}")

    for tool in ["git", "uv", "pytest"]:
        check_tool_installed(tool)

    check_branch()
    check_uncommitted_changes()

    current_version = get_current_version()
    new_version = input(
        f"{COLOR_VERSION_PROMPT}Current version is {current_version}. What should the new version be? {COLOR_RESET}"
    )

    if not is_valid_version(new_version):
        print_error("Invalid version format. Please use semantic versioning (e.g., 1.2.3).")
        sys.exit(1)

    if not run_tests():
        confirmation = input(f"{COLOR_WARNING}Tests failed. Continue anyway? (y/N): {COLOR_RESET}").lower()
        if confirmation != "y":
            print_error("Release cancelled.")
            sys.exit(1)

    update_version(new_version)
    update_docs_version(current_version, new_version)

    if not show_changes():
        print_error("Release cancelled.")
        sys.exit(1)

    commit_and_push(new_version)

    print_success(f"\n🎉✨ {PROJECT_NAME} v{new_version} has been successfully released! ✨🎉")


if __name__ == "__main__":
    main()

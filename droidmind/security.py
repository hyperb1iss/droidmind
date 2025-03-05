"""
Security module for DroidMind.

This module provides security features for DroidMind, including:
- Command sanitization and validation
- Risk level assessment for operations
- Allowed/disallowed command management

The security system is designed to prevent dangerous operations while still
allowing AI assistants to be expressive and execute common, useful commands.
"""

from enum import Enum, auto
import re
import shlex

from droidmind.log import logger


class RiskLevel(Enum):
    """Risk level for operations."""

    SAFE = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


# Set of allowed shell commands based on toybox commands
# This is a comprehensive list of generally safe commands
ALLOWED_SHELL_COMMANDS: set[str] = {
    # File operations (read-only)
    "cd",
    "ls",
    "find",
    "grep",
    "cat",
    "head",
    "tail",
    "wc",
    "du",
    "df",
    "stat",
    "file",
    "readlink",
    "dirname",
    "basename",
    "pwd",
    "realpath",
    "which",
    "whoami",
    "id",
    "groups",
    "md5sum",
    "sha1sum",
    "sha256sum",
    "sha512sum",
    "cksum",
    "cmp",
    "diff",
    "sort",
    "uniq",
    "tr",
    "cut",
    "comm",
    "od",
    "hexdump",
    "xxd",
    "strings",
    "base64",
    "expr",
    "seq",
    "printf",
    "echo",
    "yes",
    "false",
    "true",
    "test",
    "[",
    "[[",
    # Process information
    "ps",
    "pgrep",
    "pidof",
    "top",
    "uptime",
    "vmstat",
    "lsof",
    "netstat",
    "ifconfig",
    "ip",
    "ss",
    "arp",
    "route",
    "traceroute",
    "ping",
    # System information
    "uname",
    "hostname",
    "dmesg",
    "getprop",
    "getenforce",
    "date",
    "time",
    "hwclock",
    "ionice",
    "lsmod",
    "lspci",
    "lsusb",
    "free",
    "sysctl",
    # Android-specific
    "am",
    "pm",
    "dumpsys",
    "bugreport",
    "logcat",
    "settings",
    "service",
    "content",
    "input",
    "screencap",
    "screenrecord",
    "wm",
    "ime",
    # Text processing
    "awk",
    "sed",
    "xargs",
    "tee",
    "nl",
    "fold",
    "expand",
    "unexpand",
    "column",
    "rev",
    "tac",
    "less",
    "more",
    "zcat",
    "gzip",
    "gunzip",
    "bzip2",
    "bunzip2",
    "xz",
    "unxz",
    "lzma",
    "unlzma",
    "zip",
    "unzip",
    # Misc utilities
    "sleep",
    "timeout",
    "watch",
    "cal",
    "clear",
    "env",
    "printenv",
    "locale",
    "inotifyd",
    "nice",
    "nohup",
    "taskset",
    "ulimit",
    "usleep",
}

# Commands that are explicitly disallowed due to their destructive potential
DISALLOWED_SHELL_COMMANDS: set[str] = {
    # System modification
    "mkfs",
    "mke2fs",
    "mkswap",
    "swapon",
    "swapoff",
    "mount",
    "umount",
    "reboot",
    "poweroff",
    "halt",
    "shutdown",
    "init",
    "telinit",
    "runlevel",
    "insmod",
    "rmmod",
    "modprobe",
    # Process control
    "kill",
    "killall",
    "pkill",
    "renice",
    "setsid",
    "chroot",
    # User management
    "useradd",
    "userdel",
    "usermod",
    "groupadd",
    "groupdel",
    "groupmod",
    "passwd",
    "chpasswd",
    "su",
    "sudo",
    "chsh",
    "chfn",
    # Dangerous Android commands
    "setprop",
    "setenforce",
    "flash",
    "fastboot",
    "recovery",
    "format",
}

# Patterns that might indicate command injection attempts
SUSPICIOUS_PATTERNS: list[str] = [
    r";\s*rm\s+",
    r"&&\s*rm\s+",
    r"\|\s*rm\s+",  # rm command injection
    r";\s*reboot",
    r"&&\s*reboot",
    r"\|\s*reboot",  # reboot injection
    r">\s*/system",
    r">>\s*/system",  # writing to system
    r">\s*/data",
    r">>\s*/data",  # writing to data
    r">\s*/proc",
    r">>\s*/proc",  # writing to proc
    r">\s*/dev",
    r">>\s*/dev",  # writing to dev
    r";\s*dd",
    r"&&\s*dd",
    r"\|\s*dd",  # dd command injection
    r";\s*mkfs",
    r"&&\s*mkfs",
    r"\|\s*mkfs",  # filesystem formatting
]

# Paths that should be protected from modification
PROTECTED_PATHS: list[str] = [
    "/system",
    "/vendor",
    "/product",
    "/apex",
    "/boot",
    "/recovery",
    "/proc",
    "/sys",
    "/dev",
    "/etc",
    "/bin",
    "/sbin",
    "/lib",
    "/lib64",
]


def assess_command_risk(command: str) -> RiskLevel:
    """
    Assess the risk level of a shell command.

    Args:
        command: The shell command to assess

    Returns:
        RiskLevel enum indicating the risk level
    """
    # Split the command into individual piped commands
    piped_commands = [cmd.strip() for cmd in command.split("|")]

    highest_risk = RiskLevel.SAFE

    for cmd in piped_commands:
        # Split the command to get the base command
        try:
            parts = shlex.split(cmd)
        except ValueError:
            return RiskLevel.HIGH

        if not parts:
            continue

        base_cmd = parts[0]

        # Check if command is explicitly disallowed
        if base_cmd in DISALLOWED_SHELL_COMMANDS:
            return RiskLevel.CRITICAL

        # Check if command is not in allowed list
        if base_cmd not in ALLOWED_SHELL_COMMANDS:
            return RiskLevel.HIGH

        # Check for suspicious patterns
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, cmd):
                return RiskLevel.HIGH

        # Check for protected paths
        for path in PROTECTED_PATHS:
            if f" {path}" in cmd or f"={path}" in cmd or cmd.startswith(path):
                # Commands that just read from protected paths are medium risk
                if base_cmd in {"ls", "cat", "head", "tail", "grep", "find"}:
                    if highest_risk.value < RiskLevel.MEDIUM.value:
                        highest_risk = RiskLevel.MEDIUM
                else:
                    # Other operations on protected paths are high risk
                    return RiskLevel.HIGH

        # Check for specific risky operations
        if ">" in cmd or ">>" in cmd:
            if highest_risk.value < RiskLevel.MEDIUM.value:
                highest_risk = RiskLevel.MEDIUM  # File redirection

        if ";" in cmd or "&&" in cmd:
            if highest_risk.value < RiskLevel.MEDIUM.value:
                highest_risk = RiskLevel.MEDIUM  # Command chaining

    return highest_risk


def validate_shell_command(command: str) -> bool:
    """
    Validate if a shell command is allowed to run.

    Args:
        command: The shell command to validate

    Returns:
        True if command is allowed, False otherwise

    Raises:
        ValueError: If command is explicitly disallowed or contains suspicious patterns
    """
    # Split the command to get the base command
    try:
        parts = shlex.split(command)
    except ValueError as e:
        raise ValueError(f"Invalid command syntax: {e}") from e

    if not parts:
        return True

    base_cmd = parts[0]

    # Check if command is explicitly disallowed
    if base_cmd in DISALLOWED_SHELL_COMMANDS:
        raise ValueError(f"Command '{base_cmd}' is explicitly disallowed for security reasons")

    # Check if command is not in allowed list
    if base_cmd not in ALLOWED_SHELL_COMMANDS:
        raise ValueError(f"Command '{base_cmd}' is not in the allowed commands list")

    # Check for suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, command):
            raise ValueError(f"Command contains suspicious pattern: {pattern}")

    return True


def sanitize_shell_command(command: str) -> str:
    """
    Sanitize a shell command to make it safer.

    Args:
        command: The shell command to sanitize

    Returns:
        Sanitized command

    Raises:
        ValueError: If command cannot be sanitized safely
    """
    # First validate the command
    validate_shell_command(command)

    # For shell commands, we actually want to preserve the original command structure
    # Only sanitize if there are clearly malicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, command):
            raise ValueError(f"Command contains suspicious pattern: {pattern}")

    return command


async def validate_adb_command(command: list[str]) -> bool:
    """
    Validate if an ADB command is allowed to run.

    Args:
        command: The ADB command as a list of arguments

    Returns:
        True if command is allowed, False otherwise

    Raises:
        ValueError: If command is disallowed
    """
    if not command:
        return True

    # Basic ADB commands are safe
    safe_adb_commands = {"devices", "connect", "disconnect", "version", "start-server", "kill-server"}

    # If it's a basic ADB command, it's safe
    if command[0] in safe_adb_commands:
        return True

    # Handle shell commands
    try:
        shell_idx = command.index("shell")
        if len(command) > shell_idx + 1:
            shell_command = " ".join(command[shell_idx + 1 :])
            validate_shell_command(shell_command)
    except ValueError:
        # Not a shell command, assume other ADB commands are safe
        pass

    return True


def log_command_execution(command: str, risk_level: RiskLevel | None = None) -> None:
    """
    Log command execution with appropriate level based on risk.

    Args:
        command: The command being executed
        risk_level: Optional risk level override
    """
    # Extract the actual command for risk assessment
    cmd_for_risk = command

    # Handle ADB commands with device serial
    if command.startswith("-s "):
        parts = command.split()
        try:
            shell_idx = parts.index("shell")
            if shell_idx + 1 < len(parts):
                cmd_for_risk = " ".join(parts[shell_idx + 1 :])
        except ValueError:
            # Not a shell command, treat as safe ADB command
            cmd_for_risk = parts[0] if parts else command

    # Handle basic ADB commands
    elif any(cmd in command for cmd in ["devices", "connect", "disconnect", "version", "start-server", "kill-server"]):
        risk_level = RiskLevel.SAFE

    # Assess risk if not already provided
    if risk_level is None:
        risk_level = assess_command_risk(cmd_for_risk)

    # Log based on risk level
    if risk_level == RiskLevel.CRITICAL:
        logger.critical("CRITICAL RISK COMMAND EXECUTION: %s", command)
    elif risk_level == RiskLevel.HIGH:
        logger.warning("HIGH RISK COMMAND EXECUTION: %s", command)
    elif risk_level == RiskLevel.MEDIUM:
        logger.info("MEDIUM RISK COMMAND EXECUTION: %s", command)
    elif risk_level == RiskLevel.LOW:
        logger.info("LOW RISK COMMAND EXECUTION: %s", command)
    else:
        logger.debug("Command execution: %s", command)

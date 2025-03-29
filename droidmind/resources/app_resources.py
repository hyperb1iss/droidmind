"""
App resources for DroidMind.

This module provides resources for interacting with apps on Android devices.
"""

from dataclasses import dataclass
import re

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger


@dataclass
class PackageInfo:
    """Basic package information."""

    version_code: str | None = None
    version_name: str | None = None
    min_sdk: str | None = None
    target_sdk: str | None = None
    install_path: str = "Unknown"
    first_install: str = "Unknown"
    last_update: str | None = None
    user_id: str = "Unknown"
    cpu_arch: str | None = None
    data_dir: str | None = None
    flags: str | None = None


def extract_package_info(dump_output: str) -> PackageInfo:
    """Extract basic package information from dumpsys output."""
    info = PackageInfo()

    # Version info
    if match := re.search(r"versionCode=(\d+)", dump_output):
        info.version_code = match.group(1)
    if match := re.search(r"versionName=([^\s]+)", dump_output):
        info.version_name = match.group(1)
    if match := re.search(r"minSdk=(\d+)", dump_output):
        info.min_sdk = match.group(1)
    if match := re.search(r"targetSdk=(\d+)", dump_output):
        info.target_sdk = match.group(1)

    # Paths and IDs
    if match := re.search(r"codePath=([^\s]+)", dump_output):
        info.install_path = match.group(1)
    if match := re.search(r"firstInstallTime=([^\r\n]+)", dump_output):
        info.first_install = match.group(1)
    if match := re.search(r"lastUpdateTime=([^\r\n]+)", dump_output):
        info.last_update = match.group(1)
    if match := re.search(r"userId=(\d+)", dump_output):
        info.user_id = match.group(1)

    # System info
    if match := re.search(r"primaryCpuAbi=([^\s]+)", dump_output):
        if match.group(1) != "null":
            info.cpu_arch = match.group(1)
    if match := re.search(r"dataDir=([^\s]+)", dump_output):
        info.data_dir = match.group(1)
    if match := re.search(r"flags=\[\s([^\]]+)\s\]", dump_output):
        info.flags = match.group(1)

    return info


def format_package_info(info: PackageInfo) -> str:
    """Format package information as markdown."""
    manifest = "## Package Information\n\n"

    # Version info
    if any([info.version_code, info.version_name, info.min_sdk, info.target_sdk]):
        if info.version_code:
            manifest += f"- **Version Code**: {info.version_code}\n"
        if info.version_name:
            manifest += f"- **Version Name**: {info.version_name}\n"
        if info.min_sdk:
            manifest += f"- **Min SDK**: {info.min_sdk}\n"
        if info.target_sdk:
            manifest += f"- **Target SDK**: {info.target_sdk}\n"

    # Paths and dates
    manifest += f"- **Install Path**: {info.install_path}\n"
    manifest += f"- **First Install**: {info.first_install}\n"
    if info.last_update:
        manifest += f"- **Last Update**: {info.last_update}\n"
    manifest += f"- **User ID**: {info.user_id}\n"

    # Optional system info
    if info.cpu_arch:
        manifest += f"- **CPU Architecture**: {info.cpu_arch}\n"
    if info.data_dir:
        manifest += f"- **Data Directory**: {info.data_dir}\n"
    if info.flags:
        manifest += f"- **Flags**: {info.flags}\n"

    return manifest


def extract_permissions(dump_output: str) -> tuple[list[str], list[str]]:
    """Extract declared and requested permissions from dumpsys output."""
    declared_perms = []
    requested_perms = []

    # Extract declared permissions
    if declared_match := re.compile(r"declared permissions:\s*\r?\n((?:\s+[^\r\n]+\r?\n)+)", re.MULTILINE).search(
        dump_output
    ):
        declared_block = declared_match.group(1)
        for line in declared_block.split("\n"):
            if perm_match := re.match(r"\s+([^:]+):", line.strip()):
                declared_perms.append(perm_match.group(1))

    # Extract requested permissions
    if requested_match := re.compile(r"requested permissions:\s*\r?\n((?:\s+[^\r\n]+\r?\n)+)", re.MULTILINE).search(
        dump_output
    ):
        requested_block = requested_match.group(1)
        requested_perms = [line.strip() for line in requested_block.split("\n") if line.strip()]

    return declared_perms, requested_perms


def format_permissions(declared_perms: list[str], requested_perms: list[str]) -> str:
    """Format permissions as markdown."""
    manifest = "\n## Permissions\n\n"

    # Declared permissions
    manifest += "### Declared Permissions\n\n"
    if declared_perms:
        for perm in declared_perms:
            manifest += f"- `{perm}`\n"
    else:
        manifest += "No declared permissions.\n"

    # Requested permissions
    manifest += "\n### Requested Permissions\n\n"
    if requested_perms:
        for perm in requested_perms:
            manifest += f"- `{perm}`\n"
    else:
        manifest += "No requested permissions.\n"

    return manifest


def extract_components(dump_output: str, package: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """Extract activities, services, providers, and receivers from dumpsys output."""
    activities = []
    services = []
    providers = []
    receivers = []

    # Extract activities
    activity_pattern = re.compile(r"([a-zA-Z0-9_$.\/]+/[a-zA-Z0-9_$.]+) filter", re.MULTILINE)
    main_activity_pattern = re.compile(r"([a-zA-Z0-9_$.]+/\.[a-zA-Z0-9_$.]+) filter", re.MULTILINE)

    for match in activity_pattern.finditer(dump_output):
        activity = match.group(1)
        if activity not in activities and activity.startswith(f"{package}/"):
            activities.append(activity)

    for match in main_activity_pattern.finditer(dump_output):
        activity = match.group(1)
        if activity not in activities and activity.startswith(f"{package}/"):
            activities.append(activity)

    # Extract services
    if service_section_match := re.search(
        r"Service Resolver Table:(.*?)(?:\r?\n\r?\n|\r?\nProvider Resolver Table:)", dump_output, re.DOTALL
    ):
        service_section = service_section_match.group(1)
        service_pattern = re.compile(r"([a-zA-Z0-9_$.\/]+/[a-zA-Z0-9_$.]+)", re.MULTILINE)
        for match in service_pattern.finditer(service_section):
            service = match.group(1)
            if service not in services and service.startswith(f"{package}/"):
                services.append(service)

    # Extract providers
    if provider_section_match := re.search(
        r"Provider Resolver Table:(.*?)(?:\r?\n\r?\n|\r?\nReceiver Resolver Table:)", dump_output, re.DOTALL
    ):
        provider_section = provider_section_match.group(1)
        provider_pattern = re.compile(r"([a-zA-Z0-9_$.\/]+/[a-zA-Z0-9_$.]+)", re.MULTILINE)
        for match in provider_pattern.finditer(provider_section):
            provider = match.group(1)
            if provider not in providers and provider.startswith(f"{package}/"):
                providers.append(provider)

    # Extract receivers
    if receiver_section_match := re.search(
        r"Receiver Resolver Table:(.*?)(?:\r?\n\r?\n|\r?\nService Resolver Table:)", dump_output, re.DOTALL
    ):
        receiver_section = receiver_section_match.group(1)
        receiver_pattern = re.compile(r"([a-zA-Z0-9_$.\/]+/[a-zA-Z0-9_$.]+)", re.MULTILINE)
        for match in receiver_pattern.finditer(receiver_section):
            receiver = match.group(1)
            if receiver not in receivers and receiver.startswith(f"{package}/"):
                receivers.append(receiver)

    return activities, services, providers, receivers


def get_intent_filters(component: str, dump_output: str) -> list[str]:
    """Extract intent filters for a component."""
    component_short = component.split("/")[-1]
    filters = []
    in_filter = False

    for line in dump_output.splitlines():
        if component_short in line and "filter" in line:
            in_filter = True
            continue
        if in_filter:
            if not line.strip() or line.startswith("      Filter"):
                continue
            if not line.startswith(" " * 10):
                in_filter = False
                break
            filter_info = line.strip()
            if filter_info and filter_info not in filters:
                filters.append(filter_info)

    return filters


def format_component_section(title: str, components: list[str], dump_output: str) -> str:
    """Format a component section as markdown."""
    manifest = f"\n### {title}\n\n"

    if not components:
        manifest += f"No {title.lower()} found.\n"
        return manifest

    for component in components:
        manifest += f"- `{component}`\n"
        filters = get_intent_filters(component, dump_output)
        if filters:
            manifest += "  Intent Filters:\n"
            for f in filters:
                manifest += f"  - {f}\n"

    return manifest


def format_components(
    activities: list[str], services: list[str], providers: list[str], receivers: list[str], dump_output: str
) -> str:
    """Format all components as markdown."""
    manifest = "\n## Components\n"
    manifest += format_component_section("Activities", activities, dump_output)
    manifest += format_component_section("Services", services, dump_output)
    manifest += format_component_section("Content Providers", providers, dump_output)
    manifest += format_component_section("Broadcast Receivers", receivers, dump_output)
    return manifest


@mcp.resource("fs://{serial}/app/{package}/manifest")
async def app_manifest(serial: str, package: str) -> str:
    """
    Get the AndroidManifest.xml contents for an app.

    Args:
        serial: Device serial number
        package: Package name to get manifest for

    Returns:
        A markdown-formatted representation of the app manifest
    """
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            return f"Error: Device {serial} not found."

        # Get app info using dumpsys package without line limit
        cmd = f"dumpsys package {package}"
        dump_output = await device.run_shell(cmd, max_lines=None)
        if "Unable to find package" in dump_output:
            return f"Error: Package {package} not found."

        # Build the manifest sections
        manifest = f"# App Manifest for {package}\n\n"

        # Extract and format package info
        pkg_info = extract_package_info(dump_output)
        manifest += format_package_info(pkg_info)

        # Extract and format permissions
        declared_perms, requested_perms = extract_permissions(dump_output)
        manifest += format_permissions(declared_perms, requested_perms)

        # Extract and format components
        activities, services, providers, receivers = extract_components(dump_output, package)
        manifest += format_components(activities, services, providers, receivers, dump_output)

        return manifest

    except Exception as e:
        logger.exception("Error retrieving app manifest: %s", e)
        return f"Error retrieving app manifest: {e!s}"

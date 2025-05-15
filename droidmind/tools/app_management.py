"""
App Management Tools - MCP tools for installing and managing Android applications.

This module provides MCP tools for installing, uninstalling, and managing Android applications,
as well as extracting and analyzing app information like manifests, components, and permissions.
"""

from dataclasses import dataclass
from enum import Enum
import os
import re

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger


class AppAction(str, Enum):
    """Defines the available sub-actions for the 'android-app' tool."""

    INSTALL_APP = "install_app"
    UNINSTALL_APP = "uninstall_app"
    START_APP = "start_app"
    STOP_APP = "stop_app"
    CLEAR_APP_DATA = "clear_app_data"
    LIST_PACKAGES = "list_packages"
    GET_APP_MANIFEST = "get_app_manifest"
    GET_APP_PERMISSIONS = "get_app_permissions"
    GET_APP_ACTIVITIES = "get_app_activities"
    GET_APP_INFO = "get_app_info"


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


class AppAnalyzer:
    """Class for analyzing and extracting app information."""

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def format_component_section(title: str, components: list[str], dump_output: str) -> str:
        """Format a component section as markdown."""
        manifest = f"\n### {title}\n\n"

        if not components:
            manifest += f"No {title.lower()} found.\n"
            return manifest

        for component in components:
            manifest += f"- `{component}`\n"
            filters = AppAnalyzer.get_intent_filters(component, dump_output)
            if filters:
                manifest += "  Intent Filters:\n"
                for f in filters:
                    manifest += f"  - {f}\n"

        return manifest

    @staticmethod
    def format_components(
        activities: list[str], services: list[str], providers: list[str], receivers: list[str], dump_output: str
    ) -> str:
        """Format all components as markdown."""
        manifest = "\n## Components\n"
        manifest += AppAnalyzer.format_component_section("Activities", activities, dump_output)
        manifest += AppAnalyzer.format_component_section("Services", services, dump_output)
        manifest += AppAnalyzer.format_component_section("Content Providers", providers, dump_output)
        manifest += AppAnalyzer.format_component_section("Broadcast Receivers", receivers, dump_output)
        return manifest


async def _install_app_impl(
    serial: str,
    apk_path: str,
    ctx: Context,
    reinstall: bool = False,
    grant_permissions: bool = True,
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
    try:
        # Check if APK exists
        if not os.path.isfile(apk_path):
            return f"Error: APK file not found at {apk_path}"

        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Install the app
        await ctx.info(f"Installing APK {apk_path} on device {serial}...")
        result = await device.install_app(apk_path, reinstall, grant_permissions)

        if "Success" in result:
            return f"✅ Successfully installed APK on device {serial}"

        return f"❌ Failed to install APK: {result}"
    except Exception as e:
        logger.exception("Error installing APK: %s", e)
        return f"Error installing APK: {e!s}"


async def _uninstall_app_impl(serial: str, package: str, ctx: Context, keep_data: bool = False) -> str:
    """
    Uninstall an app from the device.

    Args:
        serial: Device serial number
        package: Package name to uninstall
        keep_data: Whether to keep app data and cache directories

    Returns:
        Uninstallation result message
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Uninstall the app
        await ctx.info(f"Uninstalling package {package} from device {serial}...")
        result = await device.uninstall_app(package, keep_data)

        if "Success" in result:
            data_msg = " (keeping app data)" if keep_data else ""
            return f"✅ Successfully uninstalled {package} from device {serial}{data_msg}"

        return f"❌ Failed to uninstall {package}: {result}"
    except Exception as e:
        logger.exception("Error uninstalling app: %s", e)
        return f"Error uninstalling app: {e!s}"


async def _start_app_impl(serial: str, package: str, ctx: Context, activity: str = "") -> str:
    """
    Start an app on the device.

    Args:
        serial: Device serial number
        package: Package name to start
        activity: Optional activity name to start (if empty, launches the default activity)

    Returns:
        Result message
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Start the app
        activity_str = f" (activity: {activity})" if activity else ""
        await ctx.info(f"Starting app {package}{activity_str} on device {serial}...")
        result = await device.start_app(package, activity)

        if "Error" in result:
            return f"❌ {result}"

        return f"✅ {result}"
    except Exception as e:
        logger.exception("Error starting app: %s", e)
        return f"Error starting app: {e!s}"


async def _stop_app_impl(serial: str, package: str, ctx: Context) -> str:
    """
    Force stop an app on the device.

    Args:
        serial: Device serial number
        package: Package name to stop

    Returns:
        Result message
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Stop the app
        await ctx.info(f"Stopping app {package} on device {serial}...")
        result = await device.stop_app(package)

        return f"✅ {result}"
    except Exception as e:
        logger.exception("Error stopping app: %s", e)
        return f"Error stopping app: {e!s}"


async def _clear_app_data_impl(serial: str, package: str, ctx: Context) -> str:
    """
    Clear app data and cache for the specified package.

    Args:
        serial: Device serial number
        package: Package name to clear data for

    Returns:
        Result message
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Clear app data
        await ctx.info(f"Clearing data for app {package} on device {serial}...")
        result = await device.clear_app_data(package)

        if "Successfully" in result:
            return f"✅ {result}"

        return f"❌ {result}"
    except Exception as e:
        logger.exception("Error clearing app data: %s", e)
        return f"Error clearing app data: {e!s}"


async def _list_packages_impl(serial: str, ctx: Context, include_system_apps: bool = False) -> str:
    """
    List installed packages on the device.

    Args:
        serial: Device serial number
        include_system_apps: Whether to include system apps in the list

    Returns:
        Formatted list of installed packages
    """
    try:
        device = await get_device_manager().get_device(serial)

        if not device:
            return f"Error: Device {serial} not connected or not found."

        # Get app list
        await ctx.info(f"Retrieving installed packages from device {serial}...")
        app_list = await device.get_app_list(include_system_apps)

        if not app_list:
            return "No packages found on the device."

        result = "# Installed Packages\n\n"
        result += "| Package Name | APK Path |\n"
        result += "|-------------|----------|\n"

        for app in app_list:
            package_name = app.get("package", "Unknown")
            apk_path = app.get("path", "Unknown")
            result += f"| `{package_name}` | `{apk_path}` |\n"

        return result
    except Exception as e:
        logger.exception("Error listing packages: %s", e)
        return f"Error listing packages: {e!s}"


async def _get_app_manifest_impl(serial: str, package: str, ctx: Context) -> str:
    """
    Get the AndroidManifest.xml contents for an app.

    Args:
        serial: Device serial number
        package: Package name to get manifest for
        ctx: Context for logging and progress

    Returns:
        A markdown-formatted representation of the app manifest
    """
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            return f"Error: Device {serial} not found."

        # Get app info using dumpsys package without line limit
        await ctx.info(f"Retrieving manifest for {package} on device {serial}...")
        cmd = f"dumpsys package {package}"
        dump_output = await device.run_shell(cmd, max_lines=None)
        if "Unable to find package" in dump_output:
            return f"Error: Package {package} not found."

        # Build the manifest sections
        manifest = f"# App Manifest for {package}\n\n"

        # Extract and format package info using AppAnalyzer
        pkg_info = AppAnalyzer.extract_package_info(dump_output)
        manifest += AppAnalyzer.format_package_info(pkg_info)

        # Extract and format permissions
        declared_perms, requested_perms = AppAnalyzer.extract_permissions(dump_output)
        manifest += AppAnalyzer.format_permissions(declared_perms, requested_perms)

        # Extract and format components
        activities, services, providers, receivers = AppAnalyzer.extract_components(dump_output, package)
        manifest += AppAnalyzer.format_components(activities, services, providers, receivers, dump_output)

        return manifest

    except Exception as e:
        logger.exception("Error retrieving app manifest: %s", e)
        return f"Error retrieving app manifest: {e!s}"


async def _get_app_permissions_impl(serial: str, package: str, ctx: Context) -> str:
    """
    Get the permissions used by an app.

    Args:
        serial: Device serial number
        package: Package name to get permissions for
        ctx: Context for logging and progress

    Returns:
        A markdown-formatted representation of the app's permissions
    """
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            return f"Error: Device {serial} not found."

        # Get app info using dumpsys package without line limit
        await ctx.info(f"Retrieving permissions for {package} on device {serial}...")
        cmd = f"dumpsys package {package}"
        dump_output = await device.run_shell(cmd, max_lines=None)
        if "Unable to find package" in dump_output:
            return f"Error: Package {package} not found."

        # Extract and format permissions
        declared_perms, requested_perms = AppAnalyzer.extract_permissions(dump_output)
        result = f"# Permissions for {package}\n"
        result += AppAnalyzer.format_permissions(declared_perms, requested_perms)

        # Add runtime permission status
        result += "\n## Runtime Permission Status\n\n"
        cmd = f'dumpsys package {package} | grep -A20 "runtime permissions:"'
        runtime_perms = await device.run_shell(cmd)

        if runtime_perms and "runtime permissions:" in runtime_perms:
            result += "```\n" + runtime_perms + "\n```"
        else:
            result += "No runtime permission information available.\n"

        return result

    except Exception as e:
        logger.exception("Error retrieving app permissions: %s", e)
        return f"Error retrieving app permissions: {e!s}"


async def _get_app_activities_impl(serial: str, package: str, ctx: Context) -> str:
    """
    Get the activities defined in an app.

    Args:
        serial: Device serial number
        package: Package name to get activities for
        ctx: Context for logging and progress

    Returns:
        A markdown-formatted representation of the app's activities
    """
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            return f"Error: Device {serial} not found."

        # Get app info using dumpsys package
        await ctx.info(f"Retrieving activities for {package} on device {serial}...")
        cmd = f"dumpsys package {package}"
        dump_output = await device.run_shell(cmd, max_lines=None)
        if "Unable to find package" in dump_output:
            return f"Error: Package {package} not found."

        # Extract activities
        activities, _, _, _ = AppAnalyzer.extract_components(dump_output, package)

        # Format the output
        result = f"# Activities for {package}\n\n"

        if not activities:
            result += "No activities found.\n"
        else:
            result += f"Found {len(activities)} activities:\n\n"
            for activity in activities:
                result += f"- `{activity}`\n"
                filters = AppAnalyzer.get_intent_filters(activity, dump_output)
                if filters:
                    result += "  Intent Filters:\n"
                    for f in filters:
                        result += f"  - {f}\n"

        # Add information about the main activity
        result += "\n## Main Activity\n\n"
        cmd = f"cmd package resolve-activity --brief {package}"
        main_activity = await device.run_shell(cmd)

        if main_activity and package in main_activity:
            result += f"```\n{main_activity}\n```"
        else:
            result += "No main activity information available.\n"

        return result

    except Exception as e:
        logger.exception("Error retrieving app activities: %s", e)
        return f"Error retrieving app activities: {e!s}"


async def _get_app_info_impl(serial: str, package: str, ctx: Context) -> str:
    """
    Get detailed information about an app.

    Args:
        serial: Device serial number
        package: Package name to get information for
        ctx: Context for logging and progress

    Returns:
        A markdown-formatted representation of the app information
    """
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            return f"Error: Device {serial} not found."

        # Get app info
        await ctx.info(f"Retrieving app info for {package} on device {serial}...")
        app_info = await device.get_app_info(package)

        if "error" in app_info:
            return f"Error: {app_info['error']}"

        # Format the output
        result = f"# App Information for {package}\n\n"

        if "version" in app_info:
            result += f"- **Version**: {app_info['version']}\n"
        if "install_path" in app_info:
            result += f"- **Install Path**: {app_info['install_path']}\n"
        if "first_install" in app_info:
            result += f"- **First Install**: {app_info['first_install']}\n"
        if "user_id" in app_info:
            result += f"- **User ID**: {app_info['user_id']}\n"

        # Get the app size
        if "install_path" in app_info:
            cmd = f"du -sh {app_info['install_path']}"
            size_output = await device.run_shell(cmd)
            if size_output and "No such file" not in size_output:
                size = size_output.split()[0]
                result += f"- **App Size**: {size}\n"

        # Check if app is running
        cmd = f"ps -A | grep {package}"
        process_output = await device.run_shell(cmd)
        if process_output:
            result += "- **Status**: Running\n"
        else:
            result += "- **Status**: Not running\n"

        # Add permissions section if available
        if "permissions" in app_info:
            result += "\n## Permissions\n\n"
            permissions = app_info["permissions"].split(", ")
            for perm in permissions:
                result += f"- {perm}\n"

        return result

    except Exception as e:
        logger.exception("Error retrieving app info: %s", e)
        return f"Error retrieving app info: {e!s}"


@mcp.tool(name="android-app")
async def app_operations(
    serial: str,
    action: AppAction,
    ctx: Context,
    package: str | None = None,  # Required for most actions
    apk_path: str | None = None,  # For install_app
    reinstall: bool = False,  # For install_app
    grant_permissions: bool = True,  # For install_app
    keep_data: bool = False,  # For uninstall_app
    activity: str = "",  # For start_app
    include_system_apps: bool = False,  # For list_packages
) -> str:
    """
    Perform various application management operations on an Android device.

    This single tool consolidates various app-related actions.
    The 'action' parameter determines the operation.

    Args:
        serial: Device serial number.
        action: The specific app operation to perform.
        ctx: MCP Context for logging and interaction.
        package (Optional[str]): Package name for the target application. Required by most actions.
        apk_path (Optional[str]): Path to the APK file (local to the server). Used by `install_app`.
        reinstall (Optional[bool]): Whether to reinstall if app exists. Used by `install_app`.
        grant_permissions (Optional[bool]): Whether to grant all requested permissions. Used by `install_app`.
        keep_data (Optional[bool]): Whether to keep app data and cache directories. Used by `uninstall_app`.
        activity (Optional[str]): Optional activity name to start. Used by `start_app`.
        include_system_apps (Optional[bool]): Whether to include system apps. Used by `list_packages`.

    Returns:
        A string message indicating the result or status of the operation.

    ---
    Available Actions and their specific argument usage:

    1.  `action="install_app"`
        - Requires: `apk_path`
        - Optional: `reinstall`, `grant_permissions`
    2.  `action="uninstall_app"`
        - Requires: `package`
        - Optional: `keep_data`
    3.  `action="start_app"`
        - Requires: `package`
        - Optional: `activity`
    4.  `action="stop_app"`
        - Requires: `package`
    5.  `action="clear_app_data"`
        - Requires: `package`
    6.  `action="list_packages"`
        - Optional: `include_system_apps`
    7.  `action="get_app_manifest"`
        - Requires: `package`
    8.  `action="get_app_permissions"`
        - Requires: `package`
    9.  `action="get_app_activities"`
        - Requires: `package`
    10. `action="get_app_info"`
        - Requires: `package`
    ---
    """
    try:
        # Basic argument checks
        if (
            action
            in [
                AppAction.UNINSTALL_APP,
                AppAction.START_APP,
                AppAction.STOP_APP,
                AppAction.CLEAR_APP_DATA,
                AppAction.GET_APP_MANIFEST,
                AppAction.GET_APP_PERMISSIONS,
                AppAction.GET_APP_ACTIVITIES,
                AppAction.GET_APP_INFO,
            ]
            and package is None
        ):
            return f"❌ Error: 'package' is required for action '{action.value}'."

        if action == AppAction.INSTALL_APP and apk_path is None:
            return "❌ Error: 'apk_path' is required for action 'install_app'."

        # Dispatch to implementations
        if action == AppAction.INSTALL_APP:
            # We already checked apk_path is not None
            return await _install_app_impl(serial, apk_path, ctx, reinstall, grant_permissions)  # type: ignore
        if action == AppAction.UNINSTALL_APP:
            return await _uninstall_app_impl(serial, package, ctx, keep_data)  # type: ignore
        if action == AppAction.START_APP:
            return await _start_app_impl(serial, package, ctx, activity)  # type: ignore
        if action == AppAction.STOP_APP:
            return await _stop_app_impl(serial, package, ctx)  # type: ignore
        if action == AppAction.CLEAR_APP_DATA:
            return await _clear_app_data_impl(serial, package, ctx)  # type: ignore
        if action == AppAction.LIST_PACKAGES:
            return await _list_packages_impl(serial, ctx, include_system_apps)
        if action == AppAction.GET_APP_MANIFEST:
            return await _get_app_manifest_impl(serial, package, ctx)  # type: ignore
        if action == AppAction.GET_APP_PERMISSIONS:
            return await _get_app_permissions_impl(serial, package, ctx)  # type: ignore
        if action == AppAction.GET_APP_ACTIVITIES:
            return await _get_app_activities_impl(serial, package, ctx)  # type: ignore
        if action == AppAction.GET_APP_INFO:
            return await _get_app_info_impl(serial, package, ctx)  # type: ignore

        # Should not be reached if AppAction enum is comprehensive
        valid_actions = ", ".join([act.value for act in AppAction])
        logger.error("Invalid app action '%s' received. Valid actions are: %s", action, valid_actions)
        return f"❌ Error: Unknown app action '{action}'. Valid actions are: {valid_actions}."

    except Exception as e:
        logger.exception(
            "Unexpected error during app operation %s on %s for package '%s': %s", action, serial, package, e
        )
        return f"❌ Error: An unexpected error occurred during '{action.value}': {e!s}"

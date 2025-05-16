"""
Diagnostic Tools - MCP tools for debugging Android devices.

This module provides MCP tools for capturing bug reports and memory dumps from Android devices.
"""

import asyncio
from enum import Enum
import os
import tempfile

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import Device, get_device_manager
from droidmind.log import logger
from droidmind.security import RiskLevel, log_command_execution


class DiagAction(Enum):
    """Actions available for diagnostic operations."""

    CAPTURE_BUGREPORT = "capture_bugreport"
    DUMP_HEAP = "dump_heap"


async def _analyze_temp_bugreport(serial: str, ctx: Context, actual_output_path: str, file_size_mb: float) -> str:
    """Analyzes a temporary bug report file and returns a summary."""
    await ctx.info("Analyzing bug report contents (summary)...")
    # Using a raw string for the unzip command pattern to avoid issues with backslashes
    zip_list_cmd = f'unzip -l "{actual_output_path}"'
    proc = await asyncio.create_subprocess_shell(
        zip_list_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    zip_stdout, zip_stderr = await proc.communicate()

    if proc.returncode != 0:
        await ctx.warning(f"Could not list contents of temporary bugreport zip: {zip_stderr.decode().strip()}")
        zip_contents_summary = "(Could not retrieve zip contents)"
    else:
        zip_contents_summary = zip_stdout.decode().strip()

    summary = [
        f"# Bug Report for {serial}",
        f"Bug report ({file_size_mb:.2f} MB) was processed from a temporary location.",
        f"Original temporary path: `{actual_output_path}`",
        "",
        "## Bug Report Contents (Summary)",
        "```",
        zip_contents_summary[:2000] + ("..." if len(zip_contents_summary) > 2000 else ""),
        "```",
        "",
        "Note: The temporary file has been cleaned up. If you need to keep the bug report, specify an 'output_path'.",
    ]
    return "\\n".join(summary)


async def _execute_bugreport_core(
    device: Device,
    serial: str,
    ctx: Context,
    bugreport_cmd_arg: str,
    actual_output_path: str,
    timeout_seconds: int,
    is_temporary: bool,
) -> str:
    """Core logic for executing adb bugreport, handling results, and optionally summarizing."""
    await ctx.info(f"Running command: adb -s {serial} {bugreport_cmd_arg} {actual_output_path}")
    process = None  # Define process to ensure it's available in except block
    try:
        process = await asyncio.create_subprocess_exec(
            "adb",
            "-s",
            serial,
            bugreport_cmd_arg,
            actual_output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
        stderr_str = stderr.decode().strip() if stderr else ""

        if process.returncode != 0:
            await ctx.error(f"Bug report failed with exit code {process.returncode}")
            await ctx.error(f"Error: {stderr_str}")
            return f"Failed to capture bug report: {stderr_str}"

        if not os.path.exists(actual_output_path):
            await ctx.error("Bug report file was not created")
            return "Failed to capture bug report: No output file was created."

        file_size = os.path.getsize(actual_output_path)
        file_size_mb = file_size / (1024 * 1024)
        await ctx.info(f"✅ Bug report captured successfully! File size: {file_size_mb:.2f} MB")

        if not is_temporary:
            return f"Bug report saved to: {actual_output_path} ({file_size_mb:.2f} MB)"

        # Analyze and summarize the temporary bug report
        return await _analyze_temp_bugreport(serial, ctx, actual_output_path, file_size_mb)

    except TimeoutError:
        if process and process.returncode is None:  # Process is still running
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5)
            except TimeoutError:
                process.kill()
            except ProcessLookupError:  # pragma: no cover
                pass  # Process already ended
            except Exception:  # pragma: no cover
                logger.exception("Error terminating bugreport process during timeout.")
        await ctx.error(f"Bug report timed out after {timeout_seconds} seconds")
        return f"Bug report capture timed out after {timeout_seconds} seconds. Try again with a longer timeout value."


async def _execute_bugreport_temp(
    device: Device, serial: str, ctx: Context, bugreport_cmd_arg: str, timeout_seconds: int
) -> str:
    """Handles bug report capture to a temporary directory and summarizes."""
    timestamp = (await device.run_shell("date +%Y%m%d_%H%M%S")).strip()
    with tempfile.TemporaryDirectory(prefix="droidmind_bugreport_") as temp_dir_name:
        filename = f"bugreport_{serial}_{timestamp}.zip"
        actual_output_path = os.path.join(temp_dir_name, filename)
        await ctx.info(
            f"No output path specified; bug report will be summarized from temporary file: {actual_output_path}"
        )

        return await _execute_bugreport_core(
            device, serial, ctx, bugreport_cmd_arg, actual_output_path, timeout_seconds, is_temporary=True
        )
        # temp_dir_name is cleaned up automatically by 'with' statement


async def _capture_bugreport_impl(
    serial: str, ctx: Context, output_path: str = "", include_screenshots: bool = True, timeout_seconds: int = 300
) -> str:
    """Implementation for capturing a bug report from a device."""
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return f"Error: Device {serial} not found."

        log_command_execution("capture_bugreport", RiskLevel.MEDIUM)

        await ctx.info(f"🔍 Capturing bug report from device {serial}...")
        await ctx.info("This may take a few minutes depending on the device's state.")

        if include_screenshots:
            await ctx.info("Including screenshots in the bug report.")
            bugreport_cmd_arg = "bugreport"
        else:
            await ctx.info("Excluding screenshots to reduce bug report size.")
            bugreport_cmd_arg = "bugreportz"

        if not output_path:
            # Scenario: Temporary file. This will use 'with' inside the helper.
            return await _execute_bugreport_temp(device, serial, ctx, bugreport_cmd_arg, timeout_seconds)

        # Scenario: User-specified file.
        # Ensure the output directory exists if a path is provided
        abs_output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_output_path), exist_ok=True)
        return await _execute_bugreport_core(
            device, serial, ctx, bugreport_cmd_arg, abs_output_path, timeout_seconds, is_temporary=False
        )

    except Exception as e:
        logger.exception("Error capturing bug report: %s", e)
        await ctx.error(f"Error capturing bug report: {e}")
        return f"Error: {e}"


async def _resolve_pid(device: Device, ctx: Context, package_or_pid: str) -> str:
    """
    Resolve a package name to a process ID.

    Args:
        device: The device to query
        ctx: MCP context for sending messages
        package_or_pid: Package name or process ID

    Returns:
        The process ID as a string or empty string if not found.
    """
    if package_or_pid.isdigit():
        # Validate if it's an active PID, otherwise it might be an app named like a number
        ps_check_cmd = f"ps -p {package_or_pid} -o pid="
        pid_exists_result = await device.run_shell(ps_check_cmd)
        if pid_exists_result.strip() == package_or_pid:
            return package_or_pid
        # If not an active PID, treat it as a potential package name

    # It's a package name, get its PID
    await ctx.info(f"🔍 Looking up process ID for package '{package_or_pid}'...")

    # Using ps -ef | grep might be more reliable or provide more context than pidof
    # Example: ps -ef | grep com.example.app | grep -v grep
    # Then parse the PID from the output
    # However, pidof is simpler if available and works

    pid_cmd = f"pidof {package_or_pid}"

    pid_result = await device.run_shell(pid_cmd)
    pids = pid_result.strip().split()

    if not pids:  # If pidof fails or returns nothing
        # Fallback to 'ps' command
        # Using a more robust ps command to avoid grabbing grep itself
        # and to ensure we match the full package name at the end of the line.
        ps_cmd = f"ps -A -o PID,CMD | grep '[[:space:]]{package_or_pid}$'"

        ps_result = await device.run_shell(ps_cmd)
        ps_lines = ps_result.strip().split("\\n")

        if not ps_result.strip() or not ps_lines:
            await ctx.error(f"Cannot find process ID for package '{package_or_pid}'. Is the app running?")
            return ""

        # Extract PID from the first matching line of ps output
        # Typical format from `ps -A -o PID,CMD`: "  1234 com.example.app"
        first_match = ps_lines[0].strip()
        parts = first_match.split(None, 1)  # Split only on the first whitespace
        if len(parts) < 2 or not parts[0].isdigit():
            await ctx.error(f"Unexpected ps output format when searching for PID: '{first_match}'")
            return ""
        pid = parts[0]

    elif len(pids) > 1:
        await ctx.warning(f"Package '{package_or_pid}' has multiple PIDs: {pids}. Using the first one: {pids[0]}.")
        pid = pids[0]
    else:  # Exactly one PID found
        pid = pids[0]

    if not pid.isdigit():  # Final sanity check
        await ctx.error(f"Failed to resolve a valid PID for '{package_or_pid}'. Found: '{pid}'")
        return ""

    await ctx.info(f"Found process ID: {pid} for package '{package_or_pid}'.")
    return pid


async def _generate_heap_dump_paths(
    device: Device,
    app_name_or_pid: str,
    dump_type: str,
    user_output_path: str,
    ctx: Context,
) -> tuple[str, str, tempfile.TemporaryDirectory | None]:
    """
    Generate paths for heap dumps on device and local machine.

    Args:
        device: The device to query
        app_name_or_pid: Application name or PID string for filename
        dump_type: Type of heap dump ('java' or 'native')
        user_output_path: User-specified output path (can be empty)
        ctx: MCP context for sending messages

    Returns:
        Tuple of (device_path, local_host_path, temp_dir_obj)
    """
    timestamp = (await device.run_shell("date +%Y%m%d_%H%M%S")).strip()

    # Sanitize app_name_or_pid for use in filename
    safe_app_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in app_name_or_pid)

    filename_base = f"{safe_app_name}_{dump_type}_heap_{timestamp}"
    device_dump_filename = f"{filename_base}.hprof"  # Standard extension for heap dumps
    device_dump_path = f"/data/local/tmp/{device_dump_filename}"

    actual_local_host_path = user_output_path
    temp_dir_obj = None

    if not actual_local_host_path:
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="droidmind_heapdump_")
        actual_local_host_path = os.path.join(temp_dir_obj.name, device_dump_filename)
        await ctx.info(f"No output path specified, saving to temporary file: {actual_local_host_path}")
    else:
        # If user provided a directory, append our filename. If a file, use it.
        if os.path.isdir(actual_local_host_path):
            actual_local_host_path = os.path.join(actual_local_host_path, device_dump_filename)
        os.makedirs(os.path.dirname(os.path.abspath(actual_local_host_path)), exist_ok=True)

    # Return temp_dir_obj as well so it can be cleaned up if created
    return device_dump_path, actual_local_host_path, temp_dir_obj


async def _dump_heap_impl(
    serial: str,
    ctx: Context,
    package_or_pid: str,
    output_path: str = "",
    native: bool = False,
    timeout_seconds: int = 120,
) -> str:
    """Implementation for capturing a heap dump from a running process on the device."""
    temp_dir_for_local_dump = None
    try:
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return f"Error: Device {serial} not found."

        log_command_execution("dump_heap", RiskLevel.MEDIUM)

        pid = await _resolve_pid(device, ctx, package_or_pid)
        if not pid:
            return f"Error: Cannot find process for '{package_or_pid}'. Make sure the app is running."

        app_name_for_file = package_or_pid if not package_or_pid.isdigit() else f"pid_{pid}"
        dump_type = "native" if native else "java"

        device_dump_path, local_final_path, temp_dir_for_local_dump = await _generate_heap_dump_paths(
            device, app_name_for_file, dump_type, output_path, ctx
        )

        await ctx.info(f"📊 Capturing {dump_type} heap dump for process {pid} ({package_or_pid})...")
        await ctx.info(f"Device path: {device_dump_path}, Local path: {local_final_path}")
        await ctx.info("This may take some time depending on the process size.")

        dump_cmd = f"am dumpheap {'-n ' if native else ''}{pid} {device_dump_path}"

        if native:
            is_root = "root" in (await device.run_shell("whoami")).lower()
            if not is_root:
                await ctx.warning(
                    "Native heap dumps often require root access. The command will be attempted, "
                    "but may fail if root is not available or if SELinux policies prevent it."
                )

        await ctx.info(f"Executing heap dump command on device: {dump_cmd}")
        try:
            # Execute the heap dump command
            dump_stdout = await asyncio.wait_for(device.run_shell(dump_cmd), timeout=timeout_seconds + 5)

            # Check if dump file was created on device
            # 'ls -d' checks existence of specific file/dir, returns itself if exists
            file_check_cmd = f"ls -d {device_dump_path}"
            file_check_result = await device.run_shell(file_check_cmd)

            if device_dump_path not in file_check_result:
                await ctx.error(f"Heap dump file was not created on device at {device_dump_path}.")
                await ctx.info(f"Output from dump command: {dump_stdout}")
                return f"Failed to create heap dump on device. ADB command output: {dump_stdout or '(no output)'}"

            # Get file size (optional, for info)
            size_check_cmd = f"ls -l {device_dump_path} | awk '{{print $5}}'"
            file_size_str = (await device.run_shell(size_check_cmd)).strip()
            if file_size_str.isdigit():
                file_size_mb = int(file_size_str) / (1024 * 1024)
                await ctx.info(f"Heap dump created on device: {device_dump_path} ({file_size_mb:.2f} MB).")
            else:
                await ctx.info(f"Heap dump created on device: {device_dump_path} (size unknown).")

            await ctx.info(f"Pulling heap dump from {device_dump_path} to {local_final_path}...")
            pull_success = await device.pull_file(device_dump_path, local_final_path)

            if not pull_success or not os.path.exists(local_final_path):
                await ctx.error(f"Failed to pull heap dump from device to {local_final_path}.")
                return f"Failed to retrieve heap dump from device path {device_dump_path}."

            local_size_mb = os.path.getsize(local_final_path) / (1024 * 1024)
            await ctx.info(
                f"✅ Heap dump captured successfully to {local_final_path}! File size: {local_size_mb:.2f} MB"
            )

            result_message_parts = [
                f"{'Native' if native else 'Java'} heap dump saved to: `{local_final_path}` ({local_size_mb:.2f} MB)",
                "",
                "To analyze this heap dump:",
            ]
            if native:
                result_message_parts.extend(
                    [
                        "1. Use Android Studio Memory Profiler (File > Open).",
                        "2. Or use `pprof` (common for native C++ dumps) or Google's `heapprof` tools.",
                    ]
                )
            else:
                result_message_parts.extend(
                    [
                        (
                            f'1. Convert using `hprof-conv "{local_final_path}" '
                            f'"converted_{os.path.basename(local_final_path)}"`.'
                        ),
                        "2. Open the converted file in Android Studio Memory Profiler or Eclipse MAT.",
                    ]
                )
            return "\\n".join(result_message_parts)

        except TimeoutError:
            await ctx.error(f"Heap dump command timed out after {timeout_seconds} seconds on device.")
            return (
                f"Heap dump capture timed out after {timeout_seconds} seconds during device-side operation. "
                "Try with a longer timeout or ensure the app is stable."
            )
        finally:
            # Clean up the file on the device regardless of pull success to free space
            if device_dump_path and await device.file_exists(device_dump_path):
                await ctx.info(f"Cleaning up temporary file from device: {device_dump_path}")
                await device.run_shell(f"rm {device_dump_path}")
            if temp_dir_for_local_dump:
                temp_dir_for_local_dump.cleanup()

    except Exception as e:
        logger.exception("Error dumping heap: %s", e)
        await ctx.error(f"Error dumping heap: {e!s}")
        if temp_dir_for_local_dump:
            temp_dir_for_local_dump.cleanup()
        return f"Error: {e!s}"


@mcp.tool(name="android-diag")
async def android_diag(
    ctx: Context,
    serial: str,
    action: DiagAction,
    output_path: str = "",
    include_screenshots: bool = True,
    package_or_pid: str | None = None,
    native: bool = False,
    timeout_seconds: int = 0,
) -> str:
    """
    Perform diagnostic operations like capturing bug reports or heap dumps.

    Args:
        ctx: MCP Context.
        serial: Device serial number.
        action: The diagnostic action to perform.
        output_path: Optional. Path to save the output file.
                     For bugreport: host path for adb to write the .zip. If empty, a temp file is used & summarized.
                     For dump_heap: local path to save the .hprof. If empty, a temp file is used.
        include_screenshots: For CAPTURE_BUGREPORT. Default True.
        package_or_pid: For DUMP_HEAP. App package name or process ID.
        native: For DUMP_HEAP. True for native (C/C++) heap, False for Java. Default False.
        timeout_seconds: Max time for the operation. If 0, action-specific defaults are used
                         (bugreport: 300s, dump_heap: 120s).

    Returns:
        A string message indicating the result or path to the output.
    """
    if action == DiagAction.CAPTURE_BUGREPORT:
        final_timeout = timeout_seconds if timeout_seconds > 0 else 300
        return await _capture_bugreport_impl(
            serial=serial,
            ctx=ctx,
            output_path=output_path,
            include_screenshots=include_screenshots,
            timeout_seconds=final_timeout,
        )
    if action == DiagAction.DUMP_HEAP:
        if not package_or_pid:
            msg = "Error: 'package_or_pid' is required for dump_heap action."
            await ctx.error(msg)
            return msg
        final_timeout = timeout_seconds if timeout_seconds > 0 else 120
        return await _dump_heap_impl(
            serial=serial,
            ctx=ctx,
            package_or_pid=package_or_pid,
            output_path=output_path,
            native=native,
            timeout_seconds=final_timeout,
        )

    # Should not be reached
    unhandled_action_msg = f"Error: Unhandled diagnostic action '{action}'."
    logger.error(unhandled_action_msg)
    await ctx.error(unhandled_action_msg)
    return unhandled_action_msg

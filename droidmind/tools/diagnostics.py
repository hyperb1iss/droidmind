"""
Diagnostic Tools - MCP tools for debugging Android devices.

This module provides MCP tools for capturing bug reports and memory dumps from Android devices.
"""

import asyncio
import os
import tempfile

from mcp.server.fastmcp import Context

from droidmind.context import mcp
from droidmind.devices import Device, get_device_manager
from droidmind.log import logger
from droidmind.security import RiskLevel, log_command_execution


@mcp.tool()
async def capture_bugreport(
    serial: str, ctx: Context, output_path: str = "", include_screenshots: bool = True, timeout_seconds: int = 300
) -> str:
    """
    Capture a bug report from a device.

    Bug reports are comprehensive diagnostic information packages that include
    system logs, device state, running processes, and more.

    Args:
        serial: Device serial number
        ctx: MCP context
        output_path: Where to save the bug report (leave empty to return as text)
        include_screenshots: Whether to include screenshots in the report
        timeout_seconds: Maximum time to wait for the bug report to complete (in seconds)

    Returns:
        Path to the saved bug report or a summary of the report contents
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return f"Error: Device {serial} not found."

        # Log the operation with medium risk level
        log_command_execution("capture_bugreport", RiskLevel.MEDIUM)

        # Inform the user
        await ctx.info(f"🔍 Capturing bug report from device {serial}...")
        await ctx.info("This may take a few minutes depending on the device's state.")

        if include_screenshots:
            await ctx.info("Including screenshots in the bug report.")
            bugreport_cmd = "bugreport"
        else:
            await ctx.info("Excluding screenshots to reduce bug report size.")
            bugreport_cmd = "bugreport -b"

        # Create a temporary directory if no output path is specified
        temp_dir = None
        if not output_path:
            temp_dir = tempfile.mkdtemp(prefix="droidmind_bugreport_")
            output_path = os.path.join(temp_dir, f"bugreport_{serial}.zip")
            await ctx.info(f"No output path specified, saving to temporary file: {output_path}")

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Run the bugreport command and save to the specified path
        cmd = f"bugreport {output_path}"
        await ctx.info(f"Running command: adb -s {serial} {cmd}")

        # Execute the adb bugreport command directly
        process = await asyncio.create_subprocess_exec(
            "adb",
            "-s",
            serial,
            bugreport_cmd,
            output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Set up a timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
            # We only need stderr for error messages
            stderr_str = stderr.decode().strip() if stderr else ""

            if process.returncode != 0:
                await ctx.error(f"Bug report failed with exit code {process.returncode}")
                await ctx.error(f"Error: {stderr_str}")
                return f"Failed to capture bug report: {stderr_str}"

            # Check if the file was created
            if not os.path.exists(output_path):
                await ctx.error("Bug report file was not created")
                return "Failed to capture bug report: No output file was created."

            # Get file size
            file_size = os.path.getsize(output_path)
            file_size_mb = file_size / (1024 * 1024)
            await ctx.info(f"✅ Bug report captured successfully! File size: {file_size_mb:.2f} MB")

            # If the user specified an output path, return the path
            if not temp_dir:
                return f"Bug report saved to: {output_path} ({file_size_mb:.2f} MB)"

            # If we created a temp file, analyze the bug report and return a summary
            await ctx.info("Analyzing bug report contents...")
            # Analyze zip file contents to return a summary
            zip_list_cmd = f"unzip -l {output_path}"
            proc = await asyncio.create_subprocess_shell(
                zip_list_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            zip_stdout, zip_stderr = await proc.communicate()
            zip_contents = zip_stdout.decode().strip()

            # Format a summary response
            summary = [
                f"# Bug Report for {serial}",
                f"Temporary file saved to: `{output_path}` ({file_size_mb:.2f} MB)",
                "",
                "## Bug Report Contents",
                "```",
                zip_contents[:2000] + ("..." if len(zip_contents) > 2000 else ""),
                "```",
                "",
                "To extract specific information from this bug report, you can use:",
                f"* `unzip -o {output_path} -d <extract_dir>` to extract all files",
                f"* `unzip -o {output_path} bugreport-*.txt -d <extract_dir>` to extract just the main report",
                "",
                "Note: This is a temporary file that may be cleaned up by the system later.",
            ]
            return "\n".join(summary)

        except TimeoutError:
            # Try to terminate the process if it's still running
            if process:
                process.terminate()
                await process.wait()
            await ctx.error(f"Bug report timed out after {timeout_seconds} seconds")
            return (
                f"Bug report capture timed out after {timeout_seconds} seconds. Try again with a longer timeout value."
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
        The process ID as a string
    """
    if package_or_pid.isdigit():
        return package_or_pid

    # It's a package name, get its PID
    await ctx.info(f"🔍 Looking up process ID for package {package_or_pid}...")
    pid_cmd = f"pidof {package_or_pid}"
    pid_result = await device.run_shell(pid_cmd)

    if not pid_result.strip():
        # Try ps approach if pidof fails
        ps_cmd = f"ps -A | grep {package_or_pid}"
        ps_result = await device.run_shell(ps_cmd)

        if not ps_result.strip():
            await ctx.error(f"Cannot find process ID for package {package_or_pid}. Is the app running?")
            return ""

        # Try to extract PID from ps output
        # Typical format: USER PID PPID VSIZE RSS WCHAN PC NAME
        parts = ps_result.strip().split()
        if len(parts) < 2:
            await ctx.error(f"Unexpected ps output format: {ps_result}")
            return ""
        pid = parts[1]
    else:
        parts = pid_result.strip().split()
        if not parts:
            await ctx.error(f"Unexpected pidof output format: {pid_result}")
            return ""
        pid = parts[0]  # Take the first PID if multiple are returned

    await ctx.info(f"Found process ID: {pid}")
    return pid


async def _generate_heap_dump_paths(
    device: Device,
    app_name: str,
    dump_type: str,
    output_path: str,
    ctx: Context,
) -> tuple[str, str]:
    """
    Generate paths for heap dumps on device and local machine.

    Args:
        device: The device to query
        app_name: Application name or PID
        dump_type: Type of heap dump (java or native)
        output_path: User-specified output path or empty string
        ctx: MCP context for sending messages

    Returns:
        Tuple of (device_path, local_path)
    """
    # Create a timestamp for the filename
    timestamp = await device.run_shell("date +%Y%m%d_%H%M%S")
    timestamp = timestamp.strip()

    # Set default output path if not provided
    if not output_path:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="droidmind_heapdump_")
        filename = f"{app_name}_{dump_type}_heap_{timestamp}.hprof"
        output_path = os.path.join(temp_dir, filename)
        await ctx.info(f"No output path specified, saving to temporary file: {output_path}")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Determine the device-side dump path
    device_dump_path = f"/data/local/tmp/{app_name}_{dump_type}_heap_{timestamp}.hprof"

    return device_dump_path, output_path


@mcp.tool()
async def dump_heap(
    serial: str,
    ctx: Context,
    package_or_pid: str,
    output_path: str = "",
    native: bool = False,
    timeout_seconds: int = 120,
) -> str:
    """
    Capture a heap dump from a running process on the device.

    Heap dumps are useful for diagnosing memory issues, leaks, and understanding
    object relationships in running applications.

    Args:
        serial: Device serial number
        ctx: MCP context
        package_or_pid: App package name or process ID to dump
        output_path: Where to save the heap dump (leave empty for default location)
        native: Whether to capture a native heap dump (vs Java heap)
        timeout_seconds: Maximum time to wait for the heap dump to complete (in seconds)

    Returns:
        Path to the saved heap dump or an error message
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return f"Error: Device {serial} not found."

        # Log the operation with medium risk level
        log_command_execution("dump_heap", RiskLevel.MEDIUM)

        # Resolve PID if a package name was provided
        pid = await _resolve_pid(device, ctx, package_or_pid)
        if not pid:
            return f"Error: Cannot find process for {package_or_pid}. Make sure the app is running."

        # Determine app name for file naming
        app_name = package_or_pid if not package_or_pid.isdigit() else f"pid_{pid}"
        dump_type = "native" if native else "java"

        # Generate paths for the heap dump
        device_dump_path, output_path = await _generate_heap_dump_paths(
            device, app_name, dump_type, output_path, ctx
        )

        # Inform the user
        await ctx.info(f"📊 Capturing {dump_type} heap dump for process {pid}...")
        await ctx.info("This may take some time depending on the process size.")

        # Choose the appropriate heap dump command
        if native:
            # Native heap dump using am dumpheap (requires root on most devices)
            dump_cmd = f"am dumpheap -n {pid} {device_dump_path}"
            is_root_required = True
        else:
            # Java heap dump
            dump_cmd = f"am dumpheap {pid} {device_dump_path}"
            is_root_required = False

        # Check for root if needed
        if is_root_required:
            root_test = await device.run_shell("whoami")
            if "root" not in root_test:
                await ctx.warning("Native heap dumps typically require root access.")
                # We'll still try the command but warn the user

        # Execute the heap dump
        await ctx.info(f"Running command: {dump_cmd}")
        try:
            result = await asyncio.wait_for(device.run_shell(dump_cmd), timeout=timeout_seconds)

            # Check if dump succeeded
            file_check = await device.run_shell(f"ls -la {device_dump_path}")
            if "No such file" in file_check:
                await ctx.error("Heap dump file was not created on the device")
                return f"Failed to create heap dump. Command output: {result}"

            # Get file size
            size_parts = file_check.split()
            try:
                # Expected format: "-rw-r--r-- 1 shell shell 12345678 YYYY-MM-DD HH:MM filename"
                file_size = int(size_parts[4]) if len(size_parts) >= 5 else 0
                file_size_mb = file_size / (1024 * 1024)
                await ctx.info(f"Heap dump created on device: {device_dump_path} ({file_size_mb:.2f} MB)")
            except (IndexError, ValueError):
                await ctx.info(f"Heap dump created on device, size unknown: {device_dump_path}")

            # Pull the file from the device
            await ctx.info(f"Pulling heap dump from device to {output_path}...")
            pull_result = await device.pull_file(device_dump_path, output_path)

            # Clean up the file on the device
            await ctx.info("Cleaning up temporary file from device...")
            await device.run_shell(f"rm {device_dump_path}")

            # Verify the local file exists
            if not os.path.exists(output_path):
                await ctx.error("Failed to pull heap dump from device to local machine")
                return f"Failed to retrieve heap dump: {pull_result}"

            # Report success
            local_size = os.path.getsize(output_path)
            local_size_mb = local_size / (1024 * 1024)

            await ctx.info(f"✅ Heap dump captured successfully! File size: {local_size_mb:.2f} MB")

            # Return the path and usage instructions
            if native:
                # Native heap instructions
                return (
                    f"Native heap dump saved to: {output_path} ({local_size_mb:.2f} MB)\n\n"
                    "To analyze this native heap dump:\n"
                    "1. Use the Android Studio Memory Profiler\n"
                    "2. Or use 'heapanalyzer' from the Android SDK\n"
                    "3. For lower-level analysis, tools like 'hprof-conv' and MAT can be used"
                )

            # Java heap instructions
            return (
                f"Java heap dump saved to: {output_path} ({local_size_mb:.2f} MB)\n\n"
                "To analyze this Java heap dump:\n"
                "1. Convert the file using: `hprof-conv {output_path} converted.hprof`\n"
                "2. Open in Android Studio's Memory Profiler\n"
                "3. Or use Eclipse Memory Analyzer (MAT) after conversion\n"
                "4. For CLI analysis: `python -m objgraph {output_path}`"
            )

        except TimeoutError:
            await ctx.error(f"Heap dump timed out after {timeout_seconds} seconds")
            return (
                f"Heap dump capture timed out after {timeout_seconds} seconds. "
                "Try again with a longer timeout value or a smaller process."
            )

    except Exception as e:
        logger.exception("Error dumping heap: %s", e)
        await ctx.error(f"Error dumping heap: {e}")
        return f"Error: {e}"

# DroidMind MCP Tool Reference

Welcome to the DroidMind MCP Tool Reference. This section provides a quick overview of all the tools DroidMind exposes to your AI assistant via the Model Context Protocol (MCP).

Each tool is designed to perform a specific action on your connected Android devices. Your AI assistant intelligently chooses and combines these tools based on your natural language requests.

## 🛠️ Available Tools

Below is a categorized list of DroidMind tools. For detailed parameters, refer to the specific tool documentation (future enhancement) or explore them through an MCP-compatible client that can list tool schemas (like the MCP Inspector or potentially your AI assistant itself).

### Device Connection & Management

- **`list_devices`**: Lists all connected Android devices and their basic information.
- **`connect_device`**: Connects to an Android device over TCP/IP (Wi-Fi).
  - `ip_address`: IP address of the device.
  - `port` (optional): Port number (default 5555).
- **`disconnect_device`**: Disconnects from a specified Android device (primarily for TCP/IP connections).
  - `serial`: Device serial number.
- **`device_properties`**: Retrieves detailed system properties of a specific device.
  - `serial`: Device serial number.
- **`reboot_device`**: Reboots a device into normal, recovery, or bootloader mode.
  - `serial`: Device serial number.
  - `mode` (optional): `normal` (default), `recovery`, `bootloader`.

### Diagnostics & Logging

- **`device_logcat`**: Fetches general logcat output from a device.
  - `serial`: Device serial number.
  - `lines` (optional): Number of lines.
  - `filter_expr` (optional): Logcat filter.
  - `buffer` (optional): Logcat buffer (e.g., `main`, `crash`).
  - `format_type` (optional): Log output format.
  - `max_size` (optional): Maximum output character size.
- **`app_logs`**: Fetches logcat output filtered for a specific application.
  - `serial`: Device serial number.
  - `package`: Application package name.
  - `lines` (optional): Number of lines.
- **`device_anr_logs`**: Retrieves Application Not Responding (ANR) traces.
  - `serial`: Device serial number.
- **`device_crash_logs`**: Fetetches application crash reports (tombstones, dropbox, logcat crash buffer).
  - `serial`: Device serial number.
- **`device_battery_stats`**: Gets battery statistics and history.
  - `serial`: Device serial number.
- **`capture_bugreport`**: Captures a comprehensive bug report from the device.
  - `serial`: Device serial number.
  - `output_path` (optional): Local path to save the bug report zip.
  - `include_screenshots` (optional): Default `True`.
  - `timeout_seconds` (optional): Default `300`.
- **`dump_heap`**: Captures a Java or native heap dump from a running process.
  - `serial`: Device serial number.
  - `package_or_pid`: Application package name or process ID.
  - `output_path` (optional): Local path to save the heap dump.
  - `native` (optional): `False` for Java heap (default), `True` for native heap.
  - `timeout_seconds` (optional): Default `120`.

### File System Operations

- **`list_directory`**: Lists contents of a directory on the device.
  - `serial`: Device serial number.
  - `path`: Directory path on device.
- **`read_file`**: Reads the content of a text file from the device.
  - `serial`: Device serial number.
  - `device_path`: File path on device.
  - `max_size` (optional): Max characters to read (default 100KB).
- **`write_file`**: Writes text content to a file on the device.
  - `serial`: Device serial number.
  - `device_path`: File path on device.
  - `content`: Text content to write.
- **`push_file`**: Uploads a file from the DroidMind server's machine to the device.
  - `serial`: Device serial number.
  - `local_path`: Path on the DroidMind server machine.
  - `device_path`: Destination path on device.
- **`pull_file`**: Downloads a file from the device to the DroidMind server's machine.
  - `serial`: Device serial number.
  - `device_path`: File path on device.
  - `local_path`: Destination path on the DroidMind server machine.
- **`create_directory`**: Creates a directory on the device.
  - `serial`: Device serial number.
  - `path`: Directory path to create on device.
- **`delete_file`**: Deletes a file or directory (recursively) from the device.
  - `serial`: Device serial number.
  - `path`: File or directory path to delete on device.
- **`file_exists`**: Checks if a file or directory exists on the device.
  - `serial`: Device serial number.
  - `path`: Path to check on device.
- **`file_stats`**: Gets detailed statistics for a file or directory.
  - `serial`: Device serial number.
  - `path`: Path on device.

### Application Management

- **`list_packages`**: Lists installed application packages.
  - `serial`: Device serial number.
  - `include_system_apps` (optional): Default `False`.
- **`install_app`**: Installs an APK on the device.
  - `serial`: Device serial number.
  - `apk_path`: Local path to the APK on the DroidMind server machine.
  - `reinstall` (optional): Default `False`.
  - `grant_permissions` (optional): Default `True`.
- **`uninstall_app`**: Uninstalls an application from the device.
  - `serial`: Device serial number.
  - `package`: Package name to uninstall.
  - `keep_data` (optional): Default `False`.
- **`start_app`**: Starts an application.
  - `serial`: Device serial number.
  - `package`: Package name.
  - `activity` (optional): Specific activity to launch.
- **`stop_app`**: Force stops an application.
  - `serial`: Device serial number.
  - `package`: Package name.
- **`clear_app_data`**: Clears data and cache for an application.
  - `serial`: Device serial number.
  - `package`: Package name.
- **`get_app_info`**: Retrieves detailed information about an installed application.
  - `serial`: Device serial number.
  - `package`: Package name.
- **`get_app_manifest`**: Gets the AndroidManifest.xml contents for an app.
  - `serial`: Device serial number.
  - `package`: Package name.
- **`get_app_permissions`**: Gets permissions used by an app, including runtime status.
  - `serial`: Device serial number.
  - `package`: Package name.
- **`get_app_activities`**: Gets the activities defined in an app, including intent filters and main activity.
  - `serial`: Device serial number.
  - `package`: Package name.

### Shell Command Execution

- **`shell_command`**: Executes an arbitrary shell command on the device.
  - `serial`: Device serial number.
  - `command`: The shell command string.
  - `max_lines` (optional): Limit output lines.
  - `max_size` (optional): Limit output characters.

### UI Automation

- **`screenshot`**: Captures a screenshot from the device.
  - `serial`: Device serial number.
  - `quality` (optional): JPEG quality (1-100, default 75).
- **`tap`**: Simulates a tap at specified screen coordinates.
  - `serial`: Device serial number.
  - `x`, `y`: Coordinates to tap.
- **`swipe`**: Simulates a swipe gesture.
  - `serial`: Device serial number.
  - `start_x`, `start_y`, `end_x`, `end_y`: Swipe coordinates.
  - `duration_ms` (optional): Swipe duration (default 300ms).
- **`input_text`**: Inputs text into the currently focused field.
  - `serial`: Device serial number.
  - `text`: Text to input.
- **`press_key`**: Simulates pressing an Android keycode.
  - `serial`: Device serial number.
  - `keycode`: Android keycode (e.g., 3 for HOME, 4 for BACK).
- **`start_intent`**: Starts an app activity using an intent.
  - `serial`: Device serial number.
  - `package`: Package name.
  - `activity`: Activity name (relative or fully qualified).
  - `extras` (optional): Dictionary of intent extras.

This reference provides a quick lookup for the tools DroidMind offers. Your AI assistant will use these to fulfill your requests for interacting with your Android devices.

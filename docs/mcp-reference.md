# DroidMind MCP Tool Reference

Welcome to the DroidMind MCP Tool Reference. This section provides a quick overview of all the tools DroidMind exposes to your AI assistant via the Model Context Protocol (MCP).

Each tool is designed to perform a specific action on your connected Android devices. Your AI assistant intelligently chooses and combines these tools based on your natural language requests.

## 🛠️ Available Tools

Below is a categorized list of DroidMind tools. For detailed parameters, refer to the specific tool documentation (future enhancement) or explore them through an MCP-compatible client that can list tool schemas (like the MCP Inspector or potentially your AI assistant itself).

### Device Connection & Management

- **`android-device`**: Performs various device management operations on Android devices.
  - `action`: Specifies the operation. One of:
    - `list_devices`: Lists all connected Android devices and their basic information.
        - No specific arguments required beyond `ctx`.
    - `connect_device`: Connects to an Android device over TCP/IP (Wi-Fi).
        - Requires: `ip_address`.
        - Optional: `port` (default 5555).
    - `disconnect_device`: Disconnects from a specified Android device.
        - Requires: `serial`.
    - `device_properties`: Retrieves detailed system properties of a specific device.
        - Requires: `serial`.
    - `reboot_device`: Reboots a device into normal, recovery, or bootloader mode.
        - Requires: `serial`.
        - Optional: `mode` (default `normal`; e.g., `recovery`, `bootloader`).
  - `ctx`: MCP Context.
  - `serial` (optional): Device serial number. See specific `action` for usage.
  - `ip_address` (optional): IP address for `connect_device`.
  - `port` (optional): Port for `connect_device`.
  - `mode` (optional): Reboot mode for `reboot_device`.
  - **Note**: Refer to the tool's main Python docstring in `droidmind/tools/device_management.py` for the most detailed argument requirements for each `action`.

### Diagnostics & Logging

- **`android-diag`**: Performs diagnostic operations like capturing bug reports or heap dumps.
  - `serial`: Device serial number.
  - `action`: Specifies the diagnostic operation. One of:
    - `capture_bugreport`: Captures a comprehensive bug report from the device.
        - Optional: `output_path` (host path for adb to write .zip, temp if empty), `include_screenshots` (default `True`), `timeout_seconds` (default `300s`).
    - `dump_heap`: Captures a heap dump from a running process.
        - Requires: `package_or_pid` (app package name or process ID).
        - Optional: `output_path` (local path for .hprof, temp if empty), `native` (default `False` for Java heap), `timeout_seconds` (default `120s`).
  - `ctx`: MCP Context.
  - `output_path` (optional): Path for output file. See action specifics.
  - `include_screenshots` (optional): For `capture_bugreport`.
  - `package_or_pid` (optional): For `dump_heap`.
  - `native` (optional): For `dump_heap`.
  - `timeout_seconds` (optional): Override default timeouts. If 0, action-specific defaults are used.
  - **Note**: Refer to the tool's main Python docstring in `droidmind/tools/diagnostics.py` for detailed argument requirements.

- **`android-log`**: Performs various log retrieval operations on an Android device.
  - `serial`: Device serial number.
  - `action`: Specifies the operation. One of:
    - `get_device_logcat`: Fetches general logcat output from a device.
        - Optional: `lines`, `filter_expr`, `buffer`, `format_type`, `max_size`.
    - `get_app_logs`: Fetches logcat output filtered for a specific application.
        - Requires: `package`.
        - Optional: `lines`.
    - `get_anr_logs`: Retrieves Application Not Responding (ANR) traces.
        - No specific arguments beyond `serial` and `ctx`.
    - `get_crash_logs`: Fetches application crash reports.
        - No specific arguments beyond `serial` and `ctx`.
    - `get_battery_stats`: Gets battery statistics and history.
        - No specific arguments beyond `serial` and `ctx`.
  - `ctx`: MCP Context.
  - `package` (optional): Package name for `get_app_logs`.
  - `lines` (optional): Number of lines for logcat actions.
  - `filter_expr` (optional): Filter for `get_device_logcat`.
  - `buffer` (optional): Logcat buffer for `get_device_logcat`.
  - `format_type` (optional): Output format for `get_device_logcat`.
  - `max_size` (optional): Max output size for `get_device_logcat`.
  - **Note**: Refer to the tool's main Python docstring in `droidmind/tools/logs.py` for detailed argument requirements.

### File System Operations

- **`android-file`**: Performs a variety of file and directory operations on an Android device.
  - `serial`: Device serial number.
  - `action`: Specifies the operation. One of:
    - `list_directory`: Lists contents of a directory on the device.
        - Requires: `path` (directory path on device).
    - `push_file`: Uploads a file from the DroidMind server's machine to the device.
        - Requires: `local_path` (source on server), `device_path` (destination on device).
    - `pull_file`: Downloads a file from the device to the DroidMind server's machine.
        - Requires: `device_path` (source on device), `local_path` (destination on server).
    - `delete_file`: Deletes a file or directory.
        - Requires: `path` (path to delete on device).
    - `create_directory`: Creates a directory.
        - Requires: `path` (directory path to create on device).
    - `file_exists`: Checks if a file or directory exists.
        - Requires: `path` (path to check on device). Returns: `bool`.
    - `read_file`: Reads file content.
        - Requires: `device_path` (or `path`) for the file on device.
        - Optional: `max_size` (defaults to 100KB).
    - `write_file`: Writes content to a file.
        - Requires: `device_path` (or `path`) for the file on device, `content` (text to write).
    - `file_stats`: Gets file/directory statistics.
        - Requires: `path` (path on device).
  - `ctx`: MCP Context.
  - `path` (optional): General device path. See specific `action` for usage.
  - `local_path` (optional): Server-side path for `push_file`/`pull_file`.
  - `device_path` (optional): Device-side path. See specific `action` for usage. Takes precedence over `path` if both are provided for read/write.
  - `content` (optional): Text content for `write_file`.
  - `max_size` (optional): Max size for `read_file`.
  - **Note**: Refer to the tool's main Python docstring in `droidmind/tools/file_operations.py` for the most detailed argument requirements for each `action`.

### Application Management

- **`android-app`**: Performs various application management operations on an Android device.
  - `serial`: Device serial number.
  - `action`: Specifies the operation. One of:
    - `install_app`: Installs an APK on the device.
        - Requires: `apk_path` (local path to APK on DroidMind server).
        - Optional: `reinstall` (default `False`), `grant_permissions` (default `True`).
    - `uninstall_app`: Uninstalls an application from the device.
        - Requires: `package` (package name).
        - Optional: `keep_data` (default `False`).
    - `start_app`: Starts an application.
        - Requires: `package` (package name).
        - Optional: `activity` (specific activity to launch).
    - `stop_app`: Force stops an application.
        - Requires: `package` (package name).
    - `clear_app_data`: Clears data and cache for an application.
        - Requires: `package` (package name).
    - `list_packages`: Lists installed application packages.
        - Optional: `include_system_apps` (default `False`).
    - `get_app_manifest`: Gets the AndroidManifest.xml contents for an app.
        - Requires: `package` (package name).
    - `get_app_permissions`: Gets permissions used by an app, including runtime status.
        - Requires: `package` (package name).
    - `get_app_activities`: Gets the activities defined in an app, including intent filters and main activity.
        - Requires: `package` (package name).
    - `get_app_info`: Retrieves detailed information about an installed application.
        - Requires: `package` (package name).
  - `ctx`: MCP Context.
  - `package` (optional): Package name. See specific `action` for usage.
  - `apk_path` (optional): Local path to APK for `install_app`.
  - `reinstall` (optional): For `install_app`.
  - `grant_permissions` (optional): For `install_app`.
  - `keep_data` (optional): For `uninstall_app`.
  - `activity` (optional): Specific activity for `start_app`.
  - `include_system_apps` (optional): For `list_packages`.
  - **Note**: Refer to the tool's main Python docstring in `droidmind/tools/app_management.py` for the most detailed argument requirements for each `action`.

### Shell Command Execution

- **`android-shell`**: Executes an arbitrary shell command on the device.
  - `serial`: Device serial number.
  - `command`: The shell command string.
  - `max_lines` (optional): Limit output lines.
  - `max_size` (optional): Limit output characters.

### UI Automation

- **`android-ui`**: Performs various UI interaction operations on an Android device.
  - `serial`: Device serial number.
  - `action`: Specifies the UI operation. One of:
    - `tap`: Simulates a tap at specified screen coordinates.
        - Requires: `x`, `y` (coordinates to tap).
    - `swipe`: Simulates a swipe gesture.
        - Requires: `start_x`, `start_y`, `end_x`, `end_y` (swipe coordinates).
        - Optional: `duration_ms` (swipe duration, default 300ms).
    - `input_text`: Inputs text into the currently focused field.
        - Requires: `text` (text to input).
    - `press_key`: Simulates pressing an Android keycode.
        - Requires: `keycode` (Android keycode, e.g., 3 for HOME, 4 for BACK).
    - `start_intent`: Starts an app activity using an intent.
        - Requires: `package` (package name), `activity` (activity name, relative or fully qualified).
        - Optional: `extras` (dictionary of intent extras).
  - `ctx`: MCP Context.
  - `x` (optional): X coordinate for `tap`.
  - `y` (optional): Y coordinate for `tap`.
  - `start_x` (optional): Starting X for `swipe`.
  - `start_y` (optional): Starting Y for `swipe`.
  - `end_x` (optional): Ending X for `swipe`.
  - `end_y` (optional): Ending Y for `swipe`.
  - `duration_ms` (optional): Duration for `swipe`.
  - `text` (optional): Text for `input_text`.
  - `keycode` (optional): Keycode for `press_key`.
  - `package` (optional): Package name for `start_intent`.
  - `activity` (optional): Activity name for `start_intent`.
  - `extras` (optional): Dictionary for `start_intent`.
  - **Note**: Refer to the tool's main Python docstring in `droidmind/tools/ui.py` for the most detailed argument requirements for each `action`.

- **`android-screenshot`**: Captures a screenshot from the device.
  - `serial`: Device serial number.
  - `quality` (optional): JPEG quality (1-100, default 75).

This reference provides a quick lookup for the tools DroidMind offers. Your AI assistant will use these to fulfill your requests for interacting with your Android devices.

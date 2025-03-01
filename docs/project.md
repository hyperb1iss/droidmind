# Android MCP Server

<div align="center">

![Android MCP Server Logo](https://via.placeholder.com/150x150.png?text=Android+MCP)

**Connect AI assistants to Android devices for enhanced development workflows**

[![Model Context Protocol](https://img.shields.io/badge/MCP-Compatible-brightgreen.svg)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

## 📱 Overview

Android MCP Server bridges the gap between AI assistants and Android devices, enabling seamless integration of Android development workflows with AI-powered IDEs like Cursor. By leveraging the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), the server exposes Android Debug Bridge (ADB) capabilities, device diagnostics, file systems, and development tools through standardized interfaces.

**Key Benefits:**

- 🔍 **Enhanced Debugging** - Analyze logs, capture screenshots, and diagnose issues with AI assistance
- 🛠️ **Streamlined Development** - Access device features, install apps, and manage files without leaving your IDE
- 🔄 **ROM Development** - Flash images, manage partitions, and customize system components
- 📊 **System Analysis** - Monitor performance, analyze battery usage, and collect diagnostics

---

## 🎯 Real-World Use Cases

### App Developer Scenarios

#### 1. Crash Debugging

> **Scenario**: A developer is working on an Android app that crashes intermittently on certain devices.

**Without Android MCP Server:**

1. Developer manually connects to device
2. Runs the app and reproduces the crash
3. Opens terminal to run ADB commands
4. Captures logcat output
5. Copies logs back to IDE
6. Analyzes logs manually

**With Android MCP Server:**

1. Developer asks AI: "My app just crashed on the test device. What happened?"
2. Android MCP Server automatically:
   - Captures relevant logcat entries
   - Extracts stack trace
   - Provides AI with device properties and app state
3. AI analyzes the combined context and suggests fixes

```
User: My app just crashed when testing the checkout flow. Can you help diagnose the issue?

AI: I'll help you diagnose the crash. Let me check the logs and device information.

[AI uses Android MCP Server to retrieve logs]

I found the issue in your crash logs. The app crashed with a NullPointerException in PaymentProcessor.java:218.
The device is running Android 12 (SDK 31) on a Samsung Galaxy S21.

The crash occurred because you're trying to access the PaymentIntent object before it's initialized in the
checkout flow on devices running Android 12 or higher.

Here's the fix:
```

#### 2. UI Optimization

> **Scenario**: A developer needs to optimize their app's UI for various screen sizes and densities.

**Now possible with Android MCP Server:**

1. Developer asks: "How does my UI look on these different devices?"
2. Android MCP Server:
   - Captures screenshots from connected devices
   - Provides screen dimensions and density information
   - Collects layout hierarchy data
3. AI analyzes UI across devices and suggests improvements

### System Developer Scenarios

#### 1. Custom ROM Troubleshooting

> **Scenario**: A ROM developer is debugging a custom build that fails to boot properly.

**With Android MCP Server:**

1. Developer asks: "My custom ROM isn't booting. What's going wrong?"
2. Android MCP Server:
   - Pulls boot logs from the device in recovery mode
   - Retrieves last_kmsg or kernel logs
   - Collects partition information
3. AI analyzes the boot failure and suggests solutions

#### 2. Performance Optimization

> **Scenario**: A system developer needs to optimize battery life for a custom Android build.

**With Android MCP Server:**

1. Developer requests: "Analyze battery consumption on my device"
2. Android MCP Server:
   - Collects battery stats and wakelocks
   - Monitors system processes and resource usage
   - Identifies power-hungry services
3. AI provides actionable recommendations for optimization

---

## 🏗️ Architecture

The Android MCP Server follows a modular architecture designed for reliability, security, and extensibility.

```
┌───────────────────┐     ┌─────────────────────┐     ┌───────────────────┐
│  IDE & AI Tools   │     │ Android MCP Server  │     │  Android Devices  │
│                   │     │                     │     │                   │
│  ┌─────────────┐  │     │  ┌───────────────┐  │     │  ┌─────────────┐  │
│  │ Cursor IDE  │  │     │  │ MCP Protocol │  │     │  │ Real Device │  │
│  └─────────────┘  │     │  └───────┬───────┘  │     │  └─────────────┘  │
│  ┌─────────────┐  │     │  ┌───────┴───────┐  │     │  ┌─────────────┐  │
│  │ Claude AI   │◄─┼─────┼─►│ ADB Wrapper   │◄─┼─────┼─►│  Emulator   │  │
│  └─────────────┘  │     │  └───────┬───────┘  │     │  └─────────────┘  │
│  ┌─────────────┐  │     │  ┌───────┴───────┐  │     │                   │
│  │ Other Tools │  │     │  │ Security Layer│  │     │                   │
│  └─────────────┘  │     │  └───────────────┘  │     │                   │
└───────────────────┘     └─────────────────────┘     └───────────────────┘
```

### Components

1. **MCP Protocol Layer**

   - Implements Model Context Protocol specification
   - Handles resource, tool, and prompt requests
   - Manages client communication

2. **ADB Wrapper**

   - Provides a secure interface to ADB commands
   - Handles device discovery and management
   - Processes command outputs into structured data

3. **Security Layer**
   - Command sanitization and validation
   - Permission management
   - Secure storage of sensitive information

---

## 🧰 Feature Set

### Device Management

#### Resources

| Resource URI                   | Description               | Example Usage                                   |
| ------------------------------ | ------------------------- | ----------------------------------------------- |
| `device://list`                | List of connected devices | "Show me all connected Android devices"         |
| `device://{serial}/properties` | Device properties         | "What's the Android version on my test device?" |
| `device://{serial}/features`   | Hardware capabilities     | "Does this device have NFC support?"            |
| `device://{serial}/storage`    | Storage statistics        | "How much free space is on the device?"         |

#### Tools

| Tool Name           | Description                | Parameters                                    |
| ------------------- | -------------------------- | --------------------------------------------- |
| `connect_device`    | Connect to wireless device | `ip_address`, `port` (optional)               |
| `disconnect_device` | Disconnect device          | `serial`                                      |
| `reboot_device`     | Reboot device              | `serial`, `mode` (normal/recovery/bootloader) |
| `set_property`      | Set system property        | `serial`, `property`, `value`                 |

### Application Development

#### Resources

| Resource URI                               | Description                | Example Usage                                  |
| ------------------------------------------ | -------------------------- | ---------------------------------------------- |
| `fs://{serial}/app/{package}/manifest`     | App manifest               | "Show me the permissions my app is requesting" |
| `fs://{serial}/app/{package}/data`         | App data directory listing | "What files has my app created?"               |
| `fs://{serial}/app/{package}/shared_prefs` | App preferences            | "Show me the saved preferences in my app"      |
| `logs://{serial}/app/{package}`            | App-specific logs          | "What errors is my app generating?"            |

#### Tools

| Tool Name           | Description       | Parameters                                  |
| ------------------- | ----------------- | ------------------------------------------- |
| `install_app`       | Install APK       | `serial`, `apk_path`, `options`             |
| `uninstall_app`     | Remove app        | `serial`, `package`, `keep_data` (optional) |
| `start_app`         | Launch app        | `serial`, `package`, `activity` (optional)  |
| `stop_app`          | Force stop app    | `serial`, `package`                         |
| `clear_app_data`    | Clear app data    | `serial`, `package`                         |
| `grant_permission`  | Grant permission  | `serial`, `package`, `permission`           |
| `revoke_permission` | Revoke permission | `serial`, `package`, `permission`           |

### File System Access

#### Resources

| Resource URI                | Description          | Example Usage                            |
| --------------------------- | -------------------- | ---------------------------------------- |
| `fs://{serial}/list/{path}` | Directory listing    | "Show me what's in the Downloads folder" |
| `fs://{serial}/read/{path}` | File contents        | "Let me see the contents of config.xml"  |
| `fs://{serial}/stat/{path}` | File/directory stats | "When was this file last modified?"      |
| `fs://{serial}/size/{path}` | Directory size       | "How big is the DCIM folder?"            |

#### Tools

| Tool Name          | Description               | Parameters                            |
| ------------------ | ------------------------- | ------------------------------------- |
| `push_file`        | Upload file to device     | `serial`, `local_path`, `device_path` |
| `pull_file`        | Download file from device | `serial`, `device_path`, `local_path` |
| `delete_file`      | Remove file/directory     | `serial`, `path`                      |
| `create_directory` | Create directory          | `serial`, `path`                      |
| `move_file`        | Move/rename file          | `serial`, `source_path`, `dest_path`  |
| `copy_file`        | Copy file                 | `serial`, `source_path`, `dest_path`  |

### Debugging & Diagnostics

#### Resources

| Resource URI              | Description               | Example Usage                           |
| ------------------------- | ------------------------- | --------------------------------------- |
| `logs://{serial}/logcat`  | System logs               | "Show me the recent system logs"        |
| `logs://{serial}/anr`     | App Not Responding traces | "Why did my app freeze?"                |
| `logs://{serial}/crashes` | Recent crash reports      | "Show crash reports from the last hour" |
| `logs://{serial}/battery` | Battery statistics        | "What's draining the battery?"          |
| `logs://{serial}/memory`  | Memory usage              | "What's using the most memory?"         |
| `logs://{serial}/network` | Network statistics        | "Show network usage by app"             |

#### Tools

| Tool Name            | Description            | Parameters                                    |
| -------------------- | ---------------------- | --------------------------------------------- |
| `capture_screenshot` | Take screenshot        | `serial`                                      |
| `record_screen`      | Record screen video    | `serial`, `duration`, `bitrate` (optional)    |
| `capture_bugreport`  | Generate bug report    | `serial`, `path` (output location)            |
| `dump_heap`          | Capture heap dump      | `serial`, `package`, `path` (output location) |
| `start_profiling`    | Start method profiling | `serial`, `package`, `output`                 |
| `stop_profiling`     | Stop method profiling  | `serial`                                      |

### UI Testing & Automation

#### Resources

| Resource URI                      | Description          | Example Usage                                |
| --------------------------------- | -------------------- | -------------------------------------------- |
| `screen://{serial}/hierarchy`     | UI element hierarchy | "Show me the current screen layout"          |
| `screen://{serial}/accessibility` | Accessibility info   | "Check this screen for accessibility issues" |
| `screen://{serial}/focusable`     | Focusable elements   | "What elements can receive focus?"           |

#### Tools

| Tool Name      | Description                | Parameters                                   |
| -------------- | -------------------------- | -------------------------------------------- |
| `tap`          | Tap at coordinates         | `serial`, `x`, `y`                           |
| `swipe`        | Swipe gesture              | `serial`, `x1`, `y1`, `x2`, `y2`, `duration` |
| `input_text`   | Type text                  | `serial`, `text`                             |
| `press_key`    | Press hardware/system key  | `serial`, `keycode`                          |
| `start_intent` | Launch activity via intent | `serial`, `intent`                           |

### System & ROM Development

#### Resources

| Resource URI                   | Description           | Example Usage                     |
| ------------------------------ | --------------------- | --------------------------------- |
| `system://{serial}/partitions` | Partition information | "Show me the partition layout"    |
| `system://{serial}/bootloader` | Bootloader state      | "Is the bootloader unlocked?"     |
| `system://{serial}/kernel`     | Kernel information    | "What kernel version is running?" |
| `system://{serial}/selinux`    | SELinux policy        | "Show me the SELinux policy"      |

#### Tools

| Tool Name           | Description           | Parameters                           |
| ------------------- | --------------------- | ------------------------------------ |
| `flash_image`       | Flash partition image | `serial`, `partition`, `image_path`  |
| `sideload_package`  | Install OTA package   | `serial`, `package_path`             |
| `wipe_partition`    | Erase partition       | `serial`, `partition`                |
| `unlock_bootloader` | Unlock bootloader     | `serial` (with safety confirmations) |
| `lock_bootloader`   | Lock bootloader       | `serial`                             |
| `enable_root`       | Enable root access    | `serial`                             |
| `disable_root`      | Disable root access   | `serial`                             |

### Testing & Performance

#### Resources

| Resource URI              | Description     | Example Usage                    |
| ------------------------- | --------------- | -------------------------------- |
| `perf://{serial}/cpu`     | CPU usage       | "What's the CPU utilization?"    |
| `perf://{serial}/gpu`     | GPU usage       | "What's the GPU load?"           |
| `perf://{serial}/memory`  | Memory usage    | "What's the memory consumption?" |
| `perf://{serial}/battery` | Battery usage   | "What's the power consumption?"  |
| `perf://{serial}/network` | Network traffic | "What's the network activity?"   |

#### Tools

| Tool Name               | Description         | Parameters                                       |
| ----------------------- | ------------------- | ------------------------------------------------ |
| `run_instrumented_test` | Run test            | `serial`, `package`, `test_class`, `test_method` |
| `run_monkey`            | UI stress test      | `serial`, `package`, `event_count`               |
| `analyze_startup`       | Measure app startup | `serial`, `package`                              |
| `analyze_frames`        | Measure frame rate  | `serial`, `package`, `duration`                  |
| `capture_systrace`      | System trace        | `serial`, `categories`, `duration`               |

---

## 💻 Implementation Details

### Core Technologies

- **Python 3.10+**: Base programming language
- **MCP Python SDK**: Model Context Protocol implementation
- **ADB Python Wrappers**: For interfacing with Android Debug Bridge
- **AsyncIO**: For non-blocking operations
- **Image Processing Libraries**: For screenshot manipulation

### Sample Resource Implementation

```python
@mcp.resource("device://{serial}/properties")
def device_properties(serial: str, ctx: Context) -> str:
    """
    Get detailed properties of a specific device.
    Provides system properties including Android version, build details, and hardware info.

    Args:
        serial: Device serial number

    Returns:
        Formatted device properties as text
    """
    adb_ctx = ctx.lifespan_context

    # Validate device exists
    if not device_exists(adb_ctx.adb_path, serial):
        return "Error: Device not found"

    # Get device properties
    result = subprocess.run(
        [adb_ctx.adb_path, "-s", serial, "shell", "getprop"],
        capture_output=True, text=True, check=True
    )

    # Parse and format properties for better readability
    props = {}
    for line in result.stdout.splitlines():
        match = re.match(r'\[(.+)\]: \[(.+)\]', line)
        if match:
            key, value = match.groups()
            props[key] = value

    # Extract key information
    android_version = props.get("ro.build.version.release", "Unknown")
    sdk_version = props.get("ro.build.version.sdk", "Unknown")
    device_model = props.get("ro.product.model", "Unknown")
    device_brand = props.get("ro.product.brand", "Unknown")
    device_name = props.get("ro.product.name", "Unknown")

    # Format output in a structured way
    formatted_output = f"""
# Device Properties for {serial}

## Basic Information
- Model: {device_model}
- Brand: {device_brand}
- Name: {device_name}
- Android Version: {android_version}
- SDK Level: {sdk_version}

## Build Details
- Build Number: {props.get("ro.build.display.id", "Unknown")}
- Build Type: {props.get("ro.build.type", "Unknown")}
- Build Time: {props.get("ro.build.date", "Unknown")}

## Hardware
- Chipset: {props.get("ro.hardware", "Unknown")}
- Architecture: {props.get("ro.product.cpu.abi", "Unknown")}
- Screen Density: {props.get("ro.sf.lcd_density", "Unknown")}
"""

    # Include full property dump at the end
    formatted_output += "\n## All Properties\n"
    for key, value in sorted(props.items()):
        formatted_output += f"- {key}: {value}\n"

    return formatted_output
```

### Sample Tool Implementation

```python
@mcp.tool()
async def install_app(
    serial: str,
    apk_path: str,
    reinstall: bool = False,
    grant_permissions: bool = True,
    ctx: Context
) -> str:
    """
    Install an APK on the target device

    Args:
        serial: Device serial number
        apk_path: Path to the APK file (local to the server)
        reinstall: Whether to reinstall if app exists
        grant_permissions: Whether to grant all requested permissions

    Returns:
        Installation result message
    """
    adb_ctx = ctx.lifespan_context

    # Validate device exists
    if not device_exists(adb_ctx.adb_path, serial):
        return "Error: Device not found"

    # Validate APK exists
    if not os.path.exists(apk_path):
        return f"Error: APK file not found at {apk_path}"

    # Build command with options
    cmd = [adb_ctx.adb_path, "-s", serial, "install"]

    if reinstall:
        cmd.append("-r")

    if grant_permissions:
        cmd.append("-g")

    cmd.append(apk_path)

    # Log command execution
    ctx.info(f"Installing APK: {os.path.basename(apk_path)}")

    # Execute install with progress reporting
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Process output and report progress
    total_size = os.path.getsize(apk_path)
    reported_progress = 0

    while True:
        line = await process.stdout.readline()
        if not line:
            break

        line_text = line.decode('utf-8').strip()

        # Parse progress information
        if "Performing Streamed Install" in line_text:
            ctx.info("Starting streamed install...")
        elif "%" in line_text:
            # Extract progress percentage
            match = re.search(r'(\d+)%', line_text)
            if match:
                progress = int(match.group(1))
                if progress > reported_progress:
                    reported_progress = progress
                    await ctx.report_progress(progress, 100)

    # Get final result
    await process.wait()
    stderr = (await process.stderr.read()).decode('utf-8')

    if process.returncode != 0:
        return f"Error installing APK: {stderr}"

    # Get the package name from the APK
    package_name = await get_apk_package_name(apk_path)

    return f"Successfully installed {package_name}"
```

### Handling Screenshots

```python
@mcp.tool()
async def capture_screenshot(serial: str, ctx: Context) -> Image:
    """
    Capture a screenshot from the device

    Args:
        serial: Device serial number

    Returns:
        Device screenshot as an image
    """
    adb_ctx = ctx.lifespan_context

    # Validate device exists
    if not device_exists(adb_ctx.adb_path, serial):
        raise ValueError(f"Device {serial} not found")

    # Generate temp file path
    screenshot_path = os.path.join(adb_ctx.temp_dir, f"{serial}_screen.png")

    ctx.info(f"Capturing screenshot from {serial}...")

    try:
        # Take screenshot and pull to local temp directory
        await ctx.report_progress(0, 3)

        # Step 1: Capture screenshot on device
        process = await asyncio.create_subprocess_exec(
            adb_ctx.adb_path, "-s", serial, "shell", "screencap", "-p", "/sdcard/screen.png",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Failed to capture screenshot: {stderr.decode('utf-8')}")

        await ctx.report_progress(1, 3)

        # Step 2: Pull file to local temp directory
        process = await asyncio.create_subprocess_exec(
            adb_ctx.adb_path, "-s", serial, "pull", "/sdcard/screen.png", screenshot_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Failed to pull screenshot: {stderr.decode('utf-8')}")

        await ctx.report_progress(2, 3)

        # Step 3: Clean up on device
        process = await asyncio.create_subprocess_exec(
            adb_ctx.adb_path, "-s", serial, "shell", "rm", "/sdcard/screen.png",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        await ctx.report_progress(3, 3)

        # Read the image and return it
        with open(screenshot_path, "rb") as f:
            image_data = f.read()

        ctx.info(f"Screenshot captured successfully ({len(image_data)} bytes)")
        return Image(data=image_data, format="png")

    except Exception as e:
        ctx.error(f"Error capturing screenshot: {str(e)}")
        raise
    finally:
        # Clean up local temp file
        if os.path.exists(screenshot_path):
            os.unlink(screenshot_path)
```

### Sample Prompt Implementation

```python
@mcp.prompt()
def analyze_anr(anr_trace: str) -> str:
    """
    Generate a prompt to analyze an Application Not Responding (ANR) trace

    Args:
        anr_trace: The ANR trace content to analyze
    """
    return f"""I need help analyzing this Android Application Not Responding (ANR) trace.
Can you identify the root cause and suggest potential fixes?

```

{anr_trace}

```

Please include in your analysis:
1. Which thread is causing the ANR
2. What that thread was doing when it got stuck
3. Any locks or resources being waited on
4. Potential code fixes to resolve the issue
"""
```

## 🔐 Security Considerations

Security is a critical component of the Android MCP Server, especially when dealing with development devices that may contain sensitive information or have elevated privileges.

### Command Sanitization

All inputs to ADB commands are carefully sanitized to prevent shell injection:

```python
def sanitize_path(path: str) -> str:
    """Sanitize a path to prevent command injection"""
    # Remove shell special characters and escape sequences
    sanitized = re.sub(r'[;&|<>$`\\"\']', '', path)
    # Prevent path traversal
    sanitized = os.path.normpath(sanitized)
    if sanitized.startswith('..'):
        raise ValueError("Path traversal detected")
    return sanitized
```

### Permission Model

Operations are categorized by risk level:

1. **Safe Operations**

   - Read-only operations (retrieving logs, properties)
   - Screen captures and UI inspection
   - Running safe diagnostic commands

2. **Moderate Risk Operations**

   - Installing/uninstalling applications
   - Modifying application data
   - Changing system settings
   - File transfers

3. **High Risk Operations**
   - Flashing system images
   - Bootloader operations
   - Partition wiping
   - Root access operations

High-risk operations require explicit confirmation and display detailed warnings about potential consequences.

### Device Authentication

For wireless devices, proper authentication is enforced:

```python
@mcp.tool()
async def connect_wireless_device(
    ip_address: str,
    port: int = 5555,
    pairing_code: str = None,
    ctx: Context
) -> str:
    """Connect to a wireless device with proper authentication"""

    # For Android 11+ devices, require a pairing code for secure connection
    device_os_version = await get_device_os_version(ip_address, port)

    if device_os_version >= 30:  # Android 11+
        if not pairing_code:
            return "Error: Devices running Android 11+ require a pairing code for wireless debugging"

        # Use the secure pairing method
        result = await pair_with_device(ip_address, port, pairing_code)
        if not result.success:
            return f"Pairing failed: {result.message}"

    # Connect to the device
    result = await connect_to_device(ip_address, port)

    return result.message
```

## 🏁 Getting Started

### Prerequisites

- Python 3.10 or higher
- Android SDK Platform Tools (ADB)
- Connected Android device or emulator
- MCP-compatible IDE (e.g., Cursor)

### Installation

```bash
# Install using pip
pip install android-mcp-server

# Or install with extra dependencies
pip install "android-mcp-server[gui,monitoring]"
```

### Configuration

Create a configuration file at `~/.config/android-mcp/config.yaml`:

```yaml
# Android MCP Server Configuration

# ADB Configuration
adb:
  # Path to ADB executable (leave empty to use PATH)
  path: ""

  # Default server port
  server_port: 5037

  # Additional ADB server options
  server_options: {}

# Security settings
security:
  # Require confirmation for high-risk operations (recommended)
  confirm_high_risk: true

  # Restrict access to certain device paths
  restricted_paths:
    - "/data/system"
    - "/data/misc/keystore"
    - "/data/misc/user"

  # Device permissions (serial -> allowed operations)
  device_permissions:
    "emulator-5554":
      allow_all: true
    "ABCD1234":
      allow_install: true
      allow_file_access: true
      allow_flash: false

# Server settings
server:
  # Logging verbosity (debug, info, warning, error)
  log_level: "info"

  # Temporary file directory (leave empty for system default)
  temp_dir: ""

  # Maximum file size for transfers (in bytes)
  max_file_size: 104857600 # 100 MB
```

### Running the Server

```bash
# Run with default settings
android-mcp-server

# Specify configuration file
android-mcp-server --config /path/to/config.yaml

# Connect to specific devices only
android-mcp-server --devices emulator-5554,ABCD1234

# Run with debugging enabled
android-mcp-server --debug

# Start in development mode with MCP Inspector
android-mcp-server --dev
```

### Connecting to Cursor

1. Configure Cursor to use the Android MCP Server:

   - Open Cursor settings
   - Navigate to AI Integrations -> MCP
   - Add a new MCP server with the command `android-mcp-server`

2. Start using the server in your workflow:
   - Ask Claude about connected devices
   - Request logs or screenshots
   - Analyze app performance
   - Debug crashes with AI assistance

---


## 🚀 Roadmap

### Version 1.0

- [x] Basic device management
- [x] Application installation and management
- [x] Log access and analysis
- [x] Screenshot capture
- [x] File system operations

### Version 1.1

- [ ] Wireless device connection
- [ ] Enhanced file transfer capabilities
- [ ] UI testing framework integration
- [ ] Performance monitoring dashboard

### Version 1.2

- [ ] ROM flashing and management
- [ ] System trace collection and analysis
- [ ] Network traffic monitoring
- [ ] Battery usage optimization

### Version 2.0

- [ ] Multi-device parallel operations
- [ ] Integrated CI/CD workflows
- [ ] Custom plugin architecture
- [ ] Remote device farm integration

---

## 🤝 Contributing

Contributions to the Android MCP Server are welcome! Here's how you can help:

1. **Report Issues**: Submit bugs or feature requests via GitHub issues
2. **Contribute Code**: Fork the repository and submit pull requests
3. **Improve Documentation**: Help enhance the documentation and examples
4. **Share Use Cases**: Share your Android development workflows

Please review our [contributing guidelines](CONTRIBUTING.md) before making contributions.

---

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) team for the protocol specification
- [Android Open Source Project](https://source.android.com/) for Android tools and documentation
- [Cursor IDE](https://cursor.sh/) for AI-powered development environment
- All contributors who help improve this project

---

<div align="center">

Made with ❤️ for Android developers everywhere

</div>

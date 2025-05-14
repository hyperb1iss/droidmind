# ✨ DroidMind 🤖

<div align="center">

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-9D00FF.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache_2.0-FF00FF.svg?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/status-active_development-39FF14.svg?style=for-the-badge)](docs/plan.md)
[![Code Style](https://img.shields.io/badge/code_style-ruff-00FFFF.svg?style=for-the-badge)](https://github.com/astral-sh/ruff)
[![Type Check](https://img.shields.io/badge/type_check-mypy-FFBF00.svg?style=for-the-badge)](https://mypy.readthedocs.io/en/stable/)

**Control Android devices with AI through the Model Context Protocol**

</div>

DroidMind is a powerful bridge between AI assistants and Android devices, enabling control, debugging, and system analysis through natural language. By implementing the Model Context Protocol (MCP), DroidMind allows AI models to directly interact with Android devices via ADB in a secure, structured way. When used as part of an agentic coding workflow, DroidMind can enable your assistant to build and debug with your device directly in the loop.

## 💫 Features

- 📱 **Device Control** - Connect to devices over USB or TCP/IP, run shell commands, reboot
- 📊 **System Analysis** - Inspect device properties, view hardware info, analyze system logs
- 🔍 **File System Access** - Browse directory contents and manage files on devices
- 📷 **Visual Diagnostics** - Capture device screenshots for analysis and debugging
- 📦 **App Management** - Install, uninstall, start, stop, and clear app data on connected devices
- 🔄 **Multi-Device Support** - Control and switch between multiple connected devices
- 👆 **UI Automation** - Interact with the device through taps, swipes, text input, and key presses
- 🔍 **App Inspection** - View app manifests, shared preferences, and app-specific logs
- 🔒 **Security Framework** - Protect devices with comprehensive command validation
- 💬 **MCP Integration** - Seamless connection to Claude, Cursor, Cline, and more

## 🚀 Installation

Ensure you have Python 3.13+ and `uv` installed.

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/hyperbliss/droidmind.git
    cd droidmind
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    uv pip install -e .[sse] # For SSE transport, or .[stdio] for stdio
    ```

## Running with Docker

DroidMind can also be run using Docker. This is useful for creating a consistent environment and simplifying deployment.

### Building the Docker Image

To build the DroidMind Docker image, navigate to the project's root directory (where the `Dockerfile` is located) and run:

```bash
docker build -t droidmind:latest .
```

### Running the Docker Container

Once the image is built, you can run DroidMind as a container.

**Default (Stdio Transport - Interactive CLI):**

By default, the container runs DroidMind with `stdio` transport, suitable for interactive command-line use.

```bash
docker run -it --rm --name droidmind-cli droidmind:latest
```

- `-it`: Run in interactive mode with a pseudo-TTY.
- `--rm`: Automatically remove the container when it exits.
- `--name droidmind-cli`: Assign a name to the container.

If you want to pass specific arguments to `droidmind` in `stdio` mode:

```bash
docker run -it --rm --name droidmind-cli droidmind:latest droidmind --your-options
```

**Using SSE Transport (e.g., for AI Assistant Integration):**

To run DroidMind with SSE transport (e.g., for connecting with AI assistants like Claude or Cursor), you can use the `DROIDMIND_TRANSPORT` environment variable or override the command.

Using Environment Variable:

```bash
docker run -d -p 4256:4256 -e DROIDMIND_TRANSPORT=sse --name droidmind-server droidmind:latest
```

- `-d`: Run in detached mode (in the background).
- `-p 4256:4256`: Map port 4256 of the container to port 4256 on your host.
- `-e DROIDMIND_TRANSPORT=sse`: Sets the transport mode to SSE. The entrypoint script will automatically use `--host 0.0.0.0` and `--port 4256`.
- `--name droidmind-server`: Assign a name to the container.

Overriding Command for SSE:

```bash
docker run -d -p 4256:4256 --name droidmind-server droidmind:latest droidmind --transport sse --host 0.0.0.0 --port 4256
```

This explicitly tells `droidmind` to run with SSE, host, and port settings.

**Connecting to ADB Devices:**

For DroidMind in Docker to control Android devices, the container needs access to an ADB server that can see your devices.

- **Networked ADB Devices (Recommended for Docker):**
  If your Android devices are connected via TCP/IP (e.g., after running `adb connect <device_ip>:5555` on your host or ensuring they are on the same network and ADB over network is enabled on the device), the DroidMind container should be able to connect to them directly using the `connect_device` tool, provided the container's network configuration allows outbound connections to your devices' IPs.

- **USB-Connected ADB Devices:**
  This is more complex with Docker and highly platform-dependent.

  - **Host ADB Server:** One common approach is to configure the Docker container to use the ADB server running on your _host_ machine. This might involve:
    - Sharing the host's network: `docker run --network host ...` (Linux only).
    - Mounting the ADB server socket: `docker run -v /tmp/adb.sock:/tmp/adb.sock ...` (path may vary).
    - Setting the `ADB_SERVER_SOCKET` environment variable in the container.
  - **ADB Server inside Container:** Another option is to run an ADB server _inside_ the container and pass through the USB devices from the host. This often requires privileged mode and specific volume mounts (e.g., `docker run --privileged -v /dev/bus/usb:/dev/bus/usb ...`).

  The exact commands for USB device access will vary based on your operating system (Linux, macOS, Windows) and Docker setup. Please refer to Docker and ADB documentation for advanced configurations.

**Customizing the Run Command:**

You can append arguments to `docker run droidmind:latest ...` to customize the `droidmind` execution. The `entrypoint.sh` script will manage the `--transport` argument based on the `DROIDMIND_TRANSPORT` environment variable if you don't specify `--transport` in your command arguments.

Example: Run with SSE on a different port and enable debug mode, letting the env var handle transport:

```bash
docker run -d -p 8000:8000 -e DROIDMIND_TRANSPORT=sse --name droidmind-custom droidmind:latest droidmind --port 8000 --debug
```

Example: Explicitly specify all options, including transport:

```bash
docker run -d -p 8000:8000 --name droidmind-custom droidmind:latest droidmind --transport sse --host 0.0.0.0 --port 8000 --debug
```

**Viewing Logs:**

If you're running in detached mode (`-d`), you can view the server logs using:

```bash
docker logs droidmind-server
```

Or follow them in real-time:

```bash
docker logs -f droidmind-server
```

## 📋 Prerequisites

- Python 3.13 or higher
- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed and in PATH
- UV package manager (recommended for dependency management)
- For network control: Android device with ADB over TCP/IP enabled

## 🔮 Quick Start

### Run the DroidMind server

Run DroidMind as a server to connect AI assistants via MCP:

```bash
# Start DroidMind as a network server
droidmind --transport sse
```

### Using with AI Assistants

1. Start DroidMind in SSE mode:

   ```bash
   droidmind --transport sse
   ```

2. Connect your AI assistant using the MCP protocol URI:

   ```
   sse://localhost:4256/sse
   ```

3. The AI can now control your Android devices through natural language!

## 🛠️ Available MCP Resources and Tools

### Resources

- `devices://list` - List all connected devices
- `device://{serial}/properties` - Get detailed device properties
- `logs://{serial}/logcat` - Get recent logs from the device
- `logs://{serial}/anr` - Get Application Not Responding (ANR) traces
- `logs://{serial}/crashes` - Get application crash logs
- `logs://{serial}/battery` - Get battery statistics and history
- `logs://{serial}/app/{package}` - Get application-specific logs
- `fs://{serial}/list/{path}` - List directory contents on the device
- `fs://{serial}/read/{path}` - Read file contents from the device
- `fs://{serial}/stats/{path}` - Get detailed file/directory statistics
- `app://{serial}/{package}/manifest` - Get AndroidManifest.xml contents
- `app://{serial}/{package}/data` - List files in the app's data directory
- `app://{serial}/{package}/shared_prefs` - Get app's shared preferences

### Tools

- `devicelist` - List all connected Android devices
- `device_properties` - Get detailed properties of a specific device
- `device_logcat` - Get recent logcat output from a device
- `list_directory` - List contents of a directory on the device
- `connect_device` - Connect to a device over TCP/IP
- `disconnect_device` - Disconnect from an Android device
- `shell_command` - Run a shell command on the device
- `install_app` - Install an APK on the device
- `uninstall_app` - Uninstall an app from the device
- `start_app` - Start an app on the device
- `stop_app` - Force stop an app on the device
- `clear_app_data` - Clear app data and cache
- `list_packages` - List installed packages on the device
- `get_app_manifest` - Get AndroidManifest.xml contents for an app
- `get_app_permissions` - Get permissions requested by an app
- `get_app_activities` - Get activities defined in an app
- `get_app_info` - Get detailed information about an app
- `reboot_device` - Reboot the device (normal, recovery, or bootloader)
- `screenshot` - Get a screenshot from a device
- `capture_bugreport` - Generate a comprehensive bug report from the device
- `dump_heap` - Create a heap dump from a running process for memory analysis
- `push_file` - Upload a file to the device
- `pull_file` - Download a file from the device
- `delete_file` - Delete a file or directory from the device
- `create_directory` - Create a directory on the device
- `file_exists` - Check if a file exists on the device
- `read_file` - Read the contents of a file on the device
- `write_file` - Write text content to a file on the device
- `file_stats` - Get detailed information about a file or directory
- `tap` - Tap on the device screen at specific coordinates
- `swipe` - Perform a swipe gesture from one point to another on the screen
- `input_text` - Input text on the device as if from a keyboard
- `press_key` - Press a hardware or software key (e.g., HOME, BACK, VOLUME)
- `start_intent` - Start an app activity using an Android intent

## 📊 Example AI Assistant Queries

With an AI assistant connected to DroidMind, try these queries:

- "List all connected Android devices and show me their properties"
- "Connect to my phone at 192.168.1.100 and check its battery status"
- "Take a screenshot of my Pixel and show me what's currently on screen"
- "Check the available storage space on my device"
- "Show me the ANR traces and crash logs from my device"
- "Look at recent logs and tell me if there are any errors"
- "Install this APK file on my device and tell me if it was successful"
- "Show me a list of all installed apps on my phone"
- "Reboot my device into recovery mode"
- "What Android version is my phone running?"
- "Check if my device is rooted and tell me its security patch level"
- "Show me the manifest file for com.android.settings"
- "Check the shared preferences for my app"
- "Tap on the Settings icon at coordinates 500,1000"
- "Swipe down from the top of the screen to open the notification shade"
- "Input my password into the current text field"
- "Press the back button three times to return to the home screen"
- "Open the Settings app by starting the com.android.settings package"

## 🔒 Security Features

DroidMind includes a comprehensive security framework to protect your devices while still allowing AI assistants to be expressive:

- **Command Validation**: All shell commands are validated against an allowlist of safe commands
- **Risk Assessment**: Commands are categorized by risk level (SAFE, LOW, MEDIUM, HIGH, CRITICAL)
- **Command Sanitization**: Input is sanitized to prevent command injection attacks
- **Protected Paths**: System directories and critical paths are protected from modification
- **Comprehensive Logging**: All commands are logged with their risk level for auditing
- **Suspicious Pattern Detection**: Commands with potentially dangerous patterns are blocked
- **ADB Command Security**: Special handling for ADB-specific commands with proper async validation

The security system is designed to be permissive enough to allow common operations while preventing destructive actions. High-risk commands will display warnings to users before execution, and critical operations are blocked entirely without explicit override.

## 💻 Development

DroidMind uses UV for dependency management and development workflows. UV is a fast, reliable Python package manager and resolver.

```bash
# Update dependencies
uv sync

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy .
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Set up your development environment with UV
4. Make your changes
5. Run tests and linting
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📝 License

This project is licensed under the Apache License - see the LICENSE file for details.

---

<div align="center">

Created by [Stefanie Jane 🌠](https://github.com/hyperb1iss)

If you find DroidMind useful, [buy me a Monster Ultra Violet ⚡️](https://ko-fi.com/hyperb1iss)

</div>

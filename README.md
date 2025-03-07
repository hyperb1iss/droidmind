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
- 🌈 **NeonGlam Console** - Enjoy an aesthetic terminal experience with cyberpunk vibes
- 💬 **MCP Integration** - Seamless connection to Claude, Cursor, Cline, and more

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/hyperbliss/droidmind.git
cd droidmind

# Set up a virtual environment with UV
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies with UV
uv sync
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
   sse://localhost:6463/sse
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

## 🚧 Development Status

DroidMind is in active development with approximately 90% of planned features implemented. See the [Development Roadmap](docs/plan.md) for details on current progress and upcoming features.

### Current Focus Areas:

1. ~~**UI Automation Development** - Adding touch, text input, and intent capabilities~~ ✅ Completed!
2. ~~**Security Framework** - Adding command validation and safety features~~ ✅ Completed!
3. ~~**App Management** - Completing app lifecycle and data management tools~~ ✅ Completed!
4. ~~**File System Enhancements** - Robust file operations and metadata handling~~ ✅ Completed!
5. **Diagnostic Tools** - Adding advanced diagnostics ✅ Major progress!
   - ~~Screenshot tool~~ ✅ Completed
   - ~~Bug report generation~~ ✅ Completed
   - ~~Heap dump analysis~~ ✅ Completed
   - Screen recording 🔄 Pending
6. **Documentation Enhancement** - Comprehensive API docs and tutorials 🔄 In Progress

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

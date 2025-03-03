# ✨ DroidMind 🤖

<div align="center">

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-9D00FF.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache_2.0-FF00FF.svg?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/status-active_development-39FF14.svg?style=for-the-badge)](docs/plan.md)
[![Code Style](https://img.shields.io/badge/code_style-ruff-00FFFF.svg?style=for-the-badge)](https://github.com/astral-sh/ruff)
[![Type Check](https://img.shields.io/badge/type_check-mypy-FFBF00.svg?style=for-the-badge)](https://mypy.readthedocs.io/en/stable/)

**Control Android devices with AI through the Model Context Protocol**

</div>

DroidMind is a powerful bridge between AI assistants and Android devices, enabling control, debugging, and system analysis through natural language. By implementing the Model Context Protocol (MCP), DroidMind allows AI models to directly interact with Android devices via ADB in a secure, structured way. When used as part of an agentic coding
workflow, DroidMind can enable your assistant to build and debug with your device directly in the loop.

## 💫 Features

- 📱 **Device Control** - Connect to devices over USB or TCP/IP, run shell commands, reboot
- 📊 **System Analysis** - Inspect device properties, view hardware info, analyze system logs  
- 🔍 **File System Access** - Browse directory contents and manage files on devices
- 📷 **Visual Diagnostics** - Capture device screenshots for analysis and debugging
- 📦 **App Management** - Install applications on connected devices
- 🔄 **Multi-Device Support** - Control and switch between multiple connected devices
- 🌈 **NeonGlam Console** - Enjoy an aesthetic terminal experience
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
droidmind --transport sse --host 0.0.0.0 --port 8000
```

### Using with AI Assistants

1. Start DroidMind in SSE mode:

   ```bash
   droidmind --transport sse --host 0.0.0.0 --port 8000
   ```

2. Connect your AI assistant using the MCP protocol URI:

   ```
   sse://your-ip-address:8000/sse
   ```

3. The AI can now control your Android devices through natural language!

## 🛠️ Available MCP Resources and Tools

### Resources

- `device://list` - List all connected devices
- `device://{serial}/properties` - Get detailed device properties
- `logs://{serial}/logcat` - Get recent logs from the device
- `fs://{serial}/list/{path}` - List directory contents on the device

### Tools

- `devicelist` - List all connected Android devices
- `device_properties` - Get detailed properties of a specific device
- `device_logcat` - Get recent logcat output from a device
- `list_directory` - List contents of a directory on the device
- `connect_device` - Connect to a device over TCP/IP
- `disconnect_device` - Disconnect from an Android device
- `shell_command` - Run a shell command on the device
- `install_app` - Install an APK on the device
- `reboot_device` - Reboot the device (normal, recovery, or bootloader)
- `screenshot` - Get a screenshot from a device

## 📊 Example AI Assistant Queries

With an AI assistant connected to DroidMind, try these queries:

- "List all connected Android devices and show me their properties"
- "Connect to my phone at 192.168.1.100 and check its battery status"
- "Take a screenshot of my Pixel and show me what's currently on screen"
- "Check the available storage space on my device"
- "Look at recent logs and tell me if there are any errors"
- "Install this APK file on my device and tell me if it was successful"
- "Show me a list of all installed apps on my phone"
- "Reboot my device into recovery mode"
- "What Android version is my phone running?"
- "Check if my device is rooted and tell me its security patch level"

## 🚧 Development Status

DroidMind is in active development with approximately 30% of planned features implemented. See the [Development Roadmap](docs/plan.md) for details on current progress and upcoming features.

### Current Focus Areas:

1. **File System Implementation** - Enhancing file management capabilities
2. **Security Framework** - Adding command validation and safety features
3. **Documentation** - Creating comprehensive guides and references
4. **Console UI Enhancements** - Building a more interactive user experience

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

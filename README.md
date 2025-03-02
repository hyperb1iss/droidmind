# DroidMind 🤖 ✨

Control Android devices with AI assistants using the Model Context Protocol (MCP).

DroidMind is a powerful bridge between AI assistants and Android devices, enabling control, debugging, and analysis through natural language. By implementing the Model Context Protocol (MCP), DroidMind allows AI models to directly interact with Android devices via ADB.

![DroidMind Banner](docs/images/banner.png)

## ✨ Current Features

- 📱 **Device Control**: Connect to Android devices over ADB and execute commands
- 📊 **System Analysis**: Inspect device properties and system logs
- 🔍 **File System Access**: Browse directory contents on connected devices
- 📷 **Screenshots**: Capture device screens for visual analysis and debugging
- 📦 **App Installation**: Install applications on connected devices
- 🔄 **Device Management**: Reboot devices and manage connections
- 💬 **MCP Integration**: Seamless connection to AI assistants through the Model Context Protocol

DroidMind is very much still a work in progress and better packaging and documentation is coming soon!!

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
- UV package manager (recommended)
- Android device with ADB enabled
- For network control: Android device with ADB over TCP/IP enabled

## 🔧 Quick Start

### Terminal Mode (stdio)

```bash
# Start DroidMind in terminal mode
droidmind

# Then connect to a device
> connect_device --ip_address 192.168.1.100 --port 5555
```

### Network Mode (SSE)

```bash
# Start DroidMind as a network server
droidmind --transport sse --host 0.0.0.0 --port 8000
```

### Using with Claude

1. Start DroidMind in SSE mode:

   ```bash
   droidmind --transport sse --host 0.0.0.0 --port 8000
   ```

2. Connect Claude using the MCP protocol URI:

   ```
   sse://your-ip-address:8000/sse
   ```

3. Claude can now control your Android devices through natural language!

## 📱 Preparing Android Devices

To use your Android device with DroidMind, you need to enable ADB debugging:

1. Enable Developer Options by tapping 7 times on the Build Number in Settings
2. Enable USB Debugging in Developer Options
3. For network control, enable ADB over TCP/IP:
   ```bash
   adb tcpip 5555
   ```
4. Get your device's IP address from Settings > About Phone > Status > IP Address

## 🛠️ Available MCP Resources and Tools

DroidMind currently provides these MCP resources and tools:

### Resources

- `device://list` - List all connected devices
- `device://{serial}/properties` - Get detailed device properties
- `logs://{serial}/logcat` - Get recent logs from the device
- `fs://{serial}/list/{path}` - List directory contents on the device

### Tools

- `connect_device` - Connect to a device via TCP/IP
- `disconnect_device` - Disconnect from a device
- `shell_command` - Run a shell command on the device
- `install_app` - Install an APK on the device
- `screenshot` - Take a screenshot of the device
- `reboot_device` - Reboot the device (normal, recovery, or bootloader)

## 📊 Example Queries for AI Assistants

Here are some example queries you can ask an AI assistant connected to DroidMind:

- "List all connected Android devices"
- "Connect to my phone at 192.168.1.100"
- "Show me the battery stats on my Pixel phone"
- "What's the Android version of my connected device?"
- "Take a screenshot of my phone"
- "Check if my device has any error messages in the logs"
- "Install this APK file on my device"
- "Reboot my phone into recovery mode"

## 🚧 Development Status

DroidMind is currently in active development with approximately 18% of planned features implemented. See the [Development Roadmap](docs/plan.md) for details on current progress and upcoming features.

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

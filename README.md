# DroidMind 🤖 ✨

Control Android devices with AI assistants using the Model Context Protocol (MCP).

DroidMind is a powerful bridge between AI assistants and Android devices, enabling control, debugging, and analysis through natural language. By implementing the Model Context Protocol (MCP), DroidMind allows AI models to directly interact with Android devices via ADB.

![DroidMind Banner](docs/images/banner.png)

## ✨ Features

- 📱 **Device Control**: Connect to Android devices over TCP/IP and execute commands
- 📊 **System Analysis**: Inspect device properties, logs, and system information
- 🔍 **File System Access**: Browse and manipulate files on connected devices
- 📷 **Screenshots**: Capture device screens for visual analysis and debugging
- 🔄 **App Management**: Install, uninstall, and analyze applications
- 💬 **MCP Integration**: Seamless connection to AI assistants through the Model Context Protocol

## 🚀 Installation

```bash
# Install from PyPI
pip install droidmind

# Or install from source
git clone https://github.com/hyperbliss/droidmind.git
cd droidmind
pip install -e .
```

## 📋 Prerequisites

- Python 3.8 or higher
- Android device with ADB enabled
- For network control: Android device with ADB over TCP/IP enabled

## 🔧 Quick Start

### Terminal Mode (stdio)

```bash
# Start DroidMind in terminal mode
droidmind

# Then connect to a device
> connect_device --host 192.168.1.100 --port 5555
```

### Network Mode (SSE)

```bash
# Start DroidMind as a network server
droidmind --transport sse --host 0.0.0.0 --port 8000

# Access the web interface at http://localhost:8000
```

### Using with Claude or ChatGPT

1. Start DroidMind in SSE mode:
   ```bash
   droidmind --transport sse --host 0.0.0.0 --port 8000
   ```

2. Connect your AI assistant using the MCP protocol URI:
   ```
   sse://your-ip-address:8000/sse
   ```

3. Your AI assistant can now control Android devices through natural language!

## 💻 CLI Options

DroidMind comes with a beautiful CLI that provides various options:

```
Usage: droidmind [OPTIONS]

  DroidMind MCP Server - Control Android devices with AI assistants.

  This server implements the Model Context Protocol (MCP) to allow AI
  assistants to control and interact with Android devices via ADB.

Options:
  --host TEXT                     Host to bind the server to (use 0.0.0.0 for
                                  all interfaces)
  --port INTEGER                  Port to listen on for network connections
  --transport [stdio|sse]         Transport type to use (stdio for terminal,
                                  sse for network)
  --debug / --no-debug            Enable debug mode for more verbose logging
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                  Set the logging level
  -h, --help                      Show this message and exit
```

## 📱 Preparing Android Devices

To use your Android device with DroidMind, you need to enable ADB debugging:

1. Enable Developer Options by tapping 7 times on the Build Number in Settings
2. Enable USB Debugging in Developer Options
3. For network control, enable ADB over TCP/IP:
   ```bash
   adb tcpip 5555
   ```
4. Get your device's IP address from Settings > About Phone > Status > IP Address

## 🔌 Example Usage

### Using the SSE Client Example

DroidMind includes an example client that demonstrates how to interact with the server using SSE:

```bash
# List connected devices
python examples/sse-client-example.py --action list

# Connect to a device
python examples/sse-client-example.py --action connect --host 192.168.1.100

# Get device properties
python examples/sse-client-example.py --action properties --serial 192.168.1.100:5555

# Run a shell command
python examples/sse-client-example.py --action shell --serial 192.168.1.100:5555 --command "dumpsys battery"

# Listen for events
python examples/sse-client-example.py --action listen
```

### Using DroidMind with Claude

1. Start the DroidMind server in SSE mode
2. In your conversation with Claude, enter the following:
   ```
   Please connect to my Android device using this MCP URL: sse://my-ip-address:8000/sse
   ```
3. Ask Claude to perform actions like:
   - "Connect to my Android device at 192.168.1.100"
   - "Show me all connected devices"
   - "Get properties for my Pixel phone"
   - "Capture a screenshot from my device"
   - "Check battery status on my device"

## 🛠️ Available Resources and Tools

DroidMind provides several MCP resources and tools that can be accessed by AI assistants:

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
- `capture_screenshot` - Take a screenshot of the device
- `reboot_device` - Reboot the device (normal, recovery, or bootloader)

## 📊 Example Queries

Here are some example queries you can ask an AI assistant connected to DroidMind:

- "List all connected Android devices"
- "Connect to my phone at 192.168.1.100"
- "Show me the battery stats on my Pixel phone"
- "What's the Android version of my connected device?"
- "Take a screenshot of my phone and tell me what apps are running"
- "Check if my device has any error messages in the logs"
- "Install this APK file on my device"
- "Reboot my phone into recovery mode"

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- The [MCP Protocol](https://github.com/anthropics/mcp) team for the amazing protocol
- Everyone who contributed to the adb-shell library

## 📬 Contact

- GitHub: [hyperbliss/droidmind](https://github.com/hyperbliss/droidmind)
- Email: stef@hyperbliss.tech

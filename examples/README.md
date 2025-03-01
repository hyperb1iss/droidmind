# DroidMind Examples 🚀

This directory contains examples demonstrating how to use DroidMind in various scenarios. These examples help you understand the capabilities and integration patterns for connecting AI assistants to Android devices.

## 🔍 Example Files

### 1. `example-server.py`

A minimal MCP server implementation showing the basic structure of an MCP server. This is useful for understanding how the MCP protocol works without Android-specific functionality.

```bash
python example-server.py --transport sse --port 8000
```

### 2. `sse-client-example.py`

Demonstrates how to interact with a DroidMind server using the SSE (Server-Sent Events) transport. This example shows how to:
- Connect to the SSE server
- Send requests to the server
- Handle responses and events
- Execute various Android device commands

```bash
# List connected devices
python sse-client-example.py --action list

# Connect to a device
python sse-client-example.py --action connect --host 192.168.1.100

# Get device properties
python sse-client-example.py --action properties --serial 192.168.1.100:5555

# Run a shell command
python sse-client-example.py --action shell --serial 192.168.1.100:5555 --command "dumpsys battery"

# Listen for events
python sse-client-example.py --action listen
```

## 💡 Use Cases

These examples can be used for:

1. **Learning the MCP Protocol** - Understand how the Model Context Protocol works with events and requests
2. **Building Custom Clients** - Use the SSE client example as a foundation for your own custom clients
3. **Testing DroidMind Functionality** - Verify that your DroidMind server is working properly
4. **Developing Integrations** - Learn how to integrate DroidMind with other services or applications

## 🔮 Creating Your Own Examples

Feel free to create your own examples based on these templates. Some ideas:

- **UI Automation Client** - Create a client that performs UI testing on Android apps
- **Diagnostic Dashboard** - Build a simple web dashboard using the DroidMind API to monitor device health
- **Log Analyzer** - A specialized client that processes and analyzes logcat data
- **App Deployment Tool** - A client that automates app installation and configuration

## 🧪 Testing the Examples

Before running these examples, make sure:

1. You have a DroidMind server running
2. You have the required dependencies installed
3. You have at least one Android device configured for ADB access

To install dependencies for the examples:

```bash
pip install httpx rich
```

## 📚 Additional Resources

For more information about the MCP protocol and DroidMind:

- [DroidMind Documentation](../README.md)
- [MCP Protocol Specification](https://github.com/anthropics/mcp)
- [ADB Shell Documentation](https://github.com/JeffLIrion/adb_shell) 
#🚀 Quick Start Guide

Welcome to DroidMind! This guide will help you quickly connect DroidMind to your AI assistant and run your first commands. Let's get you to that "Aha!" moment. ✨

## Prerequisites

- **Python & UV**: Ensure Python 3.13+ and `uv` are installed. DroidMind uses `uvx` for zero-install IDE integration.
- **AI Assistant with MCP Support**: You'll need an AI assistant that supports the Model Context Protocol (MCP). Examples include Claude Desktop, Cursor, or others listed [here](https://modelcontextprotocol.io/clients).
- **Android Device/Emulator**: Have an Android device connected via USB (with USB debugging enabled) or an emulator running. For network connections, ensure ADB over TCP/IP is set up.
- **ADB**: ADB must be installed and in your system PATH.

## 1. Configure Your IDE to Run DroidMind (via `uvx`)

The quickest way to get started with DroidMind and an IDE (like Cursor) is to let the IDE manage DroidMind using `uvx`. This means you don't need to manually install or run DroidMind first.

Your IDE will look for a configuration file (e.g., `.cursor/mcp.json` for Cursor) to know how to launch MCP servers. You'll add an entry for DroidMind:

```json
{
  "mcpServers": {
    "droidmind": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/hyperb1iss/droidmind",
        "droidmind",
        "--transport",
        "stdio" // The default and preferred mode for most IDE integrations
      ]
    }
  }
}
```

- **`command: "uvx"`**: Tells the IDE to use `uvx`.
- **`"--from", "git+https://github.com/hyperb1iss/droidmind"`**: `uvx` will fetch DroidMind directly from GitHub.
- **`"droidmind"`**: The package name to run.
- **`"--transport", "stdio"`**: Specifies the communication protocol. `stdio` is the default and preferred mode for direct IDE integrations.

Once configured, your IDE should automatically start DroidMind when needed. You typically won't see a separate terminal window for DroidMind, as the IDE manages it in the background.

**For other installation methods (manual, Docker, or running DroidMind separately), see the full [Installation Guide](installation.md).** This Quick Start focuses on the zero-install IDE integration.

## 2. Connect Your AI Assistant to DroidMind

With the `mcp.json` (or equivalent) configured, your AI assistant should automatically discover and connect to DroidMind when it starts up or when you try to use a DroidMind-related tool.

- **No Manual Connection URI Needed (Usually)**: Since the IDE launches DroidMind, the connection is typically handled internally. You usually don't need to manually input an MCP URI.

- **Instructions for Common Clients**:

  - **Cursor**:

    1. Ensure your project has a `.cursor/mcp.json` file with the DroidMind configuration shown in Step 1.
    2. Restart Cursor or open a new project window.
    3. Cursor will automatically start DroidMind on startup, making its tools immediately available.

  - **Claude Desktop**:
    1. Open Claude Desktop settings (from the main application menu).
    2. Go to `Developer` settings.
    3. Click `Edit Config` to open `claude_desktop_config.json`.
    4. Add or modify the `mcpServers` section similar to the example below. Claude Desktop is designed to launch MCP servers itself.
       ```json
       {
         "mcpServers": {
           "droidmind": {
             "command": "uvx",
             "args": [
               "--from",
               "git+https://github.com/hyperb1iss/droidmind",
               "droidmind",
               "--transport",
               "stdio" // Default and preferred for Claude Desktop
             ]
             // Add "workingDirectory": "/path/to/your/droidmind/project" if needed
             // Add "env": { ... } if DroidMind needs specific environment variables
           }
         }
       }
       ```
    5. Restart Claude Desktop. It will attempt to start DroidMind using this configuration.

**Note on SSE Transport (Alternative Method):**
If you need to use SSE transport instead of stdio (for specific use cases or compatibility reasons):

1. You'll need to run the DroidMind server manually with SSE enabled:

   ```bash
   uvx --from git+https://github.com/hyperb1iss/droidmind droidmind --transport sse --host localhost --port 4256
   ```

2. Then configure your AI client to connect to the SSE endpoint (e.g., `sse://localhost:4256/sse`).

This approach requires more manual setup but may be necessary for certain client configurations. See the [Installation Guide](installation.md) for more details on running DroidMind as a standalone server.

After successful connection (which is often automatic with IDE-managed servers), your AI assistant should indicate that DroidMind's tools are available (often indicated by a special icon or prefix in the chat input, or by the AI successfully executing DroidMind commands).

## 3. Your First Commands!

Now for the fun part! Try asking your AI assistant some questions that will leverage DroidMind's capabilities. Here are a few ideas:

- **List Connected Devices**:

  > "Hey AI, can you list all my connected Android devices using DroidMind?"
  > `Response should show a list of devices DroidMind can see via ADB.`

- **Device Properties (if a device is connected)**:
  Replace `emulator-5554` with your actual device serial from the list above.

  > "Tell me about the device `emulator-5554`. What are its properties?"
  > `Response should detail the Android version, model, SDK level, etc., for the specified device.`

- **Take a Screenshot (if a device is connected)**:

  > "Take a screenshot of my currently active Android device."
  > `Your AI assistant should display a screenshot.`

- **Check Storage Space**:

  > "How much storage space is free on `emulator-5554`?"

- **List Installed Apps (Third-Party)**:
  > "What apps have I installed on `emulator-5554`?"

## 🤔 Troubleshooting

- **DroidMind Server Not Starting**: Check your terminal for error messages. Ensure Python and dependencies are correctly installed. If using Docker, check `docker logs droidmind-server`.
- **AI Assistant Can't Connect / Tools Not Working**:
  - Double-check your `mcp.json` (or equivalent) configuration for typos in the command or arguments.
  - Ensure `uv` is installed and accessible in your system's PATH (as `uvx` relies on `uv`).
  - If using `sse` transport, ensure the specified port (e.g., 4256) is not being used by another application.
  - Check your IDE's output logs or console for any error messages related to starting the MCP server.
- **No Devices Listed (when DroidMind seems to be running)**:
  - Ensure your Android device has USB debugging enabled and is authorized on your computer.
  - Run `adb devices` in a separate terminal to see if ADB itself can see your device. If not, DroidMind won't be able to either.
  - If using Docker, refer to the [Docker Guide's section on ADB connectivity](docker.md#connecting-to-adb-devices), as this is often the trickiest part.

## 🎉 Congratulations!

You've successfully configured your IDE to run DroidMind on-demand and executed your first commands! This is just the beginning. Explore the [User Manual](user_manual/index.md) and [MCP Reference](mcp-reference.md) to discover the full range of what you can achieve with DroidMind.

Now, go make your Android workflow more brilliant! 💫

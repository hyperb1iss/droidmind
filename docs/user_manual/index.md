# User Manual

Welcome to the DroidMind User Manual! This section provides a comprehensive guide to understanding and utilizing DroidMind's features through your AI assistant.

Our goal is to empower you to interact with your Android devices seamlessly using natural language. Whether you're debugging apps, managing files, or analyzing system performance, DroidMind, guided by your AI, is here to assist.

## 📖 Chapters

Navigate through the chapters to learn about specific DroidMind functionalities:

- **[1. Connecting to Devices](connecting_devices.md)**

  - Listing available devices
  - Connecting via USB
  - Connecting via TCP/IP (Wi-Fi)
  - Understanding device serials
  - Disconnecting devices

- **[2. Device Information & Diagnostics](device_diagnostics.md)**

  - Retrieving device properties (model, Android version, SDK, etc.)
  - Capturing screenshots
  - Working with Logcat (device logs, app-specific logs)
  - Understanding ANR & Crash Logs
  - Analyzing battery statistics
  - Generating bug reports
  - Dumping heap for memory analysis

- **[3. File System Operations](file_system.md)**

  - Listing directory contents
  - Reading file contents
  - Writing content to files
  - Pushing (uploading) files to a device
  - Pulling (downloading) files from a device
  - Creating directories
  - Deleting files and directories
  - Checking if a file or directory exists
  - Getting file/directory statistics (size, permissions, modified date)

- **[4. Application Management](app_management.md)**

  - Listing installed packages (all or third-party)
  - Installing applications (APKs)
  - Uninstalling applications (with or without data)
  - Starting applications (default or specific activity)
  - Stopping applications (force stop)
  - Clearing application data and cache
  - Getting detailed app information (version, path, user ID)
  - Inspecting app manifests
  - Retrieving app permissions
  - Listing app activities

- **[5. Shell Command Execution](shell_commands.md)**

  - Running shell commands on a device
  - Understanding command risk assessment
  - Output handling (truncation, line limits)
  - Security considerations for shell commands

- **[6. UI Automation](ui_automation.md)**

  - Tapping on screen coordinates
  - Performing swipe gestures
  - Inputting text into fields
  - Pressing hardware/software keys (Home, Back, Volume, etc.)
  - Starting activities using intents (with extras)

- **[7. Device Management Actions](device_management_actions.md)**

  - Rebooting a device (normal, recovery, bootloader)

- **[8. Security Considerations](security.md)**

  - Understanding DroidMind's security model
  - Command validation and sanitization
  - Risk levels and user confirmation for high-risk operations

- **[9. Example AI Assistant Queries](example_queries.md)**
  - Practical examples for common tasks across all DroidMind features.

## 💡 Tips for Effective Use

- **Be Specific**: When talking to your AI, provide clear details like device serials (if you have multiple) and full paths for files.
- **Iterate**: If the first command doesn't do exactly what you want, refine your request. AI assistants learn from interaction.
- **Use Serial Numbers**: If you have multiple devices connected, always specify the device serial number in your requests to avoid ambiguity.
- **Check Output**: Pay attention to the output DroidMind provides via your AI assistant. It often contains important confirmations or error messages.

Let's begin your journey to mastering Android with DroidMind and AI! 💫

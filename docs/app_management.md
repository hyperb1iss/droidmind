# App Management in DroidMind

<div align="center">

![App Management](https://via.placeholder.com/150x150.png?text=App+Management)

**Control and monitor Android applications via MCP**

</div>

## 📱 Feature Overview

The App Management module in DroidMind provides comprehensive tools and resources for controlling and monitoring Android applications. It enables AI assistants to install, uninstall, start, stop, and manage app data, as well as access app-specific information and logs.

## 🧰 MCP Tools

### Installation and Removal

| Tool | Description | Parameters |
|------|-------------|------------|
| `install_app` | Install an APK on the device | `serial`, `apk_path`, `reinstall` (optional), `grant_permissions` (optional) |
| `uninstall_app` | Remove an app from the device | `serial`, `package`, `keep_data` (optional) |

### App Lifecycle

| Tool | Description | Parameters |
|------|-------------|------------|
| `start_app` | Launch an app | `serial`, `package`, `activity` (optional) |
| `stop_app` | Force stop an app | `serial`, `package` |
| `clear_app_data` | Clear app data and cache | `serial`, `package` |

### App Discovery

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_packages` | List installed packages | `serial`, `include_system_apps` (optional) |

## 📁 MCP Resources

### App Information

| Resource | Description | Example Use |
|----------|-------------|-------------|
| `fs://{serial}/app/{package}/manifest` | App manifest | "Show me the permissions my app is requesting" |
| `fs://{serial}/app/{package}/data` | App data directory listing | "What files has my app created?" |
| `fs://{serial}/app/{package}/shared_prefs` | App preferences | "Show me the saved preferences in my app" |
| `logs://{serial}/app/{package}` | App-specific logs | "What errors is my app generating?" |

## 💎 Usage Examples

### Installing an APK

```python
result = await install_app(
    serial="emulator-5554",
    apk_path="/path/to/app.apk",
    reinstall=True,
    grant_permissions=True
)
```

### Managing App Lifecycle

```python
# Start an app
await start_app(serial="emulator-5554", package="com.example.app")

# Stop an app
await stop_app(serial="emulator-5554", package="com.example.app")

# Clear app data
await clear_app_data(serial="emulator-5554", package="com.example.app")
```

### Accessing App Resources

```python
# Get app manifest
manifest = await app_manifest(serial="emulator-5554", package="com.example.app")

# Get app shared preferences
prefs = await app_shared_prefs(serial="emulator-5554", package="com.example.app")

# Get app-specific logs
logs = await app_logs(serial="emulator-5554", package="com.example.app")
```

## 📌 Implementation Notes

- App data access requires the app to be debuggable or the device to be rooted
- Shared preferences are accessible only if the app is debuggable or the device is rooted
- App manifest extraction uses multiple fallback methods:
  1. `aapt dump xmltree` (if available)
  2. `aapt2 dump xmltree` (if available)
  3. `dumpsys package` (fallback)
- App-specific logs are retrieved using either UID filtering or package name grep

## 🔒 Security Considerations

- All package names and paths are sanitized to prevent command injection
- High-risk operations like uninstalling apps require explicit confirmation
- App data access respects Android's permission model and security boundaries

## 🧠 AI Assistant Prompts

When working with app management, try these prompts with your AI assistant:

- "Install the APK from Downloads/my-app.apk on my device"
- "Uninstall Facebook from my phone but keep my data"
- "Start the calculator app"
- "Stop all instances of Chrome"
- "Clear data for Instagram"
- "Show me all the permissions that TikTok is requesting"
- "What shared preferences has my game saved?"
- "Show me recent crash logs for my app"

## 🔄 Future Enhancements

- App backup and restore functionality
- APK extraction and analysis
- Runtime permission management
- App usage statistics
- App network traffic monitoring
- Storage usage analysis 
# Chapter 4: Application Management

DroidMind equips your AI assistant with a comprehensive suite of tools for managing applications on your Android devices. This chapter details how to list installed packages, install and uninstall apps, control their lifecycle (start, stop, clear data), and inspect various application details like manifests, permissions, and activities.

Remember to replace `emulator-5554` or `your_device_serial` with your target device's serial, and use correct package names (e.g., `com.example.myapp`) in your queries.

## 4.1 Listing Installed Packages

Discover what applications are installed on a device.

**How to ask your AI assistant:**

> "List all installed third-party apps on `emulator-5554`."
> "Show me all packages, including system apps, on `your_device_serial`."
> "What applications are on `emulator-5554`?"

**Expected DroidMind Action:**

DroidMind will use the `list_packages` tool.

- `include_system_apps` (optional, default `False`): Set to `True` to include system applications in the list. Otherwise, only third-party (user-installed) apps are shown.

**Example Response from AI:**

```
Okay, here are the installed third-party packages on `emulator-5554`:

# Installed Packages

| Package Name          | APK Path                                      |
|-----------------------|-----------------------------------------------|
| `com.example.app1`    | `/data/app/~~random_string==/com.example.app1-another_random==/base.apk` |
| `com.example.another` | `/data/app/~~different_string==/com.example.another-more_random==/base.apk` |
| `org.thirdparty.util` | `/data/app/~~and_another==/org.thirdparty.util-random_again==/base.apk` |

```

## 4.2 Installing Applications (APKs)

Your AI assistant can install applications using their APK files. The APK file must be accessible from the machine where DroidMind is running.

**How to ask your AI assistant:**

> "Install the app from `/Users/bliss/Downloads/new_app.apk` on `emulator-5554`."
> "On `your_device_serial`, install `C:\APKs\utility.apk`, reinstall if it exists, and grant all permissions."

**Important:** The `apk_path` you specify must be a local path on the machine where the DroidMind server process is running.

**Expected DroidMind Action:**

DroidMind will use the `install_app` tool.

- `apk_path`: The local path to the APK file.
- `reinstall` (optional, default `False`): Set to `True` to allow reinstallation (equivalent to `adb install -r`).
- `grant_permissions` (optional, default `True`): Set to `True` to grant all declared permissions at install time (equivalent to `adb install -g`).

**Example Response from AI:**

```
I'm installing `/Users/bliss/Downloads/new_app.apk` on `emulator-5554`...
✅ Successfully installed APK on device emulator-5554
```

Or if it failed:

```
❌ Failed to install APK: INSTALL_FAILED_INSUFFICIENT_STORAGE
```

## 4.3 Uninstalling Applications

Remove applications from a device.

**How to ask your AI assistant:**

> "Uninstall the package `com.example.oldapp` from `emulator-5554`."
> "Remove `com.thirdparty.bloatware` from `your_device_serial` but keep its data."

**Expected DroidMind Action:**

DroidMind will use the `uninstall_app` tool.

- `package`: The package name of the app to uninstall.
- `keep_data` (optional, default `False`): Set to `True` to keep the app's data and cache directories (equivalent to `adb uninstall -k`).

**Example Response from AI:**

```
Uninstalling package `com.example.oldapp` from `emulator-5554`...
✅ Successfully uninstalled `com.example.oldapp` from device `emulator-5554`
```

Or, if keeping data:

```
✅ Successfully uninstalled `com.thirdparty.bloatware` from device `your_device_serial` (keeping app data)
```

## 4.4 Starting Applications

Launch an application on the device. You can start its default main activity or specify a particular activity.

**How to ask your AI assistant:**

> "Start the app `com.example.myapp` on `emulator-5554`."
> "Launch the activity `.ui.SettingsActivity` for package `com.example.myapp` on `your_device_serial`."
> "Open `com.android.settings` on `emulator-5554`."

**Expected DroidMind Action:**

DroidMind will use the `start_app` tool.

- `package`: The package name of the app.
- `activity` (optional): The specific activity to start. If empty, DroidMind attempts to launch the default main activity. Activity names can be relative (e.g., `.MainActivity`) or fully qualified (e.g., `com.example.myapp.MainActivity`).

**Example Response from AI:**

```
Starting app `com.example.myapp` on `emulator-5554`...
✅ Starting: Intent { act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] cmp=com.example.myapp/.MainActivity }
```

If an error occurs (e.g., app not found, activity not found):

```
❌ Error: Activity not started, component specified did not match any known component
```

## 4.5 Stopping Applications (Force Stop)

Forcefully stop a running application.

**How to ask your AI assistant:**

> "Stop the app `com.example.myapp` on `emulator-5554`."
> "Force stop `com.thirdparty.service` on `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `stop_app` tool.

**Example Response from AI:**

```
Stopping app `com.example.myapp` on `emulator-5554`...
✅ Force stopped `com.example.myapp`
```

## 4.6 Clearing Application Data and Cache

Reset an application to its default state by clearing its data and cache.

**How to ask your AI assistant:**

> "Clear the app data for `com.example.myapp` on `emulator-5554`."
> "Reset `com.example.anotherapp` on `your_device_serial` by clearing its data."

**Expected DroidMind Action:**

DroidMind will use the `clear_app_data` tool.

**Example Response from AI:**

```
Clearing data for app `com.example.myapp` on `emulator-5554`...
✅ Successfully cleared data for package `com.example.myapp`
```

If it fails:

```
❌ Failed to clear data for package `com.example.myapp`: Package not found
```

## 4.7 Getting Detailed App Information

Retrieve a summary of information about a specific installed application.

**How to ask your AI assistant:**

> "Get detailed information about the app `com.android.settings` on `emulator-5554`."
> "Show me info for `com.example.myapp` on `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `get_app_info` tool.

**Example Response from AI:**

```
# App Information for com.android.settings

- **Version**: 12.0
- **Install Path**: /system/priv-app/SettingsProvider/SettingsProvider.apk
- **First Install**: 2022-01-01 10:00:00
- **User ID**: 1000
- **App Size**: 5.3M (from du -sh)
- **Status**: Running

## Permissions

- android.permission.ACCESS_NETWORK_STATE
- android.permission.WRITE_SETTINGS
...
```

## 4.8 Inspecting App Manifests

The `AndroidManifest.xml` file contains essential information about an app, including its components, permissions, and features. DroidMind can retrieve and parse this for you.

**How to ask your AI assistant:**

> "Show me the manifest for `com.example.myapp` on `emulator-5554`."
> "Get the AndroidManifest for `com.android.settings` on `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `get_app_manifest` tool.

**Example Response from AI:**

```
# App Manifest for com.example.myapp

## Package Information

- **Version Code**: 101
- **Version Name**: 1.0.1
- **Min SDK**: 23
- **Target SDK**: 33
- **Install Path**: /data/app/~~...==/com.example.myapp-...==/base.apk
- **First Install**: 2023-01-15 10:00:00
- **User ID**: 10123

## Permissions

### Declared Permissions

No declared permissions.

### Requested Permissions

- `android.permission.INTERNET`
- `android.permission.ACCESS_FINE_LOCATION`

## Components

### Activities

- `com.example.myapp/.MainActivity`
  Intent Filters:
  - Action: android.intent.action.MAIN
  - Category: android.intent.category.LAUNCHER
- `com.example.myapp/.SettingsActivity`

### Services

- `com.example.myapp/.background.MyBackgroundService`

### Content Providers

No Content Providers found.

### Broadcast Receivers

- `com.example.myapp/.receivers.BootCompletedReceiver`
  Intent Filters:
  - Action: android.intent.action.BOOT_COMPLETED
```

## 4.9 Retrieving App Permissions

Focus specifically on the permissions declared and requested by an application, including their runtime status.

**How to ask your AI assistant:**

> "What permissions does `com.example.myapp` use on `emulator-5554`?"
> "Show the permission details for `com.android.camera` on `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `get_app_permissions` tool.

**Example Response from AI:**

```
# Permissions for com.example.myapp

## Permissions

### Declared Permissions
No declared permissions.

### Requested Permissions
- `android.permission.INTERNET`
- `android.permission.ACCESS_FINE_LOCATION`

## Runtime Permission Status

```

runtime permissions:
android.permission.ACCESS_FINE_LOCATION: granted=true, flags=[ GRANTED_BY_DEFAULT|REVIEW_REQUIRED ]

```
This app has requested Internet and Fine Location access. Fine Location is currently granted.
```

## 4.10 Listing App Activities

List all the activities defined within an application and identify the main launchable activity.

**How to ask your AI assistant:**

> "List the activities for `com.example.myapp` on `emulator-5554`."
> "What are the defined activities in `com.android.settings` on `your_device_serial`?"

**Expected DroidMind Action:**

DroidMind will use the `get_app_activities` tool.

**Example Response from AI:**

```
# Activities for com.example.myapp

Found 2 activities:

- `com.example.myapp/.MainActivity`
  Intent Filters:
  - Action: android.intent.action.MAIN
  - Category: android.intent.category.LAUNCHER
- `com.example.myapp/.SettingsActivity`

## Main Activity

```

com.example.myapp/.MainActivity

```

The main launchable activity is `.MainActivity`.
```

---

Up next, we'll cover how to execute general shell commands on your device in **[Chapter 5: Shell Command Execution](shell_commands.md)**.

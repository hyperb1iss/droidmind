# Chapter 2: Device Information & Diagnostics

Once your Android device is connected, DroidMind, through your AI assistant, can provide a wealth of information about the device and help diagnose issues. This chapter covers retrieving properties, capturing visuals, and diving into various logs and diagnostic reports.

Remember to replace `emulator-5554` or `your_device_serial` with the actual serial of your target device in the example queries.

## 2.1 Retrieving Device Properties

You can ask your AI assistant to fetch detailed properties of a connected device. This includes information like the device model, brand, Android version, SDK level, build number, and much more.

**How to ask your AI assistant:**

> "Tell me about the device `emulator-5554`."
> "What are the properties of `your_device_serial`?"
> "Get device info for `emulator-5554`."

**Expected DroidMind Action:**

DroidMind will use the `device_properties` tool.

**Example Response from AI:**

````
# Device Properties for emulator-5554

**Model**: sdk_gphone64_x86_64
**Brand**: google
**Android Version**: 12
**SDK Level**: 31
**Build Number**: SE1A.220601.001

## All Properties

```properties
[ro.product.model]: [sdk_gphone64_x86_64]
[ro.product.brand]: [google]
[ro.build.version.release]: [12]
[ro.build.version.sdk]: [31]
[ro.build.display.id]: [SE1A.220601.001]
[ro.product.manufacturer]: [Google]
[persist.sys.timezone]: [America/Los_Angeles]
...
(many more properties)
````

This information is invaluable for understanding the device's hardware and software configuration, which is often crucial for debugging.

## 2.2 Capturing Screenshots

A picture is worth a thousand words, especially in UI debugging. DroidMind can capture a screenshot of the device's current display.

**How to ask your AI assistant:**

> "Take a screenshot of `emulator-5554`."
> "Capture the current screen of `your_device_serial`."
> "Show me what's on the screen of `emulator-5554`."

**Expected DroidMind Action:**

DroidMind will use the `screenshot` tool. The AI assistant will then typically display the image.

**Example Response from AI:**

```
Okay, here is the screenshot from emulator-5554:

[Image data would be displayed here by the AI assistant]

I've captured the screen. The image shows the device's home screen with several app icons.
```

Screenshots are returned as JPEG images by default to save space, with a quality setting of 75. You can specify quality if needed, though most users won't need to.

## 2.3 Working with Logcat (Device Logs)

Logcat is Android's logging system, providing a stream of messages from the system and applications. DroidMind allows you to fetch these logs.

### 2.3.1 General Device Logcat

Retrieve recent general logs from various buffers on the device.

**How to ask your AI assistant:**

> "Show me the last 500 logcat lines from `emulator-5554`."
> "Get the device logs for `your_device_serial`, focusing on the 'crash' buffer."
> "Fetch logcat from `emulator-5554` with the filter 'ActivityManager:I \*:S' for the last 200 lines."

**Expected DroidMind Action:**

DroidMind will use the `device_logcat` tool. You can specify:

- `lines`: Number of recent lines (default: 1000).
- `filter_expr`: ADB logcat filter expression (e.g., "MyAppTag:V \*:S").
- `buffer`: Log buffer (e.g., `main`, `system`, `crash`, `radio`, `events`; default: `main`).
- `format_type`: Log output format (e.g., `threadtime`, `brief`; default: `threadtime`).
- `max_size`: Max characters for the output (default: 100KB).

**Example Response from AI:**

````
# Device Logcat Output 📱

## Last 500 Lines from 'main' Buffer

```log
01-15 10:30:01.123  1234  5678 I ActivityManager: Displayed com.example.app/.MainActivity: +100ms
01-15 10:30:01.456  8765  4321 D MyAppTag: User clicked the login button
...
````

```

### 2.3.2 App-Specific Logs

Filter logcat output for a specific application package.

**How to ask your AI assistant:**

> "Get logs for the app `com.example.myapp` on `emulator-5554`."
> "Show me the last 200 log entries for `com.example.anotherapp` on `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `app_logs` tool.
*   `package`: The package name of the app.
*   `lines`: Number of recent lines to fetch (default: 1000).

**Example Response from AI:**

```

# Logs for App 'com.example.myapp' 📱

## Recent Log Entries

```log
01-15 10:32:05.678  8765  4321 D com.example.myapp: Login successful for user 'bliss'
01-15 10:32:05.999  8765  4322 I com.example.myapp.NetworkService: Data sync initiated.
...
```

If no logs are found, it might mean the app isn't running or isn't generating logs with that package name identifier.

```

## 2.4 Understanding ANR & Crash Logs

When an app freezes or crashes, Android generates specific diagnostic logs.

### 2.4.1 Application Not Responding (ANR) Traces

ANRs occur when the UI thread is blocked for too long.

**How to ask your AI assistant:**

> "Are there any ANR traces on `emulator-5554`?"
> "Show me the latest ANR logs from `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `device_anr_logs` tool.

**Example Response from AI:**

```

# Application Not Responding (ANR) Traces

## ANR Trace #1: anr_2023-01-15-10-35-00-123.txt

**File Info:** `-rw-rw---- 1 system system 123456 2023-01-15 10:35 /data/anr/anr_2023-01-15-10-35-00-123.txt`

```
----- pid 8765 at 2023-01-15 10:35:00 -----
Cmd line: com.example.myapp

DALVIK THREADS (15):
"main" prio=5 tid=1 Blocked
  | group="main" sCount=1 dsCount=0 flags=1 obj=0x12c08a00 self=0xb4800200
  | sysTid=8765 nice=0 cgrp=top-app sched=0/0 handle=0xb73ff4f4
  | state=S schedstat=( 0 0 0 ) utm=93 stm=42 core=0 HZ=100
  | stack=0xbe227000-0xbe229000 stackSize=8MB
  | held mutexes= "mutator lock"(shared held)
  at com.example.myapp.HeavyComputation.perform(HeavyComputation.java:25)
  - waiting to lock <0x09a8f2c8> (a java.lang.Object) held by thread tid=10
...
```

I found one recent ANR trace for `com.example.myapp`. It seems the main thread was blocked waiting for a lock.

```

### 2.4.2 Application Crash Logs

These logs provide information about app crashes, including tombstones (native crashes) and Java crash reports.

**How to ask your AI assistant:**

> "Check for any application crash logs on `emulator-5554`."
> "Show me the latest crash reports from `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `device_crash_logs` tool.

**Example Response from AI:**

```

# Android Application Crash Reports

## System Tombstones

Recent system crash tombstones:

### Tombstone #1: tombstone_00

```
*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***
Build fingerprint: 'google/sdk_gphone64_x86_64/generic_x86_64:12/SE1A.220601.001/8804948:userdebug/dev-keys'
Revision: '0'
ABI: 'x86_64'
pid: 9012, tid: 9034, name: Thread-2  >>> com.example.crasher <<<
...
```

## Dropbox Crash Reports

No crash reports found in dropbox.

## Recent Crashes in Logcat

```
01-15 10:40:15.123  9012  9034 E AndroidRuntime: FATAL EXCEPTION: Thread-2
01-15 10:40:15.123  9012  9034 E AndroidRuntime: Process: com.example.crasher, PID: 9012
01-15 10:40:15.123  9012  9034 E AndroidRuntime: java.lang.NullPointerException: Attempt to invoke virtual method 'java.lang.String java.lang.Object.toString()' on a null object reference
...
```

I found a tombstone and a recent Java crash in logcat for `com.example.crasher`.

```

## 2.5 Analyzing Battery Statistics

Understand how power is being consumed on the device.

**How to ask your AI assistant:**

> "Analyze the battery usage on `emulator-5554`."
> "Show me the battery stats for `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `device_battery_stats` tool.

**Example Response from AI:**

```

# Battery Statistics Report 🔋

## Current Battery Status

```
Current Battery Service state:
  AC powered: false
  USB powered: true
  Wireless powered: false
  Max charging current: 0
  Max charging voltage: 0
  Charge counter: 0
  status: 2
  health: 2
  present: true
  level: 75
  scale: 100
  voltage: 4200
  temperature: 250
  technology: Li-ion
```

### Key Metrics

- **Battery Level:** 75%
- **Temperature:** 25.0°C
- **Health:** Good

## Battery History and Usage

...
(Details on discharge history and power consumption)

```
This can help identify apps or processes that are draining the battery.

## 2.6 Generating Bug Reports

A bug report is a comprehensive archive of diagnostic information, including system logs, device state, running processes, and more. It's very useful for in-depth debugging.

**How to ask your AI assistant:**

> "Generate a bug report for `emulator-5554`."
> "Capture a bug report from `your_device_serial` and include screenshots."
> "Create a bug report for `emulator-5554`, save it to `/tmp/my_bug_report.zip`."

**Expected DroidMind Action:**

DroidMind will use the `capture_bugreport` tool.
*   `output_path` (optional): Local path on the DroidMind server machine to save the bug report ZIP file. If empty, a summary is returned and the file is saved to a temporary location.
*   `include_screenshots` (optional, default `True`): Whether to include screenshots.
*   `timeout_seconds` (optional, default `300`): How long to wait for the bug report.

**Example Response from AI (if `output_path` is provided):**

```

Okay, I'm capturing the bug report from emulator-5554. This might take a few minutes...
...
Bug report saved to: /tmp/my_bug_report.zip (15.23 MB)

```

**Example Response from AI (if `output_path` is NOT provided):**

```

Okay, I'm capturing the bug report...
...

# Bug Report for emulator-5554

Temporary file saved to: `/tmp/droidmind_bugreport_XXXXXX/bugreport_emulator-5554.zip` (15.23 MB)

## Bug Report Contents

```
  Length      Date    Time    Name
---------  ---------- -----   ----
  1234567  01-15-2023 10:50   bugreport-emulator-5554-2023-01-15-10-50-00.txt
    56789  01-15-2023 10:50   screenshot.png
...
```

To extract specific information from this bug report, you can use:

- `unzip -o /tmp/droidmind_bugreport_XXXXXX/bugreport_emulator-5554.zip -d <extract_dir>` to extract all files
- `unzip -o /tmp/droidmind_bugreport_XXXXXX/bugreport_emulator-5554.zip bugreport-*.txt -d <extract_dir>` to extract just the main report

Note: This is a temporary file that may be cleaned up by the system later.

```

Bug reports are large and complex. Your AI assistant might be able to help you analyze specific parts of it if you extract them.

## 2.7 Dumping Heap for Memory Analysis

Heap dumps are snapshots of an app's memory, useful for diagnosing memory leaks and understanding object allocation.

**How to ask your AI assistant:**

> "Dump the Java heap for the app `com.example.memoryhog` on `emulator-5554`."
> "Capture a native heap dump for process ID `12345` on `your_device_serial` and save it to `/tmp/native_heap.hprof`."

**Expected DroidMind Action:**

DroidMind will use the `dump_heap` tool.
*   `package_or_pid`: The app package name or its Process ID (PID).
*   `output_path` (optional): Local path on the DroidMind server machine to save the heap dump file. If empty, a default temporary location is used.
*   `native` (optional, default `False`): Whether to capture a native heap dump (C/C++) instead of a Java heap dump. Native dumps often require root.
*   `timeout_seconds` (optional, default `120`): How long to wait.

**Example Response from AI (for Java heap dump):**

```

Capturing Java heap dump for process com.example.memoryhog...
...
Java heap dump saved to: /tmp/droidmind_heapdump_XXXXXX/com.example.memoryhog_java_heap_20230115_110530.hprof (5.75 MB)

To analyze this Java heap dump:

1. Convert the file using: `hprof-conv /tmp/droidmind_heapdump_XXXXXX/com.example.memoryhog_java_heap_20230115_110530.hprof converted.hprof`
2. Open in Android Studio's Memory Profiler
3. Or use Eclipse Memory Analyzer (MAT) after conversion

```

Heap dump analysis is a specialized task. The AI can guide you on how to use tools like Android Studio's Profiler or MAT to analyze the `.hprof` file.

---

Next, we'll learn how to manage files and directories on your devices in **[Chapter 3: File System Operations](file_system.md)**.
```

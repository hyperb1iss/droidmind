# Chapter 3: File System Operations

DroidMind enables your AI assistant to interact with the file system of your connected Android devices. This chapter covers listing directory contents, reading and writing files, transferring files between your host machine and the device, managing files and directories, and retrieving file statistics.

Remember to replace `emulator-5554` or `your_device_serial` with your target device's serial, and use appropriate paths in your queries.

## 3.1 Listing Directory Contents

You can explore the file system by asking your AI to list the contents of a specific directory on the device.

**How to ask your AI assistant:**

> "List the contents of `/sdcard/Download/` on `emulator-5554`."
> "Show me the files and folders in `/data/local/tmp` on `your_device_serial`."
> "What's inside the `/sdcard/Pictures` directory on `emulator-5554`?"

**Expected DroidMind Action:**

DroidMind will use the `list_directory` tool with the specified `path`.

**Example Response from AI:**

```
Okay, here are the contents of `/sdcard/Download/` on `emulator-5554`:

# 📁 Directory: /sdcard/Download/

**2 files, 1 directories**

## Directories

📁 `MySubFolder`

## Files

📄 `archive.zip` (1.2 MB)
📄 `document.pdf` (512 KB)
```

This output helps you understand the structure and contents of directories on your device.

## 3.2 Reading File Contents

Your AI assistant can read the content of text-based files stored on the device. For very large files or binary files, it's better to pull them to your computer first (see Section 3.5).

**How to ask your AI assistant:**

> "Read the file `/sdcard/Download/MySubFolder/config.txt` on `emulator-5554`."
> "Show me the content of `/data/local/tmp/output.log` on `your_device_serial`."
> "What does `/sdcard/my_notes.txt` on `emulator-5554` say?"

**Expected DroidMind Action:**

DroidMind will use the `read_file` tool. By default, there's a `max_size` limit (around 100KB) to prevent overwhelming the AI with too much data. If a file exceeds this, DroidMind will return an error suggesting to use `pull_file`.

**Example Response from AI (for a small text file):**

````
# File Contents: /sdcard/Download/MySubFolder/config.txt

```text
# Configuration File
ENABLE_FEATURE_X=true
API_ENDPOINT=https://api.example.com
DEBUG_MODE=false
````

The file `config.txt` contains these configuration settings.

```

**Example Response from AI (if file is too large):**

```

# ⚠️ File Too Large

The file `/sdcard/Download/large_log.zip` is 5.7 MB, which exceeds the maximum size limit of 100.0 KB.

Use `pull_file` to download this file to your local machine instead.

````

## 3.3 Writing Content to Files

DroidMind can write text content to new or existing files on the device. This is useful for creating configuration files, scripts, or simple text notes directly on the device via your AI.

**How to ask your AI assistant:**

> "Create a file named `hello.txt` in `/sdcard/` on `emulator-5554` with the content 'Hello, DroidMind!'."
> "Write 'Test data' to `/data/local/tmp/test.log` on `your_device_serial`."
> "On `emulator-5554`, save the following text to `/sdcard/notes/meeting_summary.md`:
> ```markdown
> # Meeting Summary - 2023-01-15
> - Discussed project milestones
> - Agreed on next steps
> ```"

**Expected DroidMind Action:**

DroidMind will use the `write_file` tool, providing the `device_path` and `content`.

**Example Response from AI:**

````

# ✨ File Written Successfully

- **Path**: /sdcard/hello.txt
- **Size**: 16 bytes
- **Device**: emulator-5554

The content has been saved to the file.

```

If the parent directory doesn't exist, DroidMind will attempt to create it first.

## 3.4 Pushing (Uploading) Files to a Device

You can upload files from the machine where DroidMind is running to a connected Android device.

**How to ask your AI assistant:**

> "Upload the file `/Users/bliss/Desktop/my_app.apk` to `/sdcard/Download/` on `emulator-5554`."
> "Push `C:\Projects\config.json` to `/data/local/tmp/app_config.json` on `your_device_serial`."

**Important:** The `local_path` you specify must be accessible from the machine where the DroidMind server process is running.

**Expected DroidMind Action:**

DroidMind will use the `push_file` tool with `local_path` and `device_path`.

**Example Response from AI:**

```

# ✅ File Uploaded Successfully

The file `my_app.apk` (12.5 MB) has been uploaded to `/sdcard/Download/` on device emulator-5554.

**Details**: 1 file pushed. 2.5 MB/s (12533120 bytes in 4.780s)

```

## 3.5 Pulling (Downloading) Files from a Device

Download files from an Android device to the machine where DroidMind is running.

**How to ask your AI assistant:**

> "Download the file `/sdcard/DCIM/Camera/IMG_20230115.jpg` from `emulator-5554` to `/Users/bliss/Pictures/`."
> "Pull `/data/anr/anr_latest.txt` from `your_device_serial` and save it as `C:\Logs\device_anr.txt`."

**Important:** The `local_path` you specify will be on the machine where the DroidMind server process is running.

**Expected DroidMind Action:**

DroidMind will use the `pull_file` tool with `device_path` and `local_path`.

**Example Response from AI:**

```

# ✅ File Downloaded Successfully

The file `IMG_20230115.jpg` (3.1 MB) has been downloaded from device emulator-5554 to `/Users/bliss/Pictures/IMG_20230115.jpg`.

**Details**: 1 file pulled. 1.8 MB/s (3145728 bytes in 1.690s)

```
If only a directory is provided for `local_path`, the file will be saved in that directory with its original name.

## 3.6 Creating Directories

Your AI assistant can create new directories on the device's file system.

**How to ask your AI assistant:**

> "Create a directory named `MyProjectData` in `/sdcard/` on `emulator-5554`."
> "Make a new folder `/data/local/tmp/my_tests/results` on `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `create_directory` tool. It can create parent directories if they don't exist (like `mkdir -p`).

**Example Response from AI:**

```

Okay, I've created the directory `/sdcard/MyProjectData` on `emulator-5554`.
(DroidMind internal response: Successfully created directory /sdcard/MyProjectData)

```

## 3.7 Deleting Files and Directories

DroidMind can delete files or directories (including their contents recursively) from the device.

**How to ask your AI assistant:**

> "Delete the file `/sdcard/Download/old_archive.zip` from `emulator-5554`."
> "Remove the directory `/data/local/tmp/test_output` and all its contents from `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `delete_file` tool. It will use `rm -rf` for directories, so be cautious.

**Example Response from AI:**

```

I have deleted the file `/sdcard/Download/old_archive.zip` from `emulator-5554`.
(DroidMind internal response: Successfully deleted /sdcard/Download/old_archive.zip)

```

## 3.8 Checking if a File or Directory Exists

You can verify the existence of a file or directory at a specific path.

**How to ask your AI assistant:**

> "Does the file `/sdcard/config.xml` exist on `emulator-5554`?"
> "Check if `/data/local/tmp/my_app_data` is present on `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `file_exists` tool.

**Example Response from AI:**

```

Yes, the file `/sdcard/config.xml` exists on `emulator-5554`.
(DroidMind internal response: True)

```
Or:
```

No, the directory `/data/local/tmp/my_app_data` does not exist on `your_device_serial`.
(DroidMind internal response: False)

```

## 3.9 Getting File/Directory Statistics

Retrieve detailed information about a file or directory, such as its type, size, permissions, and modification date.

**How to ask your AI assistant:**

> "Get the stats for `/sdcard/DCIM/Camera/IMG_20230115.jpg` on `emulator-5554`."
> "Show me the details of the directory `/sdcard/Download` on `your_device_serial`."

**Expected DroidMind Action:**

DroidMind will use the `file_stats` tool.

**Example Response from AI (for a file):**

```

# File Statistics: /sdcard/DCIM/Camera/IMG_20230115.jpg

- **Type**: File
- **Name**: IMG_20230115.jpg
- **Size**: 3.1 MB
- **Owner**: shell:shell
- **Permissions**: -rw-rw---- (read/write for owner/group)
- **Modified**: Jan 15 10:30

```

**Example Response from AI (for a directory):**

```

# Directory Statistics: /sdcard/Download

- **Type**: Directory
- **Name**: Download
- **Size**: 4.0 KB (size of directory entry, not contents)
- **Owner**: shell:shell
- **Permissions**: drwxrwx--x (directory, full perms for owner/group, execute for others)
- **Modified**: Jan 14 15:20
- **Files**: 5
- **Subdirectories**: 2

```

This information helps in understanding file system usage and managing storage.

---

In the next chapter, we'll explore how DroidMind can manage applications on your device: **[Chapter 4: Application Management](app_management.md)**.
```

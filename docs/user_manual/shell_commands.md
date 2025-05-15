# Chapter 5: Shell Command Execution

DroidMind allows your AI assistant to run shell commands directly on your connected Android devices. This provides powerful, low-level access but also comes with responsibilities. This chapter explains how to use this feature, DroidMind's built-in security measures, and how output is handled.

Always exercise caution when running shell commands, especially those that modify the system. DroidMind includes safeguards, but understanding the commands you're asking your AI to run is crucial.

## 5.1 Running Shell Commands

Your AI assistant can instruct DroidMind to execute a standard ADB shell command on a specified device.

**How to ask your AI assistant:**

> "Run the command `ls -l /sdcard/` on `emulator-5554`."
> "Execute `dumpsys battery` on `your_device_serial`."
> "On `emulator-5554`, run `ps -A | grep myapp` and show me the first 10 lines."

**Expected DroidMind Action:**

DroidMind will use the `shell_command` tool.

- `serial`: The target device's serial number.
- `command`: The shell command to execute.
- `max_lines` (optional, default `1000`): Limits the number of lines returned. Positive for first N lines, negative for last N lines. `None` for unlimited (not recommended for large outputs).
- `max_size` (optional, default `100000` characters, approx 100KB): Limits the total size of the output returned.

**Example Response from AI (for `ls -l /sdcard/`):**

```
# Command Output from emulator-5554

```

-rw-rw---- 1 u0_a123 sdcard_rw 1024 2023-01-15 10:00 myfile.txt
drwxrwx--x 1 u0_a123 sdcard_rw 0 2023-01-14 09:00 Download
drwxrwx--x 1 u0_a123 sdcard_rw 0 2023-01-13 08:00 Pictures
... (output may be truncated if it exceeds max_lines or max_size)

```
Here's the listing for `/sdcard/` on `emulator-5554`.
```

## 5.2 Understanding Command Risk Assessment

DroidMind has a built-in security system to assess the risk of shell commands. This system helps prevent accidental execution of dangerous commands.

- **Risk Levels**: `SAFE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- **Allowed Commands**: DroidMind maintains a list of generally safe shell commands (like `ls`, `cat`, `ps`, `dumpsys`, `getprop`).
- **Disallowed Commands**: Destructive commands (like `rm -rf /`, `mkfs`, `reboot` directly via shell) are typically blocked or require higher scrutiny.
- **Suspicious Patterns**: Commands containing patterns like `rm -rf /system` or trying to write to protected system paths are flagged.

**How DroidMind Responds to Risky Commands:**

- **`HIGH` or `CRITICAL` Risk**: If a command is assessed as high or critical risk, DroidMind will typically prepend a warning to the output.

  ```
  # Command Output from your_device_serial

  ⚠️ WARNING: This command has been assessed as HIGH risk.

  ```

  (Actual command output or error follows)

  ```

  ```

- **Security Rejection**: If a command is outright disallowed by the security policy (e.g., tries to use a blacklisted command or a highly suspicious pattern), DroidMind will return an error:

  ```
  # Command Output from your_device_serial

  ⚠️ WARNING: This command has been assessed as CRITICAL risk.

  Error: Command rejected for security reasons: Command 'reboot' is explicitly disallowed for security reasons
  ```

It's important for you, the user, to pay attention to these warnings. Your AI assistant will relay this information.

## 5.3 Output Handling: Truncation and Limits

Shell commands can sometimes produce very large outputs. To prevent overwhelming your AI assistant or your terminal, DroidMind has parameters to control the output size:

- **`max_lines`**: Controls the number of lines returned.
  - Positive value (e.g., `100`): Returns the first 100 lines.
  - Negative value (e.g., `-50`): Returns the last 50 lines.
  - Default is `1000` lines.
  - If `None` is specified (or a very large number), the command runs without `head` or `tail`, but `max_size` still applies.
- **`max_size`**: Controls the total number of characters in the output (default is 100,000, about 100KB).

If the output is truncated due to these limits, DroidMind will usually append a note to the output, for example:

```
...
[Output truncated: 100000 chars, 1500 lines]
[Command output truncated: 1500 lines, 97.7 KB]
```

**How to ask your AI assistant to control output:**

> "Run `logcat -d` on `emulator-5554` and show me only the last 50 lines."
> (AI should infer to use `max_lines: -50`)

> "Execute `dumpsys` on `your_device_serial`, but limit the output to 200 lines."
> (AI should infer to use `max_lines: 200`)

## 5.4 Security Considerations for Shell Commands

While DroidMind strives to provide a safe environment, the `shell_command` tool offers direct access to the device's command line. Keep these points in mind:

1.  **Understand the Command**: Even if your AI assistant formulates the command, try to understand what it does before approving its execution, especially if DroidMind flags it as medium or high risk.
2.  **Protected Paths**: DroidMind is cautious about commands that write to or heavily interact with system paths like `/system`, `/vendor`, `/data` (except for `/data/local/tmp` or app-specific data directories when appropriate).
3.  **No `sudo` or Root by Default**: Standard ADB shell does not run as root. Commands requiring root privileges will fail unless the device is rooted and ADB is configured to run as root (which is a separate, advanced setup).
4.  **Chain of Trust**: You are trusting your AI assistant to formulate commands, and DroidMind to execute them safely within its defined boundaries. Always be the final checkpoint.
5.  **Idempotency**: Shell commands are not always idempotent (running them multiple times might have different effects). Be mindful if asking your AI to re-run commands.

DroidMind's security features (see Chapter 8) are designed to prevent the most common dangerous operations, but user awareness remains key.

---

With shell access covered, let's move on to interacting with the device's user interface in **[Chapter 6: UI Automation](ui_automation.md)**.

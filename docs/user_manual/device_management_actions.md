# Chapter 7: Device Management Actions

Beyond diagnostics and app interactions, DroidMind also allows your AI assistant to perform crucial device management actions. Currently, this primarily involves rebooting the device into various modes.

## 7.1 Rebooting a Device

Your AI assistant can instruct DroidMind to reboot a connected Android device. This is useful for applying certain system updates, troubleshooting issues, or accessing special boot modes like recovery or bootloader.

**How to ask your AI assistant:**

> "Reboot `emulator-5554`."
> "Restart `your_device_serial` into recovery mode."
> "On `emulator-5554`, reboot to the bootloader."

**Expected DroidMind Action:**

DroidMind will use the `reboot_device` tool.

- `serial`: The target device's serial number.
- `mode` (optional, default `normal`): Specifies the reboot mode. Valid options are:
  - `normal`: A standard reboot of the Android system.
  - `recovery`: Reboots the device into the Android Recovery environment. This is often used for applying OTA updates, wiping data/cache, or other system-level maintenance.
  - `bootloader` (also known as Fastboot mode on some devices): Reboots the device into its bootloader. This mode is used for flashing firmware images, unlocking the bootloader, and other low-level operations.

**Example Response from AI (for a normal reboot):**

```
Okay, I am rebooting `emulator-5554` in normal mode.
(DroidMind internal response: Device emulator-5554 is rebooting in normal mode)
```

**Example Response from AI (for reboot to recovery):**

```
Alright, `your_device_serial` is now rebooting into recovery mode.
(DroidMind internal response: Device your_device_serial is rebooting in recovery mode)
```

**Important Considerations:**

- **Device Unavailability**: After a reboot command is issued, the device will become temporarily unavailable via ADB until it fully boots up into the selected mode or back into the Android system.
- **Recovery/Bootloader Interaction**: DroidMind can initiate the reboot to these modes, but further interaction within recovery or bootloader environments (which often rely on physical button inputs or specific `fastboot` commands) is typically outside the scope of standard DroidMind ADB shell tools. Specialized workflows or different tools might be needed for those interactions.
- **Risk**: Rebooting, especially into recovery or bootloader, is a system-level operation. Ensure you intend to do this, as interrupting boot processes or incorrect operations in these modes can potentially harm the device's software.

---

With device actions covered, it's crucial to understand DroidMind's safety features in **[Chapter 8: Security Considerations](security.md)**.

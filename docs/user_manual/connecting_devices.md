# Chapter 1: Connecting to Devices

DroidMind empowers your AI assistant to manage connections to your Android devices, whether they're plugged in via USB or available on your network. This chapter covers how to discover, connect to, and disconnect from your devices.

## 1.1 Listing Available Devices

Before you can interact with a device, you need to know its serial number or connection address. DroidMind can list all devices currently recognized by the Android Debug Bridge (ADB) on the machine where DroidMind is running.

**How to ask your AI assistant:**

> "Hey AI, can you list all connected Android devices using DroidMind?"
> "Show me the devices DroidMind can see."
> "What Android devices are available?"

**Expected DroidMind Action:**

DroidMind will use the `list_devices` tool.

**Example Response from AI (incorporating DroidMind's output):**

```
Okay, I found 2 Android devices connected:

## Device 1: Pixel 6 Pro
- **Serial**: `1A2B3C4D5E6F`
- **Android Version**: 13

## Device 2: Android Emulator
- **Serial**: `emulator-5554`
- **Android Version**: 12
```

- **Serial**: This is the unique identifier for your device. You'll use this serial number in many other commands to specify which device to target, especially if you have multiple devices connected.
- **USB Devices**: Physical devices connected via USB will typically show a hardware serial number (e.g., `1A2B3C4D5E6F`).
- **Emulators**: Android emulators usually have serials like `emulator-5554`.
- **Networked Devices**: Devices connected over TCP/IP will show their IP address and port (e.g., `192.168.1.100:5555`).

If no devices are listed, ensure your device has USB debugging enabled, is properly connected, and authorized on your computer. For emulators, make sure they are running. If DroidMind is in Docker, review the Docker guide for ADB connectivity.

## 1.2 Understanding Device Serials

The **serial number** is crucial for interacting with DroidMind, especially when multiple devices are connected. It's how DroidMind (and ADB) distinguishes between them.

- **Physical Devices (USB)**: Typically a unique alphanumeric string (e.g., `R5CR707QL9X`).
- **Emulators**: Usually `emulator-XXXX` (e.g., `emulator-5554`, `emulator-5556`).
- **Networked Devices (TCP/IP)**: In the format `ip_address:port` (e.g., `192.168.1.123:5555`).

When your AI assistant prompts for a device or you initiate a command, be ready to provide the correct serial if you have more than one device listed.

## 1.3 Connecting to Devices Over TCP/IP (Wi-Fi)

If your Android device is configured for ADB over Wi-Fi, DroidMind can connect to it.

**Prerequisites for TCP/IP Connection:**

1.  Your Android device and the machine running DroidMind must be on the **same network**.
2.  ADB over TCP/IP must be **enabled on your Android device**. This usually involves:
    - Connecting the device via USB first.
    - Running `adb tcpip 5555` (or another port) from your terminal.
    - Finding your device's IP address (e.g., in Settings > About phone > Status).
    - You can then disconnect the USB cable.

**How to ask your AI assistant:**

> "Connect to my Android device at IP address `192.168.1.101`."
> "DroidMind, please connect to `192.168.1.101:5555`."
> "Add a new device: `192.168.1.101` port `5556`."

**Expected DroidMind Action:**

DroidMind will use the `connect_device` tool.

**Example Response from AI:**

```
# ✨ Device Connected Successfully! ✨

- **Device**: Pixel 7
- **Connection**: 192.168.1.101:5555
- **Android Version**: 14

The device is now available for commands and operations.
```

If the connection fails, your AI assistant will relay the error message. Common issues include incorrect IP address/port, device not being on the same network, ADB over TCP/IP not being enabled correctly on the device, or firewall issues.

## 1.4 Disconnecting Devices

You can explicitly disconnect DroidMind from a device, which is primarily useful for devices connected over TCP/IP. Disconnecting a USB device via this command usually doesn't prevent it from being re-detected by ADB automatically.

**How to ask your AI assistant:**

> "Disconnect from the device `192.168.1.101:5555`."
> "DroidMind, remove `emulator-5554` from the list of active connections."

**Expected DroidMind Action:**

DroidMind will use the `disconnect_device` tool.

**Example Response from AI:**

```
Successfully disconnected from device 192.168.1.101:5555.
```

Or, if it wasn't a TCP/IP connection or already disconnected:

```
Device 192.168.1.101:5555 was not connected or could not be disconnected through this command.
```

After disconnecting, the device will no longer appear in the `list_devices` output unless it's a USB device that ADB automatically re-detects, or you explicitly connect to it again.

---

Next, let's explore how to get detailed information and diagnostics from your connected devices in **[Chapter 2: Device Information & Diagnostics](device_diagnostics.md)**.

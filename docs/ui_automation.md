# 👆 UI Automation Guide

<div align="center">

![DroidMind UI Automation](https://via.placeholder.com/200x150.png?text=DroidMind+UI)

**Control Android device interfaces with precision**

</div>

## 💫 Overview

DroidMind's UI automation tools allow AI assistants to interact with Android device touchscreens, input systems, and launch activities. These capabilities enable sophisticated automation of device interactions, from simple taps to complex multi-step workflows.

## 🛠️ Available Tools

### 🖱️ Touch Interaction

#### `tap` - Tap on specific screen coordinates

Simulates a single tap at the specified (x,y) coordinates on the device screen.

```python
tap(serial: str, x: int, y: int)
```

**Example:**
```
# Tap on the center of the screen
tap("device_serial", 540, 960)
```

#### `swipe` - Perform a swipe gesture

Simulates a swipe gesture from the starting coordinates to the ending coordinates, with optional duration.

```python
swipe(serial: str, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 300)
```

**Example:**
```
# Swipe down from top to open notification shade
swipe("device_serial", 540, 10, 540, 1000, 500)
```

### ⌨️ Input Methods

#### `input_text` - Type text

Inputs text as if typed from a keyboard. Special characters are properly escaped.

```python
input_text(serial: str, text: str)
```

**Example:**
```
# Type a search query
input_text("device_serial", "droidmind github")
```

#### `press_key` - Press hardware or software keys

Simulates pressing a key identified by its Android keycode.

```python
press_key(serial: str, keycode: int)
```

**Common Keycodes:**
- 3: HOME
- 4: BACK
- 24: VOLUME UP
- 25: VOLUME DOWN
- 26: POWER
- 82: MENU

**Example:**
```
# Press the back button
press_key("device_serial", 4)
```

### 🚀 Activity Control

#### `start_intent` - Launch activities with intents

Starts an Android activity by package and activity name, with optional extras.

```python
start_intent(serial: str, package: str, activity: str, extras: Optional[Dict[str, str]] = None)
```

**Example:**
```
# Open Settings app
start_intent("device_serial", "com.android.settings", ".Settings")

# Open browser with URL
start_intent("device_serial", "com.android.chrome", "com.google.android.apps.chrome.Main", {"url": "https://github.com/hyperbliss/droidmind"})
```

## 📊 Common Use Cases

### Complete a Login Form

```
# Tap on username field
tap("device_serial", 540, 800)

# Input username
input_text("device_serial", "droidmind_user")

# Tap on password field
tap("device_serial", 540, 900)

# Input password
input_text("device_serial", "secure_password")

# Tap login button
tap("device_serial", 540, 1050)
```

### Navigate Through an App

```
# Open settings app
start_intent("device_serial", "com.android.settings", ".Settings")

# Scroll down to find more options
swipe("device_serial", 540, 1500, 540, 500, 300)

# Tap on "About phone"
tap("device_serial", 540, 1200)

# Go back
press_key("device_serial", 4)

# Go home
press_key("device_serial", 3)
```

### Image Gallery Browsing

```
# Open gallery app
start_intent("device_serial", "com.google.android.apps.photos", ".home.HomeActivity")

# Swipe left to next image
swipe("device_serial", 100, 800, 900, 800)

# Swipe right to previous image
swipe("device_serial", 900, 800, 100, 800)

# Pinch to zoom (simulated with two swipes)
swipe("device_serial", 400, 800, 300, 700)
swipe("device_serial", 600, 800, 700, 900)
```

## 🔍 Tips for Successful UI Automation

1. **Get Screen Coordinates:** Use the `screenshot` tool first to identify the precise coordinates for your tap and swipe operations.

2. **Error Handling:** Always check for operation success and implement retries for operations that might fail due to timing issues.

3. **Device Variations:** Remember that coordinates are device-specific. Different screen sizes and resolutions will require different coordinates.

4. **Add Delays:** For complex interactions, consider adding delays between operations to allow the UI to respond.

5. **Confirmation:** Use the screenshot tool after automation sequences to verify the expected UI state.

6. **Context Awareness:** Be aware of the current app state before performing UI operations.

## 🔒 Security Considerations

- UI automation can potentially access sensitive information if used on screens with personal data
- Exercise caution when automating input on sensitive fields like passwords
- Be careful with intent extras that might contain sensitive data

## 🚧 Known Limitations

- Coordinates are absolute and device-specific
- Complex gestures like pinch-to-zoom require multiple operations
- Some UI elements may not respond to direct coordinate taps (e.g., if they use custom touch handlers)
- Animations may affect timing of operations

---

<div align="center">

✨ **Happy Automating!** ✨

</div> 
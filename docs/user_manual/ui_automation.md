# Chapter 6: UI Automation

DroidMind empowers your AI assistant to directly interact with the user interface of your Android devices. This allows for automating tasks, testing UI flows, and navigating apps as if a user were physically interacting with the screen. This chapter covers tapping, swiping, inputting text, pressing keys, and starting specific app activities using intents.

When using UI automation, it's often helpful to first use the `screenshot` tool (Chapter 2) to identify coordinates or current UI state.

## 6.1 Tapping on Screen Coordinates

Simulate a user tap at a specific X, Y coordinate on the device screen.

**How to ask your AI assistant:**

> "Tap at coordinates X 500, Y 1200 on `emulator-5554`."
> "On `your_device_serial`, simulate a tap at the center of a 1080x1920 screen."
> (AI would calculate center: X 540, Y 960)

**Expected DroidMind Action:**

DroidMind will use the `tap` tool.

- `x`: The X coordinate (pixels from left edge).
- `y`: The Y coordinate (pixels from top edge).

**Example Response from AI:**

```
Okay, I've tapped at (500, 1200) on `emulator-5554`.
(DroidMind internal response: Successfully tapped at (500, 1200))
```

## 6.2 Performing Swipe Gestures

Simulate a swipe gesture from a starting point to an ending point on the screen, with an optional duration.

**How to ask your AI assistant:**

> "Swipe from (100, 800) to (900, 800) on `emulator-5554` over 500 milliseconds."
> "On `your_device_serial`, perform a short swipe down from X 540, Y 200 to X 540, Y 600."

**Expected DroidMind Action:**

DroidMind will use the `swipe` tool.

- `start_x`, `start_y`: Starting X and Y coordinates.
- `end_x`, `end_y`: Ending X and Y coordinates.
- `duration_ms` (optional, default `300`): Duration of the swipe in milliseconds.

**Example Response from AI:**

```
Alright, I've performed a swipe from (100, 800) to (900, 800) on `emulator-5554`.
(DroidMind internal response: Successfully swiped from (100, 800) to (900, 800))
```

This can be used for scrolling, navigating carousels, etc.

## 6.3 Inputting Text

Type text into the currently focused input field on the device, as if from a keyboard.

**How to ask your AI assistant:**

> "Type 'Hello DroidMind' into the active field on `emulator-5554`."
> "On `your_device_serial`, input the text: `user@example.com`."

**Important:** Ensure the desired text field is already focused on the device screen before issuing this command. You might need to use a `tap` command first to select the field.

**Expected DroidMind Action:**

DroidMind will use the `input_text` tool.

- `text`: The text string to input.

**Example Response from AI:**

```
I have input the text "Hello DroidMind" on `emulator-5554`.
(DroidMind internal response: Successfully input text on device)
```

## 6.4 Pressing Hardware/Software Keys

Simulate pressing a standard Android key using its keycode. This can be used for actions like going Home, Back, adjusting volume, or pressing Power.

**Common Keycodes:**

- `3`: HOME
- `4`: BACK
- `24`: VOLUME UP
- `25`: VOLUME DOWN
- `26`: POWER
- `82`: MENU (Recent Apps on some devices)

**How to ask your AI assistant:**

> "Press the HOME key on `emulator-5554`."
> "On `your_device_serial`, simulate pressing the BACK button."
> "Press Volume Up (keycode 24) on `emulator-5554`."

**Expected DroidMind Action:**

DroidMind will use the `press_key` tool.

- `keycode`: The Android integer keycode.

**Example Response from AI:**

```
I've pressed the HOME key (keycode 3) on `emulator-5554`.
(DroidMind internal response: Successfully pressed key HOME)
```

## 6.5 Starting Activities using Intents

Launch a specific application component (an Activity) directly using an Android Intent. This is more precise than just starting an app by package name if you know the exact component you want to launch. You can also pass data (extras) to the activity.

**How to ask your AI assistant:**

> "Start the activity `com.android.settings/.wifi.WifiSettingsActivity` on `emulator-5554`."
> "On `your_device_serial`, launch the main activity for `com.example.myapp`."
> "Open the URL `https://droidmind.dev` in Chrome on `emulator-5554` by starting an intent for package `com.android.chrome` activity `com.google.android.apps.chrome.Main` with an extra string `url` set to `https://droidmind.dev`."

**Expected DroidMind Action:**

DroidMind will use the `start_intent` tool.

- `package`: The package name of the application (e.g., `com.android.settings`).
- `activity`: The activity name to start. This can be a relative name (e.g., `.SettingsActivity`, assuming the `package` is `com.android.settings`) or a fully qualified name (e.g., `com.android.settings.SettingsActivity`).
- `extras` (optional): A dictionary of key-value pairs to pass as intent extras. For example, `{"url": "https://example.com", "user_id": "123"}`. Values are treated as strings.

**Example Response from AI (opening Wi-Fi settings):**

```
Okay, I've started the Wi-Fi Settings activity on `emulator-5554`.
(DroidMind internal response: Successfully started com.android.settings/.wifi.WifiSettingsActivity)
```

**Example Response from AI (opening a URL in Chrome):**

```
I've launched Chrome on `emulator-5554` with the URL `https://droidmind.dev`.
(DroidMind internal response: Successfully started com.android.chrome/com.google.android.apps.chrome.Main)
```

**Tips for UI Automation:**

- **Coordinates**: Screen coordinates (X, Y) are usually 0,0 from the top-left. The exact screen dimensions can be found using `device_properties` (look for properties like `ro.surface_flinger.primary_display_width`).
- **Timing**: UI elements might take time to appear or respond. If a sequence of UI actions fails, your AI might need to be instructed to add small delays or checks (e.g., take a screenshot to verify state) between steps.
- **Context**: UI automation tools operate on the current screen. Ensure the app and screen you intend to interact with are active and visible.

---

Next, we'll look at other device management actions like rebooting in **[Chapter 7: Device Management Actions](device_management_actions.md)**.

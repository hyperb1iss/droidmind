# 🚀 Installation Guide

Get DroidMind up and running on your system. This guide covers the primary ways to install DroidMind, whether you want a quick setup for IDE integration or a full manual installation.

## 📋 Prerequisites

Before you begin, ensure you meet the following requirements:

- **Python**: DroidMind requires Python 3.13 or higher. You can [download Python](https://www.python.org/downloads/) from the official website.
- **UV**: We strongly recommend using `uv` for project and package management. It's a fast, modern Python package installer and resolver. Follow the [official uv installation guide](https://github.com/astral-sh/uv#installation).
- **Android Device**: An Android device (physical or emulator) with USB debugging enabled.
- **ADB (Android Debug Bridge)**: ADB must be installed and accessible in your system's PATH. ADB is part of the [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools).
- **(Optional for Network Control)**: If you plan to connect to devices over Wi-Fi, ensure your Android device has ADB over TCP/IP enabled and is on the same network as the machine running DroidMind.

## ⚙️ Installation Methods

Choose the installation method that best suits your needs:

### Method 1: Quick IDE Integration (via `uvx`)

This method is ideal for quickly running DroidMind as an MCP server, for example, within an IDE that supports the Model Context Protocol (like Cursor). It uses `uvx` to run DroidMind directly from its latest version on GitHub, meaning **no manual cloning or installation of DroidMind is required first**.

This setup configures your IDE to launch DroidMind, typically using `stdio` transport for direct interaction or `sse` if needed by the client.

1.  **Ensure `uv` is installed.** (See Prerequisites).
2.  **Configure your IDE**: You'll instruct your IDE to run DroidMind by adding a configuration to its MCP server settings file (e.g., `.cursor/mcp.json` for Cursor). See the **[Quick Start Guide](quickstart.md#1-configure-your-ide-to-run-droidmind-via-uvx)** for the exact JSON configuration and details on how your IDE will use `uvx` to fetch and run DroidMind.

This `uvx`-based approach is excellent for a seamless experience, development, and testing, as your IDE handles DroidMind's lifecycle.

### Method 2: Manual Installation (from Source)

This method gives you a local copy of the DroidMind codebase, allowing for development or more permanent setups.

1.  **Clone the Repository**:
    Open your terminal and clone the DroidMind repository from GitHub:

    ```bash
    git clone https://github.com/hyperb1iss/droidmind.git
    cd droidmind
    ```

2.  **Create and Activate Virtual Environment**:
    Using `uv`, create a virtual environment:

    ```bash
    uv venv
    ```

    Activate the environment:

    - On macOS and Linux:
      ```bash
      source .venv/bin/activate
      ```
    - On Windows (PowerShell):
      ```powershell
      .venv\Scripts\Activate.ps1
      ```
    - On Windows (CMD):
      ```cmd
      .venv\Scripts\activate.bat
      ```

3.  **Install Dependencies**:
    With the virtual environment activated, install DroidMind and its dependencies. Choose the extras based on your needs:

    - **For SSE Transport (Recommended for AI Assistant web UIs, Claude Desktop, etc.):**
      ```bash
      uv pip install -e .[sse]
      ```
    - **For Stdio Transport (Direct terminal interaction):**
      ```bash
      uv pip install -e .[stdio]
      ```
    - **For Development (includes all dependencies, plus dev tools):**
      ```bash
      uv pip install -e .[dev,sse]
      ```
      (Note: `dev` typically includes `stdio` and `sse` specific dependencies if structured that way in `pyproject.toml`)

## 🏃‍♀️ Running DroidMind

After installation (primarily for Method 2, as `uvx` runs it directly):

- **Stdio Mode (Direct Terminal Interaction)**:

  ```bash
  droidmind
  ```

  Or, to be explicit:

  ```bash
  droidmind --transport stdio
  ```

- **SSE Mode (for AI Assistants like Claude Desktop, Web UIs)**:
  ```bash
  droidmind --transport sse
  ```
  By default, this will start an SSE server at `http://localhost:4256`. The MCP connection URI for your AI assistant will typically be `sse://localhost:4256/sse`.

## 🐳 Docker Installation

For a containerized setup, DroidMind can also be run using Docker. This is useful for creating a consistent environment and simplifying deployment.
Refer to our **[Docker Guide](docker.md)** for detailed instructions.

## ✅ Next Steps

With DroidMind installed and running:

- **[Quick Start Guide](quickstart.md)**: Learn how to connect DroidMind to your AI assistant and start issuing commands.
- **Configure your AI Assistant**: Refer to your AI assistant's documentation (e.g., Claude Desktop, Cursor) on how to connect to an MCP server using the appropriate URI (e.g., `sse://localhost:4256/sse` for SSE mode).

Happy DroidMinding! 💫

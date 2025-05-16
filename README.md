# ✨ DroidMind 🤖

<div align="center">

<img src="docs/assets/images/logo_neon_glow_icon.png" alt="DroidMind Logo" width="180" />

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-9D00FF.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache_2.0-FF00FF.svg?style=for-the-badge&logo=apache&logoColor=white)](LICENSE)
[![Status](https://img.shields.io/badge/status-active_development-39FF14.svg?style=for-the-badge&logo=githubactions&logoColor=white)](docs/plan.md)
[![Code Style](https://img.shields.io/badge/code_style-ruff-00FFFF.svg?style=for-the-badge&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![Type Check](https://img.shields.io/badge/type_check-pyright-FFBF00.svg?style=for-the-badge&logo=typescript&logoColor=white)](https://github.com/microsoft/pyright)
[![MCP](https://img.shields.io/badge/protocol-MCP-E6E6FA.svg?style=for-the-badge&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io/)
[![Android](https://img.shields.io/badge/platform-android-A4C639.svg?style=for-the-badge&logo=android&logoColor=white)](https://www.android.com/)

**Control Android devices with AI through the Model Context Protocol**

</div>

DroidMind is a powerful bridge between AI assistants and Android devices, enabling control, debugging, and system analysis through natural language. By implementing the Model Context Protocol (MCP), DroidMind allows AI models to directly interact with Android devices via ADB in a secure, structured way. When used as part of an agentic coding workflow, DroidMind can enable your assistant to build and debug with your device directly in the loop.

## 💫 Core Features

DroidMind empowers AI assistants to:

- 📱 **Manage Devices**: Connect via USB/TCP-IP, list devices, view properties, and reboot.
- 📊 **Analyze Systems**: Access logs (logcat, ANR, crash, battery), capture bug reports, and dump heap.
- 📂 **Handle Files**: Browse, read, write, push, pull, delete, and manage device files/directories.
- 📦 **Control Apps**: Install, uninstall, start, stop, clear data, and inspect app details (manifest, permissions, activities).
- 🖼️ **Automate UI**: Perform taps, swipes, text input, and key presses.
- 🐚 **Execute Shell Commands**: Run ADB shell commands with a security-conscious framework.
- 🔒 **Operate Securely**: Benefit from command validation, risk assessment, and sanitization.
- 💬 **Integrate Seamlessly**: Connect with any MCP-compatible client (Claude, Cursor, Cline, etc.).

For a detailed list of capabilities, see the **[User Manual](docs/user_manual/index.md)** and **[MCP Reference](docs/mcp-reference.md)**.

## 🚀 Getting Started

### Quickstart for IDEs (Zero Install with `uvx`)

For the fastest way to integrate DroidMind with an MCP-compatible IDE (like Cursor), you can configure it to run DroidMind directly from its GitHub repository using `uvx`. This method **does not require you to manually clone or install DroidMind first**.

Your IDE will be configured to launch DroidMind on demand. Full instructions for this setup are in the **[Quick Start Guide](docs/quickstart.md#1-configure-your-ide-to-run-droidmind-via-uvx)**, which shows the necessary `mcp.json` configuration.

### Prerequisites

- Python 3.13 or higher
- `uv` (Python package manager)
- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed and in your system's PATH

### Installation

For detailed instructions on setting up DroidMind, including the quick IDE integration with `uvx` (covered in the Quick Start), manual installation from source, or using Docker, please see our comprehensive **[Installation Guide](docs/installation.md)**.

### Running DroidMind

How you run DroidMind depends on your setup:

- **IDE Integration (via `uvx`)**: Your IDE automatically manages running DroidMind as configured in its MCP settings (e.g., `mcp.json`). See the [Quick Start Guide](docs/quickstart.md).
- **Manual Installation**: After installing from source, you can run DroidMind directly.
  - **Stdio (for direct terminal interaction or some IDE setups):**
    ```bash
    droidmind --transport stdio
    ```
  - **SSE (for web UIs or AI assistants like Claude Desktop):**
    ```bash
    droidmind --transport sse
    ```
    This usually starts a server at `sse://localhost:4256/sse`.
- **Docker**: Refer to the [Docker Guide](docs/docker.md) for commands to run DroidMind in a container.

Refer to the **[Installation Guide](docs/installation.md)** for more details on running DroidMind in different environments.

## 🐳 Running with Docker

DroidMind can also be run using Docker for a consistent, containerized environment. This is particularly useful for deployment and isolating dependencies.

For comprehensive instructions on building the Docker image and running DroidMind in a container with `stdio` or `SSE` transport, including notes on ADB device access, please refer to our **[Docker Guide](docs/docker.md)**.

## 🔮 Example AI Assistant Queries

With an AI assistant connected to DroidMind, you can make requests like:

- "List all connected Android devices and show their properties."
- "Take a screenshot of my Pixel."
- "Install this APK on `emulator-5554`."
- "Show me the recent crash logs from `your_device_serial`."
- "Tap the 'Next' button on the current screen of `emulator-5554`."

For more inspiration, check out our **[Example Queries and Workflows](docs/user_manual/example_queries.md)** in the User Manual.

## 🔒 Security

DroidMind incorporates a security framework to protect your devices:

- **Command Validation & Sanitization**
- **Risk Assessment Categorization**
- **Protected Path Operations**
- **Comprehensive Logging**

High-risk operations are flagged, and critical ones are blocked by default. Learn more in our **[Security Considerations](docs/user_manual/security.md)** chapter.

## 💻 Development

DroidMind uses `uv` for dependency management and development workflows.

```bash
# Install/update dependencies (after cloning and activating .venv)
uv pip install -e .[dev,sse]

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
pyright # Ensure pyright is installed or use ruff's type checking capabilities
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/amazing-feature`).
3.  Set up your development environment with `uv`.
4.  Make your changes.
5.  Run tests, linting, and type checking.
6.  Commit your changes (`git commit -m 'Add some amazing feature'`).
7.  Push to the branch (`git push origin feature/amazing-feature`).
8.  Open a Pull Request.

## 📝 License

This project is licensed under the Apache License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Created by [Stefanie Jane 🌠](https://github.com/hyperb1iss)

If you find DroidMind useful, [buy me a Monster Ultra Violet ⚡️](https://ko-fi.com/hyperb1iss)

</div>

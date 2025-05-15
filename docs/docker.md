#🐳 Running DroidMind with Docker

Docker provides a convenient way to run DroidMind in a containerized, consistent environment. This guide covers building the DroidMind Docker image and running it with various configurations.

## Prerequisites

- **Docker**: Ensure Docker Desktop (for Mac/Windows) or Docker Engine (for Linux) is installed and running on your system. [Get Docker](https://docs.docker.com/get-docker/).
- **DroidMind Source Code**: You'll need the DroidMind source code, specifically the `Dockerfile`, to build the image. If you haven't already, clone the repository:
  ```bash
  git clone https://github.com/hyperbliss/droidmind.git
  cd droidmind
  ```

## 📦 Building the Docker Image

Navigate to the root directory of the DroidMind project (where the `Dockerfile` is located) and run the following command to build the image:

```bash
docker build -t droidmind:latest .
```

This command builds a Docker image tagged as `droidmind:latest` using the instructions in the `Dockerfile`.

## ධ Running the Docker Container

Once the image is built, you can run DroidMind as a container. The `entrypoint.sh` script within the Docker image handles how DroidMind starts based on environment variables and command-line arguments.

### Interactive CLI (Stdio Transport - Default)

By default, the container runs DroidMind with `stdio` transport, ideal for direct command-line interaction if you were to exec into the container or use it as part of a script.

```bash
docker run -it --rm --name droidmind-cli droidmind:latest
```

- `-it`: Runs the container in interactive mode with a pseudo-TTY.
- `--rm`: Automatically removes the container when it exits.
- `--name droidmind-cli`: Assigns a name to the container for easier management.

To pass specific arguments to `droidmind` when using `stdio` mode directly (less common for typical AI assistant use):

```bash
docker run -it --rm --name droidmind-cli droidmind:latest droidmind --your-stdio-options
```

### 🌐 SSE Transport (Recommended for AI Assistants)

To connect DroidMind with AI assistants like Claude Desktop or other MCP clients, you'll typically use the SSE (Server-Sent Events) transport. The `entrypoint.sh` script is designed to facilitate this.

**Using the `DROIDMIND_TRANSPORT` Environment Variable (Recommended):**

This is the easiest way to run in SSE mode. The entrypoint script will automatically configure DroidMind to listen on `0.0.0.0` inside the container.

```bash
docker run -d -p 4256:4256 -e DROIDMIND_TRANSPORT=sse --name droidmind-server droidmind:latest
```

- `-d`: Runs the container in detached mode (in the background).
- `-p 4256:4256`: Maps port 4256 of the container to port 4256 on your host machine. This allows your AI assistant (running on the host) to connect to DroidMind (running in the container).
- `-e DROIDMIND_TRANSPORT=sse`: Tells the entrypoint script to start DroidMind in SSE mode.
- `--name droidmind-server`: Assigns a name to the container.

Your AI assistant can then connect to `sse://localhost:4256/sse` (or `sse://<your-host-ip>:4256/sse` if connecting from a different machine on your network).

**Overriding the Command for SSE:**

You can also explicitly specify all DroidMind arguments:

```bash
docker run -d -p 4256:4256 --name droidmind-server droidmind:latest droidmind --transport sse --host 0.0.0.0 --port 4256
```

This command tells DroidMind to use SSE transport and listen on all interfaces (`0.0.0.0`) within the container on port `4256`.

### 🔌 Connecting to ADB Devices

For DroidMind in Docker to control your Android devices, the container needs access to an ADB server that can see your devices. This is the most complex part of using DroidMind with Docker.

**1. Networked ADB Devices (Recommended for Docker)**

This is the most straightforward method for Docker setups.

- **Enable ADB over TCP/IP on your Android device(s)**:
  1.  Connect your device via USB to your host machine.
  2.  Find your device's IP address (usually in Settings > About phone > Status > IP address).
  3.  Run `adb tcpip 5555` (or another port if you prefer).
  4.  Disconnect the USB cable.
  5.  Run `adb connect <device_ip_address>:5555` from your host machine to confirm it works.
- Ensure your Docker container's network configuration allows outbound connections to your device's IP address on your local network. If you're using default Docker networking (bridge), this usually works out of the box as long as your host firewall isn't blocking it.
- Once DroidMind is running in the container, you can use its `connect_device` tool (via your AI assistant) to connect to `<device_ip_address>:5555`.

**2. USB-Connected ADB Devices (Advanced)**

Connecting to USB devices from within a Docker container is platform-dependent and can be challenging.

- **Option A: Use the Host's ADB Server (More Common)**
  The idea is to make the Docker container use the ADB server already running on your host machine.

  - **Linux**: You might share the host's network: `docker run --network host ...`. This gives the container direct access to the host's network interfaces, including the ADB server. Note: `--network host` has security implications.
  - **macOS/Windows**: Docker Desktop runs in a virtual machine, making direct host ADB server access trickier. You might need to forward the ADB server port (default 5037) from the host to the Docker VM or container, or use solutions that share the ADB server socket if available for your Docker version.
  - You might need to set the `ADB_SERVER_SOCKET` environment variable inside the container to point to the correct socket (e.g., `tcp:host.docker.internal:5037` if you can forward the port, or a mounted socket path).

- **Option B: Run an ADB Server Inside the Container (More Complex)**
  This involves passing USB device access into the container and running an ADB server within it.
  - This often requires running the container in `--privileged` mode, which has significant security implications.
  - You'd need to mount the USB device bus, e.g., `-v /dev/bus/usb:/dev/bus/usb` (Linux specific).
  - The DroidMind Docker image _includes_ `android-sdk-platform-tools`, so an ADB server _can_ be started inside it. However, making this server see host-connected USB devices is the main challenge.

> ✨ **Recommendation**: For ease of use with Docker, connecting your Android devices via ADB over TCP/IP is strongly recommended. It avoids the complexities of USB passthrough and host ADB server sharing.

### ⚙️ Customizing DroidMind Arguments

You can append DroidMind-specific arguments to your `docker run` command. The `entrypoint.sh` script is designed to pass these along to the `droidmind` executable.

- **If `DROIDMIND_TRANSPORT` is set (e.g., to `sse`):** The script will inject `--transport sse --host 0.0.0.0 --port 4256` (or the value of `DROIDMIND_PORT` if set). You can still add other DroidMind arguments.

  Example: Run with SSE (handled by env var), a custom ADB path, and debug mode:

  ```bash
  docker run -d -p 4256:4256 \
    -e DROIDMIND_TRANSPORT=sse \
    -e ADB_SERVER_SOCKET=tcp:host.docker.internal:5037 \ # Example for host ADB on Mac/Win
    --name droidmind-custom-sse \
    droidmind:latest droidmind --adb-path /custom/adb --debug
  ```

- **If `DROIDMIND_TRANSPORT` is NOT set:** The script assumes you will provide all necessary arguments, including `--transport` if you don't want stdio.

  Example: Explicitly specify all options for SSE on a different port:

  ```bash
  docker run -d -p 8000:8000 \
    --name droidmind-explicit-sse \
    droidmind:latest droidmind --transport sse --host 0.0.0.0 --port 8000 --log-level DEBUG
  ```

### 📜 Viewing Logs

If you're running DroidMind in detached mode (`-d`), you can view its logs (output to stdout/stderr in the container) using:

```bash
docker logs <container_name_or_id>
```

For example:

```bash
docker logs droidmind-server
```

To follow the logs in real-time:

```bash
docker logs -f droidmind-server
```

## ✅ Next Steps

- **[Quick Start Guide](quickstart.md)**: Learn how to connect DroidMind (whether running in Docker or locally) to your AI assistant.
- **[User Manual](user_manual/index.md)**: Explore all the features DroidMind offers.

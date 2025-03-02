#!/usr/bin/env python3
"""
Example client for DroidMind MCP server using SSE transport.

This script demonstrates how to connect to a DroidMind server using the
Server-Sent Events (SSE) transport and perform basic device operations.
"""

import argparse
import asyncio
import json
import sys
from typing import Dict

import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Set up console for pretty output
console = Console()


async def send_message(server_url: str, message: Dict) -> Dict:
    """Send a message to the DroidMind server and receive the response."""
    message_id = message.get("id", "unknown")
    messages_url = f"{server_url}/messages/{message_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(messages_url, json=message, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        console.print(f"[red]Error sending message to server: {e}[/red]")
        return {"error": str(e)}


async def listen_for_events(server_url: str) -> None:
    """Listen for SSE events from the server."""
    sse_url = f"{server_url}/sse"

    console.print(f"[cyan]Connecting to SSE endpoint: {sse_url}[/cyan]")

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", sse_url) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data:
                            try:
                                event = json.loads(data)
                                await handle_event(event)
                            except json.JSONDecodeError:
                                console.print(f"[yellow]Invalid JSON in event: {data}[/yellow]")
    except httpx.HTTPError as e:
        console.print(f"[red]Error listening for events: {e}[/red]")


async def handle_event(event: Dict) -> None:
    """Handle an event received from the server."""
    event_type = event.get("type")

    if event_type == "request":
        await handle_request(event)
    elif event_type == "notification":
        handle_notification(event)
    else:
        console.print(f"[yellow]Unknown event type: {event_type}[/yellow]")


async def handle_request(request: Dict) -> None:
    """Handle a request from the server."""
    request_id = request.get("id", "unknown")
    method = request.get("method")
    request.get("params", {})

    console.print(f"[green]Received request {request_id}: {method}[/green]")

    if method == "initialize":
        # Respond to initialization request
        response = {
            "id": request_id,
            "type": "response",
            "result": {
                "name": "Example DroidMind Client",
                "version": "0.1.0",
                "capabilities": {"chat": True, "multimodal": True},
            },
        }
    else:
        # Default response for unknown methods
        response = {"id": request_id, "type": "response", "result": None}

    # Send response back to server
    server_url = "http://localhost:8000"  # Replace with actual server URL
    await send_message(server_url, response)


def handle_notification(notification: Dict) -> None:
    """Handle a notification from the server."""
    method = notification.get("method")
    params = notification.get("params", {})

    if method == "progress":
        console.print(
            f"[cyan]Progress: {params.get('current')}/{params.get('total')} - {params.get('message', '')}[/cyan]"
        )
    elif method == "log":
        level = params.get("level", "info").upper()
        message = params.get("message", "")

        if level == "ERROR":
            console.print(f"[red]ERROR: {message}[/red]")
        elif level == "WARNING":
            console.print(f"[yellow]WARNING: {message}[/yellow]")
        else:
            console.print(f"[blue]INFO: {message}[/blue]")
    else:
        console.print(f"[yellow]Notification: {method} - {json.dumps(params)}[/yellow]")


async def list_devices(server_url: str) -> None:
    """List connected Android devices using the DroidMind API."""
    console.print("[cyan]Listing connected Android devices...[/cyan]")

    request = {
        "id": "list-devices-request",
        "type": "request",
        "method": "readResource",
        "params": {"uri": "device://list"},
    }

    response = await send_message(server_url, request)

    if "result" in response:
        result = response["result"]
        console.print(Panel(Markdown(result), title="Connected Devices"))
    else:
        console.print("[red]Error listing devices[/red]")


async def connect_to_device(server_url: str, host: str, port: int = 5555) -> None:
    """Connect to an Android device using the DroidMind API."""
    console.print(f"[cyan]Connecting to device at {host}:{port}...[/cyan]")

    request = {
        "id": "connect-device-request",
        "type": "request",
        "method": "executeTool",
        "params": {"name": "connect_device", "arguments": {"host": host, "port": port}},
    }

    response = await send_message(server_url, request)

    if "result" in response:
        result = response["result"]
        console.print(f"[green]{result}[/green]")
    else:
        console.print("[red]Error connecting to device[/red]")


async def get_device_properties(server_url: str, serial: str) -> None:
    """Get device properties using the DroidMind API."""
    console.print(f"[cyan]Getting properties for device {serial}...[/cyan]")

    request = {
        "id": "device-props-request",
        "type": "request",
        "method": "readResource",
        "params": {"uri": f"device://{serial}/properties"},
    }

    response = await send_message(server_url, request)

    if "result" in response:
        result = response["result"]
        console.print(Panel(Markdown(result), title=f"Device Properties: {serial}"))
    else:
        console.print("[red]Error getting device properties[/red]")


async def run_shell_command(server_url: str, serial: str, command: str) -> None:
    """Run a shell command on the device using the DroidMind API."""
    console.print(f"[cyan]Running command on {serial}: {command}[/cyan]")

    request = {
        "id": "shell-command-request",
        "type": "request",
        "method": "executeTool",
        "params": {"name": "shell_command", "arguments": {"serial": serial, "command": command}},
    }

    response = await send_message(server_url, request)

    if "result" in response:
        result = response["result"]
        console.print(Panel(Markdown(result), title="Command Output"))
    else:
        console.print("[red]Error running command[/red]")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DroidMind SSE Client Example")
    parser.add_argument("--server", default="http://localhost:8000", help="DroidMind server URL")
    parser.add_argument(
        "--action",
        choices=["list", "connect", "properties", "shell", "listen"],
        default="listen",
        help="Action to perform",
    )
    parser.add_argument("--host", help="Device IP address (for connect)")
    parser.add_argument("--port", type=int, default=5555, help="Device port (for connect)")
    parser.add_argument("--serial", help="Device serial number (for properties, shell)")
    parser.add_argument("--command", help="Shell command to run (for shell)")

    args = parser.parse_args()

    console.print(
        Panel(
            f"[cyan bold]DroidMind SSE Client Example[/cyan bold]\n\n"
            f"Server: [green]{args.server}[/green]\n"
            f"Action: [green]{args.action}[/green]",
            title="🤖 Android Control",
            border_style="cyan",
        )
    )

    if args.action == "list":
        await list_devices(args.server)
    elif args.action == "connect":
        if not args.host:
            console.print("[red]Error: --host is required for connect action[/red]")
            return
        await connect_to_device(args.server, args.host, args.port)
    elif args.action == "properties":
        if not args.serial:
            console.print("[red]Error: --serial is required for properties action[/red]")
            return
        await get_device_properties(args.server, args.serial)
    elif args.action == "shell":
        if not args.serial or not args.command:
            console.print("[red]Error: --serial and --command are required for shell action[/red]")
            return
        await run_shell_command(args.server, args.serial, args.command)
    elif args.action == "listen":
        await listen_for_events(args.server)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[yellow]Client terminated by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

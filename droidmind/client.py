"""
DroidMind client utilities.

This module backs the `droidmind-client` console script. It provides simple
connectivity checks and introspection helpers for a running DroidMind server.
"""

from __future__ import annotations

from contextlib import AsyncExitStack
import json

import anyio
import click
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client


def _normalize_sse_url(url: str) -> str:
    # Many MCP clients use `sse://` as a scheme alias for HTTP.
    if url.startswith("sse://"):
        return "http://" + url.removeprefix("sse://")
    if url.startswith("sses://"):
        return "https://" + url.removeprefix("sses://")
    return url


async def _list_tools(url: str, connect_timeout: float) -> int:
    try:
        async with AsyncExitStack() as stack:
            read_stream, write_stream = await stack.enter_async_context(
                sse_client(_normalize_sse_url(url), timeout=connect_timeout)
            )
            session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
            await session.initialize()
            result = await session.list_tools()
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        click.echo(f"Failed to connect/list tools: {exc}", err=True)
        return 1

    click.echo(json.dumps([t.model_dump(mode="json") for t in result.tools], indent=2))
    return 0


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)
def cli() -> None:
    """Utilities for connecting to a running DroidMind MCP server."""


@cli.command("list-tools")
@click.option(
    "--url",
    default="sse://127.0.0.1:4256/sse",
    show_default=True,
    help="SSE endpoint URL (accepts sse://, sses://, http://, https://).",
)
@click.option("--timeout", default=5.0, show_default=True, type=float, help="HTTP timeout for connection setup.")
def list_tools(url: str, timeout: float) -> None:
    """List available tools from a running DroidMind server (JSON)."""
    raise SystemExit(anyio.run(_list_tools, url, timeout))


def main() -> None:
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()

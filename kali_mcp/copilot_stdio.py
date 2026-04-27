"""
MCP over stdio for VS Code / GitHub Copilot (official MCP protocol).

The HTTP server (kali-mcp / uvicorn) stays the default for Kaliyai; this entrypoint
reuses the same tool catalog and call_tool() implementation.
"""

from __future__ import annotations

import asyncio
from typing import Any

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from kali_mcp.config import load_settings
from kali_mcp.tools_impl import call_tool, reload_settings, tool_catalog_for_settings


def _outcome_to_call_result(raw: dict[str, Any]) -> types.CallToolResult:
    blocks: list[types.ContentBlock] = []
    for item in raw.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "text":
            blocks.append(types.TextContent(type="text", text=str(item.get("text", ""))))
    if not blocks:
        blocks = [types.TextContent(type="text", text=str(raw))]
    err = raw.get("isError")
    is_err = err is True or err == "true" or err == "1"
    return types.CallToolResult(content=blocks, isError=is_err)


def _build_server() -> Server:
    server = Server("kali-mcp")

    @server.list_tools()
    async def _list_tools() -> list[types.Tool]:
        reload_settings()
        s = load_settings()
        catalog = tool_catalog_for_settings(s)
        out: list[types.Tool] = []
        for t in catalog:
            out.append(
                types.Tool(
                    name=t["name"],
                    description=t.get("description") or "",
                    inputSchema=t.get("inputSchema") or {"type": "object", "properties": {}},
                )
            )
        return out

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict | None) -> types.CallToolResult:
        reload_settings()
        raw = call_tool(name, arguments or {})
        return _outcome_to_call_result(raw)

    return server


async def _amain() -> None:
    server = _build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kali-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()

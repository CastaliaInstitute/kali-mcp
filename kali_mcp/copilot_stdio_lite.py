"""
MCP over stdio for VS Code / Copilot, without importing the `mcp` package.

The PyPI `mcp` package eagerly loads a large stack on import (10–30+ seconds on
cold start). This module speaks the same line-delimited JSON-RPC used by
`mcp.server.stdio` and only uses the stdlib plus kali_mcp's tool layer.

The HTTP server (kali-mcp / uvicorn) is unchanged and remains the default for Kaliyai.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from kali_mcp.config import load_settings
from kali_mcp.tools_impl import call_tool, reload_settings, tool_catalog_for_settings

_PROTOCOL_DEFAULT = "2024-11-05"


def _as_call_tool_result(raw: dict[str, Any]) -> dict[str, Any]:
    blocks: list[dict[str, Any]] = []
    for item in raw.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "text":
            blocks.append({"type": "text", "text": str(item.get("text", ""))})
    if not blocks:
        blocks = [{"type": "text", "text": str(raw)}]
    err = raw.get("isError")
    is_err = err is True or err == "true" or err == "1"
    out: dict[str, Any] = {"content": blocks}
    if is_err:
        out["isError"] = True
    return out


def _error_response(rid: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def _handle_request(obj: dict[str, Any]) -> dict[str, Any] | None:
    """Return one JSON object to write to stdout, or None (no line for JSON-RPC notifications)."""
    if "result" in obj and "method" not in obj:
        return None
    if "method" not in obj:
        if "id" in obj and obj.get("id") is not None:
            return _error_response(obj["id"], -32600, "Invalid request")
        return None

    method = (obj.get("method") or "").strip()
    if "id" not in obj or obj.get("id") is None:
        return None
    rid = obj["id"]

    params: dict[str, Any] = obj.get("params") or {}
    if not isinstance(params, dict):
        params = {}

    if method == "initialize":
        client_version = (params.get("protocolVersion") or _PROTOCOL_DEFAULT) or _PROTOCOL_DEFAULT
        s = load_settings()
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "protocolVersion": str(client_version),
                "serverInfo": {
                    "name": "kali-mcp",
                    "version": "0.1.0",
                    "kaliMcp": {"profile": s.profile.value},
                },
                "capabilities": {
                    "tools": {},
                },
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}

    if method == "tools/list":
        reload_settings()
        s = load_settings()
        catalog = tool_catalog_for_settings(s)
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": catalog}}

    if method == "tools/call":
        name = (params.get("name") or "").strip()
        raw_args: Any = params.get("arguments")
        if raw_args is not None and not isinstance(raw_args, dict):
            if isinstance(raw_args, str):
                try:
                    raw_args = json.loads(raw_args)
                except Exception:
                    return _error_response(rid, -32602, "Invalid params: arguments must be object or JSON string")
            else:
                return _error_response(rid, -32602, "Invalid params: arguments must be object or string")
        dargs: dict[str, Any] = raw_args if isinstance(raw_args, dict) else {}
        reload_settings()
        raw = call_tool(name, dargs)
        return {"jsonrpc": "2.0", "id": rid, "result": _as_call_tool_result(raw)}

    if method == "resources/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"resources": []}}

    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"prompts": []}}

    return _error_response(rid, -32601, f"Method not found: {method}")


def main() -> None:
    stdin = sys.stdin.buffer
    for raw_line in stdin:
        if not raw_line.strip():
            continue
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        try:
            obj: Any = json.loads(line)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        out = _handle_request(obj)
        if out is not None:
            sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()

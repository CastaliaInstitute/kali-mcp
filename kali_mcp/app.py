from __future__ import annotations

import os
import uuid
from typing import Any

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from kali_mcp.config import load_settings
from kali_mcp.tools_impl import call_tool, reload_settings, tool_catalog_for_settings

_SESSION_ID: str | None = None


def _session() -> str:
    global _SESSION_ID
    if _SESSION_ID is None:
        _SESSION_ID = str(uuid.uuid4())
    return _SESSION_ID


def _json_rpc(rid: int | str | None, result: Any) -> JSONResponse:
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": rid,
            "result": result,
        },
        headers={
            "Mcp-Protocol-Version": "2024-11-05",
            "Mcp-Session-Id": _session(),
            "Content-Type": "application/json",
        },
    )


def _err_rpc(rid: int | str | None, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": rid,
            "error": {"code": code, "message": message},
        },
        status_code=200,
        headers={
            "Mcp-Protocol-Version": "2024-11-05",
            "Mcp-Session-Id": _session(),
        },
    )


def _coerce_id(v: Any) -> int | str | None:
    if v is None or isinstance(v, (int, str)):
        return v
    return v


async def mcp_entry(request) -> JSONResponse:  # type: ignore[no-untyped-def]
    if request.method not in ("POST", "OPTIONS"):
        if request.method == "GET":
            return JSONResponse(
                {
                    "service": "kali-mcp",
                    "protocol": "JSON-RPC over HTTP (Mcp-Protocol-Version: 2024-11-05)\n"
                    "compatible with the Kaliyai (nethunter-gemini-mcp) McpClient",
                }
            )
        from starlette.responses import Response

        return Response(status_code=405)

    if request.method == "OPTIONS":
        return JSONResponse(
            {},
            headers={
                "Mcp-Protocol-Version": "2024-11-05",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            },
        )

    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        return _err_rpc(None, -32700, "Parse error")

    rid = _coerce_id(body.get("id"))
    method = body.get("method")
    params: dict[str, Any] = body.get("params") or {}
    if not isinstance(params, dict):
        params = {}

    reload_settings()
    s = load_settings()

    if method == "initialize":
        return _json_rpc(
            rid,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "kali-mcp", "version": "0.1.0", "kaliMcp": {"profile": s.profile.value}},
                "capabilities": {"tools": {}},
            },
        )
    if method == "tools/list":
        return _json_rpc(
            rid,
            {"tools": tool_catalog_for_settings(s)},
        )
    if method == "tools/call":
        name = (params.get("name") or "").strip()
        raw = params.get("arguments")
        if raw is not None and not isinstance(raw, (dict, str)):
            return _err_rpc(rid, -32602, "Invalid params: arguments must be object or string")
        dargs: Any = raw if raw is not None else {}
        result = call_tool(name, dargs)
        return _json_rpc(rid, result)

    return _err_rpc(rid, -32601, f"Method not found: {method!r}")


def create_app() -> Starlette:
    m = ["GET", "POST", "OPTIONS", "HEAD"]
    r2 = [
        Route("/", mcp_entry, methods=m),
        Route("/mcp", mcp_entry, methods=m),
        Route("/rpc", mcp_entry, methods=m),
    ]
    return Starlette(
        debug=os.environ.get("KALI_MCP_DEBUG", "0") == "1",
        routes=r2,
    )


# For: uvicorn kali_mcp.app:app
app: Starlette = create_app()

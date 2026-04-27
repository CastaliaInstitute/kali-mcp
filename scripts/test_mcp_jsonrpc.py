#!/usr/bin/env python3
"""
Exercise kali-mcp the same way Kaliyai (McpClient) does: JSON-RPC over HTTP.
Run:  python3 scripts/test_mcp_jsonrpc.py
With:  KALI_MCP_TEST_URL=http://127.0.0.1:8765/  (kali-mcp must be running)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

URL = os.environ.get("KALI_MCP_TEST_URL", "http://127.0.0.1:8765/").rstrip("/") + "/"
SESSION: str | None = None
HDR = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Mcp-Protocol-Version": "2024-11-05",
}


def post(rid: int, method: str, params: dict) -> dict:
    global SESSION
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
    h = {**HDR}
    if SESSION:
        h["Mcp-Session-Id"] = SESSION
    req = urllib.request.Request(URL, data=body.encode(), method="POST", headers=h)  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310
            for k, v in r.headers.items():
                if k.lower() == "mcp-session-id":
                    SESSION = v
            t = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        t = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {t[:500]}", file=sys.stderr)
        raise
    return json.loads(t)


def main() -> int:
    print("URL:", URL, file=sys.stderr)
    r0 = post(0, "initialize", {})
    if r0.get("error"):
        print("initialize error:", r0, file=sys.stderr)
        return 1
    print("initialize: ok, session:", SESSION, file=sys.stderr)
    r1 = post(1, "tools/list", {})
    tools = (r1.get("result") or {}).get("tools", [])
    names = [t.get("name") for t in tools if isinstance(t, dict)]
    need = {
        "searchsploit",
        "resolve_dns",
        "network_status",
        "ping_host",
        "http_head",
        "run_shell",
    }
    missing = need - set(names)
    if missing:
        print("WARNING: tools missing (kali-mcp 0.1+ with exec; check KALI_MCP_* env):", missing, file=sys.stderr)
    else:
        print("tools/list: all", len(need), "Kali+shell tools present", file=sys.stderr)

    if "gvm_info" in names:
        g = post(2, "tools/call", {"name": "gvm_info", "arguments": {}})
        g0 = (g.get("result") or {}).get("content", [{}])
        gtxt = (g0[0] or {}).get("text", "") if g0 else ""
        print("gvm_info:\n", (gtxt or str(g))[:2000], "\n---", file=sys.stderr)
    else:
        print("SKIP: gvm_info not in catalog", file=sys.stderr)

    calls: list[tuple[str, int, dict]] = [
        ("searchsploit", 10, {"query": "openssh"}),
        ("resolve_dns", 11, {"name": "one.one.one.one", "type": "A"}),
        ("network_status", 12, {}),
        ("ping_host", 13, {"host": "127.0.0.1", "count": 1}),
        ("http_head", 14, {"url": "https://example.com"}),
        ("run_shell", 15, {"command": "true"}),
    ]
    for name, rid, args in calls:
        if name not in names:
            print("SKIP (not in catalog):", name, file=sys.stderr)
            continue
        res = post(rid, "tools/call", {"name": name, "arguments": args})
        if res.get("error"):
            print("FAIL (JSON-RPC)", name, res, file=sys.stderr)
            return 1
        inner = (res.get("result") or {})
        err = inner.get("isError")
        c0 = (inner.get("content") or [{}])[0]
        preview = (c0.get("text") or str(inner))[:400]
        st = "ERR" if str(err) == "true" else "ok"
        print(f"tools/call {name}: {st}\n{preview}\n---")
        if str(err) == "true" and os.environ.get("KALI_MCP_SMOKE_STRICT", "").strip() in (
            "1",
            "true",
            "yes",
        ):
            print("KALI_MCP_SMOKE_STRICT: failing on isError in result.", file=sys.stderr)
            return 1
    print(
        "Done: all JSON-RPC calls succeeded. Optional tools may report isError if binaries "
        "are missing on this host (e.g. searchsploit, ip) — set KALI_MCP_SMOKE_STRICT=1 to fail on any.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

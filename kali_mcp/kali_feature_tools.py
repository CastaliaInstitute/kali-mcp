"""Dedicated MCP tools for common Kali workflows (argv-based, no shell on desktop)."""

from __future__ import annotations

import shutil
from typing import Any

from kali_mcp.config import Settings
from kali_mcp.runtime import Outcome, run_kali_argv
from kali_mcp.validators import (
    is_safe_http_probe_url,
    is_safe_searchsploit_query,
    is_safe_target_host,
    normalize_dns_type,
)


def _tstr(args: dict[str, Any], key: str) -> str:
    v = args.get(key)
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (int, float, bool)):
        return str(v)
    return str(v).strip()


def _tint(args: dict[str, Any], key: str, default: int) -> int:
    v = args.get(key)
    if v is None:
        return default
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().lstrip("-").isdigit():
        return int(v.strip(), 10)
    return default


def tool_searchsploit(args: dict[str, Any], s: Settings) -> Outcome:
    q = _tstr(args, "query")
    if not is_safe_searchsploit_query(q):
        return Outcome(
            False,
            "searchsploit: 'query' must be 1–200 chars: letters, digits, space, - . _ / only.",
        )
    to = int(_tint(args, "timeout_sec", 60))
    bin_ = shutil.which("searchsploit")
    if not bin_:
        return Outcome(False, "searchsploit: not in PATH (install exploitdb on Kali).")
    return run_kali_argv([bin_, "-j", q], to, s, tag="searchsploit")


def tool_resolve_dns(args: dict[str, Any], s: Settings) -> Outcome:
    name = _tstr(args, "name")
    if not is_safe_target_host(name):
        return Outcome(
            False,
            "resolve_dns: 'name' must be a hostname or IP (letters, digits, - . and IPv4/6).",
        )
    dth = normalize_dns_type(_tstr(args, "type"))
    digp = shutil.which("dig")
    if not digp:
        return Outcome(
            False,
            "resolve_dns: dig(1) not in PATH (e.g. apt install dnsutils on Kali).",
        )
    to = int(_tint(args, "timeout_sec", 25))
    return run_kali_argv(
        [digp, "+time=2", "+tries=1", "-t", dth, name, "+short"],
        to,
        s,
        tag="resolve_dns",
    )


def tool_network_status(s: Settings) -> Outcome:
    to = 45
    parts: list[str] = []
    for label, av in [
        ("ip -br a", ["ip", "-br", "a"]),
        ("ip route", ["ip", "route"]),
        ("ss -tuln", ["ss", "-tuln"]),
    ]:
        b0 = av[0]
        if not shutil.which(b0):
            parts.append(f"=== {label} ===\n{b0}: not in PATH")
            continue
        o = run_kali_argv(av, to, s, tag=label)
        parts.append(f"=== {label} ===\n{o.text}")
    return Outcome(True, "\n\n".join(parts))


def tool_ping_host(args: dict[str, Any], s: Settings) -> Outcome:
    h = _tstr(args, "host")
    if not is_safe_target_host(h):
        return Outcome(
            False,
            "ping_host: 'host' must be a hostname, IPv4, or bracketed IPv6.",
        )
    c = min(max(1, int(_tint(args, "count", 3))), 10)
    to = min(90, max(5, int(_tint(args, "timeout_sec", 20)) + c * 2))
    pingp = shutil.which("ping")
    if not pingp:
        return Outcome(False, "ping_host: ping(8) not in PATH.")
    return run_kali_argv(
        [pingp, "-c", str(c), "-W", "2", h],
        to,
        s,
        tag="ping_host",
    )


def tool_http_head(args: dict[str, Any], s: Settings) -> Outcome:
    u = _tstr(args, "url")
    if not is_safe_http_probe_url(u):
        return Outcome(
            False,
            "http_head: 'url' must be http(s) with a safe host, no user:pass@, max 2k chars.",
        )
    to = int(_tint(args, "timeout_sec", 25))
    curlb = shutil.which("curl")
    if not curlb:
        return Outcome(False, "http_head: curl(1) not in PATH.")
    return run_kali_argv(
        [curlb, "-sS", "-I", "-L", "-m", "15", u],
        to,
        s,
        tag="http_head",
    )

from __future__ import annotations

import importlib.resources
import json
import os
import platform
import re
import shutil
import subprocess
from typing import Any

from kali_mcp.config import Profile, Settings, load_settings
from kali_mcp.nmap_profiles import NMAP_ALL, to_command
from kali_mcp.runtime import Outcome, gvm_cli_line, is_safe_abs_path, is_safe_host, run_kali_line
from kali_mcp.safety import is_gmp_readonly_get_request, is_safe_nmap_token, is_semi_interactive_tty_request

_NUM = re.compile(r"^[-+]?\d+$")

_SETTINGS: Settings = load_settings()


def reload_settings() -> None:
    global _SETTINGS
    _SETTINGS = load_settings()


def mcp_text(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


def mcp_err(text: str) -> dict:
    return {"isError": "true", "content": [{"type": "text", "text": text}]}


def _int(args: dict[str, Any], key: str, default: int) -> int:
    v = args.get(key)
    if v is None:
        return default
    if isinstance(v, int):
        return v
    if isinstance(v, str) and _NUM.match(v.strip()):
        return int(v.strip(), 10)
    return default


def _str(args: dict[str, Any], key: str) -> str:
    v = args.get(key)
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (int, float, bool)):
        return str(v)
    return str(v).strip()


def _wifi_scan() -> str:
    nm = shutil.which("nmcli")
    if nm:
        p = subprocess.run(
            [nm, "-e", "no", "-f", "SSID,BSSID,CHAN,ACTIVE,SIGNAL,CHAN-FREQ", "dev", "wifi"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
        if p.returncode != 0 and not p.stdout:
            return f"wifi_scan (nmcli failed)\n{out[:8000]}"
        lines = [ln for ln in out.splitlines() if ln.strip()][:100]
        return f"wifi_scan (nmcli) — {len(lines)} rows\n" + "\n".join(lines)
    return (
        "wifi_scan: nmcli not found. On Kali desktop, install `network-manager` and ensure "
        "wireless is managed (or use a NetHunter device with the Anubis built-in wifi_scan)."
    )


def _device_info() -> str:
    rel = "unknown"
    p = "/etc/os-release"
    if os.path.isfile(p):
        rel = Path_read(p)[:2000]
    u = f"{platform.system()} {platform.release()} {platform.machine()}"
    host = os.uname().nodename
    return (
        f"kali-mcp device_info (profile={_SETTINGS.profile.value})\n"
        f"host={host}\nuname={u}\n[os-release]\n{rel}"
    )


def Path_read(path: str, limit: int = 8000) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError as e:
        return f"(read error: {e})"


def _kali_nethunter_info() -> str:
    su = shutil.which("su")
    s = _SETTINGS
    p = s.profile
    if p == Profile.desktop:
        nm = shutil.which("nmap")
        gvmc = shutil.which("gvm-cli")
        return (
            "kali_nethunter_info (desktop profile: host shell, no chroot; same tool name as on NetHunter)\n"
            f"execEnabled={s.exec_enabled} suInPath={su or '(none)'} nmap={nm or 'missing'} gvm-cli={gvmc or 'missing'}"
        )
    return (
        f"kali_nethunter_info (nethunter: su→{s.su_path or 'auto'}) chroot shims={list(s.chroot_shims)}\n"
        f"execEnabled={s.exec_enabled} nmap: use nmap_scan"
    )


def _kali_nethunter_list_tools() -> str:
    names: list[str] = []
    try:
        with importlib.resources.as_file(
            importlib.resources.files("kali_mcp").joinpath("data/kali_tool_catalog.txt")
        ) as f:
            raw = f.read_text(encoding="utf-8", errors="replace")
        for line in raw.splitlines():
            line = line.split("#", 1)[0].strip()
            if line and not line.startswith("#"):
                names.append(line)
    except OSError:
        names = ["nmap", "gvm-cli", "sqlmap"]
    names = sorted({n for n in names if n}, key=str.lower)
    head = names[:400]
    return (
        f"kali_nethunter_list_tools: {len(head)} of {len(names)} names in embedded catalog (not all may be installed).\n\n"
        + "\n".join(head)
    )


def _nmap(args: dict[str, Any]) -> Outcome:
    s = _SETTINGS
    if not s.exec_enabled:
        return Outcome(
            False,
            "nmap_scan: KALI_MCP exec disabled. Set KALI_MCP_EXEC_ENABLED=1 (default) or check KALI_MCP_EXEC_DISABLED",
        )
    t = _str(args, "target")
    if not t:
        return Outcome(
            False,
            "nmap_scan: required 'target' (string): host, IP, or CIDR (e.g. 192.168.1.1, scanme.nmap.org).",
        )
    if not is_safe_nmap_token(t, 220):
        return Outcome(False, "nmap_scan: target uses unsupported characters (no shell metacharacters).")
    prof = (_str(args, "profile") or "ping").lower()
    if prof not in NMAP_ALL:
        return Outcome(False, f"nmap_scan: profile must be one of: {', '.join(NMAP_ALL)}. Default: ping")
    pt = _str(args, "ports")
    if prof == "custom_ports" and not pt:
        return Outcome(False, "nmap_scan: for profile=custom_ports, set 'ports' (e.g. 1-1024,443).")
    if pt and (len(pt) > 120 or not is_safe_nmap_token(pt, 120)):
        return Outcome(
            False,
            "nmap_scan: 'ports' use forms like 80,443 or 1-1000 (letters as nmap allows in token set).",
        )
    to = int(_int(args, "timeout_sec", 120))
    line = to_command(prof, t, pt or None)
    if is_semi_interactive_tty_request(line):
        return Outcome(False, "nmap_scan: internal build rejected (safety).")
    o = run_kali_line(line, to, s)
    rpt = (
        "NMAP SCAN REPORT (kali-mcp)\n"
        f"  profile: {prof}\n  target: {t}\n  command: {line}\n"
        f"  status: {'ok' if o.ok else 'nmap or wrapper reported a problem'}\n"
        f"{'─' * 40}\n\n" + o.text
    )
    return Outcome(o.ok, rpt)


def _gvm(args: dict[str, Any]) -> Outcome:
    s = _SETTINGS
    if not s.exec_enabled:
        return Outcome(
            False,
            "gvm_cli: KALI_MCP exec disabled. Set KALI_MCP_EXEC_ENABLED=1 and restart the server.",
        )
    x = _str(args, "gmp_xml")
    if not x:
        return Outcome(
            False,
            "gvm_cli: required 'gmp_xml' (read-only <get_…/>, e.g. <get_version/>, <get_vts filter=\"rows=20\"/>).",
        )
    if not is_gmp_readonly_get_request(x):
        return Outcome(
            False,
            "gvm_cli: gmp_xml rejected. Only read-only GMP (starts with <get_…>); no shell, max 8KiB.",
        )
    pw = _str(args, "gmp_password") or s.gmp_default_password
    if not pw:
        return Outcome(
            False,
            "gvm_cli: set GMP password via KALI_MCP_GMP_PASSWORD, GMP_PASSWORD, or gmp_password in the tool call.",
        )
    u = _str(args, "gmp_username") or s.gmp_username
    host = _str(args, "hostname") or s.gmp_host
    if not is_safe_host(host):
        return Outcome(False, "gvm_cli: hostname not allowed.")
    prt = int(_int(args, "port", s.gmp_port))
    if prt < 1 or prt > 65535:
        return Outcome(False, "gvm_cli: port 1–65535")
    ca = _str(args, "cafile") or s.gmp_cafile
    if not ca:
        return Outcome(
            False,
            "gvm_cli: set cafile (absolute) or KALI_MCP_GMP_CAFILE in the environment.",
        )
    if not is_safe_abs_path(ca):
        return Outcome(False, "gvm_cli: cafile must be an absolute, safe path.")
    to = int(_int(args, "timeout_sec", 60))
    line = gvm_cli_line(x, u, pw, host, prt, ca, s)
    if is_semi_interactive_tty_request(line):
        return Outcome(False, "gvm_cli: command build rejected (safety).")
    o = run_kali_line(line, to, s)
    head = "GMP / gvm-cli (kali-mcp — OpenVAS / Greenbone)\n" f"  host: {host}:{prt}\n  command: {line}\n"
    rpt = head + f"  status: {'ok' if o.ok else 'error in output below'}\n{'─' * 40}\n\n" + o.text
    return Outcome(o.ok, rpt)


def _run_arbitrary_command(
    args: dict[str, Any],
    tool: str,
    *,
    response_header: bool = False,
) -> Outcome:
    """Single non-interactive line: bash -lc (desktop) or chroot (nethunter)."""
    s = _SETTINGS
    c = _str(args, "command")
    if not c:
        return Outcome(False, f"{tool}: required 'command' (string)")
    t = int(_int(args, "timeout_sec", 120))
    if is_semi_interactive_tty_request(c):
        return Outcome(
            False,
            f"{tool}: use non-interactive one-liners only (no TUI, login shells, ssh, msfconsole, etc.).",
        )
    o = run_kali_line(c, t, s)
    if not response_header:
        return o
    head = f"{tool}  profile={s.profile.value}  exit_ok={o.ok}\n"
    return Outcome(o.ok, head + o.text)


def call_tool(name: str, raw: Any) -> dict:
    if raw in (None, ""):
        args: dict[str, Any] = {}
    elif isinstance(raw, dict):
        args = {str(k): v for k, v in raw.items()}
    else:
        try:
            s = str(raw) if not isinstance(raw, str) else raw
            args = json.loads(s) if s else {}
        except (json.JSONDecodeError, TypeError) as e:
            return mcp_err(f"Invalid tool arguments: {e}")
    if not isinstance(args, dict):
        return mcp_err("tool arguments must be a JSON object")
    a = {str(k): v for k, v in args.items()}

    if name == "echo":
        return mcp_text("echo: " + _str(a, "message").replace("\n", "\\n") or "empty")
    if name == "device_info":
        return mcp_text(_device_info())
    if name == "wifi_scan":
        return mcp_text(_wifi_scan())
    if name == "kali_nethunter_info":
        return mcp_text(_kali_nethunter_info())
    if name == "kali_nethunter_list_tools":
        return mcp_text(_kali_nethunter_list_tools())
    if name == "nmap_scan":
        o = _nmap(a)
        return mcp_text(o.text) if o.ok else mcp_err(o.text)
    if name == "gvm_cli":
        o = _gvm(a)
        return mcp_text(o.text) if o.ok else mcp_err(o.text)
    if name == "kali_nethunter_exec":
        if not _SETTINGS.exec_enabled:
            return mcp_err(
                "kali_nethunter_exec: KALI_MCP exec disabled. Set KALI_MCP_EXEC_ENABLED=1",
            )
        o = _run_arbitrary_command(a, "kali_nethunter_exec", response_header=False)
        return mcp_text(o.text) if o.ok else mcp_err(o.text)
    if name == "run_shell":
        if not _SETTINGS.shell_enabled:
            return mcp_err(
                "run_shell: disabled. Set KALI_MCP_EXEC_ENABLED=1 and clear KALI_MCP_SHELL_DISABLED.",
            )
        o = _run_arbitrary_command(a, "run_shell", response_header=True)
        return mcp_text(o.text) if o.ok else mcp_err(o.text)
    return mcp_err(f"unknown tool: {name}")


# Tool definitions: JSON Schemas (subset matching Anubis)
def tool_catalog_for_settings(s: Settings) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = [
        {
            "name": "echo",
            "description": "Echo a string (tests tool wiring).",
            "inputSchema": {
                "type": "object",
                "properties": {"message": {"type": "string", "description": "Text to echo"}},
                "required": ["message"],
            },
        },
        {
            "name": "device_info",
            "description": "Host uname, profile (desktop / nethunter), and /etc/os-release (server-side kali-mcp).",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "wifi_scan",
            "description": "List Wi-Fi (nmcli on Kali desktop; for Android use Anubis built-in wifi_scan).",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "kali_nethunter_info",
            "description": "Server profile, exec, su/chroot. Same tool name on NetHunter and Kali desktop.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "kali_nethunter_list_tools",
            "description": "Kali/NetHunter tool names (embedded catalog).",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]
    if s.exec_enabled:
        if s.shell_enabled:
            tools += [
                {
                    "name": "run_shell",
                    "description": "Run a single non-interactive shell line for the LLM: pipeline and && allowed; "
                    "executed as bash -lc on Kali desktop or inside the NetHunter chroot when "
                    "KALI_MCP_PROFILE=nethunter. Blocked: interactive TUIs, login shells, msfconsole, "
                    "ssh, etc. Expose this server only on trusted networks.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "One shell line (e.g. 'ls -la /tmp', 'head -5 /etc/os-release')",
                            },
                            "timeout_sec": {
                                "type": "integer",
                                "description": "Optional; default 120, max 600",
                            },
                        },
                        "required": ["command"],
                    },
                },
            ]
        tools += [
            {
                "name": "nmap_scan",
                "description": "nmap; profiles: ping, quick, standard, version, custom_ports. Authorized networks only.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"},
                        "profile": {"type": "string"},
                        "ports": {"type": "string"},
                        "timeout_sec": {"type": "integer"},
                    },
                    "required": ["target"],
                },
            },
            {
                "name": "gvm_cli",
                "description": "gvm-cli read-only <get_…> GMP XML against gvmd. Password via env or gmp_password.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "gmp_xml": {"type": "string"},
                        "gmp_username": {"type": "string"},
                        "gmp_password": {"type": "string"},
                        "hostname": {"type": "string"},
                        "port": {"type": "integer"},
                        "cafile": {"type": "string"},
                        "timeout_sec": {"type": "integer"},
                    },
                    "required": ["gmp_xml"],
                },
            },
            {
                "name": "kali_nethunter_exec",
                "description": "On desktop: one bash -lc line. On NetHunter (KALI_MCP_PROFILE=nethunter): su→chroot shims bootkali/kali/nethunter.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "timeout_sec": {"type": "integer"},
                    },
                    "required": ["command"],
                },
            },
        ]
    return tools

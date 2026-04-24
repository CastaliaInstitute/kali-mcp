import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from kali_mcp.config import Profile, Settings

MAX_OUTPUT = 256 * 1024

_HOST_RE = re.compile(r"^[a-zA-Z0-9.\-:_\[\]]{1,253}$")


@dataclass(frozen=True)
class Outcome:
    ok: bool
    text: str


def _find_su() -> str | None:
    out = (os.environ.get("KALI_MCP_SU") or os.environ.get("KALI_MCP_SU_PATH") or "").strip()
    if out and Path(out).exists():
        return out
    for p in ("/data/adb/magisk/su", "/system/xbin/su", "/system/bin/su", "/sbin/su", "/usr/bin/su"):
        if Path(p).exists():
            return p
    s = shutil.which("su")
    return s


def sh_quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


def is_safe_host(host: str) -> bool:
    return bool(host) and len(host) <= 253 and bool(_HOST_RE.match(host))


def is_safe_abs_path(p: str) -> bool:
    if not p or not p.startswith("/") or len(p) > 240:
        return False
    for c in "<>|;`$()&\n\r":
        if c in p:
            return False
    return True


def _run_direct(line: str, timeout_sec: int) -> Outcome:
    t = min(max(5, timeout_sec), 600)
    try:
        p = subprocess.run(
            ["/bin/bash", "-lc", line],
            capture_output=True,
            text=True,
            timeout=t,
        )
        out = p.stdout
        if p.stderr:
            out = (out + "\n" if out else "") + p.stderr
        if len(out) > MAX_OUTPUT:
            out = out[: MAX_OUTPUT - 32] + "\n…(output truncated)…\n"
        text = f"[bash] exit={p.returncode}\n{out}"
        return Outcome(p.returncode == 0, text)
    except subprocess.TimeoutExpired as e:
        return Outcome(False, f"[bash] (timeout {t}s)\n{e}\n")
    except OSError as e:
        return Outcome(False, f"[bash] {e}")


def _run_nethunter(line: str, timeout_sec: int, s: Settings) -> Outcome:
    su = s.su_path or _find_su()
    if not su:
        return Outcome(False, "kali_nethunter_exec: no su found. Set KALI_MCP_SU for NetHunter profile.")
    t = min(max(5, timeout_sec), 600)
    shims: list[str] = list(s.chroot_shims) or ["bootkali", "kali", "nethunter"]
    last_err: str | None = None
    for sh in shims:
        cmd = [su, "0", sh, "bash", "-lc", line]
        try:
            p = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=t,
            )
            out = p.stdout + (("\n" + p.stderr) if p.stderr else "")
            if len(out) > MAX_OUTPUT:
                out = out[: MAX_OUTPUT - 32] + "\n…(output truncated)…\n"
            body = f"[su→{sh}] exit={p.returncode}\n{out}"
            if p.returncode == 0:
                return Outcome(True, body)
            last_err = body
            low = body.lower()
            if "no such file" in low or "not found" in low:
                continue
            return Outcome(False, body)
        except subprocess.TimeoutExpired as e:
            return Outcome(False, f"[su→{sh}] (timeout {t}s)\n{e}\n")
        except OSError as e:
            last_err = f"[su→{sh}] {e}"
    return Outcome(False, last_err or "kali_nethunter_exec: all shims failed")


def run_kali_line(line: str, timeout_sec: int, s: Settings) -> Outcome:
    if s.profile == Profile.nethunter:
        return _run_nethunter(line, timeout_sec, s)
    return _run_direct(line, timeout_sec)


def run_kali_argv(
    argv: list[str],
    timeout_sec: int,
    s: Settings,
    *,
    tag: str = "argv",
) -> Outcome:
    """
    No shell. Desktop: subprocess(argv). NetHunter: chroot one-liner via shlex.join (only use with trusted argv).
    """
    if not argv or not (argv[0] or "").strip():
        return Outcome(False, f"{tag}: empty command")
    t = min(max(3, timeout_sec), 600)
    if s.profile == Profile.nethunter:
        line = shlex.join(argv)
        return _run_nethunter(line, t, s)
    return _run_argv_list(argv, t, tag=tag)


def _run_argv_list(argv: list[str], timeout_sec: int, tag: str) -> Outcome:
    t = min(max(3, timeout_sec), 600)
    try:
        p = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=t,
        )
    except FileNotFoundError as e:
        return Outcome(False, f"{tag}: not found: {argv[0]} ({e})")
    except OSError as e:
        return Outcome(False, f"{tag}: {e}")
    except subprocess.TimeoutExpired as e:
        return Outcome(False, f"{tag} (timeout {t}s): {e}")
    out = p.stdout or ""
    if p.stderr:
        out = (out + "\n" if out else "") + p.stderr
    if len(out) > MAX_OUTPUT:
        out = out[: MAX_OUTPUT - 32] + "\n…(output truncated)…\n"
    return Outcome(p.returncode == 0, f"[{tag}] exit={p.returncode}\n{out}")


def gvm_cli_line(
    gmp_xml: str,
    gmp_user: str,
    gmp_password: str,
    host: str,
    port: int,
    ca_file: str,
    s: Settings,
) -> str:
    """Build one bash line. NetHunter: runuser in chroot. Desktop: gvm-cli in PATH (often run the server as root or gvm)."""
    inner = (
        f"gvm-cli --gmp-username {sh_quote(gmp_user)} --gmp-password {sh_quote(gmp_password)} "
        f"tls --hostname {sh_quote(host)} --port {port} --cafile {sh_quote(ca_file)} "
        f"-X {sh_quote(gmp_xml)} --pretty"
    )
    if s.profile == Profile.nethunter:
        return (
            f"export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; "
            f"export HOME=/var/lib/gvm; "
            f"/usr/sbin/runuser -u _gvm -- {inner}"
        )
    return inner

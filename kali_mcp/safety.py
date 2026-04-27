"""Nmap, GMP XML, and TUI heuristics (ported from Kaliyai / BuiltinMcpEngine)."""

GMP_DANGEROUS = (
    "<create_",
    "<delete_",
    "<modify_",
    "<update_",
    "<start_",
    "<import_",
    "<empty_",
    "<stop_task",
    "<restore",
    "<rebuild",
    "<move_task",
    "<run_wizard",
    "<run",
)
GMP_BLOCKED = ("<!--", "<!doctype", "<![cdata[", "<?xml", "&#", "<script")
DISALLOWED_EXEC = (
    "msfconsole",
    "vim ",
    " vi ",
    "nano",
    "htop",
    "less ",
    "more ",
    "man ",
    "ssh ",
    "wifite",
    "wireshark",
)


def is_gmp_readonly_get_request(xml: str) -> bool:
    t = xml.strip()
    if not t or len(t) > 8192:
        return False
    for c in t:
        o = ord(c) if c != "\n" and c != "\r" and c != "\t" else 0
        if 0 < o < 32:
            return False
    if any(x in t for x in ("`", "$", "|", ";")):
        return False
    for b in GMP_BLOCKED:
        if b.lower() in t.lower():
            return False
    s = t.lstrip()
    if not s.lower().startswith("<get_"):
        return False
    for d in GMP_DANGEROUS:
        if d.lower() in t.lower():
            return False
    return True


def is_safe_nmap_token(s: str, max_len: int) -> bool:
    if not s or len(s) > max_len:
        return False
    for c in s:
        if c in "\n\r ":
            return False
    allow = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-:/%[],"
    return all(c in allow for c in s)


def is_semi_interactive_tty_request(line: str) -> bool:
    t = line.lower()
    if t.startswith("msfconsole") or t in ("sh", "bash", "zsh"):
        return True
    if t.strip() == "top" or t.startswith("top "):
        return True
    if "<<" in t:
        return True
    for d in DISALLOWED_EXEC:
        if d in t:
            return True
    return False

"""Strict input checks for Kali feature tools (no shell injection)."""

import ipaddress
import re
from urllib.parse import urlparse

# Exploit-DB / searchsploit: words, digits, space, version-ish punctuation
_SEARCHSPLOIT_RE = re.compile(r"^[a-zA-Z0-9 \-._/+]{1,200}$")
_DNS_TYPE = frozenset({"A", "AAAA", "CNAME", "MX", "NS", "PTR", "SOA", "TXT"})


def is_safe_searchsploit_query(s: str) -> bool:
    t = s.strip()
    if not t:
        return False
    return bool(_SEARCHSPLOIT_RE.match(t))


# Hostname, IPv4, or bracketed IPv6 (same spirit as nmap target token)
def is_safe_target_host(s: str) -> bool:
    t = s.strip()
    if not t or len(t) > 253:
        return False
    if t.startswith("[") and t.endswith("]") and len(t) > 2:
        inner = t[1:-1]
        try:
            ipaddress.ip_address(inner)
        except ValueError:
            return False
        return True
    if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", t):
        parts = t.split(".")
        return all(0 <= int(p) <= 255 for p in parts)
    try:
        ipaddress.ip_address(t)
        return True
    except ValueError:
        pass
    return bool(re.match(r"^[a-zA-Z0-9._\-]{1,253}$", t))


def normalize_dns_type(raw: str) -> str:
    t = (raw or "A").upper().strip()
    return t if t in _DNS_TYPE else "A"


def is_safe_http_probe_url(u: str) -> bool:
    t = (u or "").strip()
    if not t or len(t) > 2000:
        return False
    p = urlparse(t)
    if p.scheme not in ("http", "https"):
        return False
    if p.username or p.password or "@" in t.split("://", 1)[-1].split("/")[0]:
        return False
    if not p.netloc or "/" in t and not p.netloc:
        return False
    host = p.hostname
    if not host:
        return False
    if len(host) > 253:
        return False
    return is_safe_target_host(host) or host.startswith("[")

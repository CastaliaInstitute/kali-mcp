import os
from dataclasses import dataclass
from enum import Enum


class Profile(str, Enum):
    """How shell commands are executed (Kali desktop vs NetHunter chroot)."""

    desktop = "desktop"
    nethunter = "nethunter"


@dataclass(frozen=True)
class Settings:
    """Environment-driven. Same code path on Kali VM (desktop) and NetHunter (nethunter)."""

    profile: Profile
    exec_enabled: bool
    shell_enabled: bool
    kali_feature_tools_enabled: bool
    su_path: str | None
    chroot_shims: tuple[str, ...]
    gmp_username: str
    gmp_default_password: str
    gmp_host: str
    gmp_port: int
    gmp_cafile: str
    gmp_tls_insecure: bool


def _b(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default) in ("1", "true", "True", "yes", "on")


def load_settings() -> Settings:
    raw = (os.environ.get("KALI_MCP_PROFILE", "desktop") or "desktop").lower().strip()
    try:
        profile = Profile(raw)
    except ValueError:
        profile = Profile.desktop
    shims = os.environ.get("KALI_MCP_CHROOT_SHIMS", "bootkali kali nethunter")
    su = (os.environ.get("KALI_MCP_SU") or os.environ.get("KALI_MCP_SU_PATH") or "").strip() or None
    ex = not _b("KALI_MCP_EXEC_DISABLED") and _b("KALI_MCP_EXEC_ENABLED", "1")
    return Settings(
        profile=profile,
        exec_enabled=ex,
        shell_enabled=ex and not _b("KALI_MCP_SHELL_DISABLED"),
        kali_feature_tools_enabled=ex and not _b("KALI_MCP_KALI_FEATURES_DISABLED"),
        su_path=su,
        chroot_shims=tuple(s for s in shims.split() if s),
        gmp_username=(os.environ.get("KALI_MCP_GMP_USER") or os.environ.get("GMP_USER") or "_gvm")
        or "_gvm",
        gmp_default_password=os.environ.get("KALI_MCP_GMP_PASSWORD", "")
        or os.environ.get("GMP_PASSWORD", "")
        or "",
        gmp_host=(os.environ.get("KALI_MCP_GMP_HOST") or "127.0.0.1").strip() or "127.0.0.1",
        gmp_port=int(
            (os.environ.get("KALI_MCP_GMP_PORT") or "9390").split("#", 1)[0].strip() or "9390"
        ),
        gmp_cafile=(os.environ.get("KALI_MCP_GMP_CAFILE") or "").strip() or "/var/lib/gvm/CA/cacert.pem",
        gmp_tls_insecure=_b("KALI_MCP_GMP_TLS_INSECURE"),
    )

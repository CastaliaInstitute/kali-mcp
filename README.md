# kali-mcp

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/CastaliaInstitute/kali-mcp?quickstart=1)

**One MCP, two ways to use it (same `tools/*` contract, different “where the server runs”):**

1. **Anubis (Android app)** — Anubis stays the **Gemini client and optional built-in** tools. Point **Settings → MCP base URL** at a running kali-mcp. Anubis still loads **remote** tools from this server; built-in (e.g. Android `wifi_scan`) is unchanged. Same JSON-RPC as `McpClient` (`initialize`, `tools/list`, `tools/call`, `Mcp-Protocol-Version` / `Mcp-Session-Id`).

2. **GitHub Codespace (Kali devcontainer here)** — Run the **same** `kali-mcp` process in the Kali container for local testing: `./scripts/test-mcp-like-anubis.sh`, VS Code **Tasks** (`kali-mcp: run server` / `test JSON-RPC`), and forwarded port **8765**. The Codespaces “Ports” tab shows a public HTTPS URL; you can use that in Anubis on a real phone **only if** the device can reach the internet and that host (treat it like a dev server URL).

3. **Any Kali/VM/NetHunter** — `pip install -e .` and `kali-mcp` (default `0.0.0.0:8765`).

`KALI_MCP_PROFILE=desktop` on full Kali; `nethunter` = `su` + chroot shims (`bootkali` / `kali` / `nethunter`).

| Where kali-mcp runs | How you connect Anubis (or curl) |
|--------------------|----------------------------------|
| This repo in **Codespace** | Forward **8765**; test from the Codespace terminal with `http://127.0.0.1:8765/`; for a phone, use the forwarded public URL in Settings if reachable. |
| **Kali/VM** on your LAN | `http://<machine-ip>:8765/` (same network as the phone) |
| **USB to dev machine** | `adb reverse tcp:8765 tcp:8765` and `http://127.0.0.1:8765/` in Anubis (localhost is the dev machine) |
| **kali-mcp on the same phone** (Anubis + server both on Android) | Run the Python app **on the device** (e.g. **Termux** or inside the **NetHunter chroot**), bind `0.0.0.0:8765`, set Anubis **MCP base URL** to `http://127.0.0.1:8765/` — **no** `adb reverse` (see below). |

**kali-mcp does not replace** the Anubis app — it is the **deployable MCP process** for Kali feature tools so tests and the phone can share one server implementation.

### kali-mcp on the Android device (no PC)

The server does **not** have to be Linux-on-desktop: it is plain **Python 3** + **uvicorn**. You can run it **on the phone** so tool execution and Anubis share the same machine.

1. **Termux** (common path): install [Termux](https://github.com/termux/termux-app), `pkg update && pkg install python python-pip`, clone or copy the `kali-mcp` tree, `pip install -e .`, then:
   ```bash
   export KALI_MCP_HOST=0.0.0.0 KALI_MCP_PORT=8765 KALI_MCP_PROFILE=nethunter
   kali-mcp
   ```
   In Anubis: **MCP base URL** `http://127.0.0.1:8765/`, **Refresh MCP**. Keep Termux in the foreground (or use a wakelock); Android may kill background servers.

2. **NetHunter chroot** (you already have Kali userland on the device): use a **root** or **NetHunter terminal** so `su` and the chroot shims match what kali-mcp expects. Typical flow:
   ```bash
   # Example; your image may use `bootkali`, `kali`, `nethunter -c`, etc.
   bootkali kali          # or:  nethunter -c "bash -l"  — enter Kali environment
   apt update && apt install -y python3 python3-venv python3-pip   # if not already
   cd /path/to/kali-mcp && python3 -m venv .venv && . .venv/bin/activate && pip install -e .
   export KALI_MCP_HOST=0.0.0.0 KALI_MCP_PORT=8765 KALI_MCP_PROFILE=nethunter
   kali-mcp
   ```
   If `which su` / chroot paths differ from the defaults, set `KALI_MCP_SU` and `KALI_MCP_CHROOT_SHIMS` (see **Environment** below). **Anubis → MCP base URL:** `http://127.0.0.1:8765/` then **Refresh MCP** — traffic stays on the phone; **no** USB `adb reverse` to a PC when the server runs on-device.

3. **Not the same** as `builtin` Anubis tools: those run **inside the app**. **kali-mcp on device** is still a **separate process**; it’s just that both run on Android instead of a laptop.

4. If you do **not** need a second HTTP process on the phone, you can keep using only **in-app** Kali/NetHunter tools (no kali-mcp) — but a **single** on-device kali-mcp gives one JSON-RPC server for the same `tools/*` contract as your desktop image.

## Test (same wire format as Anubis)

With `kali-mcp` running (default `8765`):

```bash
./scripts/test-mcp-like-anubis.sh
# or:  KALI_MCP_TEST_URL=http://127.0.0.1:8765/ python3 scripts/test_mcp_jsonrpc.py
```

Exercises `initialize`, `tools/list`, and `tools/call` for `searchsploit`, `resolve_dns`, `network_status`, `ping_host`, `http_head`, `run_shell`. A missing `searchsploit` or `ip` binary shows `isError` in the result but still exits 0; use `KALI_MCP_SMOKE_STRICT=1` to fail in that case.

**Anubis (device)**: in the **nethunter-gemini-mcp (Anubis)** repo, `scripts/ask-kali-mcp-prompts.sh` sends user messages that should trigger the LLM to call the tools above. Set the app **MCP Base URL** to your kali-mcp, tap **Refresh MCP**; for USB to a host on port 8765: `adb reverse tcp:8765 tcp:8765` and `http://127.0.0.1:8765/`; emulators often use `http://10.0.2.2:8765/`.

## Container deploy (GHCR + Docker)

On every push to `main` (and **workflow dispatch**), GitHub Actions builds and pushes:

`ghcr.io/<lowercase-owner>/kali-mcp:latest` and `:sha-<commit>`

**Pull and run** (package may be private to the org until you make it public: **Package settings → Change visibility**):

```bash
docker pull ghcr.io/castaliainstitute/kali-mcp:latest
docker run --rm -p 8765:8765 ghcr.io/castaliainstitute/kali-mcp:latest
```

**Compose** (from this repo): `docker compose up --build` — same port **8765** as everywhere else (Anubis MCP URL `http://<host>:8765/`).

## Run (local or VM)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
export KALI_MCP_PROFILE=desktop   # default
kali-mcp
# or: python -m kali_mcp
```

List tools:

```bash
curl -sS -X POST http://127.0.0.1:8765/ -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | jq .
```

## Environment (selection)

| Variable | Meaning |
|----------|---------|
| `KALI_MCP_PROFILE` | `desktop` (default) or `nethunter` |
| `KALI_MCP_HOST` / `KALI_MCP_PORT` | Bind address (default `0.0.0.0:8765`) |
| `KALI_MCP_EXEC_ENABLED` | `1` (default) — if `0` or set `KALI_MCP_EXEC_DISABLED=1`, nmap/gvm/exec and `run_shell` are off |
| `KALI_MCP_SHELL_DISABLED` | set to `1` to hide the **`run_shell`** tool only (keeps nmap, gvm, `kali_nethunter_exec` when exec is on) |
| `KALI_MCP_KALI_FEATURES_DISABLED` | set to `1` to hide the extra Kali helpers (`searchsploit`, `resolve_dns`, `network_status`, `ping_host`, `http_head`) |
| `KALI_MCP_SU` / `KALI_MCP_SU_PATH` | NetHunter: path to `su` |
| `KALI_MCP_CHROOT_SHIMS` | NetHunter: e.g. `bootkali kali nethunter` |
| `KALI_MCP_GMP_HOST` / `KALI_MCP_GMP_PORT` / `KALI_MCP_GMP_USER` / `KALI_MCP_GMP_CAFILE` / `KALI_MCP_GMP_PASSWORD` | defaults for `gvm_cli` (also `GMP_USER` / `GMP_PASSWORD`) |
| `KALI_MCP_GMP_TLS_INSECURE` | `1` to use `gvm-cli tls --insecure` and skip a CA file (**dev only**; e.g. tunnel or lab). |

## GitHub Codespaces (Kali) — test the same MCP as Anubis

Open the repo in a **Codespace** (badge or **Code → Codespace** on [github.com/CastaliaInstitute/kali-mcp](https://github.com/CastaliaInstitute/kali-mcp)). The **devcontainer** is **Kali rolling**: installs `nmap`, `iproute2` (`ip`, `ss`), `dnsutils` (`dig`), optional `exploitdb` (for `searchsploit`), `network-manager` (`nmcli`), then `pip install -e .` on create.

After the container is ready: `source .venv/bin/activate && kali-mcp`, or **Run Task → kali-mcp: run server (8765)**. For GMP (Greenbone) credentials in one place, prefer `./scripts/codespace-kali-mcp.sh` — it sources **`.devcontainer/gmp.env`** if present, then `exec kali-mcp` (default bind `0.0.0.0:8765`). Copy **`.devcontainer/gmp.env.example` → `gmp.env`** and fill in host, port, user, password, and either a CA file path or `KALI_MCP_GMP_TLS_INSECURE=1` for a dev-insecure path. `gmp.env` is git-ignored. Use **Run Task → kali-mcp: test JSON-RPC** only while the server is up (or run the smoke script). Port **8765** is forwarded; use the **ports** view for the public URL to paste into Anubis in dev.

### GMP / OpenVAS (Greenbone) from Codespace

- **Client:** the devcontainer installs `gvm-cli` (or `gvm-tools`) on create. Point **`KALI_MCP_GMP_HOST` / `KALI_MCP_GMP_PORT`** at a reachable `gvmd` (another VM, a tunnel, or a shared scanner). The Codespace container does **not** run a full Greenbone stack by default.
- **Diagnostics (no GMP call):** call the **`gvm_info`** tool — it reports whether `gvm-cli` is on `PATH`, env defaults, whether a password is set, CA file path, and the TLS-insecure flag.
- **Read-only GMP:** **`gvm_cli`** sends read-only `<get_…/>` XML (e.g. `<get_version/>`). It never prints the password in the tool output.

## Tools

- **`run_shell`**: for LLM-driven one-liners (same engine as `kali_nethunter_exec`: desktop = `bash -lc`, NetHunter = `su` + chroot shims). Block lists stop obvious interactive/TUI use (`msfconsole`, bare `sh`/`zsh`/`bash` as a shell, `ssh `, `vim `, etc.). Pipelines (`|`, `&&`) on one line are allowed. Disable the tool (keep other exec tools) with `KALI_MCP_SHELL_DISABLED=1`.
- **Kali helpers (argv-based on desktop, no shell; NetHunter uses a quoted chroot line):** **`searchsploit`** (`-j` JSON, validated query), **`resolve_dns`** (`dig +short`), **`network_status`** (`ip -br a`, `ip route`, `ss -tuln`), **`ping_host`** (ICMP, count 1–10), **`http_head`** (curl response headers, http(s) URLs only, no `user:pass@`). These share `KALI_MCP_KALI_FEATURES_DISABLED=1` to turn off as a group.
- **Greenbone (GMP):** **`gvm_info`** (local only — `gvm-cli` presence, env, TLS options), **`gvm_cli`** (read-only GMP via `gvm-cli`; use env from **Environment** and optional **`gmp.env`** in Codespaces).

## Security

Only use on networks you are allowed to test. The server runs shell-bound tools; do not expose to the public internet without authentication.

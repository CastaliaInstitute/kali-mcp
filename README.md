# kali-mcp

[Open in GitHub Codespaces](https://codespaces.new/CastaliaInstitute/kali-mcp?quickstart=1)

### Suggested prompts (analyze *your* network)

Use these with **GitHub Copilot**, **Kaliyai**, or any client attached to kali-mcp. Replace hosts, CIDRs, and domains with addresses **you own** or are **explicitly allowed** to test (home lab, office with permission, your cloud VPC, etc.).


| You might ask                                                                                     | Maps to kali-mcp tools                      |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| *“Show **network status** on this host: interfaces, default route, and listening TCP/UDP ports.”* | `network_status`                            |
| *“**Resolve** `router.lan` (or `example.com`) and show the result.”*                              | `resolve_dns`                               |
| *“**Ping** my gateway `192.168.1.1` a few times and summarize latency.”*                          | `ping_host`                                 |
| *“Run `**nmap_scan*`* with the **ping** profile on `10.0.0.0/24`”* (or a single lab IP)           | `nmap_scan` — use only on authorized ranges |
| *“What does `**device_info`** report for the machine running kali-mcp?”*                          | `device_info`                               |
| *“List **Wi‑Fi** networks visible from this Kali desktop.”*                                       | `wifi_scan` (where `nmcli` exists)          |
| *“Show `**gvm_info*`*, then if GMP is configured, call `**gvm_cli**` with `<get_version/>`.”*     | `gvm_info` → `gvm_cli` (Greenbone in scope) |
| *“**Searchsploit** for a CVE or product name I’m checking in my lab.”*                            | `searchsploit`                              |


Deeper port scans, shell one-liners, and OpenVAS targets should stay on **isolated** or **documented** lab systems. See **Security** at the end of this file.

### Pentest lab in a Codespace (Docker virtual network for students)

The devcontainer includes **Docker-in-Docker** and a small `**lab/*`* stack: an **isolated bridge network** (`172.30.0.0/24`) and [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/) (training use only) published at `**http://127.0.0.1:3000`**. Instructors: see **[lab/README.md](lab/README.md)** for scope, `lab-up` / `lab-down`, and how to extend the compose file.

```bash
./scripts/lab-up.sh    # docker compose -f lab/docker-compose.yaml up -d
# … students use nmap / http / browser against 127.0.0.1:3000 or the lab network per lab/README.md …
./scripts/lab-down.sh
```

A **4 vCPU / 8 GiB** (or better) machine is recommended for the Codespace (see `hostRequirements` in the devcontainer). The lab is **not** started automatically, so you control when images are pulled and exposed.

**One MCP, two ways to use it (same `tools/`* contract, different “where the server runs”):**

1. **Kaliyai (Android app)** — Kaliyai stays the **Gemini client and optional built-in** tools. Point **Settings → MCP base URL** at a running kali-mcp. Kaliyai still loads **remote** tools from this server; built-in (e.g. Android `wifi_scan`) is unchanged. Same JSON-RPC as `McpClient` (`initialize`, `tools/list`, `tools/call`, `Mcp-Protocol-Version` / `Mcp-Session-Id`).
2. **GitHub Codespace (Kali devcontainer here)** — Run the **same** `kali-mcp` process in the Kali container for local testing: `./scripts/test-mcp-like-kaliyai.sh`, VS Code **Tasks** (`kali-mcp: run server` / `test JSON-RPC`), and forwarded port **8765**. The Codespaces “Ports” tab shows a public HTTPS URL; you can use that in Kaliyai on a real phone **only if** the device can reach the internet and that host (treat it like a dev server URL).
3. **Any Kali/VM/NetHunter** — `pip install -e .` and `kali-mcp` (default `0.0.0.0:8765`).

`KALI_MCP_PROFILE=desktop` on full Kali; `nethunter` = `su` + chroot shims (`bootkali` / `kali` / `nethunter`).


| Where kali-mcp runs                                               | How you connect Kaliyai (or curl)                                                                                                                                                                            |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| This repo in **Codespace**                                        | Forward **8765**; test from the Codespace terminal with `http://127.0.0.1:8765/`; for a phone, use the forwarded public URL in Settings if reachable.                                                        |
| **Kali/VM** on your LAN                                           | `http://<machine-ip>:8765/` (same network as the phone)                                                                                                                                                      |
| **USB to dev machine**                                            | `adb reverse tcp:8765 tcp:8765` and `http://127.0.0.1:8765/` in Kaliyai (localhost is the dev machine)                                                                                                       |
| **kali-mcp on the same phone** (Kaliyai + server both on Android) | Run the Python app **on the device** (e.g. **Termux** or inside the **NetHunter chroot**), bind `0.0.0.0:8765`, set Kaliyai **MCP base URL** to `http://127.0.0.1:8765/` — **no** `adb reverse` (see below). |


**kali-mcp does not replace** the Kaliyai app — it is the **deployable MCP process** for Kali feature tools so tests and the phone can share one server implementation.

### kali-mcp on the Android device (no PC)

The server does **not** have to be Linux-on-desktop: it is plain **Python 3** + **uvicorn**. You can run it **on the phone** so tool execution and Kaliyai share the same machine.

1. **Termux** (common path): install [Termux](https://github.com/termux/termux-app), `pkg update && pkg install python python-pip`, clone or copy the `kali-mcp` tree, `pip install -e .`, then:
  ```bash
   export KALI_MCP_HOST=0.0.0.0 KALI_MCP_PORT=8765 KALI_MCP_PROFILE=nethunter
   kali-mcp
  ```
   In Kaliyai: **MCP base URL** `http://127.0.0.1:8765/`, **Refresh MCP**. Keep Termux in the foreground (or use a wakelock); Android may kill background servers.
2. **NetHunter chroot** (you already have Kali userland on the device): use a **root** or **NetHunter terminal** so `su` and the chroot shims match what kali-mcp expects. Typical flow:
  ```bash
   # Example; your image may use `bootkali`, `kali`, `nethunter -c`, etc.
   bootkali kali          # or:  nethunter -c "bash -l"  — enter Kali environment
   apt update && apt install -y python3 python3-venv python3-pip   # if not already
   cd /path/to/kali-mcp && python3 -m venv .venv && . .venv/bin/activate && pip install -e .
   export KALI_MCP_HOST=0.0.0.0 KALI_MCP_PORT=8765 KALI_MCP_PROFILE=nethunter
   kali-mcp
  ```
   If `which su` / chroot paths differ from the defaults, set `KALI_MCP_SU` and `KALI_MCP_CHROOT_SHIMS` (see **Environment** below). **Kaliyai → MCP base URL:** `http://127.0.0.1:8765/` then **Refresh MCP** — traffic stays on the phone; **no** USB `adb reverse` to a PC when the server runs on-device.
3. **Not the same** as `builtin` Kaliyai tools: those run **inside the app**. **kali-mcp on device** is still a **separate process**; it’s just that both run on Android instead of a laptop.
4. If you do **not** need a second HTTP process on the phone, you can keep using only **in-app** Kali/NetHunter tools (no kali-mcp) — but a **single** on-device kali-mcp gives one JSON-RPC server for the same `tools/`* contract as your desktop image.

## Pentest education Jupyter Book (Thebe + `%%copilot`)

A small **[Jupyter Book 1](https://jupyterbook.org/)** in **`pentest-book/`** demonstrates educational pentesting prompts. **Thebe** (Live Code) and Binder are configured in `pentest-book/_config.yml`; the **`%%copilot` cell magic** in `kali_mcp/copilot_jupyter.py` calls the official **GitHub Copilot Python SDK** — [`github/copilot-sdk`](https://github.com/github/copilot-sdk) (see also [PyPI: `github-copilot-sdk`](https://pypi.org/project/github-copilot-sdk/)). **Jupyter AI** is included in the `book` extra for `%load_ext jupyter_ai` / `%%ai` alongside the Copilot SDK. Install and build:

```bash
pip install -e ".[book]"
jupyter-book build pentest-book
```

In **VS Code** (local or **GitHub Codespaces**), the workspace opens **`pentest-book/content/intro.md`** in the editor (not README) via the **on-folder-open** task, and the **Thebe** static site on `http://127.0.0.1:8788/` is started from **Tasks** → *pentest book: Thebe static server (build + http.server)*, then *pentest book: open Thebe site in system browser* if you want a browser. You can also open the built `pentest-book/_build/html/index.html` directly. A **`binder/postBuild`** installs `.[book]` on [MyBinder](https://mybinder.org) for in-page Thebe; full Copilot auth still needs your own runtime for real answers. See `pentest-book/content/intro.md` for more.

## Test (same wire format as Kaliyai)

With `kali-mcp` running (default `8765`):

```bash
./scripts/test-mcp-like-kaliyai.sh
# or:  KALI_MCP_TEST_URL=http://127.0.0.1:8765/ python3 scripts/test_mcp_jsonrpc.py
```

Exercises `initialize`, `tools/list`, and `tools/call` for `searchsploit`, `resolve_dns`, `network_status`, `ping_host`, `http_head`, `run_shell`. A missing `searchsploit` or `ip` binary shows `isError` in the result but still exits 0; use `KALI_MCP_SMOKE_STRICT=1` to fail in that case.

**Kaliyai (device)**: in the **nethunter-gemini-mcp (Kaliyai)** repo, `scripts/ask-kali-mcp-prompts.sh` sends user messages that should trigger the LLM to call the tools above. Set the app **MCP Base URL** to your kali-mcp, tap **Refresh MCP**; for USB to a host on port 8765: `adb reverse tcp:8765 tcp:8765` and `http://127.0.0.1:8765/`; emulators often use `http://10.0.2.2:8765/`.

## Container deploy (GHCR + Docker)

On every push to `main` (and **workflow dispatch**), GitHub Actions builds and pushes:

`ghcr.io/<lowercase-owner>/kali-mcp:latest` and `:sha-<commit>`

**Pull and run** (package may be private to the org until you make it public: **Package settings → Change visibility**):

```bash
docker pull ghcr.io/castaliainstitute/kali-mcp:latest
docker run --rm -p 8765:8765 ghcr.io/castaliainstitute/kali-mcp:latest
```

**Compose** (from this repo): `docker compose up --build` — same port **8765** as everywhere else (Kaliyai MCP URL `http://<host>:8765/`).

## Run (local or VM)

On a **Kali** (or compatible) system, install the same **apt** surface the MCP calls (nmap, gvm-cli, searchsploit, dig, `ip`/`ss`, ping, curl, nmcli, sqlmap, etc.):

```bash
sudo bash scripts/install-kali-mcp-prereqs.sh
```

The **devcontainer** and **Dockerfile** use this script so the container matches a properly provisioned Kali.

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


| Variable                                                                                                          | Meaning                                                                                                                                                                                                                                                                        |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `KALI_MCP_PROFILE`                                                                                                | `desktop` (default) or `nethunter`                                                                                                                                                                                                                                             |
| `KALI_MCP_HOST` / `KALI_MCP_PORT`                                                                                 | Bind address (default `0.0.0.0:8765`)                                                                                                                                                                                                                                          |
| `KALI_MCP_EXEC_ENABLED`                                                                                           | `1` (default) — if `0` or set `KALI_MCP_EXEC_DISABLED=1`, nmap/gvm/exec and `run_shell` are off                                                                                                                                                                                |
| `KALI_MCP_SHELL_DISABLED`                                                                                         | set to `1` to hide the `**run_shell**` tool only (keeps nmap, gvm, `kali_nethunter_exec` when exec is on)                                                                                                                                                                      |
| `KALI_MCP_KALI_FEATURES_DISABLED`                                                                                 | set to `1` to hide the extra Kali helpers (`searchsploit`, `resolve_dns`, `network_status`, `ping_host`, `http_head`)                                                                                                                                                          |
| `KALI_MCP_SU` / `KALI_MCP_SU_PATH`                                                                                | NetHunter: path to `su`                                                                                                                                                                                                                                                        |
| `KALI_MCP_CHROOT_SHIMS`                                                                                           | NetHunter: e.g. `bootkali kali nethunter`                                                                                                                                                                                                                                      |
| `KALI_MCP_GMP_HOST` / `KALI_MCP_GMP_PORT` / `KALI_MCP_GMP_USER` / `KALI_MCP_GMP_CAFILE` / `KALI_MCP_GMP_PASSWORD` | defaults for `gvm_cli` (also `GMP_USER` / `GMP_PASSWORD`)                                                                                                                                                                                                                      |
| `KALI_MCP_GMP_TLS_INSECURE`                                                                                       | `1` to use `gvm-cli tls --insecure` and skip a CA file (**dev only**; e.g. tunnel or lab).                                                                                                                                                                                     |
| `KALI_MCP_GVM_RUN_AS_GVM`                                                                                         | `auto` (default): on **desktop** profile, when `euid` is **root** and system user `_gvm` exists, run `gvm-cli` as `_gvm` (same as NetHunter path) to avoid **permission** errors on `/var/lib/gvm/`. `0` = always plain `gvm-cli`; `1` = use `runuser` whenever `_gvm` exists. |
| `KALI_MCP_MAX_TIMEOUT_SEC`                                                                                        | **kali-mcp server only:** max seconds for subprocess tools (`run_shell`, `nmap` argv path, `gvm_cli` shell, etc.). Default **600**, range **5–10800** (3 hours). Does **not** change GitHub Copilot’s own MCP/chat limits in VS Code. |


## Timeouts (GitHub Copilot / VS Code vs kali-mcp)

- **VS Code + Copilot** do **not** yet expose a supported `tool_timeout_sec` / `startup_timeout_sec` in `mcp.json` (see [microsoft/vscode#261734](https://github.com/microsoft/vscode/issues/261734), [vscode-copilot-release#14130](https://github.com/microsoft/vscode-copilot-release/issues/14130)). Long **MCP tool** calls can still be cut off by the client, independent of this repo.
- **Long-running agent *terminal* commands** (not the stdio MCP process) are affected by `**chat.tools.terminal.enforceTimeoutFromModel**` in this workspace: it is set to `**false**` in `[.vscode/settings.json](.vscode/settings.json)` so the agent is less likely to stop a long shell command early when the model requests a timeout.
- **kali-mcp tools** honor per-tool `**timeout_sec**` and the server cap **`KALI_MCP_MAX_TIMEOUT_SEC`** (see table above). Set it in the devcontainer `**containerEnv**`, the shell when running `kali-mcp`, or the `**env**` in `mcp.json` for a stdio server.


## GitHub Copilot, Cursor, and MCP (HTTP + autostart)

**MCP in the devcontainer** is defined in `**[.devcontainer/devcontainer.json](.devcontainer/devcontainer.json)**` under `**customizations.vscode.mcp**` (see [Add an MCP server to a dev container](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#configure-the-mcpjson-file)). It registers **`kaliMcpHttp`:** `**type: http**`, `**url: http://127.0.0.1:8765/mcp**` so **VS Code / Copilot** and **Cursor** (when attached to the same dev environment) use the same **JSON-RPC** `tools/list` and `tools/call` as Kaliyai. The `**kali-mcp**` process is **autostarted** on every container start by `**.devcontainer/post-start-mcp.sh**` (it binds `**0.0.0.0:8765**`). Workspace `**[.vscode/mcp.json](.vscode/mcp.json)**` is left empty; add entries there only for **optional** per-machine overrides, or for **local (non-container)** workflows.

**MCP autostart in the editor:** `**chat.mcp.autostart**` (`**"always"**` — not a boolean) / `**chat.mcp.autoStart**` / `**chat.mcp.apps.enabled**` are set in `[.vscode/settings.json](.vscode/settings.json)` and `[.devcontainer/devcontainer.json](.devcontainer/devcontainer.json)` so Copilot **starts workspace MCPs** when appropriate ([MCP in VS Code](https://code.visualstudio.com/docs/copilot/reference/mcp-configuration)). The devcontainer also sets `**chat.extensionUnification.enabled**` to `**false**` to work around a known race where **Copilot Chat** can time out in **remote Linux** (logs sometimes show **“Copilot extension not found”**; see [vscode#288021](https://github.com/microsoft/vscode/issues/288021), [vscode#286626](https://github.com/microsoft/vscode/issues/286626)). You can turn unification back on in **User** settings if you prefer the default.

**If you see: “Chat took too long to get ready…”** — that is **GitHub Copilot Chat** (sign-in, extensions, or a slow/remote host), not kali-mcp. (1) **Accounts**: sign in to **GitHub**. (2) **Extensions**: wait until **GitHub Copilot** and **GitHub Copilot Chat** finish installing, then run **Developer: Reload Window** if they asked for a reload. (3) **Output** → **GitHub Copilot Chat** for the real error. (4) Confirm you have a [Copilot](https://docs.github.com/copilot) entitlement that includes chat, given current [usage limits](https://docs.github.com/copilot/concepts/usage-limits).

**Public port (local Cursor on your machine → Codespace):** `**.devcontainer/devcontainer.json**` sets **`"visibility": "public"**` for port **8765**. In the **Codespace → Ports** view, open **port 8765** and copy the `**https://…-8765.app.github.dev**` URL. On your **laptop**, add that URL (with `**/mcp` path) to **Cursor**’s user MCP config — see the template [`cursor-mcp-codespace-public.example.json`](.vscode/cursor-mcp-codespace-public.example.json) and replace the placeholder. **Do not** commit secrets; treat a public kali-mcp as **lab-only** exposure.

**Stdio instead of HTTP (optional):** to use **`python -m kali_mcp.copilot_stdio_lite`**, add the `**kaliMcpStdio**` block from `[.vscode/mcp.json.example](.vscode/mcp.json.example)` to **`devcontainer.json`**’s `**mcp.servers**` (or to workspace `mcp.json` for local use). Avoid **two** overlapping definitions for the same tools if your client would duplicate them.

## GitHub Codespaces (Kali) — test the same MCP as Kaliyai

Open the repo in a **Codespace** (badge or **Code → Codespace** on [github.com/CastaliaInstitute/kali-mcp](https://github.com/CastaliaInstitute/kali-mcp)). The **devcontainer** is **Kali rolling** and on create runs `[scripts/install-kali-mcp-prereqs.sh](scripts/install-kali-mcp-prereqs.sh)` (Kali tools for the MCP) then `**pip install -e .**` (HTTP server; optional `**[copilot]**` for `kali_mcp.copilot_stdio` if you add stdio from `mcp.json.example`).

On every start, `**.devcontainer/post-start-mcp.sh`** runs `**kali-mcp**` in the background (log: `**/tmp/kali-mcp.log**`; `gmp.env` is loaded if present). You usually do not need to start the server by hand. **Port 8765** is in `forwardPorts` with **public** visibility. To debug, use **Run Task → kali-mcp: run server (8765)** in the foreground, or `tail -f /tmp/kali-mcp.log`. GMP: copy `**.devcontainer/gmp.env.example` → `gmp.env`**. **Run Task → kali-mcp: test JSON-RPC** while the server is up.

### GMP / OpenVAS (Greenbone) from Codespace

- **Client:** the devcontainer installs `gvm-cli` (or `gvm-tools`) on create. Point `**KALI_MCP_GMP_HOST` / `KALI_MCP_GMP_PORT`** at a reachable `gvmd` (another VM, a tunnel, or a shared scanner). The Codespace container does **not** run a full Greenbone stack by default.
- **Diagnostics (no GMP call):** call the `**gvm_info`** tool — it reports whether `gvm-cli` is on `PATH`, env defaults, whether a password is set, CA file path, and the TLS-insecure flag.
- **Read-only GMP:** `**gvm_cli`** sends read-only `<get_…/>` XML (e.g. `<get_version/>`). It never prints the password in the tool output.

## Tools

- `**run_shell**`: for LLM-driven one-liners (same engine as `kali_nethunter_exec`: desktop = `bash -lc`, NetHunter = `su` + chroot shims). Block lists stop obvious interactive/TUI use (`msfconsole`, bare `sh`/`zsh`/`bash` as a shell, `ssh` , `vim` , etc.). Pipelines (`|`, `&&`) on one line are allowed. Disable the tool (keep other exec tools) with `KALI_MCP_SHELL_DISABLED=1`.
- **Kali helpers (argv-based on desktop, no shell; NetHunter uses a quoted chroot line):** `**searchsploit`** (`-j` JSON, validated query), `**resolve_dns**` (`dig +short`), `**network_status**` (`ip -br a`, `ip route`, `ss -tuln`), `**ping_host**` (ICMP, count 1–10), `**http_head**` (curl response headers, http(s) URLs only, no `user:pass@`). These share `KALI_MCP_KALI_FEATURES_DISABLED=1` to turn off as a group.
- **Greenbone (GMP):** `**gvm_info`** (local only — `gvm-cli` presence, env, TLS options), `**gvm_cli**` (read-only GMP via `gvm-cli`; use env from **Environment** and optional `**gmp.env`** in Codespaces).

## Security

Only use on networks you are allowed to test. The server runs shell-bound tools; do not expose to the public internet without authentication.
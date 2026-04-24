# kali-mcp

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/CastaliaInstitute/kali-mcp?quickstart=1)

HTTP **JSON-RPC** MCP server aligned with the **Anubis** Android client (`nethunter-gemini-mcp` / `McpClient`): `initialize`, `tools/list`, `tools/call`, headers `Mcp-Protocol-Version` / `Mcp-Session-Id`.

Use the same tool names on **Kali desktop** (default) and **NetHunter** (`KALI_MCP_PROFILE=nethunter` — `su` + `bootkali` / `kali` / `nethunter` shims).

**Host this repository** under the Castalia Institute org (e.g. `github.com/castaliainstitute/kali-mcp`) and point Anubis “MCP URL” at `http://<host>:8765/`.

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
| `KALI_MCP_EXEC_ENABLED` | `1` (default) — if `0` or set `KALI_MCP_EXEC_DISABLED=1`, nmap/gvm/exec tools are hidden |
| `KALI_MCP_SU` / `KALI_MCP_SU_PATH` | NetHunter: path to `su` |
| `KALI_MCP_CHROOT_SHIMS` | NetHunter: e.g. `bootkali kali nethunter` |
| `KALI_MCP_GMP_HOST` / `KALI_MCP_GMP_PORT` / `KALI_MCP_GMP_CAFILE` / `KALI_MCP_GMP_PASSWORD` | defaults for `gvm_cli` |

## GitHub Codespaces

Use the badge at the top (or: **Code → Open in… → Codespace** on [github.com/CastaliaInstitute/kali-mcp](https://github.com/CastaliaInstitute/kali-mcp)). The org must have **GitHub Codespaces** enabled (Org **Settings → Codespaces**). The **devcontainer** is **Kali rolling**: installs `nmap`, `NetworkManager` (`nmcli` for `wifi_scan`), and `python3-venv`, then `pip install -e .` on create. Port **8765** auto-forwards; run `kali-mcp` after the container finishes.

## Security

Only use on networks you are allowed to test. The server runs shell-bound tools; do not expose to the public internet without authentication.

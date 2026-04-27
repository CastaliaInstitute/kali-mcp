#!/usr/bin/env bash
# Start kali-mcp HTTP (JSON-RPC) in the background on every container start (Codespace resume / local devcontainer).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LOG=/tmp/kali-mcp.log
PIDF=/tmp/kali-mcp.pid

if [[ ! -f "$ROOT/.venv/bin/kali-mcp" ]]; then
  echo "[devcontainer] kali-mcp not installed (no .venv or postCreate incomplete). Log: $LOG" | tee -a "$LOG" >&2
  exit 0
fi

if [[ -f "$PIDF" ]]; then
  oldpid="$(tr -d ' \n' < "$PIDF" 2>/dev/null || true)"
  if [[ -n "${oldpid:-}" ]] && kill -0 "$oldpid" 2>/dev/null; then
    echo "[devcontainer] kali-mcp already running (pid $oldpid). Log: $LOG" >&2
    exit 0
  fi
fi

{
  set -euo pipefail
  cd "$ROOT"
  # shellcheck source=/dev/null
  . "$ROOT/.venv/bin/activate"
  if [[ -f "$ROOT/.devcontainer/gmp.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    . "$ROOT/.devcontainer/gmp.env"
    set +a
  fi
  export KALI_MCP_HOST="${KALI_MCP_HOST:-0.0.0.0}"
  export KALI_MCP_PORT="${KALI_MCP_PORT:-8765}"
  exec kali-mcp
} >>"$LOG" 2>&1 &

echo $! >"$PIDF"
cat <<'EOF' >&2
[devcontainer] kali-mcp: background JSON-RPC
  * URL (in container):  http://127.0.0.1:8765/
  * In GitHub Codespaces: Ports -> 8765 -> public https://<codespace>-8765.app.github.dev/
  * Log:                 tail -f /tmp/kali-mcp.log
  * Optional Copilot stdio: copy .vscode/mcp.json.example -> .vscode/mcp.json, then MCP: List Servers
===============================================================================
EOF

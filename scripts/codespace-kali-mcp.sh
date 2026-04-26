#!/usr/bin/env bash
# Start kali-mcp in a GitHub Codespace (Kali devcontainer) with GMP environment applied.
# Usage:  source .venv/bin/activate && ./scripts/codespace-kali-mcp.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
GMP_FILE="$ROOT/.devcontainer/gmp.env"
if [[ -f "$GMP_FILE" ]]; then
  set -a
  # shellcheck source=/dev/null
  . "$GMP_FILE"
  set +a
  echo "Loaded GMP env from .devcontainer/gmp.env" >&2
else
  echo "Note: no .devcontainer/gmp.env — GMP uses config defaults (see gvm_info tool and gmp.env.example)." >&2
fi
export KALI_MCP_HOST="${KALI_MCP_HOST:-0.0.0.0}"
export KALI_MCP_PORT="${KALI_MCP_PORT:-8765}"
if [[ ! -d "$ROOT/.venv" ]]; then
  echo "No .venv — run postCreate in devcontainer or: python3 -m venv .venv && . .venv/bin/activate && pip install -e ." >&2
  exit 1
fi
# shellcheck source=/dev/null
. "$ROOT/.venv/bin/activate"
exec kali-mcp "$@"

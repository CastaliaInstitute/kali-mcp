#!/usr/bin/env bash
# Run the JSON-RPC smoke test (same contract as the Anubis McpClient).
# Prereq:  . .venv/bin/activate && kali-mcp   (default port 8765)
# Optional:  KALI_MCP_TEST_URL=http://127.0.0.1:19876/ ./scripts/test-mcp-like-anubis.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  . .venv/bin/activate
fi
export KALI_MCP_TEST_URL="${KALI_MCP_TEST_URL:-http://127.0.0.1:8765/}"
exec python3 "$ROOT/scripts/test_mcp_jsonrpc.py"

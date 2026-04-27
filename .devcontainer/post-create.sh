#!/usr/bin/env bash
# venv + kali-mcp; in GitHub Codespaces, wire git to the built-in GitHub token (no extra browser login).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
. .venv/bin/activate
pip install -U pip setuptools wheel
# Base install (stdio_lite + HTTP server). Optional: pip install -e '.[copilot]' for kali_mcp.copilot_stdio (full PyPI mcp SDK).
pip install -e .

if [[ "${CODESPACES:-false}" == "true" ]] && command -v gh >/dev/null 2>&1; then
  # Codespaces pre-authenticates `gh`; this points git(1) at the same token (HTTPS to github.com).
  gh auth setup-git || echo "[devcontainer] gh auth setup-git failed — try: gh auth status" >&2
fi

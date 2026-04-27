#!/usr/bin/env bash
# postStart: auto-start kali-mcp; never fail the devcontainer if the server hiccups.
set +e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
bash "$ROOT/.devcontainer/post-start-mcp.sh" || true

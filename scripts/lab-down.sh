#!/usr/bin/env bash
# Stop the training lab.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
docker compose -f "$ROOT/lab/docker-compose.yaml" down
echo "[lab] Stopped (docker compose down)."

#!/usr/bin/env bash
# Bring up the training lab: isolated network + Juice Shop.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if ! command -v docker >/dev/null 2>&1; then
  echo "lab-up: docker not in PATH. Use the devcontainer with the docker-in-docker feature, or install Docker on the host." >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "lab-up: Docker daemon not reachable. In Codespaces: wait a few seconds after the container starts, or restart the devcontainer once." >&2
  exit 1
fi
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
docker compose -f "$ROOT/lab/docker-compose.yaml" up -d
cat <<'EOF' >&2

[lab] Stack is up. Training web app: http://127.0.0.1:3000/ (see lab/README.md)
      docker compose -f lab/docker-compose.yaml ps
EOF

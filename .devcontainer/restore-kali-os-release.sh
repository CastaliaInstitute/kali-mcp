#!/usr/bin/env bash
# Undo Debian bookworm shim in .devcontainer/Dockerfile (needed only for dind feature install at build).
set -euo pipefail
if [[ -f /etc/os-release.vendorsave ]]; then
	cp -f /etc/os-release.vendorsave /etc/os-release
fi

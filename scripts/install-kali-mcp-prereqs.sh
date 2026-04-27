#!/usr/bin/env bash
# apt packages for binaries invoked by kali_mcp (tools_impl, kali_feature_tools, runtime).
# See README "Kali tools for MCP"; keep in sync with Dockerfile + .devcontainer.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  bash \
  coreutils \
  curl \
  dnsutils \
  exploitdb \
  git \
  iproute2 \
  iputils-ping \
  nmap \
  nmap-common \
  network-manager \
  procps \
  python3 \
  python3-pip \
  python3-venv \
  sqlmap \
  sudo
# gvm-cli (GMP client) — package name varies (gvm-tools on Debian-style repos)
if ! apt-get install -y --no-install-recommends gvm-tools; then
  apt-get install -y --no-install-recommends gvm-cli || {
    echo "[install-kali-mcp-prereqs] WARNING: gvm-tools/gvm-cli not installed; gvm_cli tool will fail until you install a GMP client" >&2
  }
fi
apt-get clean
rm -rf /var/lib/apt/lists/* || true

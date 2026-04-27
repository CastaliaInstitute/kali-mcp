# kali-mcp: same tool surface as local / Codespace; bind to 0.0.0.0:8765
# Build:  docker build -t kali-mcp .
# Run:    docker run --rm -p 8765:8765 kali-mcp
FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    KALI_MCP_HOST=0.0.0.0 \
    KALI_MCP_PORT=8765 \
    KALI_MCP_PROFILE=desktop

COPY scripts/install-kali-mcp-prereqs.sh /tmp/install-kali-mcp-prereqs.sh
RUN bash /tmp/install-kali-mcp-prereqs.sh && rm -f /tmp/install-kali-mcp-prereqs.sh

WORKDIR /app
COPY pyproject.toml README.md LICENSE /app/
COPY kali_mcp /app/kali_mcp

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install -U pip setuptools wheel \
    && /opt/venv/bin/pip install -e /app

ENV PATH="/opt/venv/bin:$PATH"
EXPOSE 8765
CMD ["kali-mcp"]

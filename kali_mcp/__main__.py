import os

import uvicorn


def main() -> None:
    host = os.environ.get("KALI_MCP_HOST", "0.0.0.0")
    port = int((os.environ.get("KALI_MCP_PORT", "8765") or "8765").split("#", 1)[0].strip())
    uvicorn.run("kali_mcp.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()

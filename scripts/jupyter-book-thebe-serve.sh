#!/usr/bin/env bash
# Serve built Jupyter Book HTML so Thebe / Live Code works over http:// (file://
# can break thebe and assets). Kernels: MyBinder (built-in) unless you reconfigure
# sphinx-thebe for a local jupyter server.
set -euo pipefail
ROOT="${ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"
if [[ -d .venv ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi
export JUPYTER_BOOK_THEBE_PORT="${JUPYTER_BOOK_THEBE_PORT:-8788}"
if [[ "${JUPYTER_BOOK_BUILD:-1}" != "0" ]]; then
  jupyter-book build pentest-book
fi
cd pentest-book/_build/html
echo "Thebe / book preview:  http://127.0.0.1:${JUPYTER_BOOK_THEBE_PORT}/  (use index.html redirect; Live Code + Binder in-page)"
echo "Local HTTP only — stop with Ctrl+C"
exec python3 -m http.server "$JUPYTER_BOOK_THEBE_PORT"

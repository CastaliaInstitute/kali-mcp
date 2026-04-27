"""
Jupyter: ``%%copilot`` line/cell magic using the **GitHub Copilot Python SDK**
(``https://github.com/github/copilot-sdk`` — ``pip install github-copilot-sdk``).

**Load:** ``%load_ext kali_mcp.copilot_jupyter``

**Jupyter AI:** use ``%load_ext jupyter_ai`` for the generic ``%%ai`` magics; this
module keeps ``%%copilot`` on the official Copilot agent runtime.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import shlex
import sys
import traceback
from collections.abc import Awaitable
from typing import Any

from IPython.core.magic import Magics, line_cell_magic, line_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

__all__ = ["load_ipython_extension", "CopilotSDKMagics"]


def _run_async_in_notebook(coro: Awaitable[T]) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import nest_asyncio  # type: ignore[import-untyped]

    nest_asyncio.apply()
    return asyncio.get_event_loop().run_until_complete(coro)


async def _ask_copilot(
    user_message: str,
    *,
    model: str,
    timeout: float,
) -> str:
    from copilot import CopilotClient
    from copilot.generated.session_events import AssistantMessageData, SessionIdleData
    from copilot.session import PermissionHandler

    parts: list[str] = []

    async with CopilotClient() as client:
        async with await client.create_session(
            model=model,
            on_permission_request=PermissionHandler.approve_all,
        ) as session:
            done = asyncio.Event()

            def on_event(event: object) -> None:
                data = getattr(event, "data", None)
                if data is None:
                    return
                if isinstance(data, AssistantMessageData):
                    c = getattr(data, "content", None) or ""
                    if c:
                        parts.append(c)
                elif isinstance(data, SessionIdleData):
                    done.set()

            session.on(on_event)  # type: ignore[union-attr,attr-defined]
            await session.send(user_message)
            await asyncio.wait_for(done.wait(), timeout=timeout)
    return "".join(parts).strip()


def _parse_copilot_first_line(line: str) -> tuple[str, float, str]:
    """Return (model, timeout, inline_prompt). *inline_prompt* is text after flags on the same line."""
    d_model = os.environ.get("COPILOT_JUPYTER_MODEL", "gpt-5")
    p = argparse.ArgumentParser(prog="%%copilot", add_help=False)
    p.add_argument(
        "-m",
        "--model",
        default=d_model,
    )
    p.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=600.0,
    )
    p.add_argument("rest", nargs=argparse.REMAINDER, default=[])
    if not (line and str(line).strip()):
        return d_model, 600.0, ""
    try:
        parts = shlex.split(str(line), posix=True)
    except ValueError:
        parts = str(line).split()
    a = p.parse_args(parts)
    return str(a.model), float(a.timeout), " ".join(a.rest or []).strip()


@magics_class
class CopilotSDKMagics(Magics):
    @line_cell_magic
    def copilot(self, line: str = "", cell: str | None = None) -> None:
        """:**%%copilot** *[-m MODEL] [-t SECS]*  …

        **Cell body** = user message. Flags live on the same line as ``%%copilot``
        (see :func:`_parse_copilot_first_line`). Uses `github-copilot-sdk`:
        <https://github.com/github/copilot-sdk>
        """
        from IPython.core.display import Markdown, display

        m_line, t_line, inline = _parse_copilot_first_line(line or "")
        model, timeout = m_line, t_line

        body = (cell or "").strip()
        if not body and inline:
            body = inline
        if not body:
            print(  # noqa: T201
                "%%copilot: add a prompt in the cell, or on the same line after flags. "
                "https://github.com/github/copilot-sdk"
            )
            return

        try:
            out = _run_async_in_notebook(
                _ask_copilot(
                    body,
                    model=str(model),
                    timeout=float(timeout),
                )
            )
        except ModuleNotFoundError as e:
            if e.name in ("copilot", "nest_asyncio", None):
                print(  # noqa: T201
                    "pip install 'kali-mcp[book]'   # or: pip install github-copilot-sdk nest-asyncio\n"
                    "https://github.com/github/copilot-sdk"
                )
            else:
                print(f"Module not found: {e!r}", file=sys.stderr)  # noqa: T201
        except Exception as e:  # noqa: BLE001
            print("".join(traceback.format_exception(e)), file=sys.stderr)  # noqa: T201
            display(Markdown(f"**Error:** `{e!s}`"))
        else:
            if out:
                display(Markdown(out))
            else:
                display(
                    Markdown(
                        "_No assistant text. Check `copilot` / GitHub auth, model name, and request limits._"
                    )
                )

    @line_magic
    @magic_arguments()
    @argument("package", nargs="?", default="")
    def copilot_sdk_version(self, line: str) -> None:
        """:%copilot_sdk_version [importname] — PyPI version and optional import test."""
        from importlib import metadata

        from IPython.core.display import Markdown, display

        args = parse_argstring(self.copilot_sdk_version, line)
        try:
            v = metadata.version("github-copilot-sdk")
        except Exception:
            v = "not installed"
        text = (
            f"**github-copilot-sdk** — `{v}`\n\n"
            "- [github/copilot-sdk](https://github.com/github/copilot-sdk)\n"
            "- [PyPI: github-copilot-sdk](https://pypi.org/project/github-copilot-sdk/)\n"
        )
        display(Markdown(text))
        pkg = (args.package or "").strip()
        if not pkg:
            return
        try:
            __import__(pkg)
        except Exception as e:  # noqa: BLE001
            display(f"`import {pkg!r}` → **{e!r}**")
        else:
            display(f"`import {pkg!r}` **ok**")


def load_ipython_extension(ipython: Any) -> None:
    """:%load_ext kali_mcp.copilot_jupyter"""
    ipython.register_magics(CopilotSDKMagics)

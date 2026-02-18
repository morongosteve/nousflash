#!/usr/bin/env python3
"""
xortron_mcp_bridge.py
━━━━━━━━━━━━━━━━━━━━━
Self-Correcting MCP ↔ LlamaIndex bridge.

Architecture: Self-Correcting Path
  • Spawns mcp_code_server.py as a stdio MCP server subprocess.
  • Wraps its tools as LlamaIndex FunctionTools.
  • Adds a retry layer: if Python execution exits non-zero, the bridge
    analyses the error, patches common issues (missing imports, syntax),
    and re-submits automatically (up to MAX_SELF_CORRECT_ATTEMPTS).
  • No Docker, no Jupyter, no external API key required for execution.

Public API:
  bridge = await McpCodeBridge.create()
  result = await bridge.execute_python(code)
  result = await bridge.execute_shell(cmd)
  await bridge.close()
"""

import asyncio
import json
import re
import sys
import textwrap
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ── Constants ──────────────────────────────────────────────────────────────
SERVER_SCRIPT  = Path(__file__).parent / "mcp_code_server.py"
MAX_SELF_CORRECT_ATTEMPTS = 3

# ── Self-correction heuristics ─────────────────────────────────────────────
_IMPORT_MAP = {
    "np":     "import numpy as np",
    "pd":     "import pandas as pd",
    "plt":    "import matplotlib.pyplot as plt",
    "math":   "import math",
    "random": "import random",
    "json":   "import json",
    "re":     "import re",
    "os":     "import os",
    "sys":    "import sys",
    "time":   "import time",
    "decimal": "from decimal import Decimal, getcontext",
    "fractions": "from fractions import Fraction",
    "itertools": "import itertools",
    "functools": "import functools",
    "collections": "import collections",
    "statistics": "import statistics",
    "hashlib": "import hashlib",
}

def _auto_fix(code: str, stderr: str) -> str | None:
    """
    Attempt to auto-fix common execution errors.
    Returns patched code, or None if no fix is known.
    """
    # NameError / ModuleNotFoundError → inject missing import
    name_match = re.search(r"NameError: name '(\w+)'", stderr)
    if name_match:
        sym = name_match.group(1)
        if sym in _IMPORT_MAP:
            return _IMPORT_MAP[sym] + "\n" + code

    mod_match = re.search(r"ModuleNotFoundError: No module named '(\w+)'", stderr)
    if mod_match:
        mod = mod_match.group(1)
        if mod in _IMPORT_MAP:
            return _IMPORT_MAP[mod] + "\n" + code
        # Attempt pip-install on-the-fly
        return (
            f"import subprocess, sys\n"
            f"subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', '{mod}'])\n"
            + code
        )

    # IndentationError — strip leading whitespace uniformly
    if "IndentationError" in stderr:
        try:
            return textwrap.dedent(code)
        except Exception:
            pass

    # SyntaxError: print used without parens (Python 2 style)
    if "SyntaxError" in stderr and re.search(r'\bprint\s+[^(]', code):
        fixed = re.sub(r'\bprint\s+(.+)', lambda m: f'print({m.group(1)})', code)
        if fixed != code:
            return fixed

    return None  # no known fix


# ── Bridge class ───────────────────────────────────────────────────────────

class McpCodeBridge:
    """
    Manages a live MCP ClientSession connected to mcp_code_server.py.
    Provides execute_python() and execute_shell() with self-correction.
    Also exposes llama_tools() → list[FunctionTool] for drop-in agent use.
    """

    def __init__(self, session: ClientSession, _cm):
        self._session = session
        self._cm      = _cm   # keep context manager alive

    # ── Lifecycle ──────────────────────────────────────────────────────────

    @classmethod
    async def create(cls) -> "McpCodeBridge":
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER_SCRIPT)],
        )
        cm      = stdio_client(server_params)
        streams = await cm.__aenter__()
        read, write = streams
        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()
        instance = cls(session, cm)
        # Validate tools are reachable
        tools = await session.list_tools()
        tool_names = [t.name for t in tools.tools]
        assert "execute_python" in tool_names, "MCP server missing execute_python tool"
        assert "execute_shell"  in tool_names, "MCP server missing execute_shell tool"
        return instance

    async def close(self):
        try:
            await self._session.__aexit__(None, None, None)
        except Exception:
            pass
        try:
            await self._cm.__aexit__(None, None, None)
        except Exception:
            pass

    # ── Core call ──────────────────────────────────────────────────────────

    async def _call_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        result = await self._session.call_tool(name, args)
        if not result.content:
            return {"error": "MCP server returned empty content", "exit_code": -1}
        # content[0] can be TextContent, ImageContent, etc. — extract text safely
        item = result.content[0]
        raw  = item.text if hasattr(item, "text") else str(item)
        if not raw:
            return {"error": "MCP server returned blank text", "exit_code": -1}
        return json.loads(raw)

    # ── Public methods ─────────────────────────────────────────────────────

    async def execute_python(
        self,
        code: str,
        timeout: float = 30.0,
        self_correct: bool = True,
    ) -> dict[str, Any]:
        """
        Execute Python code. If it fails and self_correct=True, attempt
        auto-repair up to MAX_SELF_CORRECT_ATTEMPTS times.
        """
        current_code = textwrap.dedent(code).strip()
        attempt = 0

        while attempt < (MAX_SELF_CORRECT_ATTEMPTS if self_correct else 1):
            attempt += 1
            result = await self._call_tool("execute_python", {"code": current_code, "timeout": timeout})

            # Success or no stderr
            if result.get("exit_code", 0) == 0:
                result["attempts"] = attempt
                result["final_code"] = current_code
                return result

            stderr = result.get("stderr", "") or result.get("error", "")

            if attempt >= MAX_SELF_CORRECT_ATTEMPTS or not self_correct:
                break

            fixed = _auto_fix(current_code, stderr)
            if fixed is None:
                break  # no known fix, stop trying

            print(f"  [self-correct] attempt {attempt} failed — applying fix, retrying…",
                  flush=True)
            current_code = fixed

        result["attempts"]   = attempt
        result["final_code"] = current_code
        return result

    async def execute_shell(self, cmd: str, timeout: float = 15.0) -> dict[str, Any]:
        return await self._call_tool("execute_shell", {"cmd": cmd, "timeout": timeout})

    # ── LlamaIndex tool adapter ────────────────────────────────────────────

    def llama_tools(self):
        """
        Returns a list of llama_index.core.tools.FunctionTool instances
        wrapping execute_python and execute_shell.
        Compatible with any LlamaIndex agent (ReActAgent, OpenAIAgent, etc.).

        Uses ThreadPoolExecutor to bridge sync FunctionTool calls into async
        coroutines without conflicting with the caller's running event loop.
        """
        import concurrent.futures
        from llama_index.core.tools import FunctionTool

        bridge = self  # capture for closures

        # nest_asyncio allows run_until_complete() even inside a running loop,
        # which is necessary when a sync FunctionTool is called from async context.
        import nest_asyncio
        nest_asyncio.apply()

        def run_python(code: str, timeout: float = 30.0) -> str:
            """Execute Python 3 code. Returns JSON with stdout, stderr, exit_code, attempts."""
            loop = asyncio.get_event_loop()
            r = loop.run_until_complete(bridge.execute_python(code, timeout))
            return json.dumps(r, indent=2)

        def run_shell(cmd: str, timeout: float = 15.0) -> str:
            """Run a shell command. Returns JSON with stdout, stderr, exit_code."""
            loop = asyncio.get_event_loop()
            r = loop.run_until_complete(bridge.execute_shell(cmd, timeout))
            return json.dumps(r, indent=2)

        return [
            FunctionTool.from_defaults(fn=run_python, name="execute_python",
                description="Execute Python 3 code. Returns JSON with stdout, stderr, exit_code."),
            FunctionTool.from_defaults(fn=run_shell,  name="execute_shell",
                description="Run a shell command. Returns JSON with stdout, stderr, exit_code."),
        ]


# ── Convenience async context manager ─────────────────────────────────────

@asynccontextmanager
async def code_bridge():
    """
    Async context manager for clean resource lifecycle:

        async with code_bridge() as bridge:
            result = await bridge.execute_python("print('hello')")
    """
    bridge = await McpCodeBridge.create()
    try:
        yield bridge
    finally:
        await bridge.close()

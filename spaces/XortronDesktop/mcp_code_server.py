#!/usr/bin/env python3
"""
mcp_code_server.py — Lightweight MCP server for Python/shell code execution.

Exposes two tools:
  • execute_python(code, timeout?)  — runs code in an isolated subprocess
  • execute_shell(cmd, timeout?)    — runs a shell command, returns stdout/stderr

Communicates over stdio using the MCP protocol.
"""

import asyncio
import json
import signal
import subprocess
import sys
import textwrap
import time
import traceback
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

# ── Server instance ────────────────────────────────────────────────────────
app = Server("xortron-code-executor")

TOOLS = [
    Tool(
        name="execute_python",
        description=(
            "Execute arbitrary Python 3 code in an isolated subprocess. "
            "stdout + stderr are captured and returned. "
            "The subprocess is killed after `timeout` seconds (default 30)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python source code to execute.",
                },
                "timeout": {
                    "type": "number",
                    "description": "Max seconds to run (default 30).",
                    "default": 30,
                },
            },
            "required": ["code"],
        },
    ),
    Tool(
        name="execute_shell",
        description=(
            "Run a shell command. stdout + stderr returned. "
            "Killed after `timeout` seconds (default 15). "
            "Dangerous commands (rm -rf /, :(){ ...) are blocked."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "cmd": {
                    "type": "string",
                    "description": "Shell command to run.",
                },
                "timeout": {
                    "type": "number",
                    "description": "Max seconds to run (default 15).",
                    "default": 15,
                },
            },
            "required": ["cmd"],
        },
    ),
]

BLOCKED_SHELL_PATTERNS = [
    "rm -rf /",
    "mkfs",
    "dd if=/dev/zero",
    ":(){",
    "fork bomb",
]


@app.list_tools()
async def list_tools() -> list[Tool]:
    # mcp 1.x: handler receives no args, returns list of Tool
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # mcp 1.x decorator passes (name, arguments) directly — do NOT return CallToolResult
    args = arguments or {}

    try:
        if name == "execute_python":
            result = await _run_python(
                code=args["code"],
                timeout=float(args.get("timeout", 30)),
            )
        elif name == "execute_shell":
            result = await _run_shell(
                cmd=args["cmd"],
                timeout=float(args.get("timeout", 15)),
            )
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as exc:
        result = {"error": str(exc), "traceback": traceback.format_exc()}

    # Return a list of content blocks — decorator wraps into CallToolResult automatically
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ── Execution helpers ──────────────────────────────────────────────────────

async def _run_python(code: str, timeout: float = 30.0) -> dict[str, Any]:
    """Execute Python code in a clean subprocess, return stdout/stderr/exit_code."""
    start = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", textwrap.dedent(code),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        elapsed = time.monotonic() - start
        return {
            "stdout":    stdout.decode(errors="replace").strip(),
            "stderr":    stderr.decode(errors="replace").strip(),
            "exit_code": proc.returncode,
            "elapsed_s": round(elapsed, 4),
        }
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        return {"error": f"Execution timed out after {timeout}s", "exit_code": -1}


async def _run_shell(cmd: str, timeout: float = 15.0) -> dict[str, Any]:
    """Run a shell command, return stdout/stderr/exit_code."""
    for blocked in BLOCKED_SHELL_PATTERNS:
        if blocked in cmd:
            return {"error": f"Blocked pattern detected: '{blocked}'", "exit_code": -1}

    start = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        elapsed = time.monotonic() - start
        return {
            "stdout":    stdout.decode(errors="replace").strip(),
            "stderr":    stderr.decode(errors="replace").strip(),
            "exit_code": proc.returncode,
            "elapsed_s": round(elapsed, 4),
        }
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        return {"error": f"Shell command timed out after {timeout}s", "exit_code": -1}


# ── Entry point ────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

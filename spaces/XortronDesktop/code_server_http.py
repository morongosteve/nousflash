#!/usr/bin/env python3
"""
code_server_http.py — Thin HTTP server that exposes Python code execution
over a simple REST API so the XortronDesktop browser UI can call it directly.

Endpoints:
  POST /execute          { "code": "...", "timeout": 30 }
                         → { "stdout": "...", "stderr": "...",
                             "exit_code": 0, "elapsed_s": 0.12 }

  GET  /health           → { "status": "ok" }

  OPTIONS *              CORS preflight handled automatically

Usage:
  python3 code_server_http.py [--port 8081] [--host 127.0.0.1]

Requires only stdlib — no FastAPI/aiohttp needed.
"""

import asyncio
import json
import sys
import textwrap
import time
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# ── Blocked patterns (same as MCP server) ─────────────────────────────────
BLOCKED = ["rm -rf /", "mkfs", "dd if=/dev/zero", ":(){", "fork bomb"]

# ── Execution logic (stdlib only) ─────────────────────────────────────────

def execute_python(code: str, timeout: float = 30.0) -> dict:
    """Run Python code in a subprocess; return stdout/stderr/exit_code."""
    import subprocess, time as _time
    start = _time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", textwrap.dedent(code)],
            capture_output=True,
            timeout=timeout,
            text=True,
        )
        elapsed = _time.monotonic() - start
        return {
            "stdout":    proc.stdout.strip(),
            "stderr":    proc.stderr.strip(),
            "exit_code": proc.returncode,
            "elapsed_s": round(elapsed, 4),
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Execution timed out after {timeout}s",
                "stdout": "", "stderr": "", "exit_code": -1, "elapsed_s": timeout}
    except Exception as e:
        return {"error": str(e), "stdout": "", "stderr": "", "exit_code": -1}


# ── HTTP handler ───────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    """Minimal HTTP handler with CORS support."""

    def log_message(self, fmt, *args):
        print(f"[code-http] {self.address_string()} {fmt % args}", flush=True)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/health", "/health/"):
            body = json.dumps({"status": "ok", "server": "xortron-code-http"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path not in ("/execute", "/execute/"):
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length).decode())
        except Exception:
            self._json_response(400, {"error": "Invalid JSON body"})
            return

        code    = payload.get("code", "")
        timeout = float(payload.get("timeout", 30))

        if not code.strip():
            self._json_response(400, {"error": "No code provided"})
            return

        result = execute_python(code, timeout)
        self._json_response(200, result)

    def _json_response(self, status: int, data: dict):
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="XortronDesktop code execution HTTP server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8081, help="Port (default: 8081)")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), Handler)
    print(f"[code-http] Listening on http://{args.host}:{args.port}", flush=True)
    print(f"[code-http] POST /execute  {{\"code\": \"print('hello')\"}}", flush=True)
    print(f"[code-http] GET  /health", flush=True)
    print(f"[code-http] Press Ctrl-C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[code-http] Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()

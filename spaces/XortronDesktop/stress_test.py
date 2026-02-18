#!/usr/bin/env python3
"""
stress_test.py — Exercises every path of the MCP ↔ LlamaIndex bridge.

Tests:
  1. Basic execution          — hello world sanity check
  2. Complex math             — prime sieve, Fibonacci, modular exponentiation
  3. Data manipulation        — matrix ops, frequency analysis, sorting
  4. Multi-package import     — json + hashlib + statistics pipeline
  5. Self-correction          — code with a missing import (auto-fixed)
  6. Shell tool               — uname, disk usage
  7. Timeout guard            — infinite loop killed cleanly
  8. Error propagation        — deliberate SyntaxError
  9. LlamaIndex FunctionTool  — tool invocation through llama_index adapter
 10. Concurrent executions    — 4 tasks in parallel
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xortron_mcp_bridge import McpCodeBridge, code_bridge

# ── Pretty printer ─────────────────────────────────────────────────────────
PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
INFO = "\033[94m·\033[0m"

results = []

def report(label: str, passed: bool, detail: str = ""):
    mark = PASS if passed else FAIL
    results.append((label, passed))
    print(f"  {mark}  {label}")
    if detail:
        for line in detail.strip().splitlines():
            print(f"      {INFO} {line}")

# ── Tests ──────────────────────────────────────────────────────────────────

async def test_basic(bridge: McpCodeBridge):
    r = await bridge.execute_python("print('XortronDesktop MCP bridge online')")
    ok = r.get("exit_code") == 0 and "online" in r.get("stdout", "")
    report("Basic execution", ok, r.get("stdout",""))

async def test_complex_math(bridge: McpCodeBridge):
    code = """
import math
from decimal import Decimal, getcontext

# 1. Sieve of Eratosthenes — primes up to 1000
def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n+1, i):
                is_prime[j] = False
    return [x for x in range(2, n+1) if is_prime[x]]

primes = sieve(1000)
print(f"Primes ≤ 1000: {len(primes)} found, last={primes[-1]}")

# 2. Fast Fibonacci via matrix exponentiation
def mat_mul(A, B):
    return [
        [A[0][0]*B[0][0] + A[0][1]*B[1][0], A[0][0]*B[0][1] + A[0][1]*B[1][1]],
        [A[1][0]*B[0][0] + A[1][1]*B[1][0], A[1][0]*B[0][1] + A[1][1]*B[1][1]],
    ]
def mat_pow(M, n):
    if n == 1: return M
    if n % 2 == 0:
        half = mat_pow(M, n // 2)
        return mat_mul(half, half)
    return mat_mul(M, mat_pow(M, n - 1))
def fib(n):
    if n <= 1: return n
    return mat_pow([[1,1],[1,0]], n)[0][1]

print(f"Fib(50) = {fib(50)}")
print(f"Fib(100) = {fib(100)}")

# 3. High-precision π via Machin-like formula (100 decimal places)
getcontext().prec = 110
four = Decimal(4)
one  = Decimal(1)
def atan_dec(x):
    x = Decimal(x)
    result = x; power = x; sign = -1
    for k in range(1, 200):
        power *= x * x
        term = power / (2*k + 1)
        result += sign * term
        sign = -sign
    return result
pi = four * (four * atan_dec(Decimal(1)/5) - atan_dec(Decimal(1)/239))
print(f"π (100 dp): {str(pi)[:103]}")

# 4. RSA-style modular exponentiation
base, exp, mod = 65537, 2**31 - 1, 10**18 + 9
result = pow(base, exp, mod)
print(f"pow({base}, 2^31-1, 10^18+9) = {result}")
"""
    r = await bridge.execute_python(code)
    ok = r.get("exit_code") == 0 and "Fib(100)" in r.get("stdout", "")
    detail = r.get("stdout", "")[:600]
    report("Complex math (sieve + fib-matrix + decimal π + modexp)", ok, detail)

async def test_data_manipulation(bridge: McpCodeBridge):
    code = """
import json, statistics, hashlib, collections, functools

# Caesar cipher round-trip
def caesar(text, shift):
    out = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            out.append(chr((ord(c) - base + shift) % 26 + base))
        else:
            out.append(c)
    return ''.join(out)

msg   = "XortronDesktop is chaotic neutral"
enc   = caesar(msg, 13)
dec   = caesar(enc, 13)
assert dec == msg, "Caesar round-trip failed"
print(f"Caesar ROT13: '{msg[:20]}…' → '{enc[:20]}…' → round-trip OK")

# Statistical pipeline
data = [x**2 - 3*x + 1 for x in range(-20, 21)]
print(f"Dataset n={len(data)}, mean={statistics.mean(data):.2f}, "
      f"stdev={statistics.stdev(data):.2f}, median={statistics.median(data)}")

# Top-N frequency
words  = "the quick brown fox jumps over the lazy dog the fox".split()
freq   = collections.Counter(words).most_common(3)
print(f"Top-3 words: {freq}")

# SHA-256 chain (10 iterations)
h = "xortron"
for _ in range(10):
    h = hashlib.sha256(h.encode()).hexdigest()
print(f"SHA-256 chain (10x): {h[:32]}…")

# Flatten + sort + dedupe pipeline
nested = [[3,1,4],[1,5,9],[2,6,5],[3,5],[8,9,7,9]]
flat   = sorted(set(functools.reduce(lambda a,b: a+b, nested)))
print(f"Flatten+dedup+sort: {flat}")
"""
    r = await bridge.execute_python(code)
    ok = r.get("exit_code") == 0 and "SHA-256" in r.get("stdout", "")
    report("Data manipulation (cipher, stats, counter, hash, reduce)", ok, r.get("stdout","")[:400])

async def test_self_correction(bridge: McpCodeBridge):
    """Code references 'math' without importing it — bridge should auto-fix."""
    code = "result = math.factorial(20)\nprint(f'20! = {result}')"
    r = await bridge.execute_python(code, self_correct=True)
    ok = (r.get("exit_code") == 0
          and "2432902008176640000" in r.get("stdout", "")
          and r.get("attempts", 1) > 1)
    report(
        "Self-correction (auto-inject missing import)",
        ok,
        f"attempts={r.get('attempts')}, stdout={r.get('stdout','')}",
    )

async def test_shell(bridge: McpCodeBridge):
    r = await bridge.execute_shell("uname -s && python3 --version && df -h / | tail -1")
    ok = r.get("exit_code") == 0 and len(r.get("stdout", "")) > 0
    report("Shell execution (uname + python version + df)", ok, r.get("stdout",""))

async def test_timeout(bridge: McpCodeBridge):
    """Infinite loop must be killed cleanly within the timeout window."""
    r = await bridge.execute_python("while True: pass", timeout=2.0, self_correct=False)
    ok = r.get("exit_code") == -1 or "timed out" in str(r.get("error", "")).lower()
    report("Timeout guard (infinite loop killed in 2s)", ok, str(r.get("error","")))

async def test_error_propagation(bridge: McpCodeBridge):
    """Deliberate SyntaxError — self_correct=False, error must be captured, not thrown."""
    r = await bridge.execute_python("def f(:\n    pass", self_correct=False)
    ok = r.get("exit_code") != 0 and ("SyntaxError" in r.get("stderr","") or r.get("exit_code") == 1)
    report("Error propagation (SyntaxError captured, not raised)", ok, r.get("stderr","")[:120])

async def test_llamaindex_tool(bridge: McpCodeBridge):
    """Invoke bridge via the LlamaIndex FunctionTool interface."""
    tools = bridge.llama_tools()
    assert len(tools) == 2

    run_python_tool = next(t for t in tools if t.metadata.name == "execute_python")
    tool_output = run_python_tool(
        code="import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor} via LlamaIndex FunctionTool')"
    )
    # LlamaIndex wraps the return value in a ToolOutput — extract the raw content string
    raw  = tool_output.content if hasattr(tool_output, "content") else str(tool_output)
    data = json.loads(raw)
    ok = data.get("exit_code") == 0 and "LlamaIndex FunctionTool" in data.get("stdout","")
    report("LlamaIndex FunctionTool adapter", ok, data.get("stdout",""))

async def test_concurrent(bridge: McpCodeBridge):
    """Four Python executions running in parallel."""
    snippets = [
        "import time; time.sleep(0.1); print('task A done')",
        "print(sum(range(1_000_000)))",
        "print([x*x for x in range(10)])",
        "print('hello from task D')",
    ]
    t0    = time.monotonic()
    tasks = [bridge.execute_python(s) for s in snippets]
    outs  = await asyncio.gather(*tasks)
    elapsed = time.monotonic() - t0
    ok = all(r.get("exit_code") == 0 for r in outs)
    report(
        f"Concurrent execution (4 tasks in parallel, {elapsed:.2f}s total)",
        ok,
        "\n".join(r.get("stdout","")[:60] for r in outs),
    )

# ── Main runner ────────────────────────────────────────────────────────────

async def main():
    print("\n" + "━"*58)
    print("  XortronDesktop — MCP Code Execution Bridge Stress Test")
    print("  Architecture Path: Self-Correcting (no Docker/Jupyter)")
    print("━"*58 + "\n")

    print("Connecting to MCP server…")
    async with code_bridge() as bridge:
        print("Connected.\n")

        await test_basic(bridge)
        await test_complex_math(bridge)
        await test_data_manipulation(bridge)
        await test_self_correction(bridge)
        await test_shell(bridge)
        await test_timeout(bridge)
        await test_error_propagation(bridge)
        await test_llamaindex_tool(bridge)
        await test_concurrent(bridge)

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "━"*58)
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    color  = "\033[92m" if passed == total else "\033[91m"
    print(f"  {color}{passed}/{total} tests passed\033[0m")
    print("━"*58 + "\n")

    if passed < total:
        print("  FAILED:")
        for name, ok in results:
            if not ok:
                print(f"    ✗  {name}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

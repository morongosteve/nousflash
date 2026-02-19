# XortronDesktop — Quick Start

**Static chat UI with streaming support, code execution, and dual backends (llama-server + Anthropic).**

---

## Files

| File | Purpose |
|------|---------|
| `index.html` | Chat UI (static, purple/pink theme) |
| `app.js` | Frontend logic: streaming, commands, settings |
| `test.html` | 18 test suites (~130 tests), open in browser to run |
| `start_server.sh` | Launch llama-server (llama.cpp HTTP backend) |
| `code_server_http.py` | HTTP server for `/run` command (Python code execution) |
| `mcp_code_server.py` | MCP stdio server (used by `xortron_mcp_bridge.py`) |
| `xortron_mcp_bridge.py` | LlamaIndex ↔ MCP bridge (async, self-correcting) |
| `stress_test.py` | 9-test suite for MCP bridge (all passing) |

---

## Quick Start — Local Stack

```bash
# 1. Download the model (one-time, ~19.3 GB)
cd ../../agent/local_inference
./download_xortron.sh
cd ../../spaces/XortronDesktop

# 2. Start llama-server (OpenAI-compatible endpoint on :8080)
./start_server.sh

# 3. Start code execution server (for /run command on :8081)
python3 code_server_http.py

# 4. Open the chat UI
open index.html          # macOS
xdg-open index.html      # Linux
start index.html         # Windows
```

**Settings:**
- Backend: `OpenAI-compatible`
- Endpoint: `http://localhost:8080/v1/chat/completions`
- Model: `Xortron2025-24B`
- Code server: `http://localhost:8081/execute` (default)
- Streaming: ✓ enabled (default)

---

## Using Anthropic API Instead

```bash
# No local model needed — skip steps 1 & 2
python3 code_server_http.py    # only for /run command

open index.html
```

**Settings:**
- Backend: `Anthropic API`
- API Key: `sk-ant-...` (your key)
- Model: `claude-opus-4-5-20250929`
- Streaming: ✓ enabled

---

## Commands

| Command | Effect |
|---------|--------|
| `/help` | Show command list |
| `/clear` | Clear chat history |
| `/settings` | Open settings panel |
| `/model` | Show current backend/model/endpoint |
| `/system <text>` | Set system prompt |
| `/temp <0–2>` | Set temperature |
| `/tokens <n>` | Set max tokens |
| `/retry` | Retry last message |
| `/export` | Download chat as `.txt` |
| `/run <code>` | Execute Python on local code server |

**Example:**
```
/run import math; print(f"π = {math.pi:.15f}"); print(f"e = {math.e:.15f}")
```

---

## Features

### Streaming (SSE)
- Tokens appear live as they arrive
- Works with llama-server and Anthropic Messages API
- Toggle off via Settings if you prefer batch responses

### Code Execution (`/run`)
- Python 3 subprocess execution
- Timeout guard (default 30s)
- Blocked patterns: `rm -rf /`, `mkfs`, fork bombs
- Results render with:
  - Green ✓ for exit 0
  - Red ✗ for errors
  - Stdout in dark pre block
  - Stderr in red pre block

### Self-Correcting MCP Bridge (`xortron_mcp_bridge.py`)
- Auto-injects missing imports (`import math`, `import numpy as np`, etc.)
- Fixes common errors (IndentationError, Python 2-style `print`)
- Up to 3 retry attempts before giving up
- See `stress_test.py` for usage examples

---

## Tests

### Browser Tests (`test.html`)
Open `test.html` in any browser — auto-runs on load.

**18 suites:**
1. Config persistence
2. HTML escaping (XSS prevention)
3. Status indicator
4. Panel toggles
5. Backend selector
6. Settings save/load
7. Chat rendering
8. Welcome screen
9. Commands (all 10)
10. `sendMessage` input handling
11. `runInference` lifecycle
12. `callOpenAICompat` (non-streaming)
13. `callAnthropic` (non-streaming)
14. `callLLM` routing
15. `testConnection` (settings stays open)
16. **Streaming SSE parsing** (delta.content, text_delta, malformed chunks)
17. **Code execution** (/run, stdout/stderr rendering)
18. **Integration** (runInference with stream:true/false)

### MCP Bridge Tests (`stress_test.py`)
```bash
python3 stress_test.py
```

**9 tests:**
1. Basic execution
2. Complex math (prime sieve, Fibonacci, π to 100 decimals, modexp)
3. Data manipulation (ROT13, stats, SHA-256 chain)
4. Self-correction (auto-inject missing import)
5. Shell execution
6. Timeout guard
7. Error propagation
8. LlamaIndex FunctionTool adapter
9. Concurrent execution (4 tasks in parallel)

---

## Deployment

### Local (current setup)
- Works out of the box
- All three servers run on localhost

### Hugging Face Spaces (static)
- Upload `index.html`, `app.js`
- Works for **Anthropic backend only** (no local model/code server)
- `/run` command will fail (no backend to POST to)

### Hugging Face Spaces (Gradio)
To support local model + code execution on HF:
1. Convert to `sdk: gradio`
2. Wrap `code_server_http.py` as a Gradio API route
3. Bundle llama-server startup in `app.py`

### Docker
- Use `agent/Dockerfile` with `WITH_LOCAL_INFERENCE=true`
- Expose ports 8080 (llama-server), 8081 (code server), 80 (static UI)
- Mount `agent/local_inference/models/` as volume

---

## Troubleshooting

**"Empty response from server"**
- Check llama-server is running: `curl http://localhost:8080/health`
- Verify model was downloaded: `ls -lh ../../agent/local_inference/models/`

**"Cannot reach code server"**
- Check code server is running: `curl http://localhost:8081/health`
- Should return `{"status": "ok", "server": "xortron-code-http"}`

**llama-server fails to start**
- Model missing → run `../../agent/local_inference/download_xortron.sh`
- Not enough RAM → need 21GB+ for Q6_K quantization
- Binary missing → run `../../agent/local_inference/setup_llama_cpp.sh`

**Streaming not working**
- Check Settings → Streaming is enabled (toggle should be purple)
- Some endpoints don't support SSE — disable streaming if broken

**Anthropic "temperature must be ≤ 1.0"**
- Already clamped in code — if you see this, clear cache and reload

---

## Architecture

```
┌──────────────┐
│ index.html   │  ← Static UI (browser)
│ app.js       │
└──────┬───────┘
       │
       ├─HTTP──→ llama-server :8080         (optional, local model)
       │         ↓
       │         llama.cpp → Xortron2025-24B.gguf
       │
       ├─HTTPS─→ api.anthropic.com          (optional, remote API)
       │
       └─HTTP──→ code_server_http.py :8081  (optional, /run command)
                 ↓
                 subprocess.run(python3 -c "...")
```

**MCP bridge** (separate Python stack, not used by browser UI):
```
LlamaIndex Agent
    ↓ llama_tools()
xortron_mcp_bridge.py (async)
    ↓ stdio
mcp_code_server.py
    ↓ subprocess
Python / shell execution
```

---

## License

WTFPL (same as Xortron2025 model)

#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# start_server.sh — Launch llama-server (llama.cpp HTTP backend) for Xortron2025
#
# Usage:
#   ./start_server.sh [OPTIONS]
#
# Options (all optional, env vars also accepted):
#   --model    PATH   Path to GGUF model file  [default: auto-detected]
#   --host     ADDR   Bind address              [default: 0.0.0.0]
#   --port     PORT   HTTP port                 [default: 8080]
#   --ctx-size INT    Context window in tokens  [default: 8192]
#   --threads  INT    CPU threads to use        [default: physical core count]
#   --gpu-layers INT  Layers to offload to GPU  [default: 0 = CPU-only]
#   --api-key  KEY    Require this Bearer token [default: none]
#
# Environment variables (override defaults, overridden by flags):
#   MODEL_PATH, SERVER_HOST, SERVER_PORT, CTX_SIZE, THREADS, GPU_LAYERS, API_KEY
# ---------------------------------------------------------------------------

set -euo pipefail

# ---- helpers ---------------------------------------------------------------
die()  { echo "ERROR: $*" >&2; exit 1; }
info() { echo "[xortron] $*"; }

# ---- locate repo root -------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOCAL_INFERENCE="$REPO_ROOT/agent/local_inference"

# ---- defaults ---------------------------------------------------------------
HOST="${SERVER_HOST:-0.0.0.0}"
PORT="${SERVER_PORT:-8080}"
CTX_SIZE="${CTX_SIZE:-8192}"
GPU_LAYERS="${GPU_LAYERS:-0}"
API_KEY="${API_KEY:-}"

# Default thread count = physical cores
THREADS="${THREADS:-$(nproc 2>/dev/null || sysctl -n hw.physicalcpu 2>/dev/null || echo 4)}"

# ---- parse flags ------------------------------------------------------------
MODEL_PATH="${MODEL_PATH:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)      MODEL_PATH="$2";  shift 2 ;;
        --host)       HOST="$2";        shift 2 ;;
        --port)       PORT="$2";        shift 2 ;;
        --ctx-size)   CTX_SIZE="$2";    shift 2 ;;
        --threads)    THREADS="$2";     shift 2 ;;
        --gpu-layers) GPU_LAYERS="$2";  shift 2 ;;
        --api-key)    API_KEY="$2";     shift 2 ;;
        -h|--help)
            sed -n '/^# Usage/,/^# ---/p' "$0"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# ---- find model file --------------------------------------------------------
if [[ -z "$MODEL_PATH" ]]; then
    CANDIDATE_PATHS=(
        "$LOCAL_INFERENCE/models/Xortron2025-24B.Q6_K.gguf"
        "$SCRIPT_DIR/../local_inference/models/Xortron2025-24B.Q6_K.gguf"
        "$HOME/models/Xortron2025-24B.Q6_K.gguf"
        "/data/models/Xortron2025-24B.Q6_K.gguf"
    )
    for p in "${CANDIDATE_PATHS[@]}"; do
        if [[ -f "$p" ]]; then
            MODEL_PATH="$p"
            break
        fi
    done
fi

[[ -n "$MODEL_PATH" ]] || die "Model not found. Download it first:\n  cd $LOCAL_INFERENCE && ./download_xortron.sh\nor pass --model /path/to/Xortron2025-24B.Q6_K.gguf"
[[ -f "$MODEL_PATH" ]] || die "Model file does not exist: $MODEL_PATH"

# ---- find llama-server binary -----------------------------------------------
find_binary() {
    local name="$1"
    local candidates=(
        "$LOCAL_INFERENCE/llama.cpp/build/bin/$name"
        "$LOCAL_INFERENCE/llama.cpp/build/bin/Release/$name.exe"
        "$(command -v "$name" 2>/dev/null || true)"
    )
    for c in "${candidates[@]}"; do
        [[ -f "$c" && -x "$c" ]] && { echo "$c"; return; }
    done
}

SERVER_BIN="$(find_binary "llama-server")"

if [[ -z "$SERVER_BIN" ]]; then
    die "llama-server not found. Build llama.cpp first:
  cd $LOCAL_INFERENCE && ./setup_llama_cpp.sh
or install from: https://github.com/ggerganov/llama.cpp/releases"
fi

# ---- print config summary ---------------------------------------------------
info "=============================="
info "  Xortron2025 Local Backend"
info "=============================="
info "Binary : $SERVER_BIN"
info "Model  : $MODEL_PATH"
info "Listen : http://$HOST:$PORT"
info "Context: ${CTX_SIZE} tokens"
info "Threads: $THREADS"
info "GPU    : ${GPU_LAYERS} layers"
[[ -n "$API_KEY" ]] && info "Auth   : Bearer token enabled" || info "Auth   : none (open)"
info ""
info "OpenAI-compatible endpoint:"
info "  POST http://localhost:$PORT/v1/chat/completions"
info ""
info "Paste this into XortronDesktop → Settings:"
info "  Backend : OpenAI-compatible"
info "  Endpoint: http://localhost:$PORT/v1/chat/completions"
[[ -n "$API_KEY" ]] && info "  API Key : $API_KEY"
info "=============================="
info "Starting server... (Ctrl-C to stop)"
info ""

# ---- build argument list ----------------------------------------------------
ARGS=(
    --model          "$MODEL_PATH"
    --host           "$HOST"
    --port           "$PORT"
    --ctx-size       "$CTX_SIZE"
    --threads        "$THREADS"
    --n-gpu-layers   "$GPU_LAYERS"
    --log-format     text
)

[[ -n "$API_KEY" ]] && ARGS+=(--api-key "$API_KEY")

# ---- launch -----------------------------------------------------------------
exec "$SERVER_BIN" "${ARGS[@]}"

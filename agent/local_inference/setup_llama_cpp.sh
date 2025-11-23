#!/bin/bash
# Setup script for llama.cpp
# This script clones and builds llama.cpp for local GGUF model inference

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LLAMA_CPP_DIR="$SCRIPT_DIR/llama.cpp"

echo "Setting up llama.cpp for local inference..."

# Check if llama.cpp already exists
if [ -d "$LLAMA_CPP_DIR" ]; then
    echo "llama.cpp directory already exists. Pulling latest changes..."
    cd "$LLAMA_CPP_DIR"
    git pull
else
    echo "Cloning llama.cpp repository..."
    cd "$SCRIPT_DIR"
    git clone https://github.com/ggml-org/llama.cpp
    cd llama.cpp
fi

echo "Building llama.cpp..."
cmake -S . -B build
cmake --build build -j

echo ""
echo "✓ llama.cpp setup complete!"
echo "Binary location: $LLAMA_CPP_DIR/build/bin/llama-cli"
echo ""
echo "Next steps:"
echo "1. Run ./download_xortron.sh to download the Xortron2025 model"
echo "2. Use the Python wrapper to run inference"

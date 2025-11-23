#!/bin/bash
# Download Xortron2025-24B GGUF model from Hugging Face
# Model: darkc0de/Xortron2025
# Size: ~19.3 GB (Q6_K quantization)

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODELS_DIR="$SCRIPT_DIR/models"
MODEL_FILE="Xortron2025-24B.Q6_K.gguf"
MODEL_URL="https://huggingface.co/darkc0de/Xortron2025/resolve/main/$MODEL_FILE"

echo "Downloading Xortron2025-24B GGUF model..."
echo "Size: ~19.3 GB - This will take a while!"
echo ""

# Create models directory
mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

# Check if model already exists
if [ -f "$MODEL_FILE" ]; then
    echo "Model file already exists at $MODELS_DIR/$MODEL_FILE"
    echo "Delete it if you want to re-download."
    exit 0
fi

# Download with curl (with resume support)
echo "Downloading from: $MODEL_URL"
echo "Destination: $MODELS_DIR/$MODEL_FILE"
echo ""
curl -L -C - -o "$MODEL_FILE" "$MODEL_URL"

echo ""
echo "✓ Download complete!"
echo "Model location: $MODELS_DIR/$MODEL_FILE"
echo ""
echo "Model details:"
echo "- Architecture: Mistral/Llama-family (24B parameters)"
echo "- Quantization: Q6_K (6-bit)"
echo "- RAM requirement: ~21GB+"
echo "- License: WTFPL"
echo ""
echo "You can now use the Python wrapper to run inference!"

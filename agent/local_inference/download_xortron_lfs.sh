#!/bin/bash
# Alternative download method using git-lfs for Xortron2025-24B
# This method clones the entire repository including the GGUF model
# Requires: git-lfs

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODELS_DIR="$SCRIPT_DIR/models"
REPO_DIR="$MODELS_DIR/Xortron2025-repo"
MODEL_FILE="Xortron2025-24B.Q6_K.gguf"

echo "Downloading Xortron2025-24B using git-lfs..."
echo "This method clones the entire Hugging Face repository."
echo ""

# Check if git-lfs is installed
if ! command -v git-lfs &> /dev/null; then
    echo "Error: git-lfs is not installed."
    echo ""
    echo "Install git-lfs:"
    echo "  Ubuntu/Debian: sudo apt-get install git-lfs"
    echo "  macOS: brew install git-lfs"
    echo "  Fedora: sudo dnf install git-lfs"
    echo ""
    echo "After installation, run: git lfs install"
    exit 1
fi

# Create models directory
mkdir -p "$MODELS_DIR"

# Check if repo already exists
if [ -d "$REPO_DIR" ]; then
    echo "Repository already exists at $REPO_DIR"
    echo "Pulling latest changes..."
    cd "$REPO_DIR"
    git pull
else
    echo "Cloning repository from Hugging Face..."
    echo "Repository: darkc0de/Xortron2025"
    echo ""
    cd "$MODELS_DIR"
    git lfs install
    git clone https://huggingface.co/darkc0de/Xortron2025 Xortron2025-repo
    cd Xortron2025-repo
fi

# Create symlink to model file for consistency
if [ ! -f "$MODELS_DIR/$MODEL_FILE" ]; then
    echo "Creating symlink to model file..."
    ln -s "$REPO_DIR/$MODEL_FILE" "$MODELS_DIR/$MODEL_FILE"
fi

echo ""
echo "✓ Download complete!"
echo "Repository location: $REPO_DIR"
echo "Model location: $REPO_DIR/$MODEL_FILE"
echo "Symlink: $MODELS_DIR/$MODEL_FILE"
echo ""
echo "Model details:"
echo "- Architecture: Mistral/Llama-family (24B parameters)"
echo "- Quantization: Q6_K (6-bit)"
echo "- RAM requirement: ~21GB+"
echo "- License: WTFPL"
echo ""
echo "Additional files in repository:"
echo "- README.md - Model card and documentation"
echo "- config.json - Model configuration"
echo ""
echo "You can now use the Python wrapper to run inference!"

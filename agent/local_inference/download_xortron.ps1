# PowerShell script for downloading Xortron2025-24B GGUF model from Hugging Face
# Model: darkc0de/Xortron2025
# Size: ~19.3 GB (Q6_K quantization)

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$MODELS_DIR = Join-Path $SCRIPT_DIR "models"
$MODEL_FILE = "Xortron2025-24B.Q6_K.gguf"
$MODEL_URL = "https://huggingface.co/darkc0de/Xortron2025/resolve/main/$MODEL_FILE"

Write-Host "Downloading Xortron2025-24B GGUF model..." -ForegroundColor Green
Write-Host "Size: ~19.3 GB - This will take a while!" -ForegroundColor Yellow
Write-Host ""

# Create models directory
New-Item -ItemType Directory -Force -Path $MODELS_DIR | Out-Null
Set-Location $MODELS_DIR

# Check if model already exists
$MODEL_PATH = Join-Path $MODELS_DIR $MODEL_FILE
if (Test-Path $MODEL_PATH) {
    Write-Host "Model file already exists at $MODEL_PATH" -ForegroundColor Yellow
    Write-Host "Delete it if you want to re-download." -ForegroundColor Yellow
    exit 0
}

# Download with curl (with resume support)
Write-Host "Downloading from: $MODEL_URL" -ForegroundColor Cyan
Write-Host "Destination: $MODEL_PATH" -ForegroundColor Cyan
Write-Host ""

# Use curl.exe (included in Windows 10+)
curl.exe -L -C - -o $MODEL_FILE $MODEL_URL

Write-Host ""
Write-Host "✓ Download complete!" -ForegroundColor Green
Write-Host "Model location: $MODEL_PATH" -ForegroundColor Cyan
Write-Host ""
Write-Host "Model details:" -ForegroundColor Yellow
Write-Host "- Architecture: Mistral/Llama-family (24B parameters)"
Write-Host "- Quantization: Q6_K (6-bit)"
Write-Host "- RAM requirement: ~21GB+"
Write-Host "- License: WTFPL"
Write-Host ""
Write-Host "You can now use the Python wrapper to run inference!" -ForegroundColor Green

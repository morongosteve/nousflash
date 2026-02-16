# PowerShell script for setting up llama.cpp on Windows
# Requires: cmake, Visual Studio Build Tools (Desktop development with C++)

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$LLAMA_CPP_DIR = Join-Path $SCRIPT_DIR "llama.cpp"

Write-Host "Setting up llama.cpp for local inference on Windows..." -ForegroundColor Green

# Check if llama.cpp already exists
if (Test-Path $LLAMA_CPP_DIR) {
    Write-Host "llama.cpp directory already exists. Pulling latest changes..." -ForegroundColor Yellow
    Set-Location $LLAMA_CPP_DIR
    git pull
} else {
    Write-Host "Cloning llama.cpp repository..." -ForegroundColor Cyan
    Set-Location $SCRIPT_DIR
    git clone https://github.com/ggml-org/llama.cpp
    Set-Location llama.cpp
}

Write-Host "Building llama.cpp..." -ForegroundColor Cyan
cmake -S . -B build
cmake --build build --config Release

Write-Host ""
Write-Host "✓ llama.cpp setup complete!" -ForegroundColor Green
Write-Host "Binary location: $LLAMA_CPP_DIR\build\bin\Release\llama-cli.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run .\download_xortron.ps1 to download the Xortron2025 model"
Write-Host "2. Use the Python wrapper to run inference"

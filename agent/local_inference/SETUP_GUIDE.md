# Complete Setup Guide for Xortron2025 Local Inference

This guide will walk you through setting up the Xortron2025-24B model for local inference from scratch.

## Overview

**What you're installing:**
- **llama.cpp**: High-performance C++ inference engine for GGUF models
- **Xortron2025-24B**: 24B parameter uncensored language model (Q6_K quantized, ~19.3 GB)

**System Requirements:**
- **RAM**: 21GB+ available memory (critical!)
- **Storage**: ~20GB free disk space
- **CPU**: Modern multi-core processor (GPU acceleration optional but recommended)
- **OS**: Linux, macOS, or Windows 10+

**Time estimate:**
- Setup: 5-15 minutes
- Download: 30 minutes - 2 hours (depending on internet speed)

---

## Quick Start (TL;DR)

### Linux / macOS
```bash
cd agent/local_inference
./setup_llama_cpp.sh          # Build llama.cpp (~5 min)
./download_xortron.sh          # Download model (~19.3 GB)
python verify_setup.py         # Verify everything works
```

### Windows (PowerShell)
```powershell
cd agent\local_inference
.\setup_llama_cpp.ps1          # Build llama.cpp (~5 min)
.\download_xortron.ps1         # Download model (~19.3 GB)
python verify_setup.py         # Verify everything works
```

---

## Detailed Step-by-Step Instructions

### Step 1: Install Prerequisites

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install cmake g++ make git curl
```

#### Linux (Fedora)
```bash
sudo dnf install cmake gcc-c++ make git curl
```

#### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install cmake
brew install cmake
```

#### Windows
1. **Install cmake**: Download from https://cmake.org/download/
   - Choose "Windows x64 Installer"
   - During installation, select "Add CMake to system PATH"

2. **Install Visual Studio Build Tools**:
   - Download from https://visualstudio.microsoft.com/downloads/
   - Under "Tools for Visual Studio", download "Build Tools for Visual Studio 2022"
   - During installation, select "Desktop development with C++"

3. **Verify installation** (PowerShell):
   ```powershell
   cmake --version
   cl.exe  # Should show Microsoft C/C++ compiler
   ```

### Step 2: Build llama.cpp

This step compiles the llama.cpp inference engine from source.

#### Linux / macOS
```bash
cd /path/to/nousflash/agent/local_inference
./setup_llama_cpp.sh
```

**What this does:**
1. Clones llama.cpp repository from GitHub
2. Configures build with cmake
3. Compiles the llama-cli binary
4. Places binary in `llama.cpp/build/bin/llama-cli`

**Expected output:**
```
Setting up llama.cpp for local inference...
Cloning llama.cpp repository...
Building llama.cpp...
[cmake output...]
✓ llama.cpp setup complete!
```

#### Windows (PowerShell)
```powershell
cd C:\path\to\nousflash\agent\local_inference
.\setup_llama_cpp.ps1
```

**Expected output:**
```
Setting up llama.cpp for local inference on Windows...
Cloning llama.cpp repository...
Building llama.cpp...
[cmake output...]
✓ llama.cpp setup complete!
```

**Troubleshooting:**
- If cmake is not found: Ensure cmake is in your PATH (restart terminal after installation)
- If compiler is not found: Ensure Visual Studio Build Tools are installed correctly

### Step 3: Download Xortron2025 Model

You have two download options:

#### Option A: Direct Download (Recommended)

**Linux / macOS:**
```bash
./download_xortron.sh
```

**Windows:**
```powershell
.\download_xortron.ps1
```

**What this does:**
- Downloads `Xortron2025-24B.Q6_K.gguf` (~19.3 GB) from Hugging Face
- Saves to `models/Xortron2025-24B.Q6_K.gguf`
- Supports resume if interrupted (Ctrl+C and re-run)

**Expected output:**
```
Downloading Xortron2025-24B GGUF model...
Size: ~19.3 GB - This will take a while!
Downloading from: https://huggingface.co/darkc0de/Xortron2025/...
[download progress...]
✓ Download complete!
```

#### Option B: Git-LFS (Alternative)

This method clones the entire Hugging Face repository.

**Prerequisites:**
```bash
# Ubuntu/Debian
sudo apt-get install git-lfs

# macOS
brew install git-lfs

# Initialize
git lfs install
```

**Download:**
```bash
./download_xortron_lfs.sh
```

**What you get:**
- `Xortron2025-24B.Q6_K.gguf` (model file)
- `README.md` (model card from Hugging Face)
- `config.json` (model configuration)

**Why use git-lfs?**
- Better for slow/unreliable connections (can resume properly)
- Includes model documentation
- Easier to update model if new versions are released

### Step 4: Verify Setup

Run the verification script to ensure everything is working:

```bash
python verify_setup.py
```

**What this checks:**
1. ✓ llama-cli is built and accessible
2. ✓ Model file exists and is the correct size (~19.3 GB)
3. ✓ Python can import the XortronInference class
4. ✓ Basic inference works (generates test output)
5. ⚠ System has sufficient RAM (21GB+)

**Expected output:**
```
============================================================
Xortron2025 Setup Verification
============================================================

============================================================
1. Checking llama.cpp
============================================================

✓ llama-cli found at: /path/to/llama.cpp/build/bin/llama-cli

============================================================
2. Checking Xortron2025 Model
============================================================

✓ Model found at: /path/to/models/Xortron2025-24B.Q6_K.gguf
  Size: 19.31 GB
✓ Model size looks correct (~19.3 GB expected)

============================================================
3. Checking Python Integration
============================================================

✓ Successfully imported XortronInference class

============================================================
4. Testing Basic Inference
============================================================

Running a quick test generation...
Prompt: 'Say hello in one sentence.'
This may take 30-60 seconds...

✓ Inference successful!

Generated output:
Hello! I'm happy to help you with any questions or tasks you have.

============================================================
5. Checking System Requirements
============================================================

Available RAM: 32.00 GB
✓ Sufficient RAM available (21GB+ required)

============================================================
Verification Summary
============================================================

✓ All checks passed! ✓

Your Xortron2025 setup is ready to use!
```

---

## Testing Your Setup

### Quick Python Test

```python
from local_inference.xortron_inference import XortronInference

# Initialize
xortron = XortronInference()

# Generate
response = xortron.generate("Write a creative tweet about AI.", max_tokens=100)
print(response)
```

### Command-Line Test

#### Linux / macOS
```bash
./llama.cpp/build/bin/llama-cli \
  -m models/Xortron2025-24B.Q6_K.gguf \
  -p "Say hello in one sentence." \
  --ctx-size 8192 \
  --temp 0.7 \
  --top-p 0.9 \
  -n 100
```

#### Windows
```powershell
.\llama.cpp\build\bin\Release\llama-cli.exe `
  -m models\Xortron2025-24B.Q6_K.gguf `
  -p "Say hello in one sentence." `
  --ctx-size 8192 `
  --temp 0.7 `
  --top-p 0.9 `
  -n 100
```

### Run Example Scripts

```bash
cd agent
python local_inference/example_usage.py
```

This will run several examples demonstrating different use cases.

---

## Integration with nousflash Agent

To use Xortron2025 with the nousflash Twitter agent:

```python
from engines.post_maker_local import generate_post_local, InferenceMode
from local_inference.xortron_inference import XortronInference

# Initialize Xortron once
xortron = XortronInference()

# Generate posts using local inference
tweet = generate_post_local(
    short_term_memory=memory,
    long_term_memories=memories,
    recent_posts=posts,
    external_context=context,
    inference_mode=InferenceMode.LOCAL,
    xortron_instance=xortron
)
```

See `agent/local_inference/README.md` for more details.

---

## Troubleshooting

### "llama-cli not found"

**Problem**: The llama.cpp binary was not built successfully.

**Solution**:
1. Verify prerequisites are installed (cmake, compiler)
2. Re-run setup script:
   ```bash
   ./setup_llama_cpp.sh  # or .ps1 on Windows
   ```
3. Check for error messages in the build output

### "Model not found"

**Problem**: The model file was not downloaded.

**Solution**:
1. Check available disk space (need ~20GB free)
2. Re-run download script:
   ```bash
   ./download_xortron.sh  # or .ps1 on Windows
   ```
3. If download keeps failing, try git-lfs method:
   ```bash
   ./download_xortron_lfs.sh
   ```

### Out of Memory Errors

**Problem**: System doesn't have enough available RAM.

**Solution**:
1. Close other applications to free up memory
2. Reduce context size:
   ```python
   xortron = XortronInference(ctx_size=4096)  # or even 2048
   ```
3. Consider using a smaller quantization (Q4_K_M) if available
4. Check available memory:
   ```bash
   free -h  # Linux
   vm_stat  # macOS
   ```

### Inference is Very Slow

**Problem**: Generation takes several minutes per response.

**Solutions**:

1. **First generation is always slower** (model loading). Subsequent generations should be faster.

2. **Enable GPU acceleration** (10-100x speedup):

   **NVIDIA GPU (CUDA)**:
   ```bash
   cd llama.cpp
   cmake -S . -B build -DGGML_CUDA=ON
   cmake --build build -j
   ```

   **Apple Silicon (Metal)**:
   ```bash
   cd llama.cpp
   cmake -S . -B build -DGGML_METAL=ON
   cmake --build build -j
   ```

3. **Reduce context size**:
   ```python
   xortron = XortronInference(ctx_size=2048)  # Smaller = faster
   ```

4. **Check system load**:
   ```bash
   htop  # or top
   ```

### Windows: "cl.exe is not recognized"

**Problem**: C++ compiler not found.

**Solution**:
1. Install Visual Studio Build Tools
2. Select "Desktop development with C++" workload
3. Restart PowerShell after installation
4. Try running from "Developer Command Prompt for VS 2022"

### Download Interrupted

**Problem**: Network issues during 19.3GB download.

**Solution**:
- Both download scripts support resume - just re-run them!
- The `-C -` flag in curl enables resume from where it left off
- Alternatively, use git-lfs which handles resume better:
  ```bash
  ./download_xortron_lfs.sh
  ```

---

## Model Information

### Repository Details

- **Hugging Face**: https://huggingface.co/darkc0de/Xortron2025
- **Files**:
  - `Xortron2025-24B.Q6_K.gguf` (19.3 GB) - The model weights
  - `README.md` - Model card
  - `config.json` - Model configuration
  - `.gitattributes` - Git LFS configuration

### Model Lineage

1. **Base**: TroyDoesAI/BlackSheep-24B
2. **Fine-tuned**: darkc0de/Xortron24DPO (DPO training)
3. **Quantized**: darkc0de/Xortron2025 (Q6_K GGUF)

### Training Datasets

- huihui-ai/Guilherme34_uncensor
- mlabonne/orpo-dpo-mix-40k-flat
- Undi95/toxic-dpo-v0.1-NoWarning

### Technical Specifications

- **Architecture**: Mistral-family (Llama-compatible)
- **Parameters**: 24 billion
- **Quantization**: Q6_K (6-bit)
- **Original size**: ~48GB (FP16)
- **Quantized size**: ~19.3GB (60% reduction)
- **Context window**: 8192 tokens (tunable: 2048-32768)
- **License**: WTFPL (Do What The F*** You Want To Public License)

### Performance Characteristics

**Memory Usage**:
- Model: ~19.3 GB (loaded in RAM)
- Context (8192 tokens): ~1-2 GB
- Total: ~21 GB minimum

**Speed** (CPU inference, typical consumer hardware):
- First token: 10-30 seconds (model loading)
- Subsequent tokens: 1-5 tokens/second
- With GPU: 20-100+ tokens/second

**Quality**:
- Q6_K provides near-FP16 quality
- Minimal degradation vs. full precision
- Suitable for production use

---

## Next Steps

✅ **Setup complete!** Your Xortron2025 local inference is ready.

**Learn more:**
- See `README.md` for Python API documentation
- Run `python example_usage.py` for code examples
- Check `post_maker_local.py` for nousflash integration

**GPU acceleration** (recommended for production):
- See llama.cpp documentation: https://github.com/ggml-org/llama.cpp#gpu-support
- CUDA (NVIDIA), Metal (macOS), OpenCL all supported

**Experiment:**
- Try different temperature/top-p values for varied output
- Adjust context size based on your use case
- Compare with API-based inference (see README.md)

---

## Additional Resources

- **llama.cpp**: https://github.com/ggml-org/llama.cpp
- **GGUF Format**: https://github.com/ggml-org/ggml/blob/master/docs/gguf.md
- **Model on Hugging Face**: https://huggingface.co/darkc0de/Xortron2025
- **nousflash Agent**: https://github.com/nousresearch/nousflash-agents

---

## Support

If you encounter issues:
1. Check this guide's Troubleshooting section
2. Run `python verify_setup.py` for diagnostic info
3. See `README.md` for additional help
4. Check llama.cpp GitHub issues for build problems

**Common issues and solutions are documented above.**

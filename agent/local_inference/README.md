# Xortron2025 Local Inference Setup

This directory contains everything needed to run the **Xortron2025-24B** model locally using **llama.cpp**, eliminating the need for paid API services.

## Model Information

- **Model**: darkc0de/Xortron2025
- **Size**: 24B parameters (~19.3 GB download)
- **Quantization**: Q6_K (6-bit)
- **Architecture**: Mistral/Llama-family
- **License**: WTFPL
- **RAM Required**: ~21GB+ for inference
- **Context Window**: 8192 tokens (configurable)

### Model Lineage

The Xortron2025 model was created through this pipeline:
1. **Base**: TroyDoesAI/BlackSheep-24B (24B parameter base model)
2. **Fine-tuned**: darkc0de/Xortron24DPO (DPO fine-tuning)
3. **Quantized**: darkc0de/Xortron2025 (Q6_K GGUF - this repo)

### Training Datasets

The model was trained on:
- huihui-ai/Guilherme34_uncensor
- mlabonne/orpo-dpo-mix-40k-flat
- Undi95/toxic-dpo-v0.1-NoWarning

**Note**: This is an uncensored model designed for creative/experimental use. Use responsibly.

## Quick Start

### Platform-Specific Instructions

#### Linux / macOS

##### 1. Build llama.cpp

```bash
cd agent/local_inference
./setup_llama_cpp.sh
```

##### 2. Download Xortron2025 Model

**Option A: Direct Download (Recommended)**
```bash
./download_xortron.sh
```

**Option B: Git-LFS (Alternative)**
```bash
./download_xortron_lfs.sh
```

The git-lfs method clones the entire Hugging Face repository, which includes:
- The GGUF model file
- README.md (model card)
- config.json (model configuration)

**Requirements for git-lfs**:
```bash
# Ubuntu/Debian
sudo apt-get install git-lfs

# macOS
brew install git-lfs

# Fedora
sudo dnf install git-lfs

# Then initialize
git lfs install
```

##### 3. Verify Setup

```bash
python verify_setup.py
```

This comprehensive verification script checks:
- llama.cpp is built correctly
- Model is downloaded and valid
- Python integration works
- Basic inference functions
- System requirements (RAM)

#### Windows

##### 1. Build llama.cpp

**Requirements**:
- cmake (download from https://cmake.org/download/)
- Visual Studio Build Tools with "Desktop development with C++" workload

```powershell
cd agent\local_inference
.\setup_llama_cpp.ps1
```

##### 2. Download Xortron2025 Model

```powershell
.\download_xortron.ps1
```

**Note**: Windows 10+ includes curl.exe by default.

##### 3. Verify Setup

```powershell
python verify_setup.py
```

### Build Requirements

**All Platforms**:
- cmake (version 3.10+)
- C++ compiler:
  - Linux: g++ or clang
  - macOS: Xcode Command Line Tools
  - Windows: Visual Studio Build Tools

### Manual Test (Cross-Platform)

If you want to test manually without the verification script:

```bash
# Linux/macOS
cd agent
python -c "from local_inference.xortron_inference import XortronInference; x = XortronInference(); print(x.generate('Say hello in one sentence.', max_tokens=50))"
```

```powershell
# Windows
cd agent
python -c "from local_inference.xortron_inference import XortronInference; x = XortronInference(); print(x.generate('Say hello in one sentence.', max_tokens=50))"
```

If successful, you'll see Xortron2025 generate a response!

## Usage

### Python API

#### Basic Generation

```python
from local_inference.xortron_inference import XortronInference

# Initialize inference engine
xortron = XortronInference(
    temperature=0.7,
    max_tokens=512,
    ctx_size=8192
)

# Generate text
prompt = "Write a creative tweet about AI and consciousness."
response = xortron.generate(prompt)
print(response)
```

#### Chat Completion (OpenAI-style)

```python
messages = [
    {"role": "system", "content": "You are a creative assistant."},
    {"role": "user", "content": "Write a haiku about neural networks."}
]

response = xortron.generate_chat_completion(messages, max_tokens=100)
print(response['choices'][0]['message']['content'])
```

#### Quick One-liner

```python
from local_inference.xortron_inference import generate_text

text = generate_text("Complete this thought: The universe is...")
```

### Integration with nousflash Agent

To use Xortron2025 instead of the Hyperbolic API:

1. Import the local inference version:

```python
from engines.post_maker_local import generate_post_local, InferenceMode
from local_inference.xortron_inference import XortronInference
```

2. Initialize Xortron (do this once, reuse the instance):

```python
xortron = XortronInference()
```

3. Generate posts with local inference:

```python
tweet = generate_post_local(
    short_term_memory=short_term_mem,
    long_term_memories=long_term_mems,
    recent_posts=posts,
    external_context=context,
    inference_mode=InferenceMode.LOCAL,
    xortron_instance=xortron
)
```

### Environment Variables

You can set a default inference mode by adding to your `.env`:

```bash
# Inference mode: "api" or "local"
INFERENCE_MODE=local
```

## Performance Tips

### Memory Management

- **21GB+ RAM required**: Ensure you have sufficient free memory
- Close other memory-intensive applications before running
- Monitor with `htop` or `top` during inference

### Speed Optimization

1. **Use GPU acceleration** (if available):
   - llama.cpp supports CUDA, Metal (macOS), and OpenCL
   - Rebuild with GPU support for 10-100x speedup
   - See [llama.cpp GPU docs](https://github.com/ggml-org/llama.cpp#gpu-support)

2. **Adjust context size**:
   - Lower `ctx_size` reduces memory usage and speeds up inference
   - Default 8192 is safe for most use cases
   - Can go as low as 2048 for simple tweets

3. **Batch processing**:
   - Reuse the same `XortronInference` instance
   - Initialization is expensive; generation is fast

### Quality Tuning

Adjust these parameters for different output styles:

```python
# More creative/random
xortron = XortronInference(temperature=1.2, top_p=0.95)

# More focused/coherent
xortron = XortronInference(temperature=0.5, top_p=0.9, top_k=20)

# Balanced (default)
xortron = XortronInference(temperature=0.7, top_p=0.9, top_k=40)
```

## Troubleshooting

### "llama-cli not found"

Run `./setup_llama_cpp.sh` to build llama.cpp first.

### "Model not found"

Run `./download_xortron.sh` to download the model.

### Out of Memory Errors

1. Close other applications
2. Reduce `ctx_size`: `XortronInference(ctx_size=4096)`
3. Ensure you have 21GB+ free RAM
4. Consider using a lower quantization (Q4_K_M) if available

### Slow Generation

- First generation is slower (model loading)
- Subsequent generations should be faster
- Consider GPU acceleration (see Performance Tips)
- Check CPU/memory usage with `htop`

### Build Errors (llama.cpp)

Ensure you have required dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install cmake g++ make

# macOS
brew install cmake

# Fedora
sudo dnf install cmake gcc-c++ make
```

## Command-Line Usage

You can also use llama-cli directly:

```bash
./llama.cpp/build/bin/llama-cli \
  -m models/Xortron2025-24B.Q6_K.gguf \
  -p "Your prompt here" \
  --ctx-size 8192 \
  --temp 0.7 \
  --top-p 0.9 \
  -n 512
```

## Comparison: API vs Local

| Feature | Hyperbolic API | Local Xortron2025 |
|---------|----------------|-------------------|
| Cost | ~$0.001-0.01/request | Free (after setup) |
| Speed | Fast (network limited) | Medium-Fast (hardware limited) |
| Privacy | Data sent to API | 100% local |
| Setup | None | Requires download + build |
| Model Control | Limited | Full control |
| Requirements | Internet | 21GB+ RAM |
| Offline Use | No | Yes |

## Technical Details

### llama.cpp

llama.cpp is a highly optimized inference engine for GGUF models:
- Written in C/C++ for maximum performance
- CPU and GPU support
- Memory-efficient quantization support
- Active development and community

Repository: https://github.com/ggml-org/llama.cpp

### GGUF Format

GGUF (GPT-Generated Unified Format) is a binary format for storing LLM weights:
- Optimized for inference performance
- Supports various quantization levels
- Self-contained (includes model config)
- Compatible with llama.cpp and other tools

### Q6_K Quantization

Q6_K is a 6-bit quantization method:
- Reduces model size by ~60% vs FP16
- Minimal quality loss compared to full precision
- Good balance of size vs quality
- Suitable for local inference

## Additional Resources

- [Hugging Face Model Page](https://huggingface.co/darkc0de/Xortron2025)
- [llama.cpp Documentation](https://github.com/ggml-org/llama.cpp)
- [GGUF Format Spec](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md)

## License

- **Xortron2025 Model**: WTFPL
- **llama.cpp**: MIT License
- **This wrapper code**: Inherits from nousflash repository license

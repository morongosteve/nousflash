#!/usr/bin/env python3
"""
Verification script for Xortron2025 local inference setup

This script checks that all components are properly installed and configured:
- llama.cpp is built
- Xortron2025 model is downloaded
- Python can interface with the model
- Basic inference works
"""

import sys
import os
from pathlib import Path
import subprocess

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")

def check_llama_cpp():
    """Check if llama.cpp is built."""
    print_header("1. Checking llama.cpp")

    base_dir = Path(__file__).parent
    llama_cli_path = base_dir / "llama.cpp" / "build" / "bin" / "llama-cli"
    llama_cli_path_windows = base_dir / "llama.cpp" / "build" / "bin" / "Release" / "llama-cli.exe"

    # Check Linux/macOS path
    if llama_cli_path.exists():
        print_success(f"llama-cli found at: {llama_cli_path}")
        return True, str(llama_cli_path)

    # Check Windows path
    if llama_cli_path_windows.exists():
        print_success(f"llama-cli found at: {llama_cli_path_windows}")
        return True, str(llama_cli_path_windows)

    print_error("llama-cli not found")
    print_warning("Run setup script:")
    print("  Linux/macOS: ./setup_llama_cpp.sh")
    print("  Windows:     .\\setup_llama_cpp.ps1")
    return False, None

def check_model():
    """Check if Xortron2025 model is downloaded."""
    print_header("2. Checking Xortron2025 Model")

    base_dir = Path(__file__).parent
    model_path = base_dir / "models" / "Xortron2025-24B.Q6_K.gguf"

    if model_path.exists():
        # Get file size
        size_bytes = model_path.stat().st_size
        size_gb = size_bytes / (1024**3)
        print_success(f"Model found at: {model_path}")
        print(f"  Size: {size_gb:.2f} GB")

        # Verify size is reasonable (should be ~19.3 GB)
        if 18.0 < size_gb < 21.0:
            print_success("Model size looks correct (~19.3 GB expected)")
        else:
            print_warning(f"Model size is {size_gb:.2f} GB (expected ~19.3 GB)")
            print_warning("The download may be incomplete or corrupted")
            return False, None

        return True, str(model_path)

    print_error("Model not found")
    print_warning("Run download script:")
    print("  curl method:    ./download_xortron.sh")
    print("  git-lfs method: ./download_xortron_lfs.sh")
    print("  Windows:        .\\download_xortron.ps1")
    return False, None

def check_python_imports():
    """Check if Python can import the xortron_inference module."""
    print_header("3. Checking Python Integration")

    try:
        # Add parent directory to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from local_inference.xortron_inference import XortronInference
        print_success("Successfully imported XortronInference class")
        return True
    except ImportError as e:
        print_error(f"Failed to import: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def check_basic_inference(llama_cli_path, model_path):
    """Test basic inference with a simple prompt."""
    print_header("4. Testing Basic Inference")

    print("Running a quick test generation...")
    print("Prompt: 'Say hello in one sentence.'")
    print(f"{YELLOW}This may take 30-60 seconds...{RESET}\n")

    try:
        # Build command
        cmd = [
            llama_cli_path,
            "-m", model_path,
            "-p", "Say hello in one sentence.",
            "--ctx-size", "512",
            "--temp", "0.7",
            "-n", "50",
            "--log-disable"
        ]

        # Run inference with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                print_success("Inference successful!")
                print(f"\n{BOLD}Generated output:{RESET}")
                print(f"{BLUE}{output[:500]}{RESET}\n")
                return True
            else:
                print_error("Inference completed but produced no output")
                return False
        else:
            print_error(f"Inference failed with return code {result.returncode}")
            if result.stderr:
                print(f"\nError: {result.stderr[:500]}")
            return False

    except subprocess.TimeoutExpired:
        print_error("Inference timed out after 2 minutes")
        print_warning("This may indicate:")
        print("  - Insufficient RAM (need 21GB+)")
        print("  - CPU too slow for reasonable inference")
        return False
    except Exception as e:
        print_error(f"Error running inference: {e}")
        return False

def check_system_requirements():
    """Check system requirements."""
    print_header("5. Checking System Requirements")

    # Check available RAM
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
            for line in meminfo.split('\n'):
                if 'MemAvailable' in line:
                    # Extract available memory in KB
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / (1024**2)
                    print(f"Available RAM: {mem_gb:.2f} GB")

                    if mem_gb >= 21:
                        print_success("Sufficient RAM available (21GB+ required)")
                    else:
                        print_warning(f"Low available RAM: {mem_gb:.2f} GB (21GB+ recommended)")
                        print_warning("Close other applications before running inference")
                    break
    except Exception as e:
        print_warning(f"Could not check RAM: {e}")
        print("  Ensure you have 21GB+ available RAM")

def main():
    """Run all verification checks."""
    print(f"\n{BOLD}Xortron2025 Setup Verification{RESET}")
    print(f"{'='*60}\n")

    # Track overall status
    all_checks_passed = True

    # Run checks
    llama_ok, llama_path = check_llama_cpp()
    all_checks_passed = all_checks_passed and llama_ok

    model_ok, model_path = check_model()
    all_checks_passed = all_checks_passed and model_ok

    python_ok = check_python_imports()
    all_checks_passed = all_checks_passed and python_ok

    # Only run inference test if basic checks pass
    inference_ok = False
    if llama_ok and model_ok:
        inference_ok = check_basic_inference(llama_path, model_path)
        all_checks_passed = all_checks_passed and inference_ok
    else:
        print_header("4. Testing Basic Inference")
        print_warning("Skipping inference test (prerequisites not met)")

    # Check system requirements (informational, doesn't affect overall status)
    check_system_requirements()

    # Final summary
    print_header("Verification Summary")

    if all_checks_passed:
        print_success("All checks passed! ✓")
        print(f"\n{GREEN}Your Xortron2025 setup is ready to use!{RESET}")
        print(f"\nNext steps:")
        print(f"  - See {BLUE}README.md{RESET} for usage examples")
        print(f"  - Run {BLUE}python example_usage.py{RESET} for demonstrations")
        print(f"  - Integrate with nousflash agent using {BLUE}post_maker_local.py{RESET}")
        return 0
    else:
        print_error("Some checks failed")
        print(f"\n{RED}Please fix the issues above and run this script again.{RESET}")
        print(f"\nFor help, see: {BLUE}README.md{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

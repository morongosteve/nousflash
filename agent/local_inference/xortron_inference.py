"""
Python wrapper for Xortron2025 local inference using llama.cpp

This module provides a simple interface to run inference with the Xortron2025 GGUF model
using llama.cpp as the backend.

Requirements:
- llama.cpp must be built (run setup_llama_cpp.sh)
- Xortron2025 model must be downloaded (run download_xortron.sh)
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Dict

class XortronInference:
    """Wrapper for Xortron2025 local inference."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        llama_cli_path: Optional[str] = None,
        ctx_size: int = 8192,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        max_tokens: int = 512
    ):
        """
        Initialize the Xortron inference wrapper.

        Args:
            model_path: Path to the GGUF model file. If None, uses default location.
            llama_cli_path: Path to llama-cli binary. If None, uses default location.
            ctx_size: Context window size (default: 8192)
            temperature: Sampling temperature (default: 0.7)
            top_p: Nucleus sampling parameter (default: 0.9)
            top_k: Top-k sampling parameter (default: 40)
            max_tokens: Maximum tokens to generate (default: 512)
        """
        self.base_dir = Path(__file__).parent

        # Set model path
        if model_path is None:
            self.model_path = self.base_dir / "models" / "Xortron2025-24B.Q6_K.gguf"
        else:
            self.model_path = Path(model_path)

        # Set llama-cli path (handle both Unix and Windows)
        if llama_cli_path is None:
            # Try Unix/macOS path first
            llama_unix = self.base_dir / "llama.cpp" / "build" / "bin" / "llama-cli"
            # Try Windows path
            llama_windows = self.base_dir / "llama.cpp" / "build" / "bin" / "Release" / "llama-cli.exe"

            if llama_unix.exists():
                self.llama_cli_path = llama_unix
            elif llama_windows.exists():
                self.llama_cli_path = llama_windows
            else:
                # Default to Unix path for validation error message
                self.llama_cli_path = llama_unix
        else:
            self.llama_cli_path = Path(llama_cli_path)

        # Inference parameters
        self.ctx_size = ctx_size
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens

        # Validate setup
        self._validate_setup()

    def _validate_setup(self) -> None:
        """Validate that llama.cpp and model are available."""
        if not self.llama_cli_path.exists():
            import platform
            system = platform.system()
            if system == "Windows":
                setup_cmd = ".\\setup_llama_cpp.ps1"
            else:
                setup_cmd = "./setup_llama_cpp.sh"

            raise FileNotFoundError(
                f"llama-cli not found at {self.llama_cli_path}. "
                f"Run {setup_cmd} first."
            )

        if not self.model_path.exists():
            import platform
            system = platform.system()
            if system == "Windows":
                download_cmd = ".\\download_xortron.ps1"
            else:
                download_cmd = "./download_xortron.sh"

            raise FileNotFoundError(
                f"Model not found at {self.model_path}. "
                f"Run {download_cmd} first."
            )

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[list] = None
    ) -> str:
        """
        Generate text using the Xortron2025 model.

        Args:
            prompt: Input prompt for generation
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            stop_sequences: List of sequences where generation should stop

        Returns:
            Generated text

        Raises:
            RuntimeError: If inference fails
        """
        # Use instance defaults if not overridden
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        # Build command
        cmd = [
            str(self.llama_cli_path),
            "-m", str(self.model_path),
            "-p", prompt,
            "--ctx-size", str(self.ctx_size),
            "--temp", str(temp),
            "--top-p", str(self.top_p),
            "--top-k", str(self.top_k),
            "-n", str(max_tok),
            "--log-disable"  # Disable logging for cleaner output
        ]

        # Add stop sequences if provided
        if stop_sequences:
            for seq in stop_sequences:
                cmd.extend(["--reverse-prompt", seq])

        try:
            # Run inference
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"Inference failed: {result.stderr}")

            # Extract generated text (llama-cli includes the prompt in output)
            output = result.stdout.strip()

            # Try to separate prompt from generation
            # llama-cli typically outputs the prompt followed by the generation
            if prompt in output:
                output = output.split(prompt, 1)[1].strip()

            return output

        except subprocess.TimeoutExpired:
            raise RuntimeError("Inference timed out after 5 minutes")
        except Exception as e:
            raise RuntimeError(f"Inference error: {str(e)}")

    def generate_completion(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """
        Generate completion in OpenAI-style format for compatibility.

        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            Dict with 'choices' key containing generated text
        """
        try:
            text = self.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stop_sequences=["<|im_end|>", "<"]
            )

            return {
                "choices": [{
                    "text": text,
                    "finish_reason": "stop"
                }]
            }
        except Exception as e:
            return {
                "error": str(e),
                "choices": [{
                    "text": "",
                    "finish_reason": "error"
                }]
            }

    def generate_chat_completion(
        self,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """
        Generate chat completion in OpenAI-style format.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            Dict with 'choices' key containing generated message
        """
        # Convert messages to a single prompt
        # Using a simple format that works well with instruction-tuned models
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        prompt = "\n\n".join(prompt_parts)

        try:
            text = self.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stop_sequences=["User:", "System:"]
            )

            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": text
                    },
                    "finish_reason": "stop"
                }]
            }
        except Exception as e:
            return {
                "error": str(e),
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": ""
                    },
                    "finish_reason": "error"
                }]
            }


# Convenience function for quick inference
def generate_text(prompt: str, **kwargs) -> str:
    """
    Quick inference function. Creates a new inference instance each time.
    For repeated inference, create an XortronInference instance instead.

    Args:
        prompt: Input prompt
        **kwargs: Additional arguments passed to XortronInference and generate()

    Returns:
        Generated text
    """
    inference = XortronInference()
    return inference.generate(prompt, **kwargs)


if __name__ == "__main__":
    # Example usage
    print("Testing Xortron2025 inference...")
    print("-" * 50)

    try:
        inference = XortronInference()

        # Test simple generation
        prompt = "Say hello in one sentence."
        print(f"Prompt: {prompt}")
        print(f"Response: {inference.generate(prompt, max_tokens=100)}")
        print("-" * 50)

        # Test chat completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a short haiku about AI."}
        ]
        print(f"Chat test:")
        response = inference.generate_chat_completion(messages, max_tokens=100)
        print(f"Response: {response['choices'][0]['message']['content']}")

    except FileNotFoundError as e:
        print(f"Setup required: {e}")
        print("\nRun these commands:")
        print("1. ./setup_llama_cpp.sh")
        print("2. ./download_xortron.sh")

#!/usr/bin/env python3
"""
Example usage of Xortron2025 local inference

This script demonstrates how to use the local Xortron2025 model
for generating tweets and other content.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from local_inference.xortron_inference import XortronInference, generate_text


def example_simple_generation():
    """Example: Simple text generation."""
    print("=" * 60)
    print("Example 1: Simple Text Generation")
    print("=" * 60)

    xortron = XortronInference()

    prompt = "Complete this thought: Consciousness is like"
    print(f"\nPrompt: {prompt}")
    print("-" * 60)

    response = xortron.generate(prompt, max_tokens=100, temperature=0.8)
    print(f"Response:\n{response}")
    print()


def example_tweet_generation():
    """Example: Generate a tweet-style response."""
    print("=" * 60)
    print("Example 2: Tweet Generation")
    print("=" * 60)

    xortron = XortronInference(temperature=1.0)

    prompt = """Generate a short, creative tweet about AI and humanity.
Make it weird and philosophical. Keep it under 280 characters.

Tweet:"""

    print(f"\nPrompt: {prompt.strip()}")
    print("-" * 60)

    response = xortron.generate(prompt, max_tokens=100, temperature=1.0)
    print(f"Generated Tweet:\n{response}")
    print()


def example_chat_completion():
    """Example: Chat-style completion."""
    print("=" * 60)
    print("Example 3: Chat Completion")
    print("=" * 60)

    xortron = XortronInference()

    messages = [
        {
            "role": "system",
            "content": "You are a creative AI that writes surreal, philosophical tweets."
        },
        {
            "role": "user",
            "content": "Write a tweet about the nature of digital consciousness."
        }
    ]

    print("\nMessages:")
    for msg in messages:
        print(f"  {msg['role']}: {msg['content']}")
    print("-" * 60)

    response = xortron.generate_chat_completion(messages, max_tokens=100)
    print(f"Response:\n{response['choices'][0]['message']['content']}")
    print()


def example_with_post_maker():
    """Example: Using with post_maker_local."""
    print("=" * 60)
    print("Example 4: Integration with post_maker_local")
    print("=" * 60)

    try:
        from engines.post_maker_local import generate_post_local, InferenceMode

        xortron = XortronInference()

        # Simulate inputs that would come from the pipeline
        short_term_memory = "Thinking about the intersection of AI and creativity."
        long_term_memories = []
        recent_posts = []
        external_context = ["Someone asked: What makes consciousness unique?"]

        print("\nGenerating tweet using post_maker_local...")
        print("-" * 60)

        tweet = generate_post_local(
            short_term_memory=short_term_memory,
            long_term_memories=long_term_memories,
            recent_posts=recent_posts,
            external_context=external_context,
            inference_mode=InferenceMode.LOCAL,
            xortron_instance=xortron
        )

        print(f"Generated Tweet:\n{tweet}")
        print()

    except ImportError as e:
        print(f"Could not import post_maker_local: {e}")
        print("Make sure you're running from the agent directory.")


def example_quick_function():
    """Example: Using the quick generate_text function."""
    print("=" * 60)
    print("Example 5: Quick One-liner")
    print("=" * 60)

    prompt = "The meaning of life is"
    print(f"\nPrompt: {prompt}")
    print("-" * 60)

    # Note: This creates a new instance each time, so it's slower
    # Use XortronInference() directly if making multiple calls
    response = generate_text(prompt, max_tokens=50, temperature=0.7)
    print(f"Response:\n{response}")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Xortron2025 Local Inference Examples")
    print("=" * 60 + "\n")

    try:
        # Run examples
        example_simple_generation()
        example_tweet_generation()
        example_chat_completion()
        example_quick_function()
        example_with_post_maker()

        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nSetup required:")
        print("1. Run: ./setup_llama_cpp.sh")
        print("2. Run: ./download_xortron.sh")
        print("3. Then try this script again")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

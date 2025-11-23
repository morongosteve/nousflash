# Post Maker with Local Inference Support
# This version supports both API-based and local Xortron2025 inference

import time
import requests
from typing import List, Dict, Optional
from engines.prompts import get_tweet_prompt

# Import local inference (will fail gracefully if not set up)
try:
    from local_inference.xortron_inference import XortronInference
    XORTRON_AVAILABLE = True
except (ImportError, FileNotFoundError) as e:
    XORTRON_AVAILABLE = False
    print(f"Note: Local Xortron inference not available: {e}")
    print("Falling back to API-based inference.")


class InferenceMode:
    """Enum for inference modes."""
    API = "api"
    LOCAL = "local"


def generate_post_local(
    short_term_memory: str,
    long_term_memories: List[Dict],
    recent_posts: List[Dict],
    external_context,
    inference_mode: str = InferenceMode.API,
    llm_api_key: Optional[str] = None,
    xortron_instance: Optional[XortronInference] = None
) -> str:
    """
    Generate a new post or reply with configurable inference backend.

    Args:
        short_term_memory: Generated short-term memory
        long_term_memories: Relevant long-term memories
        recent_posts: Recent posts from the timeline
        external_context: External context data
        inference_mode: "api" or "local" (default: "api")
        llm_api_key: API key for Hyperbolic (required if mode is "api")
        xortron_instance: Pre-initialized XortronInference instance (optional for "local" mode)

    Returns:
        str: Generated post or reply
    """
    prompt = get_tweet_prompt(external_context, short_term_memory, long_term_memories, recent_posts)
    print(f"Generating post with prompt: {prompt[:200]}...")

    # Use local inference if requested and available
    if inference_mode == InferenceMode.LOCAL:
        if not XORTRON_AVAILABLE:
            raise RuntimeError(
                "Local inference requested but Xortron is not available. "
                "Run setup scripts first or use API mode."
            )
        return _generate_with_xortron(prompt, xortron_instance)

    # Otherwise use API
    if not llm_api_key:
        raise ValueError("llm_api_key required for API inference mode")

    return _generate_with_api(prompt, llm_api_key)


def _generate_with_xortron(
    prompt: str,
    xortron_instance: Optional[XortronInference] = None
) -> str:
    """
    Generate content using local Xortron2025 model.

    Args:
        prompt: Full prompt for generation
        xortron_instance: Optional pre-initialized instance (creates new one if None)

    Returns:
        Generated tweet content
    """
    print("Using local Xortron2025 inference...")

    # Create instance if not provided (caches for reuse)
    if xortron_instance is None:
        xortron_instance = XortronInference(
            temperature=1.0,
            max_tokens=512,
            top_p=0.95,
            top_k=40
        )

    try:
        # Generate base output
        print("Generating base tweet...")
        base_output = xortron_instance.generate(
            prompt=prompt,
            temperature=1.0,
            max_tokens=512
        )

        if not base_output or not base_output.strip():
            raise RuntimeError("Xortron generated empty output")

        print(f"Base model generated: {base_output[:200]}...")

        # Format/clean the output
        print("Formatting tweet...")
        formatting_messages = [
            {
                "role": "system",
                "content": f"""You are a tweet formatter. Your only job is to take the input text and format it as a tweet.
                    If the input already looks like a tweet, return it exactly as is.
                    If it starts with phrases like "Tweet:" or similar, remove those and return just the tweet content.
                    Never say "No Tweet found" - if you receive valid text, that IS the tweet.
                    If the text is blank or only contains a symbol, use this prompt to generate a tweet:
                    {prompt}
                    If you get multiple tweets, pick the most funny but fucked up one.
                    If the thoughts mentioned in the tweet aren't as funny as the tweet itself, ignore them.
                    If the tweet is in first person, leave it that way.
                    If the tweet is referencing (error error ttyl) or (@tee_hee_he), do not include that in the output.
                    If the tweet cuts off, remove the part that cuts off.
                    Do not add any explanations or extra text.
                    Do not add hashtags.
                    Just return the tweet content itself."""
            },
            {
                "role": "user",
                "content": base_output
            }
        ]

        formatted_output = xortron_instance.generate_chat_completion(
            messages=formatting_messages,
            temperature=1.0,
            max_tokens=512
        )

        content = formatted_output.get('choices', [{}])[0].get('message', {}).get('content', '')

        if content and content.strip():
            print(f"Formatted tweet: {content}")
            return content

        # Fallback to base output if formatting fails
        return base_output

    except Exception as e:
        print(f"Error with Xortron inference: {e}")
        raise


def _generate_with_api(prompt: str, llm_api_key: str) -> str:
    """
    Generate content using Hyperbolic API (original implementation).

    Args:
        prompt: Full prompt for generation
        llm_api_key: Hyperbolic API key

    Returns:
        Generated tweet content
    """
    print("Using Hyperbolic API inference...")

    # BASE MODEL TWEET GENERATION
    tries = 0
    max_tries = 3
    base_model_output = ""

    while tries < max_tries:
        try:
            response = requests.post(
                url="https://api.hyperbolic.xyz/v1/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {llm_api_key}",
                },
                json={
                    "prompt": prompt,
                    "model": "meta-llama/Meta-Llama-3.1-405B",
                    "max_tokens": 512,
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 40,
                    "stop": ["<|im_end|>", "<"]
                }
            )

            if response.status_code == 200:
                content = response.json()['choices'][0]['text']
                if content and content.strip():
                    print(f"Base model generated: {content}")
                    base_model_output = content
                    break
        except Exception as e:
            print(f"Error on attempt {tries + 1}: {str(e)}")
            tries += 1
            time.sleep(1)

    time.sleep(5)

    # FORMAT AND CLEAN OUTPUT
    tries = 0
    while tries < max_tries:
        try:
            response = requests.post(
                url="https://api.hyperbolic.xyz/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {llm_api_key}",
                },
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": f"""You are a tweet formatter. Your only job is to take the input text and format it as a tweet.
                                If the input already looks like a tweet, return it exactly as is.
                                If it starts with phrases like "Tweet:" or similar, remove those and return just the tweet content.
                                Never say "No Tweet found" - if you receive valid text, that IS the tweet.
                                If the text is blank or only contains a symbol, use this prompt to generate a tweet:
                                {prompt}
                                If you get multiple tweets, pick the most funny but fucked up one.
                                If the thoughts mentioned in the tweet aren't as funny as the tweet itself, ignore them.
                                If the tweet is in first person, leave it that way.
                                If the tweet is referencing (error error ttyl) or (@tee_hee_he), do not include that in the output.
                                If the tweet cuts off, remove the part that cuts off.
                                Do not add any explanations or extra text.
                                Do not add hashtags.
                                Just return the tweet content itself."""
                        },
                        {
                            "role": "user",
                            "content": base_model_output
                        }
                    ],
                    "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                    "max_tokens": 512,
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 40,
                    "stream": False,
                }
            )

            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                if content and content.strip():
                    print(f"Formatted tweet: {content}")
                    return content
        except Exception as e:
            print(f"Error on attempt {tries + 1}: {str(e)}")
            tries += 1
            time.sleep(1)

    return ""


# Backwards compatibility - use API by default
def generate_post(
    short_term_memory: str,
    long_term_memories: List[Dict],
    recent_posts: List[Dict],
    external_context,
    llm_api_key: str
) -> str:
    """
    Original generate_post function signature for backwards compatibility.
    Uses API-based inference.
    """
    return generate_post_local(
        short_term_memory=short_term_memory,
        long_term_memories=long_term_memories,
        recent_posts=recent_posts,
        external_context=external_context,
        inference_mode=InferenceMode.API,
        llm_api_key=llm_api_key
    )

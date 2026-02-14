# Short Term Memory Engine
# Objective: Ephemeral memory. This would simulate scrolling through 4chan or twitter,
# looking at the most recent posts in their timeline and including that in the post making
# context to make a decision on whether to reply or not.

import time
from typing import List, Dict
import requests
from engines.prompts import get_short_term_memory_prompt


def generate_short_term_memory(
    posts: List[Dict],
    external_context: List[str],
    llm_api_key: str,
    inference_mode: str = "api",
    anthropic_api_key: str = None,
) -> str:
    """
    Generate short-term memory based on recent posts and external context.

    Args:
        posts: List of recent posts
        external_context: List of external context items
        llm_api_key: Hyperbolic API key (used when inference_mode is "api")
        inference_mode: "api" or "anthropic" (local mode falls back to api)
        anthropic_api_key: Anthropic API key (used when inference_mode is "anthropic")

    Returns:
        Generated short-term memory string, or empty string on total failure
    """
    prompt = get_short_term_memory_prompt(posts, external_context)
    max_tries = 3

    for attempt in range(1, max_tries + 1):
        try:
            content = _call_memory(prompt, llm_api_key, inference_mode, anthropic_api_key)
            if content and content.strip():
                print(f"Short-term memory generated: {content}")
                return content
            print(f"Empty short-term memory response on attempt {attempt}/{max_tries}")
        except Exception as e:
            print(f"Short-term memory attempt {attempt}/{max_tries} failed: {e}")
        time.sleep(5)

    return ""


def _call_memory(
    prompt: str,
    llm_api_key: str,
    inference_mode: str,
    anthropic_api_key: str,
) -> str:
    """Route to the appropriate LLM backend and return raw text."""
    if inference_mode == "anthropic":
        try:
            import anthropic as anthropic_sdk
        except ImportError:
            raise RuntimeError("anthropic package not installed; run: pip install anthropic")

        client = anthropic_sdk.Anthropic(api_key=anthropic_api_key)
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Fast model for internal memory pass
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": prompt + "\nRespond only with your internal monologue based on the given context.",
                }
            ],
        )
        return response.content[0].text.strip()

    # Default: Hyperbolic
    resp = requests.post(
        url="https://api.hyperbolic.xyz/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm_api_key}",
        },
        json={
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Respond only with your internal monologue based on the given context."},
            ],
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "max_tokens": 512,
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "stream": False,
        },
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Hyperbolic short-term memory HTTP {resp.status_code}: {resp.text}")
    return resp.json()["choices"][0]["message"]["content"]

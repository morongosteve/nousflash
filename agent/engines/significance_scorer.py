import re
import time
import requests
from engines.prompts import get_significance_score_prompt, get_reply_worthiness_score_prompt


def _call_scorer(prompt: str, llm_api_key: str, inference_mode: str, anthropic_api_key: str) -> str:
    """
    Call an LLM to get a score, routing to Anthropic or Hyperbolic based on inference_mode.
    Returns the raw text content from the response, or raises on failure.
    """
    if inference_mode == "anthropic":
        try:
            import anthropic as anthropic_sdk
        except ImportError:
            raise RuntimeError("anthropic package not installed; run: pip install anthropic")

        client = anthropic_sdk.Anthropic(api_key=anthropic_api_key, timeout=60.0)
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Fast/cheap model for scoring
            max_tokens=16,
            messages=[
                {"role": "user", "content": prompt + "\nRespond only with the numeric score."}
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
                {"role": "user", "content": "Respond only with the score you would give for the given memory."},
            ],
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Hyperbolic scorer HTTP {resp.status_code}: {resp.text}")
    return resp.json()["choices"][0]["message"]["content"].strip()


def _parse_score(raw: str) -> int:
    """Extract an integer 1–10 from a model response."""
    numbers = re.findall(r"\d+", raw)
    if not numbers:
        raise ValueError(f"No numeric score in response: {raw!r}")
    return max(1, min(10, int(numbers[0])))


def _score(
    prompt: str,
    llm_api_key: str,
    inference_mode: str = "api",
    anthropic_api_key: str = None,
    max_tries: int = 5,
) -> int:
    """Shared retry loop for both scoring functions."""
    for attempt in range(1, max_tries + 1):
        try:
            raw = _call_scorer(prompt, llm_api_key, inference_mode, anthropic_api_key)
            if not raw:
                print(f"Empty scorer response on attempt {attempt}")
                continue
            score = _parse_score(raw)
            print(f"Score: {score} (raw: {raw!r})")
            return score
        except Exception as e:
            print(f"Scorer attempt {attempt}/{max_tries} failed: {e}")
            time.sleep(1)
    return 5  # neutral fallback so the pipeline continues


def score_significance(
    memory: str,
    llm_api_key: str,
    inference_mode: str = "api",
    anthropic_api_key: str = None,
) -> int:
    prompt = get_significance_score_prompt(memory)
    return _score(prompt, llm_api_key, inference_mode, anthropic_api_key)


def score_reply_significance(
    tweet: str,
    llm_api_key: str,
    inference_mode: str = "api",
    anthropic_api_key: str = None,
) -> int:
    prompt = get_reply_worthiness_score_prompt(tweet)
    return _score(prompt, llm_api_key, inference_mode, anthropic_api_key)

"""
LLM service — thin wrapper around the OpenAI-compatible LM Studio API.

All agent modules call this service rather than making raw HTTP requests so
we have a single place to swap models, add retries, or switch providers.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

log = logging.getLogger(__name__)

# Re-usable client (connection pool) — created lazily
_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.LLM_BASE_URL,
            timeout=httpx.Timeout(settings.LLM_TIMEOUT, connect=30.0),
        )
    return _client


async def close() -> None:
    """Shutdown the underlying HTTP client (call during app shutdown)."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


# -------------------------------------------------------------------------
# Core chat completion
# -------------------------------------------------------------------------

async def chat(
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    model: str | None = None,
    response_format: Dict[str, Any] | None = None,
) -> str:
    """Send a chat completion request and return the assistant message text.

    Parameters
    ----------
    messages : list[dict]
        Standard OpenAI-style messages: [{"role": "system", "content": "..."}]
    temperature : float
        Sampling temperature.
    max_tokens : int
        Maximum tokens to generate.
    model : str | None
        Override the model name. Defaults to ``settings.LLM_MODEL``.
    response_format : dict | None
        Optional JSON-mode hint, e.g. ``{"type": "json_object"}``.

    Returns
    -------
    str  — The raw assistant reply text.
    """
    client = _get_client()
    payload: Dict[str, Any] = {
        "model": model or settings.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    log.debug("LLM request → %s tokens max, temp=%.2f", max_tokens, temperature)

    resp = await client.post("/chat/completions", json=payload)
    resp.raise_for_status()
    data = resp.json()

    content = data["choices"][0]["message"]["content"]
    log.debug("LLM response ← %d chars", len(content))
    return content


async def chat_json(
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    model: str | None = None,
) -> Any:
    """Like :func:`chat` but requests JSON mode and parses the response.

    Falls back to extracting JSON from markdown code-fences if the model
    doesn't honour ``response_format``.
    """
    raw = await chat(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model,
        response_format={"type": "json_object"},
    )
    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Fallback: extract from ```json ... ``` fences
    if "```" in raw:
        for block in raw.split("```"):
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue
    # Last resort
    raise ValueError(f"LLM did not return valid JSON:\n{raw[:500]}")

"""Groq LLM client — the single 'called' model in Feature 4.

Groq exposes an OpenAI-compatible endpoint. This client is deliberately tiny and
DEFENSIVE: it never raises on a missing key, a timeout, or a bad response — it
returns None and lets the caller fall back to a deterministic template. That is
what keeps the demo alive with no key / no network (RULE 3).

Pattern mirrors the proven client in sviam-interview-lab (Groq-first, lazy key,
timeout -> fallback).
"""
from __future__ import annotations

import requests

from .config import GROQ_URL, compose_model, fast_model, groq_api_key


def available() -> bool:
    """True if a Groq key is configured (does not guarantee the network works)."""
    return bool(groq_api_key())


def chat(
    messages: list[dict],
    *,
    fast: bool = False,
    model: str | None = None,
    temperature: float = 0.4,
    max_tokens: int = 700,
    timeout: float = 20.0,
    json_mode: bool = False,
) -> str | None:
    """Call Groq chat/completions. Return the assistant text, or None on any failure.

    `fast=True` selects the small/quick model (good for translation + intent).
    """
    key = groq_api_key()
    if not key:
        return None

    mdl = model or (fast_model() if fast else compose_model())
    body: dict = {
        "model": mdl,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        # Provider-enforced valid JSON — the prompt must mention "JSON".
        body["response_format"] = {"type": "json_object"}

    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=timeout,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        if content and str(content).strip():
            return str(content).strip()
        return None
    except Exception:
        # Any error (no network, timeout, rate limit, bad key) -> caller falls back.
        return None

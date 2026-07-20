"""Server-side text-to-speech — a warm, human voice for the citizen bot.

Tries a real neural TTS (ElevenLabs multilingual → Deepgram Aura) and returns MP3
bytes. If no key is set or a call fails, returns None so the browser falls back to
its built-in speech synthesis. Same defensive contract as the Groq client: it never
raises, so the demo always talks.

ElevenLabs is primary because its multilingual model speaks BOTH English and Hindi;
Deepgram Aura (English-only) is the fallback. Results are cached in-memory to save
free-tier characters and to make repeat plays instant.
"""
from __future__ import annotations

import hashlib
import os
from collections import OrderedDict

import requests

_CACHE: "OrderedDict[str, tuple[bytes, str, str]]" = OrderedDict()
_CACHE_MAX = 128


def available() -> bool:
    return bool(os.getenv("ELEVENLABS_API_KEY", "").strip()
               or os.getenv("DEEPGRAM_API_KEY", "").strip())


def _elevenlabs(text: str, lang: str):
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not key:
        return None
    voice = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # "Sarah" (premade)
    try:
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
            f"?output_format=mp3_44100_128",
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={"text": text, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.4, "similarity_boost": 0.75}},
            timeout=25,
        )
        if r.ok and "audio" in r.headers.get("content-type", ""):
            return r.content, "audio/mpeg", "elevenlabs"
    except Exception:
        pass
    return None


def _deepgram(text: str, lang: str):
    key = os.getenv("DEEPGRAM_API_KEY", "").strip()
    if not key or lang != "en":          # Aura voices are English-only
        return None
    model = os.getenv("DEEPGRAM_TTS_MODEL", "aura-2-athena-en")
    try:
        r = requests.post(
            f"https://api.deepgram.com/v1/speak?model={model}&encoding=mp3",
            headers={"Authorization": f"Token {key}", "Content-Type": "application/json"},
            json={"text": text}, timeout=25,
        )
        if r.ok and "audio" in r.headers.get("content-type", ""):
            return r.content, "audio/mpeg", "deepgram"
    except Exception:
        pass
    return None


def synthesize(text: str, lang: str = "en"):
    """Return (audio_bytes, mime, engine) or None (→ browser fallback)."""
    text = (text or "").strip()[:800]
    if not text:
        return None
    ckey = hashlib.sha1(f"{lang}:{text}".encode()).hexdigest()
    if ckey in _CACHE:
        _CACHE.move_to_end(ckey)
        return _CACHE[ckey]

    out = _elevenlabs(text, lang) or _deepgram(text, lang)
    if out:
        _CACHE[ckey] = out
        if len(_CACHE) > _CACHE_MAX:
            _CACHE.popitem(last=False)
    return out

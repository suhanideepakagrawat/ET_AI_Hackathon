"""Server-side text-to-speech — a warm, human voice for the citizen bot.

Providers: ElevenLabs multilingual (EN+HI) and Deepgram Aura (EN only). Both are
optional; when neither serves a request the caller returns 204 and the browser
falls back to its built-in speech. Same defensive contract as the Groq client:
nothing here ever raises.

Latency design (the reason this module looks the way it does):
  - **Smart order.** For English, Deepgram goes FIRST (fast, funded). ElevenLabs
    leads only for languages Deepgram can't speak (Hindi). The old fixed order
    burned a failing ElevenLabs round-trip on every English call.
  - **Failure cooldown.** A provider that errors (quota, auth, timeout) is skipped
    for 30 minutes instead of being retried on every request.
  - **Streaming.** `open_stream()` yields MP3 chunks as the provider produces
    them, so the browser starts playback on the first bytes instead of waiting
    for the full file. Completed streams are cached in-memory; repeat plays are
    served whole and instantly via `get_cached()`.
"""
from __future__ import annotations

import hashlib
import os
import time
from collections import OrderedDict

import requests

_CACHE: "OrderedDict[str, tuple[bytes, str, str]]" = OrderedDict()
_CACHE_MAX = 128

# provider name -> unix time until which it is skipped (set on any failure).
_COOLDOWN: dict[str, float] = {}
_COOLDOWN_S = 30 * 60

_CHUNK = 8192


def available() -> bool:
    return bool(os.getenv("ELEVENLABS_API_KEY", "").strip()
               or os.getenv("DEEPGRAM_API_KEY", "").strip())


def _down(name: str) -> bool:
    return time.time() < _COOLDOWN.get(name, 0.0)


def _mark_down(name: str) -> None:
    _COOLDOWN[name] = time.time() + _COOLDOWN_S


def _open_elevenlabs(text: str, lang: str):
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not key or _down("elevenlabs"):
        return None
    voice = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # "Sarah" (premade)
    try:
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/stream"
            f"?output_format=mp3_44100_128",
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={"text": text, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.4, "similarity_boost": 0.75}},
            timeout=(5, 20), stream=True,
        )
        if r.ok and "audio" in r.headers.get("content-type", ""):
            return r, "audio/mpeg", "elevenlabs"
        r.close()
        _mark_down("elevenlabs")          # quota/auth dead -> stop paying for it
    except Exception:
        _mark_down("elevenlabs")
    return None


def _open_deepgram(text: str, lang: str):
    key = os.getenv("DEEPGRAM_API_KEY", "").strip()
    if not key or lang != "en" or _down("deepgram"):  # Aura voices are English-only
        return None
    model = os.getenv("DEEPGRAM_TTS_MODEL", "aura-2-athena-en")
    try:
        r = requests.post(
            f"https://api.deepgram.com/v1/speak?model={model}&encoding=mp3",
            headers={"Authorization": f"Token {key}", "Content-Type": "application/json"},
            json={"text": text}, timeout=(5, 20), stream=True,
        )
        if r.ok and "audio" in r.headers.get("content-type", ""):
            return r, "audio/mpeg", "deepgram"
        r.close()
        _mark_down("deepgram")
    except Exception:
        _mark_down("deepgram")
    return None


def _providers_for(lang: str):
    # English: Deepgram first (fast, funded). Other languages: ElevenLabs only.
    if lang == "en":
        return (_open_deepgram, _open_elevenlabs)
    return (_open_elevenlabs,)


def _key(text: str, lang: str) -> str:
    return hashlib.sha1(f"{lang}:{text}".encode()).hexdigest()


def _norm(text: str) -> str:
    return (text or "").strip()[:800]


def get_cached(text: str, lang: str = "en"):
    """(audio_bytes, mime, engine) from cache, or None."""
    hit = _CACHE.get(_key(_norm(text), lang))
    if hit:
        _CACHE.move_to_end(_key(_norm(text), lang))
    return hit


def open_stream(text: str, lang: str = "en"):
    """Return (chunk_iterator, mime, engine) or None (→ caller sends 204).

    The iterator yields MP3 chunks as they arrive and caches the joined bytes
    once the stream completes, so the next play of the same text is instant.
    """
    text = _norm(text)
    if not text:
        return None
    for opener in _providers_for(lang):
        opened = opener(text, lang)
        if not opened:
            continue
        resp, mime, engine = opened
        ckey = _key(text, lang)

        def _gen(resp=resp, ckey=ckey, mime=mime, engine=engine):
            parts: list[bytes] = []
            try:
                for chunk in resp.iter_content(chunk_size=_CHUNK):
                    if chunk:
                        parts.append(chunk)
                        yield chunk
                if parts:
                    _CACHE[ckey] = (b"".join(parts), mime, engine)
                    if len(_CACHE) > _CACHE_MAX:
                        _CACHE.popitem(last=False)
            finally:
                resp.close()

        return _gen(), mime, engine
    return None


def synthesize(text: str, lang: str = "en"):
    """Buffered variant kept for tests/scripts: (bytes, mime, engine) or None."""
    hit = get_cached(text, lang)
    if hit:
        return hit
    opened = open_stream(text, lang)
    if not opened:
        return None
    gen, mime, engine = opened
    data = b"".join(gen)
    return (data, mime, engine) if data else None

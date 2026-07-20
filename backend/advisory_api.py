"""FastAPI backend for Feature 4 (Citizen Advisory) + Feature 5 (Multi-city).

Owner: Bind. Self-contained and runnable today:

    uvicorn backend.advisory_api:app --reload --port 8000

It serves the standalone chat demo at "/" and a clean JSON API the team's React
dashboard can consume as-is (or mount this router into the shared app later):

    from backend.advisory_api import router          # for app.include_router(...)

Every endpoint runs with zero external data (mock) and zero LLM key (templates).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the repo root importable whether launched via uvicorn or python -m.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import APIRouter, FastAPI, HTTPException, Query  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import (FileResponse, JSONResponse, Response,  # noqa: E402
                               StreamingResponse)
from pydantic import BaseModel  # noqa: E402

from advisory import advisory_engine, chat as chat_mod, llm, sources, tts  # noqa: E402
from advisory.config import city_config, languages  # noqa: E402
from advisory.data import data_source_kind, list_zones  # noqa: E402
from advisory.health_bands import band_for_aqi  # noqa: E402
from advisory.personas import list_personas  # noqa: E402
from compare.city_compare import compare  # noqa: E402

router = APIRouter()

_FRONTEND = _REPO_ROOT / "frontend" / "advisory_demo.html"

# What the assistant can do — surfaced in the welcome message so users don't hunt.
FEATURES = [
    {"icon": "📍", "en": "Air quality for your area",
     "hi": "आपके क्षेत्र की वायु गुणवत्ता"},
    {"icon": "👶", "en": "Personal advice (child, elderly, asthma, outdoor worker…)",
     "hi": "व्यक्तिगत सलाह (बच्चा, बुज़ुर्ग, अस्थमा, मज़दूर…)"},
    {"icon": "📅", "en": "24–72h forecast: is it getting better or worse?",
     "hi": "24–72घं पूर्वानुमान: हवा सुधरेगी या बिगड़ेगी?"},
    {"icon": "😷", "en": "Should you go out, exercise, or wear a mask?",
     "hi": "बाहर जाएँ, व्यायाम करें या मास्क पहनें?"},
    {"icon": "🏭", "en": "What's polluting your area (traffic/industry/dust)",
     "hi": "आपके क्षेत्र में प्रदूषण का स्रोत"},
    {"icon": "📖", "en": "Every answer cited to CPCB · SAFAR · WHO · GRAP",
     "hi": "हर सलाह CPCB · SAFAR · WHO · GRAP से प्रमाणित"},
    {"icon": "🗣️", "en": "Talk or type, in English or हिन्दी — with voice",
     "hi": "बोलें या टाइप करें, अंग्रेज़ी या हिन्दी में — आवाज़ के साथ"},
]


def _zone_summary(z: dict) -> dict:
    band = band_for_aqi(z.get("current_aqi", 0))
    return {
        "zone_id": z["zone_id"],
        "name": z.get("name"),
        "lat": z.get("lat"),
        "lon": z.get("lon"),
        "aqi": round(z.get("current_aqi", 0)),
        "band": band.key,
        "band_label": band.label_en,
        "color": band.color,
        "dominant_source": z.get("dominant_source"),
        "dominant_source_pct": round(z.get("dominant_source_pct", 0)),
        "confidence": z.get("confidence"),
    }


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm": "groq" if llm.available() else "template-fallback",
        "voice": "neural" if tts.available() else "browser-fallback",
    }


@router.get("/tts")
def tts_endpoint(text: str = Query(...), lang: str = Query(default="en")) -> Response:
    """MP3 audio for `text` — cached whole, or streamed as the provider produces
    it (playback starts on first bytes). 204 → the browser uses its own voice."""
    cached = tts.get_cached(text, lang)
    if cached:
        audio, mime, engine = cached
        return Response(content=audio, media_type=mime,
                        headers={"X-TTS-Engine": engine,
                                 "Cache-Control": "public, max-age=86400"})
    opened = tts.open_stream(text, lang)
    if not opened:
        return Response(status_code=204)
    gen, mime, engine = opened
    return StreamingResponse(gen, media_type=mime,
                             headers={"X-TTS-Engine": engine,
                                      "Cache-Control": "public, max-age=86400"})


@router.get("/meta")
def meta() -> dict:
    cfg = city_config()
    cities = [
        {"key": k, "name": v.get("name", k.title()), "data_kind": data_source_kind(k)}
        for k, v in cfg.get("cities", {}).items()
    ]
    return {
        "active_city": cfg.get("active_city"),
        "cities": cities,
        "personas": list_personas(),
        "languages": languages(),
        "features": FEATURES,
        "llm_available": llm.available(),
        "voice_available": tts.available(),
    }


@router.get("/sources")
def sources_endpoint() -> dict:
    return {"count": len(sources.all_sources()), "sources": sources.all_sources()}


@router.get("/wards")
def wards(city: str | None = Query(default=None)) -> dict:
    zones = list_zones(city)
    return {
        "city": city or city_config().get("active_city"),
        "data_kind": data_source_kind(city),
        "count": len(zones),
        "wards": [_zone_summary(z) for z in zones],
    }


@router.get("/advisory")
def advisory(
    zone: str = Query(...),
    persona: str = Query(default="general"),
    horizon: str = Query(default="24"),
    lang: str = Query(default="en"),
    city: str | None = Query(default=None),
) -> dict:
    try:
        return advisory_engine.build_advisory(zone, persona, horizon, lang, city)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class ChatRequest(BaseModel):
    zone: str
    message: str
    persona: str | None = None
    lang: str = "en"
    horizon: str = "24"
    history: list[dict] | None = None
    city: str | None = None


@router.post("/chat")
def chat_endpoint(req: ChatRequest) -> dict:
    try:
        return chat_mod.answer(
            zone_id=req.zone,
            message=req.message,
            persona_key=req.persona,
            lang=req.lang,
            horizon=req.horizon,
            history=req.history,
            city_key=req.city,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/compare")
def compare_endpoint(cities: str | None = Query(default=None)) -> dict:
    keys = [c.strip() for c in cities.split(",")] if cities else None
    return compare(keys)


def create_app() -> FastAPI:
    app = FastAPI(
        title="PS5 · Citizen Air-Quality Advisory API",
        description="Feature 4 (multilingual citizen health advisory) + "
                    "Feature 5 (multi-city comparison).",
        version="1.0.0",
    )
    # Demo-friendly CORS. Tighten to the deployed frontend origin in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/", include_in_schema=False)
    def home():
        if _FRONTEND.exists():
            return FileResponse(str(_FRONTEND))
        return JSONResponse({"status": "ok", "hint": "GET /wards, /advisory, /chat, /compare"})

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

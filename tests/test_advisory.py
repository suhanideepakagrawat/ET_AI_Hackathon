"""Deterministic tests for Feature 4 + 5 (offline: no network, no LLM key).

Run:  python -m pytest tests/ -q      (or)   python tests/test_advisory.py

These force the zero-key path so they're reproducible in CI. A separate live
smoke (scripts/live_smoke.py) exercises the real Groq path.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Force the deterministic, no-network path for every test in this module.
os.environ["GROQ_API_KEY"] = ""
os.environ["ELEVENLABS_API_KEY"] = ""
os.environ["DEEPGRAM_API_KEY"] = ""

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from advisory import chat as chat_mod  # noqa: E402
from advisory import translate  # noqa: E402
from advisory.advisory_engine import build_advisory  # noqa: E402
from advisory.data import data_source_kind, get_zone, list_zones  # noqa: E402
from advisory.health_bands import band_for_aqi  # noqa: E402
from advisory.personas import detect_persona, get_persona  # noqa: E402
from compare.city_compare import compare  # noqa: E402


def test_band_boundaries():
    cases = {0: "good", 50: "good", 51: "satisfactory", 100: "satisfactory",
             101: "moderate", 200: "moderate", 201: "poor", 300: "poor",
             301: "very_poor", 400: "very_poor", 401: "severe", 650: "severe"}
    for aqi, key in cases.items():
        assert band_for_aqi(aqi).key == key, f"AQI {aqi} -> {band_for_aqi(aqi).key} != {key}"


def test_persona_escalation_outdoor():
    zone = get_zone("DL-PUNJABIBAGH")  # 24h ~178 (Moderate)
    child = build_advisory("DL-PUNJABIBAGH", "child", "24", "en")
    adult = build_advisory("DL-PUNJABIBAGH", "general", "24", "en")
    # At Moderate a sensitive child is advised to avoid outdoor; a healthy adult isn't.
    assert child["guidance"]["outdoor_ok"] is False
    assert adult["guidance"]["outdoor_ok"] is True
    assert zone is not None


def test_general_public_restricted_at_poor():
    a = build_advisory("DL-ITO", "general", "24", "en")  # ~287 Poor
    assert a["band"]["key"] == "poor"
    assert a["guidance"]["outdoor_ok"] is False
    assert a["guidance"]["mask"] is True


def test_assess_has_citation_and_disclaimer():
    a = build_advisory("DL-ANANDVIHAR", "respiratory", "48", "en")
    assert a["citation"]["authority"].startswith("CPCB")
    assert a["citation"]["range"]
    assert "not a medical diagnosis" in a["message_en"].lower()
    assert str(a["aqi"]) in a["message_en"]
    # respiratory persona at high AQI -> meds handy flag
    assert a["guidance"]["meds_handy"] is True


def test_data_loader_contract():
    zones = list_zones("delhi")
    assert len(zones) >= 8
    z = get_zone("DL-DWARKA")
    assert z and set(z["forecast"]) >= {"24", "48", "72"}
    assert z["dominant_source"] in {"Traffic/Roads", "Industry", "Construction/Dust"}
    assert data_source_kind("delhi") == "mock"  # no real CSV committed


def test_translation_fallback_hindi():
    hi = translate.translate("Wear an N95 mask outdoors", "hi")
    assert any("ऀ" <= ch <= "ॿ" for ch in hi), "expected Devanagari output"
    # English is a passthrough.
    assert translate.translate("hello", "en") == "hello"


def test_build_advisory_hindi_message():
    a = build_advisory("DL-ITO", "child", "24", "hi")
    assert a["lang"] == "hi"
    assert any("ऀ" <= ch <= "ॿ" for ch in a["message"])


def test_chat_outdoor_child_offline():
    r = chat_mod.answer("DL-PUNJABIBAGH", "can my child play outside this evening?")
    assert r["persona"] == "child"          # inferred from the question
    assert r["intent"] == "outdoor"
    assert r["outdoor_ok"] is False
    assert r["reply"].startswith("In") or "No" in r["reply"]
    assert "CPCB" in r["reply"]


def test_chat_detects_persona():
    assert detect_persona("I have asthma, can I go for a walk?").key == "respiratory"
    assert get_persona(None).key == "general"


def test_compare_two_cities():
    out = compare(["delhi", "mumbai"])
    assert out["count"] == 2
    for c in out["cities"]:
        assert c["avg_aqi"] > 0
        assert c["intervention"]["reduction_pct"] >= 0
        assert "band_distribution" in c
    # Delhi should be the worse (listed first, sorted desc).
    assert out["cities"][0]["city"] == "delhi"


def test_api_endpoints_offline():
    from fastapi.testclient import TestClient

    from backend.advisory_api import app
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    meta = client.get("/meta").json()
    assert len(meta["personas"]) >= 5 and len(meta["cities"]) >= 2

    wards = client.get("/wards").json()
    assert wards["count"] >= 8 and wards["data_kind"] == "mock"

    adv = client.get("/advisory", params={"zone": "DL-ITO", "persona": "elderly",
                                          "horizon": "24", "lang": "en"}).json()
    assert adv["aqi"] > 0 and "message" in adv

    assert client.get("/advisory", params={"zone": "NOPE"}).status_code == 404

    chat = client.post("/chat", json={"zone": "DL-ANANDVIHAR",
                                      "message": "should I wear a mask?",
                                      "lang": "en"}).json()
    assert "reply" in chat and "CPCB" in chat["reply"]

    comp = client.get("/compare").json()
    assert comp["count"] >= 2


def test_sources_grounding_in_advisory():
    a = build_advisory("DL-ITO", "elderly", "24", "en")   # Poor -> GRAP applies
    assert len(a["sources"]) >= 3
    ids = {s["id"] for s in a["sources"]}
    assert {"cpcb_aqi", "safar", "who_aqg"} <= ids
    assert "grap" in ids                      # Poor band pulls in GRAP
    assert a["grap_stage"] == "Stage I"
    assert a["provenance"].startswith("Based on:")
    for s in a["sources"]:
        assert s["url"].startswith("http") and s["publisher"] and s["year"]


def test_good_air_has_no_grap():
    from advisory.data import list_zones
    from advisory.advisory_engine import assess
    from advisory.personas import get_persona
    # Fabricate a good-air zone assessment.
    z = dict(list_zones("delhi")[0]); z["forecast"] = {"24": 40, "48": 40, "72": 40}
    a = assess(z, get_persona("general"), "24")
    assert a["grap_stage"] is None
    assert "grap" not in {s["id"] for s in a["sources"]}


def test_chat_area_switch_by_text():
    # Start in one zone, ask about another by name -> follows the user.
    r = chat_mod.answer("DL-ITO", "what about the air in Dwarka right now?")
    assert r["zone_switched"] is True
    assert "Dwarka" in r["zone_name"]
    assert r["sources"] and r["provenance"]


def test_sources_and_features_api():
    from fastapi.testclient import TestClient
    from backend.advisory_api import app
    client = TestClient(app)
    src = client.get("/sources").json()
    assert src["count"] >= 5 and all(s["url"].startswith("http") for s in src["sources"])
    meta = client.get("/meta").json()
    assert len(meta["features"]) >= 5


def test_tts_falls_back_when_no_keys():
    from fastapi.testclient import TestClient
    from backend.advisory_api import app
    client = TestClient(app)
    # No voice keys in this test env -> 204 so the browser uses its own voice.
    r = client.get("/tts", params={"text": "hello", "lang": "en"})
    assert r.status_code == 204
    assert client.get("/health").json()["voice"] == "browser-fallback"


def _run_all():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} tests passed (offline path).")


if __name__ == "__main__":
    _run_all()

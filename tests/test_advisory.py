"""Deterministic tests for Feature 4 + 5 (offline: no network, no LLM key).

Run:  python -m pytest tests/ -q      (or)   python tests/test_advisory.py

Data-agnostic by design: these pass whether the serving layer is on the REAL
pipeline CSVs (data/*.csv) or the committed mock. Band-specific logic is tested
on fabricated zones via assess(); integration paths use whatever zones are live.
A separate live smoke (scripts/live_smoke.py) exercises the real Groq path.
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
from advisory.advisory_engine import assess, build_advisory, compose_message  # noqa: E402
from advisory.data import data_source_kind, get_zone, list_zones  # noqa: E402
from advisory.health_bands import band_for_aqi  # noqa: E402
from advisory.personas import detect_persona, get_persona  # noqa: E402
from compare.city_compare import compare  # noqa: E402

ZONES = list_zones("delhi")
Z0 = ZONES[0]  # worst zone in whatever data is live


def _fab(aqi: float) -> dict:
    """A fabricated zone at a chosen AQI, shaped like a real one."""
    z = dict(Z0)
    z["forecast"] = {"24": aqi, "48": aqi, "72": aqi}
    z["current_aqi"] = aqi
    return z


def test_band_boundaries():
    cases = {0: "good", 50: "good", 51: "satisfactory", 100: "satisfactory",
             101: "moderate", 200: "moderate", 201: "poor", 300: "poor",
             301: "very_poor", 400: "very_poor", 401: "severe", 650: "severe"}
    for aqi, key in cases.items():
        assert band_for_aqi(aqi).key == key, f"AQI {aqi} -> {band_for_aqi(aqi).key} != {key}"


def test_persona_escalation_outdoor():
    # At Moderate (150) a sensitive child is told to stay in; a healthy adult isn't.
    child = assess(_fab(150), get_persona("child"), "24")
    adult = assess(_fab(150), get_persona("general"), "24")
    assert child["guidance"]["outdoor_ok"] is False
    assert adult["guidance"]["outdoor_ok"] is True


def test_general_public_restricted_at_poor():
    a = assess(_fab(250), get_persona("general"), "24")
    assert a["band"]["key"] == "poor"
    assert a["guidance"]["outdoor_ok"] is False
    assert a["guidance"]["mask"] is True


def test_assess_has_citation_and_meds():
    a = assess(_fab(310), get_persona("respiratory"), "48")
    assert a["citation"]["authority"].startswith("CPCB")
    assert a["citation"]["range"]
    assert a["guidance"]["meds_handy"] is True
    msg = compose_message(a, get_persona("respiratory"))
    assert "not a medical diagnosis" in msg.lower()
    assert str(a["aqi"]) in msg


def test_build_advisory_on_live_data():
    a = build_advisory(Z0["zone_id"], "elderly", "24", "en")
    assert a["zone_name"] == Z0["name"]
    assert a["aqi"] > 0
    assert "not a medical diagnosis" in a["message_en"].lower()
    assert a["provenance"].startswith("Based on:")


def test_data_loader_contract():
    assert len(ZONES) >= 8
    z = get_zone(Z0["zone_id"])
    assert z and set(z["forecast"]) >= {"24", "48", "72"}
    assert z["dominant_source"] in {"Traffic/Roads", "Industry", "Construction/Dust"}
    assert data_source_kind("delhi") in {"real", "mock"}
    # Every zone is well-formed (foolproof check across the whole dataset).
    for zz in ZONES:
        assert zz["current_aqi"] >= 0 and zz["name"] and zz["zone_id"]
        assert set(zz["forecast"]) >= {"24", "48", "72"}


def test_translation_fallback_hindi():
    hi = translate.translate("Wear an N95 mask outdoors", "hi")
    assert any("ऀ" <= ch <= "ॿ" for ch in hi), "expected Devanagari output"
    assert translate.translate("hello", "en") == "hello"


def test_build_advisory_hindi_message():
    a = build_advisory(Z0["zone_id"], "child", "24", "hi")
    assert a["lang"] == "hi"
    assert any("ऀ" <= ch <= "ॿ" for ch in a["message"])


def test_chat_outdoor_child_offline():
    r = chat_mod.answer(Z0["zone_id"], "can my child play outside this evening?")
    assert r["persona"] == "child"          # inferred from the question
    assert r["intent"] == "outdoor"
    assert "CPCB" in r["reply"]
    assert isinstance(r["outdoor_ok"], bool)


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
    # Sorted worst-first by average AQI, whichever city that is.
    avgs = [c["avg_aqi"] for c in out["cities"]]
    assert avgs == sorted(avgs, reverse=True)


def test_api_endpoints_offline():
    from fastapi.testclient import TestClient

    from backend.advisory_api import app
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    meta = client.get("/meta").json()
    assert len(meta["personas"]) >= 5 and len(meta["cities"]) >= 2

    wards = client.get("/wards").json()
    assert wards["count"] >= 8 and wards["data_kind"] in {"real", "mock"}
    zid = wards["wards"][0]["zone_id"]

    adv = client.get("/advisory", params={"zone": zid, "persona": "elderly",
                                          "horizon": "24", "lang": "en"}).json()
    assert adv["aqi"] > 0 and "message" in adv

    assert client.get("/advisory", params={"zone": "NOPE"}).status_code == 404

    chat = client.post("/chat", json={"zone": zid,
                                      "message": "should I wear a mask?",
                                      "lang": "en"}).json()
    assert "reply" in chat and "CPCB" in chat["reply"]

    comp = client.get("/compare").json()
    assert comp["count"] >= 2


def test_sources_grounding_at_poor():
    a = assess(_fab(250), get_persona("elderly"), "24")   # Poor -> GRAP applies
    ids = {s["id"] for s in a["sources"]}
    assert {"cpcb_aqi", "safar", "who_aqg", "grap"} <= ids
    assert a["grap_stage"] == "Stage I"
    for s in a["sources"]:
        assert s["url"].startswith("http") and s["publisher"] and s["year"]


def test_good_air_has_no_grap():
    a = assess(_fab(40), get_persona("general"), "24")
    assert a["grap_stage"] is None
    assert "grap" not in {s["id"] for s in a["sources"]}


def test_chat_area_switch_by_text():
    # Start in the worst zone, name another zone -> the bot follows the user.
    other = ZONES[min(3, len(ZONES) - 1)]
    r = chat_mod.answer(Z0["zone_id"], f"what about the air in {other['name']} right now?")
    assert r["zone_switched"] is True
    assert r["zone_name"] == other["name"]
    assert r["sources"] and r["provenance"]


def test_sources_and_features_api():
    from fastapi.testclient import TestClient
    from backend.advisory_api import app
    client = TestClient(app)
    src = client.get("/sources").json()
    assert src["count"] >= 5 and all(s["url"].startswith("http") for s in src["sources"])
    meta = client.get("/meta").json()
    assert len(meta["features"]) >= 5


def test_enforcement_and_deployment_endpoints():
    from fastapi.testclient import TestClient
    from backend.advisory_api import app
    client = TestClient(app)
    top = client.get("/enforcement/top").json()
    dep = client.get("/deployment").json()
    # Foolproof contract: always 200 with an availability flag; items well-formed
    # when the real CSVs are present.
    assert "available" in top and "items" in top
    assert "available" in dep and "items" in dep
    if top["available"]:
        assert top["items"] and {"lat", "lon", "action"} <= set(top["items"][0])
    if dep["available"]:
        assert dep["items"] and {"ward_name", "deployment_score"} <= set(dep["items"][0])


def test_locate_resolves_delhi_coordinate():
    from fastapi.testclient import TestClient
    from backend.advisory_api import app
    client = TestClient(app)
    # A point well inside Delhi resolves to a ward with usable zone data
    # (boundary hit, or honest nearest-forecast-ward fallback).
    r = client.get("/locate?lat=28.656&lon=77.292").json()
    assert r["in_delhi"] is True
    assert r["matched"] in ("boundary", "nearest")
    assert r["zone"] and {"zone_id", "name", "aqi", "band"} <= set(r["zone"])


def test_locate_rejects_outside_delhi():
    from fastapi.testclient import TestClient
    from backend.advisory_api import app
    client = TestClient(app)
    r = client.get("/locate?lat=19.07&lon=72.87").json()  # Mumbai
    assert r["in_delhi"] is False
    assert r["matched"] == "none"
    assert r["zone"] is None


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
    print(f"\n{passed}/{len(fns)} tests passed "
          f"(offline path, data={data_source_kind('delhi')}).")


if __name__ == "__main__":
    _run_all()

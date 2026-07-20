"""Authentic reference layer — the documented basis for every advisory.

This is a small, curated "mini-RAG" over PUBLIC, AUTHORITATIVE Indian + global
air-quality health documents. The advisory never invents health thresholds: the
band definitions and health notes come from CPCB's National AQI, and each reply
can name the exact sources it stands on. Kept honest: we cite publisher + year and
link the official domain; we do not paraphrase these bodies into false specifics.
"""
from __future__ import annotations

# Each source: what it IS, who published it, and precisely what it grounds.
SOURCES: list[dict] = [
    {
        "id": "cpcb_aqi",
        "title": "National Air Quality Index (AQI) — categories, breakpoints & health statements",
        "publisher": "Central Pollution Control Board (CPCB), MoEFCC, Govt. of India",
        "year": 2014,
        "url": "https://cpcb.nic.in/National-Air-Quality-Index/",
        "grounds": "The 6 AQI categories (Good…Severe) and the official health-impact "
                   "statement quoted in every advisory.",
    },
    {
        "id": "safar",
        "title": "SAFAR-India — category-wise public health advisory",
        "publisher": "SAFAR, Indian Institute of Tropical Meteorology (IITM), "
                     "Ministry of Earth Sciences",
        "year": 2015,
        "url": "https://safar.tropmet.res.in/",
        "grounds": "Category-wise guidance on outdoor exertion, masks and sensitive groups.",
    },
    {
        "id": "who_aqg",
        "title": "WHO Global Air Quality Guidelines (2021)",
        "publisher": "World Health Organization",
        "year": 2021,
        "url": "https://www.who.int/publications/i/item/9789240034228",
        "grounds": "Health-based limits (PM2.5 24-hr 15 µg/m³) — why 'safe' air is a low AQI.",
    },
    {
        "id": "grap",
        "title": "Graded Response Action Plan (GRAP) for Delhi-NCR",
        "publisher": "Commission for Air Quality Management in NCR (CAQM)",
        "year": 2022,
        "url": "https://caqm.nic.in/",
        "grounds": "AQI-stage emergency measures (Stage I Poor 201–300 … Stage IV Severe+ >450).",
    },
    {
        "id": "ncap",
        "title": "National Clean Air Programme (NCAP)",
        "publisher": "MoEFCC, Govt. of India",
        "year": 2019,
        "url": "https://prana.cpcb.gov.in/",
        "grounds": "National programme to cut particulate pollution (target ~40% by 2025–26).",
    },
]

_BY_ID = {s["id"]: s for s in SOURCES}

# Which GRAP stage is typically in force at each CPCB band (CAQM, revised 2022).
_GRAP_STAGE = {
    "poor": "Stage I",
    "very_poor": "Stage II",
    "severe": "Stage III–IV",
}


def all_sources() -> list[dict]:
    return [dict(s) for s in SOURCES]


def sources_for(band_key: str, persona_key: str | None = None) -> list[dict]:
    """The authentic references backing a specific advisory."""
    ids = ["cpcb_aqi", "safar", "who_aqg"]
    if band_key in _GRAP_STAGE:          # Poor and worse -> emergency plan applies
        ids.append("grap")
    return [dict(_BY_ID[i]) for i in ids]


def grap_stage(band_key: str) -> str | None:
    return _GRAP_STAGE.get(band_key)


def grounding_context(band, persona=None) -> str:
    """Compact authentic facts fed to the LLM so it stays grounded (no invention)."""
    lines = [
        f"CPCB National AQI category '{band.label_en}' = AQI {band.range_str()}; "
        f"official CPCB health statement: \"{band.note_en}\"",
        "WHO 2021 guideline: PM2.5 24-hour mean 15 µg/m³ — Indian urban AQI is often "
        "far above this, so caution at 'Moderate' and worse is well-founded.",
    ]
    stage = _GRAP_STAGE.get(band.key)
    if stage:
        lines.append(f"At this level Delhi-NCR GRAP {stage} emergency measures typically apply "
                     f"(CAQM).")
    return " ".join(lines)


def citation_line(band) -> str:
    """One-line 'based on' provenance string for UI/messages."""
    names = ["CPCB AQI", "SAFAR", "WHO 2021"]
    if band.key in _GRAP_STAGE:
        names.append(f"GRAP {_GRAP_STAGE[band.key]}")
    return "Based on: " + " · ".join(names)

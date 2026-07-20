"""Forecast + source-attribution loader (the Feature 1 & 2 -> Feature 4 bridge).

Reads the REAL attribution CSV produced by the source-attribution notebook
(`data/source_attribution.csv`) when present; otherwise falls back to a committed
mock (`data/mock/<city>_wards_forecast.json`) so the advisory always runs with
zero external data (RULE 1/2).

Both inputs are normalised to ONE zone schema the rest of Feature 4 consumes:

    {
      zone_id, name, lat, lon,
      forecast: {"24": aqi, "48": aqi, "72": aqi},
      current_aqi,
      sources: {traffic, industry, construction},   # percentages
      dominant_source, dominant_source_pct,
      confidence, confidence_label,
    }
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .config import REPO_ROOT, get_city

# Real attribution CSV columns (from the notebook contract).
_REAL_COLS = {"cell_id", "lat", "lon", "horizon_hours", "forecast_aqi",
              "dominant_source"}


def _friendly_name(zone_id: str) -> str:
    return f"Zone {zone_id}"


def _confidence_label(conf: float) -> str:
    if conf >= 0.6:
        return "High-confidence directional evidence"
    if conf >= 0.25:
        return "Medium-confidence directional evidence"
    return "Low-confidence directional evidence"


def _load_real_csv(path: Path) -> list[dict]:
    """Pivot the per-(cell, horizon) CSV into per-zone records."""
    import pandas as pd  # local import so the mock path needs no pandas

    df = pd.read_csv(path)
    if not _REAL_COLS.issubset(df.columns):
        missing = _REAL_COLS - set(df.columns)
        raise ValueError(f"attribution CSV missing columns: {missing}")

    zones: list[dict] = []
    for cell_id, grp in df.groupby("cell_id"):
        grp = grp.sort_values("horizon_hours")
        first = grp.iloc[0]
        forecast = {
            str(int(r.horizon_hours)): float(r.forecast_aqi)
            for r in grp.itertuples()
            if not pd.isna(r.horizon_hours)
        }
        # Ensure all three horizons exist (carry forward if a horizon is absent).
        last = None
        for h in ("24", "48", "72"):
            if h in forecast:
                last = forecast[h]
            elif last is not None:
                forecast[h] = last
        current = forecast.get("24") or float(first.forecast_aqi)
        conf = float(first.confidence) if "confidence" in df.columns else 0.5
        zones.append({
            "zone_id": str(cell_id),
            "name": str(first.get("name", _friendly_name(str(cell_id))))
            if hasattr(first, "get") else _friendly_name(str(cell_id)),
            "lat": float(first.lat),
            "lon": float(first.lon),
            "forecast": forecast,
            "current_aqi": current,
            "sources": {
                "traffic": float(getattr(first, "traffic_pct", 0) or 0),
                "industry": float(getattr(first, "industry_pct", 0) or 0),
                "construction": float(getattr(first, "construction_pct", 0) or 0),
            },
            "dominant_source": str(first.dominant_source),
            "dominant_source_pct": float(getattr(first, "dominant_source_pct", 0) or 0),
            "confidence": conf,
            "confidence_label": str(getattr(first, "confidence_label", "")
                                    or _confidence_label(conf)),
        })
    return zones


def _load_mock(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    zones = raw["zones"] if isinstance(raw, dict) else raw
    for z in zones:
        z.setdefault("current_aqi", z.get("forecast", {}).get("24"))
        z.setdefault("confidence_label", _confidence_label(z.get("confidence", 0.5)))
    return zones


@lru_cache(maxsize=8)
def load_zones(city_key: str | None = None) -> tuple[dict, ...]:
    """All zones for a city (cached). Real CSV if present, else the mock."""
    city = get_city(city_key)
    real = REPO_ROOT / city.get("data_file", "")
    mock = REPO_ROOT / city.get("mock_file", "")

    if city.get("data_file") and real.exists():
        zones = _load_real_csv(real)
    elif city.get("mock_file") and mock.exists():
        zones = _load_mock(mock)
    else:
        zones = []
    # Sort worst-first so the UI leads with the most urgent zone.
    zones.sort(key=lambda z: z.get("current_aqi", 0), reverse=True)
    return tuple(zones)


def list_zones(city_key: str | None = None) -> list[dict]:
    return [dict(z) for z in load_zones(city_key)]


def get_zone(zone_id: str, city_key: str | None = None) -> dict | None:
    for z in load_zones(city_key):
        if str(z["zone_id"]) == str(zone_id) or z.get("name") == zone_id:
            return dict(z)
    return None


_AREA_STOPWORDS = {"sector", "junction", "road", "east", "west", "north",
                   "south", "puram", "bagh", "vihar", "nagar", "block"}


def find_zone_by_text(text: str, city_key: str | None = None) -> dict | None:
    """Best-effort: match a spoken/typed area name to a known zone.

    Tries a full name substring first, then a distinctive single token (so
    "what about Dwarka?" or "Rohini abhi kaisa hai" resolves the zone).
    """
    low = (text or "").lower()
    if not low:
        return None
    zones = load_zones(city_key)
    for z in zones:                       # full-name match wins
        name = str(z.get("name", "")).lower()
        if name and name in low:
            return dict(z)
    for z in zones:                       # distinctive-token match
        for tok in str(z.get("name", "")).lower().replace("/", " ").split():
            if len(tok) > 4 and tok not in _AREA_STOPWORDS and tok in low:
                return dict(z)
    return None


def data_source_kind(city_key: str | None = None) -> str:
    """'real' or 'mock' — surfaced in the API so the demo is honest."""
    city = get_city(city_key)
    real = REPO_ROOT / city.get("data_file", "")
    return "real" if (city.get("data_file") and real.exists()) else "mock"

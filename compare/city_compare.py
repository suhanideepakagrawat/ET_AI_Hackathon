"""Cross-city aggregation for the comparative dashboard.

Everything is derived from the SAME per-zone schema used by Feature 4, so adding a
city is purely a config + data question — no new code. The intervention metric is
an explicitly-labelled MODEL projection, not a measured outcome (honesty rule).
"""
from __future__ import annotations

from advisory.config import city_config
from advisory.data import data_source_kind, list_zones
from advisory.health_bands import band_for_aqi

# Rough share of a source's contribution that targeted enforcement can cut in the
# short term (dust suppression / stack checks / traffic diversion). Modelled.
_ADDRESSABILITY = {
    "Construction/Dust": 0.45,
    "Traffic/Roads": 0.30,
    "Industry": 0.35,
}


def _summarise_city(city_key: str) -> dict | None:
    zones = list_zones(city_key)
    if not zones:
        return None

    aqis = [z.get("current_aqi", 0) for z in zones]
    n = len(zones)
    avg = sum(aqis) / n
    worst = max(zones, key=lambda z: z.get("current_aqi", 0))

    # Band distribution.
    dist: dict[str, int] = {}
    for z in zones:
        key = band_for_aqi(z.get("current_aqi", 0)).key
        dist[key] = dist.get(key, 0) + 1

    # Average source mix + overall dominant source.
    mix = {"traffic": 0.0, "industry": 0.0, "construction": 0.0}
    for z in zones:
        for k in mix:
            mix[k] += float(z.get("sources", {}).get(k, 0))
    mix = {k: round(v / n, 1) for k, v in mix.items()}
    dominant = max(mix, key=mix.get) if any(mix.values()) else None

    # Modelled intervention effectiveness: cut each zone's AQI by the addressable
    # share of ITS dominant source, then re-average.
    projected = []
    for z in zones:
        cut = _ADDRESSABILITY.get(z.get("dominant_source", ""), 0.25)
        share = float(z.get("dominant_source_pct", 0)) / 100.0
        projected.append(z.get("current_aqi", 0) * (1 - cut * share))
    avg_after = sum(projected) / n

    cfg = city_config().get("cities", {}).get(city_key, {})
    return {
        "city": city_key,
        "name": cfg.get("name", city_key.title()),
        "center": cfg.get("center"),
        "data_kind": data_source_kind(city_key),
        "zones": n,
        "avg_aqi": round(avg),
        "max_aqi": round(max(aqis)),
        "min_aqi": round(min(aqis)),
        "worst_zone": {"name": worst.get("name"), "aqi": round(worst.get("current_aqi", 0))},
        "band_distribution": dist,
        "source_mix": mix,
        "dominant_source": dominant,
        "intervention": {
            "avg_aqi_before": round(avg),
            "avg_aqi_after": round(avg_after),
            "reduction_pct": round((avg - avg_after) / avg * 100, 1) if avg else 0.0,
            "note": "Modelled projection from source addressability, not a measured outcome.",
        },
    }


def compare(city_keys: list[str] | None = None) -> dict:
    """Comparative summary across cities (defaults to all configured cities)."""
    cfg = city_config()
    keys = city_keys or list(cfg.get("cities", {}).keys())
    summaries = [s for s in (_summarise_city(k) for k in keys) if s]
    summaries.sort(key=lambda s: s["avg_aqi"], reverse=True)
    return {
        "cities": summaries,
        "count": len(summaries),
        "note": (
            "Delhi is built deep; other cities demonstrate the parameterised "
            "architecture — a new city is a config block, not new code."
        ),
    }

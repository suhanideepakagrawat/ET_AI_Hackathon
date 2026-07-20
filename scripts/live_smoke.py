"""Live smoke test — exercises the REAL Groq path (needs GROQ_API_KEY in .env).

    python scripts/live_smoke.py

Prints composed advisories + a chat turn in English and Hindi so you can eyeball
quality before recording the demo. Falls back to templates if the key is absent.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Windows consoles default to cp1252 and can't print Devanagari; force UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from advisory import chat, llm  # noqa: E402
from advisory.advisory_engine import build_advisory  # noqa: E402


def main() -> None:
    print(f"Groq key present: {llm.available()}\n" + "=" * 66)

    for zone, persona in [("DL-ITO", "child"), ("DL-WAZIRPUR", "respiratory")]:
        for lang in ("en", "hi"):
            a = build_advisory(zone, persona, "24", lang)
            print(f"\n[{a['zone_name']} · {a['persona']['label_en']} · {lang} · "
                  f"AQI {a['aqi']} {a['band']['label_en']}]")
            print(" ", a["message"])

    print("\n" + "=" * 66 + "\nCHAT:")
    for q, lang in [("can my child play outside this evening?", "en"),
                    ("क्या मैं आज सुबह टहलने जा सकता हूँ? मुझे अस्थमा है", "hi")]:
        r = chat.answer("DL-ANANDVIHAR", q, lang=lang)
        print(f"\nQ ({lang}): {q}\nA: {r['reply']}")


if __name__ == "__main__":
    main()

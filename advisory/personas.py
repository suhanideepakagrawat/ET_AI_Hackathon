"""Vulnerable-population personas for the citizen advisory.

Each persona carries an `extra_sensitivity` (0-2 band bumps) so sensitive groups
are warned *earlier* than the general public — e.g. a child is told to stay in at
"Moderate" while a healthy adult is told so only at "Poor". This is what makes
"can my child play outside?" answer differently from "can I go for a run?".
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Persona:
    key: str
    label_en: str
    label_hi: str
    icon: str
    # How many severity bands to escalate vs. the general public (0 = none).
    extra_sensitivity: int = 0
    # Short descriptor woven into LLM prompts + templates.
    profile_en: str = ""
    profile_hi: str = ""
    keywords: tuple[str, ...] = field(default_factory=tuple)

    def label(self, lang: str = "en") -> str:
        return self.label_hi if lang == "hi" else self.label_en

    def profile(self, lang: str = "en") -> str:
        return self.profile_hi if lang == "hi" else self.profile_en


PERSONAS: dict[str, Persona] = {
    "general": Persona(
        key="general", label_en="General public", label_hi="आम नागरिक", icon="🧑",
        extra_sensitivity=0,
        profile_en="a healthy adult",
        profile_hi="एक स्वस्थ वयस्क",
        keywords=("me", "myself", "adult", "general", "run", "jog", "gym", "exercise"),
    ),
    "child": Persona(
        key="child", label_en="Child / School", label_hi="बच्चा / स्कूल", icon="🧒",
        extra_sensitivity=2,
        profile_en="a young child (or a school planning outdoor activity)",
        profile_hi="एक छोटा बच्चा (या बाहरी गतिविधि की योजना बनाता स्कूल)",
        keywords=("child", "kid", "children", "school", "son", "daughter", "baby",
                  "play", "बच्चा", "बच्चे", "स्कूल"),
    ),
    "elderly": Persona(
        key="elderly", label_en="Elderly (60+)", label_hi="बुज़ुर्ग (60+)", icon="🧓",
        extra_sensitivity=2,
        profile_en="an elderly person (age 60+)",
        profile_hi="एक बुज़ुर्ग व्यक्ति (60 वर्ष से अधिक)",
        keywords=("elderly", "old", "senior", "grandmother", "grandfather",
                  "बुज़ुर्ग", "बूढ़े", "दादा", "दादी"),
    ),
    "respiratory": Persona(
        key="respiratory", label_en="Asthma / Heart patient",
        label_hi="अस्थमा / हृदय रोगी", icon="🫁",
        extra_sensitivity=2,
        profile_en="a person with asthma, a lung condition or a heart condition",
        profile_hi="अस्थमा, फेफड़े या हृदय रोग से पीड़ित व्यक्ति",
        keywords=("asthma", "asthmatic", "copd", "lung", "heart", "breathing",
                  "respiratory", "inhaler", "अस्थमा", "साँस", "दमा"),
    ),
    "outdoor_worker": Persona(
        key="outdoor_worker", label_en="Outdoor worker",
        label_hi="बाहरी कर्मचारी", icon="👷",
        extra_sensitivity=1,
        profile_en="an outdoor worker spending long hours outside",
        profile_hi="लंबे समय तक बाहर काम करने वाला मज़दूर",
        keywords=("worker", "labour", "labor", "construction", "traffic police",
                  "vendor", "delivery", "outdoor work", "मज़दूर", "काम"),
    ),
    "pregnant": Persona(
        key="pregnant", label_en="Pregnant", label_hi="गर्भवती", icon="🤰",
        extra_sensitivity=2,
        profile_en="a pregnant woman",
        profile_hi="एक गर्भवती महिला",
        keywords=("pregnant", "pregnancy", "expecting", "गर्भवती", "गर्भ"),
    ),
}

DEFAULT_PERSONA = "general"


def get_persona(key: str | None) -> Persona:
    return PERSONAS.get((key or DEFAULT_PERSONA).lower(), PERSONAS[DEFAULT_PERSONA])


def detect_persona(text: str) -> Persona:
    """Best-effort persona inference from free-text (offline keyword match)."""
    low = (text or "").lower()
    # Prefer the most-sensitive matching persona if several hit.
    matches = [
        p for p in PERSONAS.values()
        if any(kw in low for kw in p.keywords)
    ]
    if not matches:
        return PERSONAS[DEFAULT_PERSONA]
    return max(matches, key=lambda p: p.extra_sensitivity)


def list_personas() -> list[dict]:
    return [
        {
            "key": p.key,
            "label_en": p.label_en,
            "label_hi": p.label_hi,
            "icon": p.icon,
            "sensitive": p.extra_sensitivity > 0,
        }
        for p in PERSONAS.values()
    ]

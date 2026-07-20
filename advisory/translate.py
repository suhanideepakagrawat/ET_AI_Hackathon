"""English -> target-language translation for citizen messages.

Primary path: Groq (fast model) translates naturally. Fallback path: a curated
phrase table so the two demo languages (English + Hindi) ALWAYS work offline —
covering the sentences the template composer produces.
"""
from __future__ import annotations

from . import llm

# Offline phrase table: canonical English fragment -> Hindi. Kept in sync with
# the template sentences in advisory_engine.py so the zero-key path reads well.
_HI: dict[str, str] = {
    "Air quality advisory for": "वायु गुणवत्ता सलाह —",
    "The forecast air quality is": "अनुमानित वायु गुणवत्ता है",
    "which is": "जो कि",
    "As": "चूँकि आप",
    "you are more sensitive to polluted air.": "आप प्रदूषित हवा के प्रति अधिक संवेदनशील हैं।",
    "Avoid outdoor activity": "बाहरी गतिविधि से बचें",
    "Limit prolonged outdoor exertion": "लंबे समय तक बाहर मेहनत का काम सीमित करें",
    "Outdoor activity is generally safe": "बाहरी गतिविधि आमतौर पर सुरक्षित है",
    "Wear an N95 mask outdoors": "बाहर N95 मास्क पहनें",
    "Keep windows closed": "खिड़कियाँ बंद रखें",
    "Keep quick-relief medication handy": "तुरंत राहत देने वाली दवा पास रखें",
    "The dominant pollution source here is": "यहाँ प्रदूषण का मुख्य स्रोत है",
    "This is health guidance, not a medical diagnosis.":
        "यह स्वास्थ्य सलाह है, चिकित्सीय निदान नहीं।",
    "Yes": "हाँ", "No": "नहीं",
    "Traffic/Roads": "यातायात/सड़कें", "Industry": "उद्योग",
    "Construction/Dust": "निर्माण/धूल",
}


def _table_translate(text: str) -> str:
    out = text
    # Longest fragments first to avoid partial clobbering.
    for en in sorted(_HI, key=len, reverse=True):
        out = out.replace(en, _HI[en])
    return out


def _has_devanagari(text: str) -> bool:
    return any("ऀ" <= ch <= "ॿ" for ch in text)


# Scripts we require to be *native*, not romanized, plus a "must contain a char
# in this range" test to reject Latin-transliterated output from the LLM.
_NATIVE_SCRIPT = {"hi": ("Devanagari (देवनागरी)", _has_devanagari)}


def _prompt(lang_name: str, script_hint: str) -> str:
    base = (
        f"You are a professional translator. Translate the user's public-health "
        f"advisory into natural, simple, respectful {lang_name}. Keep it concise. "
        f"Preserve AQI numbers and the CPCB band name. Output ONLY the translation, "
        f"no notes, no transliteration guide."
    )
    if script_hint:
        base += (f" CRITICAL: write the translation in {script_hint} script ONLY — "
                 f"never romanized/Latin letters.")
    return base


def translate(text: str, target_lang: str, *, source_lang: str = "en") -> str:
    """Translate `text` into `target_lang`. English is a no-op.

    Groq first (natural, context-aware). For languages with a required native
    script (e.g. Hindi -> Devanagari), the output is script-checked; if the model
    romanized it, we retry once on the stronger model, then fall back to the phrase
    table. Any total failure returns the source text unchanged.
    """
    if not text or target_lang == source_lang or target_lang == "en":
        return text

    lang_name = {"hi": "Hindi"}.get(target_lang, target_lang)
    script_name, checker = _NATIVE_SCRIPT.get(target_lang, ("", None))
    system = _prompt(lang_name, script_name)

    # Attempt 1: fast model. Attempt 2 (only if script check fails): strong model.
    for fast in (True, False):
        out = llm.chat(
            [{"role": "system", "content": system},
             {"role": "user", "content": text}],
            fast=fast, temperature=0.2, max_tokens=700,
        )
        if out and (checker is None or checker(out)):
            return out
        if checker is None:  # no script constraint -> first good answer wins
            if out:
                return out
            break

    # LLM unavailable or refused the script -> deterministic phrase table.
    if target_lang == "hi":
        return _table_translate(text)
    return text

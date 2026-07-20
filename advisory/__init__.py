"""Feature 4 — Citizen Health Risk Advisory (multilingual).

Owner: Bind (+ Suhani). Turns the ward/cell-level AQI forecast + source
attribution (Features 1 & 2) into a persona-specific, health-band-cited,
multilingual advisory — and a conversational citizen bot.

Design rules (from IMPLEMENTATION_PLAN.md):
  - Mock-first: runs with zero external data (RULE 1/2).
  - Zero-key: every LLM call degrades to a deterministic template (RULE 3).
  - Honest: guidance, not diagnosis; low false-positive tone.
"""

__all__ = [
    "health_bands",
    "personas",
    "data",
    "llm",
    "translate",
    "advisory_engine",
    "chat",
]

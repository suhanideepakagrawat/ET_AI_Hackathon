---
target: frontend/advisory_demo.html
total_score: 33
p0_count: 0
p1_count: 0
timestamp: 2026-07-20T20-35-06Z
slug: frontend-advisory-demo-html
---
Method: dual-agent (A: aa18ee8ec3b9da094 · B: a9e00fbe8b8616125)

# Re-critique — frontend/advisory_demo.html (post-polish)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Strong states; loadWards was outside try/catch (fixed post-review) |
| 2 | Match System / Real World | 4 | Bulletin register; plain speech; CPCB vocabulary |
| 3 | User Control and Freedom | 3 | Pause/stop/mute; chip taps overwrite typed drafts |
| 4 | Consistency and Standards | 3 | Coherent; ⏸/⏹ glyphs clashed with SVG (fixed post-review) |
| 5 | Error Prevention | 3 | Re-ask fallback, 6s TTS bail; draft-clobber remains |
| 6 | Recognition Rather Than Recall | 4 | Tappable options everywhere; card restates full context |
| 7 | Flexibility and Efficiency | 4 | Type / tap / speak; bilingual intent matching |
| 8 | Aesthetic and Minimalist Design | 3 | Clean flat bulletin; deferred chip overload still costs |
| 9 | Error Recovery | 3 | Bilingual citizen error copy; showSources silent-fail (fixed post-review) |
| 10 | Help and Documentation | 3 | Capability list + help intent + first-class sources |
| **Total** | | **33/40** | **Good — production-viable** (prev: 28/40) |

## Resolution of prior findings

- **P0 contrast (white on light bands): RESOLVED** — BANDTEXT map, ink on Good/Sat/Moderate/Poor, white only on Very Poor/Severe; applied to ball, badges, chips, compare bars.
- **P0 keyboard/SR-dead sources & voice: RESOLVED** — real buttons throughout, aria-expanded/pressed/live/status/img, global 2px teal :focus-visible (verified with real Tab), full prefers-reduced-motion block.
- **P1 visual register: RESOLVED** (emoji remnants on Pause/Stop/📖 fixed post-review; act-tag pictograms retained deliberately as low-literacy comprehension aids paired with text).
- **P1 developer error string: RESOLVED** — bilingual citizen copy at every failure path.
- **P2 choice overload: DEFERRED** (user-scoped out).
- **P3 CPCB drift + muted contrast: RESOLVED** — exact standard hexes; muted #47585c (~7:1).

## Deterministic scan
detect.mjs: **52 findings → 1**. Side-tab warning gone. The sole remaining `flat-type-hierarchy` (11/12.5/14/16/20px, 1.8:1) is **explicitly endorsed by DESIGN.md's fixed product-register scale** — classified false positive. Screenshots confirm: no side-stripes, no eyebrows, no white-on-light text, single-teal + CPCB palette.

## AI slop verdict
**No longer reads as AI-made.** All absolute bans clear. Faint WhatsApp ancestry only in retained pictographic act tags (deliberate).

## Post-review fixes applied in-session
Hindi act tags + Pause/Resume labels; 📖 removed from source buttons; loadWards/showSources error feedback; document.lang switches with UI language.

## Remaining (backlog)
- [P2] Server-side provenance line + compare tab still English-first in Hindi mode.
- [P3] Chip tap overwrites a typed draft.
- [P2, deferred] Choice count at area/follow-up steps.

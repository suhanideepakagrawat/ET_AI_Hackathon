---
target: frontend/advisory_demo.html
total_score: 28
p0_count: 2
p1_count: 2
timestamp: 2026-07-20T19-43-07Z
slug: frontend-advisory-demo-html
---
Method: dual-agent (A: a2096e2158749edce · B: ae06b2a9e477561ed)

# Critique — frontend/advisory_demo.html (VayuMitra citizen advisory)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Typing dots, online dot, voice bar, mic pulse are solid; no chip-tap latency feedback. |
| 2 | Match System / Real World | 4 | Namaste, plain neighborly language, real Hindi parity; only "GRAP Stage II" jargon leaks. |
| 3 | User Control and Freedom | 3 | Change area/person + voice pause/stop; but no "back," and language switch silently re-renders a new card. |
| 4 | Consistency and Standards | 1 | Systematically contradicts its OWN design system (beige, neon green, side-stripe, emoji-UI) + drifts CPCB hexes. |
| 5 | Error Prevention | 3 | Re-ask on unmatched area; fragile free-text area match (tok.length>4). |
| 6 | Recognition Rather Than Recall | 4 | Chips for area/persona/follow-ups; selected context echoed in the card. |
| 7 | Flexibility and Efficiency | 3 | Chips + free text + voice + intent parsing; power hidden. |
| 8 | Aesthetic and Minimalist Design | 2 | Emoji density + gradients + WhatsApp chrome compete with the data. |
| 9 | Error Recovery | 2 | API-down message shows a citizen a Python command (uvicorn ...). |
| 10 | Help and Documentation | 3 | Feature list on greet + "what can you do" intent. |
| **Total** | | **28/40** | **Good (bottom of band)** |

## Anti-Patterns Verdict

**Does it look AI-generated? Yes — and it trips three of the four PRODUCT.md anti-references at once.** This is, almost line-for-line, the WhatsApp-clone first draft that DESIGN.md explicitly says "should be pulled toward credible."

**LLM assessment:** warm-beige body `--bg:#e9e2db` (the exact retired AI-SaaS hex), neon `--accent:#25D366` + green `--out:#d6f5c6` bubbles, emoji AS the affordance system (send ➤, mic 🎤, tabs, 📍👤📖 labels), WhatsApp chrome (gradient avatar + online pulse, tailed bubbles, typing dots). Absolute-ban audit: colored **side-stripe VIOLATED** (`.card border-left:6px`, recolored per band); decorative gradient fills on avatar/bubble; gradient-text/glassmorphism/hero-metric/eyebrows all clean.

**Deterministic scan:** `detect.mjs` exit 2, **52 findings** — `side-tab` ×1 (L65), `single-font` ×1 (L14), `design-system-color` ×22, `design-system-font-size` ×19, `design-system-radius` ×9.
- Agreement: the **side-tab (L65)** matches the LLM's banned side-stripe — highest-confidence finding.
- Detector caught, LLM contextualized: the 50 color/size/radius hits are "outside DESIGN.md" because the file predates the DESIGN.md just written — evidence it needs migration, not 50 separate bugs.
- False positives: `single-font` is a **false positive** — DESIGN.md's "One Family Rule" deliberately uses one system sans for the product register. Six `rgba(0,0,0,.x)` color hits are box-shadow alphas, not palette drift. `#25D366` and the CPCB band colors are intentional tokens (detector labels them advisory/may-be-legitimate).

**Visual overlays:** no live overlay injected (the page needs the backend API to render); evidence is the static scan + the three rendered screenshots, which visually confirm the crimson left side-stripe, the single-font uniformity, and the green/red/orange/yellow palette.

## Overall Impression

The *brain* is genuinely on-brief — cited sources, personal + multilingual advice, working voice — but the *skin* is the exact toy aesthetic PRODUCT.md and DESIGN.md were written to reject. The single biggest opportunity: this is a **CSS-layer reskin**, not a rebuild. The conversation logic can stay untouched while the surface moves from WhatsApp-toy to Public-Health-Bulletin — and two accessibility P0s must be fixed for the product's own pillars (Sources, Voice) to be usable by the citizens it centers.

## What's Working

1. **Source citation is a real first-class element, not fine print** — the inline "Based on: CPCB · SAFAR · WHO · GRAP" expands to titled entries with publisher + year + link. Directly realizes "trust is the product."
2. **Severity stated three ways + genuinely personal** — the card carries number (356) + band name + color, plus persona, dominant source, and confidence. "Personal, not general" and "act, don't just inform" both honored.
3. **Multilingual + voice are real, not cosmetic** — full EN/Hindi parity into the advisory body, chips, placeholder, and TTS; server-neural voice with browser fallback and working pause/resume/stop.

## Priority Issues

**[P0] Legible Band Rule broken — severity unreadable on light bands.** `.aqiball`/`.badge`/`.chip .b` hardcode `color:#fff` on every band; Satisfactory `#84cf33` and Moderate render white numbers at ~2.5:1 (visible on "196"/"218" in screenshot 01).
- *Why it matters:* the number IS the message and it fails for the low-vision / bright-outdoor citizens PRODUCT centers; also violates a named absolute ban.
- *Fix:* ink `#0e1a1c` on good/satisfactory/moderate, white only on poor/very-poor/severe — one conditional in `renderCard`.
- *Suggested command:* /impeccable audit

**[P0] Signature interactions are keyboard/screen-reader dead; no focus states.** Source-expand is `<div onclick>`, every speaker is `<span onclick>` — not focusable/operable. `input{outline:none}` and no `:focus-visible` anywhere, despite DESIGN.md's "never remove the focus ring." Emoji-only controls lack `aria-label`; no `prefers-reduced-motion` guard.
- *Why it matters:* the Sam persona is locked out of the two product pillars — Sources (trust) and Voice.
- *Fix:* real `<button>`s with aria-labels, a visible 2px `#0a746a` focus ring, reduced-motion fallbacks.
- *Suggested command:* /impeccable audit

**[P1] Whole visual register violates the design system (the AI-slop/toy verdict).** Beige, neon green + green bubbles, WhatsApp chrome, emoji-as-affordance, colored side-stripe, decorative gradients — all named bans.
- *Why it matters:* shipping the exact draft DESIGN.md says to move away from undercuts the trust the numbers depend on.
- *Fix:* reskin to the Bulletin palette (surface `#f2f5f5`, single-teal voice, bubble-out `#dbeeeb`, 1px hairline borders, no side-stripe), replace emoji controls with labeled/iconed buttons, delete gradients. CSS-layer only; logic untouched.
- *Suggested command:* /impeccable polish

**[P1] Developer error string shown to citizens.** The API-down state renders "Start it: `uvicorn backend.advisory_api:app --port 8000`" to end users.
- *Why it matters:* a parent hitting a hiccup sees a Python command — instant credibility loss.
- *Fix:* citizen copy ("We can't reach the service right now — please try again in a moment"); log technical detail to console only.
- *Suggested command:* /impeccable clarify

**[P2] Choice overload at both decision points.** 7 area chips + 6 follow-up chips exceed the ≤4 rule; the greeting stacks a 7-item feature list onto the area question.
- *Why it matters:* moderate cognitive load on the first, most fragile screen for a first-timer / low-literacy user.
- *Fix:* top-3 areas + "More / type your area"; 3–4 context-ranked follow-ups; shorten or defer the feature list.
- *Suggested command:* /impeccable layout

**[P3] CPCB palette drift + muted contrast.** Moderate `#c9a800` (spec `#ffde33`) and Poor `#ff8c1a` (spec `#ff9933`) recolor a public standard; muted `#63727a` (spec `#47585c`) puts timestamps near ~4:1, under AA.
- *Fix:* restore exact CPCB hexes; use `#47585c` for muted.
- *Suggested command:* /impeccable polish

## Persona Red Flags

**Casey (distracted, one-handed mobile):** language toggle, autoplay 🔊, and both tabs sit at the *top* of a tall phone, unreachable by thumb; only send/mic are in the thumb zone. Chips are ~30px tall with 6px gaps — sub-44px targets packed close, so "Change area" vs "Change person" mis-taps are likely.

**Jordan (confused first-timer):** hit with a 7-item feature list + area question + 7 chips on the first screen. "Other area" silently just focuses the input with no prompt change. Three ambiguous emoji audio affordances (header 🔊, per-message 🔊, mic 🎤). "GRAP Stage II" unexplained.

**Sam (screen-reader / keyboard / low-vision):** Source-expand and speaker are non-focusable `<div>`/`<span>` onclick — sources list and voice playback unreachable; no focus ring anywhere; emoji labels read as "loudspeaker / rightwards arrow"; AQI ball white number fails contrast on light bands; muted meta misses 4.5:1; no reduced-motion (pulsing mic + popping bubbles fire regardless — vestibular risk).

**Kamala, 68, low-literacy Hindi reader relying on voice (project persona):** the voice she needs is opt-in and hidden — autoplay defaults off behind a top-corner 🔊 emoji; nothing speaks until she finds the tiny per-message 🔊. Advice arrives as a dense 10-line Hindi paragraph with no spoken-first / summary-first path. Onboarding expects her to read tiny AQI numbers or type an area. Voice-first — the reason she's in scope — is not the default journey.

## Minor Observations

- Autoplay defaults off, yet the mic auto-enables it on a result — inconsistent audio behavior.
- A language switch re-renders a fresh advisory card, duplicating content and growing the transcript.
- `title` attributes used where `aria-label` is needed.
- Compare-tab avg badge uses ad-hoc `>200`/`>100` thresholds instead of the full CPCB band scale.
- Desktop shows a dark letterbox around a 470px "phone" — reads as an emulator.
- Confidence/source percentages are strong evidence but unexplained to lay users.

## Questions to Consider

1. DESIGN.md already says this WhatsApp draft "should be pulled toward credible" — what stops you reskinning it to the Bulletin palette tonight without touching a line of conversation logic, and what are you protecting by keeping the green?
2. For a low-literacy elderly user who can't read a 10-line Hindi paragraph, why is voice opt-in and buried as an emoji — what breaks if VayuMitra's *first act* is to speak, and text becomes the fallback?
3. When a parent sees a wall of red for their child, what on screen says "this is manageable, here's exactly what keeps them safe today" — and if the answer is "the last sentence of a paragraph," is that reassurance or a disclaimer?

---
name: PS5 Urban Air Quality Intelligence
description: Trustworthy civic-tech for hyperlocal air-quality advice and enforcement — a public-health bulletin you act on.
colors:
  primary: "#075e54"
  primary-strong: "#0a746a"
  primary-hover: "#064a42"
  ink: "#0e1a1c"
  ink-muted: "#47585c"
  surface: "#f2f5f5"
  panel: "#ffffff"
  panel-2: "#e9eeee"
  line: "#d6dedd"
  bubble-out: "#dbeeeb"
  aqi-good: "#009966"
  aqi-satisfactory: "#84cf33"
  aqi-moderate: "#ffde33"
  aqi-poor: "#ff9933"
  aqi-very-poor: "#cc0033"
  aqi-severe: "#7e0023"
typography:
  title:
    fontFamily: "system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "normal"
  body:
    fontFamily: "system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.005em"
  data:
    fontFamily: "system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.01em"
    fontFeature: "tabular-nums"
  caption:
    fontFamily: "system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "11px"
    fontWeight: 400
    lineHeight: 1.35
    letterSpacing: "normal"
rounded:
  sm: "8px"
  md: "12px"
  pill: "999px"
  bubble: "11px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.panel}"
    rounded: "{rounded.pill}"
    size: "45px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.panel}"
  chip:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.primary-strong}"
    rounded: "{rounded.pill}"
    padding: "7px 12px"
  chip-selected:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.panel}"
  card-advisory:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "12px"
  bubble-in:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.bubble}"
    padding: "9px 11px"
  bubble-out:
    backgroundColor: "{colors.bubble-out}"
    textColor: "{colors.ink}"
    rounded: "{rounded.bubble}"
    padding: "9px 11px"
  input-chat:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "11px 15px"
---

# Design System: PS5 Urban Air Quality Intelligence

## 1. Overview

**Creative North Star: "The Public Health Bulletin"**

This system carries the composure of an official air-quality advisory: the kind of notice a citizen reads and acts on, and an inspector cites in a decision. It is calm, legible, and sourced. Authority comes from restraint and evidence, not from decoration — the interface recedes so the number, the band, and the recommended action stand forward. The register is product: design serves the task of deciding *should I go out, and where should we act.*

Warmth lives in the language and the human framing, never in the chrome. The palette is a cool, quiet neutral with a single deep-teal voice; the only loud colors on screen are the CPCB AQI bands, and they are loud on purpose because severity is the message. This is deliberately positioned between two failures it rejects: the machine-made **generic AI-SaaS** look (cream backgrounds, gradient heroes, identical icon-cards) and the **boring corporate-government** portal (navy-and-grey, stock photos, unstyled tables). It also refuses the **childish/messaging-app** aesthetic its first draft leaned on — neon greens, emoji-as-UI — and any **flashy/gimmicky** motion.

**Key Characteristics:**
- Cool neutral surface, one deep-teal action voice, CPCB AQI bands as the only saturated color.
- One sans family, fixed rem scale, tabular figures for AQI numbers.
- Flat by default; depth is a response to state, never ambient decoration.
- Every severity is stated three ways — color, band name, number — never color alone.
- Evidence is visible: sources are cited inline, not hidden.

## 2. Colors: The Bulletin Palette

A cool, near-silent neutral field so the AQI bands and the teal voice carry all the meaning.

### Primary
- **Deep Civic Teal** (#075e54): The single brand voice — app header, primary buttons, the send/mic controls, selected chips. Deep enough to read as institutional, teal enough to read as air-and-water rather than corporate navy.
- **Active Teal** (#0a746a): The interactive brightening — links, focus rings, active/selected states. This is the only teal that signals "you can touch this."
- **Teal Pressed** (#064a42): Hover/pressed state on filled teal surfaces.

### Neutral
- **Ink** (#0e1a1c): Primary text and icons. Near-black with a faint cool cast; the body-copy default.
- **Muted Ink** (#47585c): Secondary text — timestamps, meta rows, source lines. Chosen to clear 4.5:1 on both surface and panel; never lighter.
- **Surface** (#f2f5f5): The page background. A cool off-white that replaces the old warm-beige body — the anti-AI-SaaS move.
- **Panel** (#ffffff): Cards, incoming chat bubbles, inputs. The raised reading layer.
- **Panel-2** (#e9eeee): The quiet second layer — control strips, unselected chip fills, toolbars.
- **Line** (#d6dedd): Hairline borders and dividers. 1px, never a colored stripe.
- **Bubble Out** (#dbeeeb): The citizen's own chat bubble — a whisper of teal tint that replaces the neon WhatsApp green.

### AQI Band Scale (signature — the authentic data palette)
The CPCB National AQI categories. These are not brand colors and must never be recolored for taste; they are a public standard.
- **Good** (#009966) · **Satisfactory** (#84cf33) · **Moderate** (#ffde33) · **Poor** (#ff9933) · **Very Poor** (#cc0033) · **Severe** (#7e0023).

### Named Rules
**The One Voice Rule.** Teal is the only chrome accent, and it appears only on interactive or brand elements — actions, selection, focus, header. It never decorates. On any screen the saturated non-AQI color stays a small share of the surface; its restraint is what makes the AQI bands read as urgent.

**The Legible Band Rule.** An AQI band fill carries **white text only on Very Poor and Severe**. Good, Satisfactory, Moderate, and Poor are too light for white — they carry **Ink text** (#0e1a1c; white on Poor #ff9933 is ~2.3:1 and fails). Severity is always paired with the band name and the number, so a color-blind reader loses nothing.

## 3. Typography

**Display / Body / Label / Data Font:** one system sans stack — `system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`.

**Character:** Deliberately one neutral, highly-legible family, no pairing. Product UIs earn trust through consistency, not contrast; a system stack also means zero webfont latency for citizens on slow mobile connections. Weight and size carry the whole hierarchy.

### Hierarchy
- **Title** (700, 1rem/16px, 1.25): Zone names, screen and card titles.
- **Body** (400–500, 0.875rem/14px, 1.5): Advisory messages, chat, most prose. Cap prose at 65–75ch.
- **Label** (600, 0.78rem/12.5px, +0.005em): Chips, badges, meta rows, buttons.
- **Data** (700, 1.25rem/20px, -0.01em, tabular-nums): The AQI number in the indicator. Tabular figures so digits don't jitter as values change.
- **Caption** (400, 0.69rem/11px, Muted Ink): Timestamps and source-provenance lines.

### Named Rules
**The One Family Rule.** No display face, no second sans, no mono. If a moment needs emphasis, change weight or size — never family.

## 4. Elevation

Flat by default. Surfaces sit on the cool neutral field separated by 1px Line borders and tonal contrast (Surface vs Panel), not by resting shadows. Depth is introduced only as a **response to state**: a card lifts slightly on hover, and true overlays (the voice bar, dropdowns, dialogs) float above the reading plane. No ambient card shadows, no glassmorphism.

### Shadow Vocabulary
- **Hover Lift** (`box-shadow: 0 2px 8px rgba(9,20,28,0.08)`): A card or chip on hover; pairs with a 1–2px `translateY`.
- **Overlay** (`box-shadow: 0 8px 28px rgba(9,20,28,0.18)`): Floating surfaces only — voice bar, menus, dialogs.

### Named Rules
**The Flat-By-Default Rule.** Surfaces are flat at rest. A shadow on screen means something changed state or something is floating. If a card has a resting shadow "for depth," delete it.

## 5. Components

### Buttons
- **Shape:** Icon actions are circles (`rounded.pill`, 45px); text buttons are pills.
- **Primary:** Deep Civic Teal fill (#075e54), Panel-white glyph/label. The send and mic controls, primary confirmations.
- **Hover / Focus:** Hover → Teal Pressed (#064a42) with a 1px lift. Focus-visible → 2px Active Teal (#0a746a) ring at 2px offset. Never remove the focus ring.
- **Recording state:** The mic uses a distinct alert fill while listening, with a slow pulse — the one place motion signals live state.

### Chips
- **Style:** Pill (`rounded.pill`). Default is Panel-white fill, Active-Teal label, 1.4px Active-Teal border — a quiet outline.
- **State:** Selected/active → Deep Civic Teal fill, white label. Hover on default → teal fill, white label. Area chips embed a small AQI-band badge (band-colored, text per the Legible Band Rule).

### Cards / Containers
- **Corner Style:** `rounded.md` (12px).
- **Background:** Panel-white on the Surface field.
- **Border:** Full 1px Line border on all four sides.
- **Shadow Strategy:** None at rest (see Elevation); Hover Lift on interactive cards only.
- **Severity:** Carried by the AQI indicator and a band badge inside the card — never by a colored side-stripe.
- **Internal Padding:** `spacing.md` (12px).

### Inputs / Fields
- **Style:** Pill (`rounded.pill`), Panel-white, 1px Line border, Ink text.
- **Focus:** Border shifts to Active Teal with a 2px teal ring. Placeholder uses Muted Ink (clears 4.5:1), never a pale gray.

### Navigation
- **Style:** A flat top app-bar in Deep Civic Teal with white title and status; tabs below it use a white/teal active underline. Active tab → white label + 3px Active-Teal underline; inactive → translucent white label. Mobile-first single column throughout.

### AQI Indicator (signature component)
A filled circle showing the AQI number (Data type) over a smaller "AQI" label, background = the band color, text color per the Legible Band Rule. It is the primary severity carrier — the reason cards need no colored stripe. Always sits beside the band name so severity is legible without color.

### Source Citation (signature component)
An inline, tappable "Based on: CPCB · SAFAR · WHO · GRAP" line that expands to a list of authorities (title, publisher, year, link). Flat, Muted-Ink, hairline-separated. Evidence is a first-class UI element, not fine print.

## 6. Do's and Don'ts

### Do:
- **Do** ground the page in cool neutrals — Surface #f2f5f5 with Panel-white cards and 1px Line borders.
- **Do** carry AQI severity three ways at once: the band color on the indicator, the band name, and the number. Use Ink text on Good/Satisfactory/Moderate fills.
- **Do** keep Deep Civic Teal as the single action voice; accent = actions, selection, focus only.
- **Do** cite every number to its authority inline (CPCB / SAFAR / WHO / GRAP).
- **Do** use one system sans at a fixed rem scale with tabular figures for data.
- **Do** keep motion to state feedback — 150–250ms, ease-out — with a `prefers-reduced-motion` fallback.

### Don't:
- **Don't** use warm cream/sand/beige body backgrounds (the retired #e9e2db family) — that's the generic AI-SaaS tell.
- **Don't** use neon/candy greens (#25d366) or WhatsApp-style messaging chrome; this is a public-health service, not a chat toy.
- **Don't** use emoji as load-bearing UI or icons; keep them to sparse persona/domain accents, never the affordance system.
- **Don't** use side-stripe borders — `border-left`/`border-right` greater than 1px as a colored accent — on cards, callouts, or list items. The AQI indicator carries severity; the border stays a full 1px hairline.
- **Don't** put white text on light AQI bands (Good, Satisfactory, Moderate). It fails contrast.
- **Don't** ship the boring corporate-government look: navy-and-grey, stock photos, clip-art icons, walls of unstyled tables.
- **Don't** reach for gradient text, glassmorphism-by-default, hero-metric templates, identical icon-card grids, or tiny uppercase tracked eyebrows.
- **Don't** add decorative or gimmicky motion (neon glow, orchestrated page-load, elastic bounce). Motion conveys state, nothing else.

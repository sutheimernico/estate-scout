# UI redesign, October 2026

## Verdict on the old UI

A dark, 820 px wide column of gray cards: six calculator forms stacked, one table row per object,
raw tool output in chat bubbles. Nothing in it said "real estate" or "finance", and the width of a
desktop screen was unused.

## Concept: "Zeichenblatt" (the drawing sheet)

estate-scout is a tool that turns a purchase into dimensions: price, rate, Restschuld, yield. The
visual world of that is the German building drawing and the Liegenschaftskarte: tracing paper,
black ink, dimension lines with 45-degree end ticks (Maßketten), one survey-red for what matters.
So the app is a drawing sheet. Every result is a *dimensioned* number: the headline figure sits on
a dimension line, the Restschuld curve is drawn like a section with its Zinsbindung marked as a
dimension, the yield is read from a ruler, the score is a gauge on a scale. Objects get three
small line drawings (Wohnung, Haus, Grundstück) instead of a generic icon set.

**Where the boldness is spent:** the Rechner result, a single very large condensed number on a
dimension line, with the curve drawing itself beneath it. Everything else stays quiet.

**Counter-check (would I land here for any other real-estate tool?):** the obvious answer is
blueprint blue on dark, or cream + serif + terracotta. Both are rejected: the first is the
default "Immobilien" stock look, the second is the AI-default second wave named in the rubric.
This one is a cool, greenish tracing-paper grey with blue-black ink and a vermilion that is
taken from the Flurkarte, where buildings are drawn in red. It does not fit a bakery or a trading
dashboard.

## Tokens

| Token | Value | Role |
| --- | --- | --- |
| `--paper` | `#E7EBE6` | page, "Pauspapier" (cool grey-green, not cream) |
| `--sheet` | `#F6F7F3` | working surfaces, "Zeichenblatt" |
| `--ink` | `#142029` | text, primary buttons, curves ("Tusche", blue-black, not `#0B0B0B`) |
| `--ink-2` | `#4A5A63` | secondary text (5.9:1 on paper) |
| `--rule` / `--rule-strong` | `#C5CCC5` / `#9AA59F` | hairlines, dimension lines |
| `--red` | `#C0301C` | "Katasterrot": interest, Zinsbindung marker, errors, the active tick |
| `--green` | `#3E6B4F` | "Flurgrün": Tilgung, equity, good score |
| `--ochre` | `#8A5E08` | warnings, partial data |

Contrast (AA): ink on paper 13.7, ink-2 on sheet 6.7, red on sheet 5.3, green on sheet 5.7.
Light only. No gradients, no glow, no glass, no shadows beyond one hairline lift on drawers.

## Type

Barlow (text) and Barlow Semi Condensed (numbers, headings), self-hosted via `@fontsource`,
Latin subset only. Barlow descends from the signage lettering of road and rail; it is the
closest free relative of the DIN 1451 Normschrift that German technical drawings are lettered
in, so it is chosen from the subject, not from the usual list. The condensed cut gives the hero
figures their drawing-sheet proportions; `font-variant-numeric: tabular-nums` keeps count-ups
from jittering. No monospace for labels (only for the copyable shell commands), no
all-caps-tracked eyebrows, no italics for emphasis.

## Layout

- **Rechner:** three columns at 1440 (calculator list | inputs | result), two at 820 (chips +
  inputs | result), stacked at 390 (calculator chips, inputs, result). Live recalculation on
  input, 350 ms debounce, previous result stays visible (dimmed) while the next one loads.
- **Chat:** conversation column plus a "Rechenspur" side column (every tool call of the
  session with inputs) from 1100 px; on narrower screens the trace is under each answer.
  Answers carry the same result view as the Rechner, with a stamp "Zahl stammt aus Werkzeug
  `annuity`". Waiting state with elapsed time and cancel; errors 424/503/504/offline are states
  with a fix (copyable command), not red text.
- **Objekte:** responsive tile grid (1 / 2 / 3 columns), score gauge and a four-pip data-coverage
  indicator on each tile, the example object with its own badge, capture form and details as a
  side sheet (bottom sheet at 390).

## Motion

150-400 ms, transform and opacity (plus stroke-dashoffset for the two draw-ins: curve and
gauge). Tab panes slide/fade in, tiles and facts stagger in, hero numbers count up, the curve
draws, the gauge sweeps, buttons press (scale .98), sheets slide. One helper (`motion.ts`)
decides whether to animate (`prefers-reduced-motion`, no `matchMedia` in tests), and a CSS
class `.reveal` with `--i` index does the staggering. No motion library: nothing here needs
spring physics or layout animation, and the helper is ~40 lines.

## Dependencies

`@fontsource/barlow`, `@fontsource/barlow-semi-condensed` (fonts, bundled, no CDN: the app
must run offline). Nothing else.

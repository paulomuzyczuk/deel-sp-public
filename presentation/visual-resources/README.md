# Deel visual resources

Brand assets and a validated chart palette for the case-study deck.

**Sources**
- Rebrand announcement: <https://www.deel.com/blog/weve-got-a-new-look/> — logos,
  imagery, typeface name, palette rationale.
- Live design tokens: CSS custom properties served from
  `https://website-media.deel.com/_next/static/css/*.css` (fetched 2026-08-07) —
  every hex code below is copied verbatim from Deel's own tokens, **not** sampled
  by eye from a screenshot. Token names (`acai`, `blueberry`, `cornbread`,
  `latte`) are Deel's own naming.

> These are Deel's trademarks and copyrighted assets, downloaded from Deel's
> public site for a Deel hiring case study. Fine for this deck; not for
> redistribution or any other use.

---

## Contents

```
visual-resources/
├── logos/
│   ├── deel-logo-black-transparent.png   4432×2428, alpha — primary wordmark
│   ├── deel-logo-latte-on-dark.png       4432×2428, alpha — knock-out for dark slides
│   ├── deel-lettermark-black.png          459×423,  alpha — "d." mark, slide corners
│   └── deel-logo.webp                    1400×787  — wordmark as shown in the blog post
└── palette/
    ├── deel_palette.py                   all tokens as Python dicts + chart palettes
    ├── deel.mplstyle                     matplotlib style for analysis/figures/
    ├── deel-palette-swatches.png         printable swatch sheet
    └── make_assets.py                    regenerates the swatch sheet + inverted logo
```

Regenerate derived assets: `.venv/bin/python visual-resources/palette/make_assets.py`

---

## Colour

Deel's three core hues map to a work cycle — yellow is bright morning, blue is
mid-day sky, purple is afterglow.

| Role | Deel name | Hex | Token |
|---|---|---|---|
| Purple | Acai | `#5938B7` | `--color-core-acai` |
| Blue | Blueberry | `#00499D` | `--color-core-blue-berry` |
| Yellow | Cornbread | `#FFCF25` | `--color-core-cornbread` |

Backgrounds are **warm off-white, not white** — this is the single most
recognisable thing about the brand. Default page surface is `#FFFBF4`
(`latte-25`); cards and highlights use `#FAF4EE` (`latte-125`). Dark sections use
`#201547` (dark purple) or `#1B1B1B`. Body ink is `#141414`, secondary text
`#1B1B1B` at 85% alpha.

Full ramps (purple 25→950, blue 50→825, cornbread, green, red, neutral) are in
`palette/deel_palette.py` and rendered in `palette/deel-palette-swatches.png`.

### Chart palette

Deel's brand ramps are tuned for web surfaces, not for encoding data, so the
categorical set below was **derived** from them and then machine-validated
against surface `#FFFBF4` — lightness band, chroma floor, colour-vision-deficiency
separation and normal-vision separation all pass (worst adjacent pair ΔE 14.1
deutan / 19.4 normal).

Assign in fixed order **by entity**, never cycled, never by rank:

| # | Hex | Origin |
|---|---|---|
| 1 | `#5938B7` | Acai — Deel core purple |
| 2 | `#2187CF` | blue-600 (lighter than Blueberry, which is too dark to sit next to Acai) |
| 3 | `#C98A00` | Cornbread darkened — `#FFCF25` itself is far too light to carry a data mark |
| 4 | `#A98DF6` | purple-525 |
| 5 | `#15740F` | green-675 — only where no good/bad meaning is implied |

Two caveats that carry real obligations:

- **Slots 3 and 4 fall below 3:1 contrast** on the latte surface (2.86:1 and
  2.60:1). Any chart using them must carry visible direct labels or an
  accompanying table — the fill alone is not legible enough to stand on its own.
- **Beyond 5 series, do not invent a 6th hue.** The dataset has 7 teams; for a
  7-way comparison use small multiples, or keep the top 4–5 and fold the rest
  into "Other". Adding hues past this set breaks CVD separation (verified —
  a 6-slot attempt failed at ΔE 3.9 deutan).

Magnitude (sequential) uses Deel's own acai ramp light→dark. Polarity
(diverging) uses cornbread ← neutral grey → acai. `#15740F` / `#FFCF25` /
`#F95250` are reserved as good / warning / critical and should not double as
series colours.

**Dark backgrounds:** Deel's tints are low-chroma pastels that fail separation
against `#201547`. No validated dark-mode chart palette is provided — keep the
deck's chart slides on the light latte surface.

---

## Typography

The brand typeface is **Bagoss** — Bagoss Standard, Condensed and Extended, by
Daniel Quisek at [Displaay Type Foundry](https://displaay.net/typeface/bagoss)
(Prague). Characterful grotesque: large x-height, diagonal terminals, a tiny
single-edge serif, moderate stroke contrast.

**Bagoss is commercially licensed and is deliberately not included in this repo.**
Deel's own stylesheet declares `Inter` alongside the three Bagoss families, so:

- **Use Inter** for the deck — free, and genuinely part of Deel's stack.
- If you want closer to Bagoss's display personality for titles, *Archivo* or
  *Space Grotesk* are the nearest free approximations. Don't mix more than two.

Headline style in Deel's own materials: tight leading, sentence case, heavy
weight, left-aligned, often with individual lines highlighted in a latte or
purple block behind the text — a cheap and very on-brand device for takeaway
slide titles.

---

## Visual language

From the rebrand post: "chunky" illustration shapes, abstract background shapes,
a grain/stipple texture, and design references to cave paintings, cuneiform,
Matisse and Lygia Clark.

Practical rules for the deck:

- Warm off-white background everywhere; reserve full-bleed purple or dark-purple
  for section dividers.
- Flat two-to-three colour illustration, no gradients, no drop shadows.
- Large flat colour blocks, generous margins, left-aligned text.
- Deel's own materials draw charts as flat cornbread and acai bars on latte.
  Worth matching.

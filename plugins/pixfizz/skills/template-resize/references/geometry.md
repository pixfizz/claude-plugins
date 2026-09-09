# Geometry: spreads, grids, transforms and gotchas

## Spread arithmetic

```
Spread trim  (finished, after cutting) = (2W - bleed) x (H - bleed)   <- NOT the XML value
Output dims  (trim + bleed both sides) = (2W)         x (H)           <- THIS is the XML value
```

The XML `width`/`height` are the finished production file size, bleed included.
`bleed` is a virtual guide only; it is never added on top. Use the "Output
Dimensions" columns of the supplier spec, never "Spread (after cutting)" —
building from trim figures makes every album 1/8" undersized in both directions.

**The marketing size is not the physical size.** A finished "8x8" page is
7.9375 x 7.875 — wider than tall. Layouts designed on a true square are 1/16" out.

## Verified spread sizes

| Book | Page (in) | Spread XML (in) | Spread (mm) | Aspect |
|---|---|---|---|---|
| 4x6 | 4 x 6 | 8 x 6 | 203.2 x 152.4 | 1.333:1 |
| 5x5 | 5 x 5 | 10 x 5 | 254 x 127 | 2:1 |
| 5x7 | 5 x 7 | 10 x 7 | 254 x 177.8 | 1.429:1 |
| 8x8 | 8 x 8 | 16 x 8 | 406.4 x 203.2 | 2:1 |
| 10x10 | 10 x 10 | 20 x 10 | 508 x 254 | 2:1 |
| 12x12 | 12 x 12 | 24 x 12 | 609.6 x 304.8 | 2:1 |
| 14x14 | 14 x 14 | 28 x 14 | 711.2 x 355.6 | 2:1 |

**Every square-page album is a 2:1 spread**, so all square→square derivations are a
single uniform factor off one master. Non-square pages each change the aspect.

Factors used in production so far: 5x5→8x8 = 1.6, 8x8→10x10 = 1.25,
10x10→12x12 = 1.2, 12x12→14x14 = 7/6, 4x6→5x7 = margin rule at 1.16667.

## Detecting the authored grid

The declared `<page>` canvas is unreliable **in both directions**:

- observed stale — holding the cover size while frames were on the spread grid
- observed prematurely correct — already the target size while frames were still
  on the source grid, presumably written by a theme-copy that did not touch artwork

Two independent detectors, which must agree:

1. **Full bleed** — a lone frame anchored at `0,0` gives the grid directly.
2. **Margin symmetry** — the mode of `min_edge + max_extent` across all layouts.
   Centred layouts vote for the true size; anchored layouts are the outliers and
   lose. In practice the height vote is unanimous and the width vote a clear
   plurality.

## Transform rules

### Uniform (aspect unchanged) — the solved case

Multiply `x`, `y`, `width`, `height` by the factor. Leave `left`/`top`. Set the
page absolutely, never by scaling the old value. Preserve `id`, `number`, `tags`,
`name`, `usage_flags` and order.

Margins scale with everything else — a 6.35 mm (0.25") margin at 1.6x becomes
10.16 mm (0.4"), still outside the safe line, and the layouts stay visually
identical to their picker thumbnails. Pinning margins back is a redesign, not a
rescale.

### Aspect change — pick which cost to pay

> You cannot simultaneously preserve frame shapes, preserve grid adjacency, and
> fill the page when the page aspect changes. A tight tiling that keeps every
> frame's aspect can only be scaled uniformly, and a uniform scale cannot fill a
> page of different aspect.

| Rule | Cost |
|---|---|
| `stretch` | **shapes distort** by `fx/fy` — squares stop being square |
| `fit` | **dead space** — 5x5→4x6 dropped coverage 65.8% → 45.8% |
| `cell` | **grid breaks** — adjacent frames drift into ragged gaps |
| `margin` | mild distortion, but margins stay in proportion and the page fills |

**`margin` is the default and the one confirmed against hand edits.** Scale all
four content-bbox margins by `min(fx, fy)`, then let frames fill what is left. It
reproduced 6 of 17 hand-corrected layouts exactly, and matched the horizontal
treatment on all 17.

`fit` was tried first on 4x6 and rejected in review: leaving a third of the page
empty was worse than distorting frames.

**Full-bleed frames always stay full bleed under every rule.** A frame covering
>=99% of the page anchored at the origin maps to `(0, 0, W', H')`.

**Re-centre rows.** Source layouts carry accumulated float drift — margins of
7.800 left against 7.339 right where equal was intended. Equalise them when the
two sides are within 0.75 mm; gutters are preserved and the whole row shifts.

### Band vocabulary — the override for aspect changes

The `margin` rule predicts the horizontal completely and the vertical about half
the time. The remainder is design judgement. In a reviewed 4x6 set, all 17 layouts
used only **four vertical bands**, every one a clean inch value:

| top / height / bottom (in) | layouts |
|---|---|
| 0 / 6.0 / 0 | full bleed |
| 0.2 / 5.6 / 0.2 | near-full-bleed |
| 1.0 / 4.0 / 1.0 | the default |
| 1.5 / 3.0 / 1.5 | rows of four or more, so frames do not become slivers |

So the vertical margin is the **one exposed parameter**. Emit the per-layout margin
table with the result and offer the vocabulary; overriding is then picking one of
four values rather than editing coordinates. Ask the user for the vocabulary when
converting to a new aspect — do not invent clean values.

## Numeric gotchas

- **Pixfizz emits inch→mm float noise.** Real values include `609.5999999999999`.
  Verify with a tolerance, never string equality.
- **Output rounding is load-bearing.** Format to 12 decimals then strip trailing
  zeros. Non-terminating factors such as 7/6 then land exactly: `609.6 x 7/6`
  becomes exactly `711.2`. Without it a full-bleed frame comes out at
  `711.19999999...` against a `711.2` page — a hairline white edge down the trim of
  every full-bleed spread. `verify_layouts.py` asserts edge landing for this reason.
- **Elements can be negative and overhang the page.** Cover artwork legitimately
  sits at negative `x` with widths exceeding the page. Handle negative offsets;
  only bounds-check interior spread layouts.

## Stale page sizes propagate

The same three theme-level stubs were wrong in every theme examined, having ridden
along through each clone:

| Template | Typically holds | Note |
|---|---|---|
| `preview` | 127 x 127 | 5x5-era |
| `spread` | 254 x 127 | 5x5-era, and collides on `number: 3` with `spread01` — may be dead |
| `cover` | 307.975 x 180.975 | 5x5-era |

**Never auto-fix `cover`.** The correct size depends on the album family — Leather
Layflat covers are never printed (`fulfillment="false"`), Fabric 8x8 is
19.35 x 10.188 in, Photographic 8x8 is 18.625 x 9.813 in. A wrong guess sends a
wrong-size PDF to the press, which is worse than leaving it stale. Report and let
the user decide. Because this propagates on every clone, suggest fixing it once at
the source rather than per-theme.

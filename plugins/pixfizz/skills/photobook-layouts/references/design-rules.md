# Design rules - what makes a layout set worth shipping

## The grid vocabulary

Derive these from the theme rather than importing a house style. On the 10x10
album seed they came out as:

| | mm | in | Used for |
|---|---|---|---|
| Gutter | 6.35 | 0.25 | every gap between frames, whole set |
| House margin | 22.225 | 0.875 | the default content inset |
| Narrow margin | 12.7 | 0.5 | near-full-bleed variants |
| Bleed | 0 | 0 | frames running to trim |

**One gutter for the whole set.** Mixed gutters read as a mistake, not variety.
Vary the margin instead - that is what makes a layout feel airy or full.

**Margins scale, they do not pin.** A 0.25 in gutter on a 10x10 becomes 0.3 in
on a 12x12 under a uniform rescale, and that is correct. Pinning it back is a
redesign.

## Coverage

The picker is grouped by photo count, so the set is judged per group, not in
total. Target six to eight per group across 1, 2, 3, 4 and 5+.

**Spread the 5+ group.** It is a catch-all with no upper bound, and filling it
with five dense grids wastes it. A good spread is 5, 6, 7, 8, 9, 10 and 12
frames, mixing a feature-plus-grid against plain grids.

**Roughly 70/30 aligned to asymmetric** unless the user asks otherwise. All
grids is dull. All scatter is unusable, and overlapping placeholders are almost
never wanted - `verify_layouts.py` warns on them.

**Never duplicate a shape already in the theme.** `fill_layouts.py` compares
frame geometry rounded to 0.01 mm and drops matches, reporting the count. Check
that report - a high number means the theme is fuller than the user thought.

## The archetype families

The library carries 45, nine per group, in five families:

| Family | Idea |
|---|---|
| **Full-bleed** | one or more frames to trim, gutter only |
| **Content grid** | `cols x rows` filling the content box at the house margin |
| **Centred band** | a block sized by cell aspect, centred in the content box |
| **Feature plus row** | one large frame and a row or grid of small ones |
| **Offset** | a frame anchored to one corner or bleeding off one edge |

## Adding an archetype

In `scripts/layout_library.py`:

```python
A(3, "Feature left, stack right",
  lambda p: [(p.m, p.m, p.cw * 0.6, p.ch)]
            + p.col(2, p.m + p.cw * 0.6 + p.g, p.m, p.cw * 0.4 - p.g, p.ch))
```

Rules, all of which the cross-page test enforces:

1. **Pure function of the `Page`.** Never hard-code a millimetre value that is
   not derived from `p.w p.h p.m p.n p.g` or a helper. A literal `139.7` is
   correct on a 10x10 and wrong everywhere else.
2. **Cap anything driven by width against the height.** `p.cw / 1.5` for a 3:2
   feature overflows a 2:1 spread and leaves a negative-height row beneath on a
   4x6. Use `p.lh(w, cap=p.ch * 0.65)`.
3. **Use `p.block(cols, rows, ratio)` for centred grids.** It drives from width
   when the block fits and from height when it does not, which is what keeps a
   3x2 of squares inside a wide spread.
4. **Group 1-4 must hold exactly that many frames.** Group 5 holds five or more.
5. **No overlaps** unless that genuinely is the design.

Test any addition across page shapes before shipping it:

```python
from pxgrid import Page
from layout_library import build
for w, h in [(254,254), (508,254), (203.2,152.4), (254,177.8), (152.4,203.2)]:
    p = Page(w, h)
    for g, n, fr in build(p):
        for (x, y, fw, fh) in fr:
            assert -1e-6 <= x and -1e-6 <= y and x+fw <= w+1e-6 and y+fh <= h+1e-6 \
                   and fw > 0 and fh > 0, (w, h, n, (x, y, fw, fh))
```

## Numeric rules

- **Format to 12 decimals then strip.** Load-bearing: without it a
  non-terminating division leaves a full-bleed frame at `253.99999999` against a
  `254` page - a hairline white edge down the trim of every full-bleed print,
  invisible on a proof sheet. `pxgrid.fmt()` does this and
  `verify_layouts.py` asserts edge landing.
- **Long decimals are not automatically drift.** Dividing a 209.55 mm content
  box into three gives `65.616666666667` legitimately. Drift is a value that is
  not a clean fraction of a clean number - `7.800` left against `7.339` right
  where equal was intended.
- **Pixfizz emits its own inch-to-mm float noise** (`609.5999999999999`,
  `130.174999999999`). Compare with a tolerance, never string equality, and do
  not "fix" it in layouts you were not asked to touch.

## Reference sets

When the user supplies screenshots of a competitor's or a reference picker,
read the arrangements off them and name the ones being reproduced. Do not copy a
proprietary set wholesale - take the arrangement idea, which is not protectable,
and rebuild it on this theme's own grid vocabulary.

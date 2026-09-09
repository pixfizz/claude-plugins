# Product families

The mechanism is identical across families — same export format, same YAML
surgery, same reference graph, same verification. What differs is a small set of
facts. Add a section here when a new family is handled for the first time.

## Books and albums — PROVEN

Six themes and one full template retargeted end to end, then a 5x7 layflat album
derived to five sizes (6x8, 8x6, 6x9, 8x10, 8x12).

- Page types: `preview`, `cover`, `first_page`, `spread01..03`, `last_page`, plus a
  stale `spread`
- Interior pages are **layflat spreads**: one page element is two physical pages
  side by side, with `<filter type="binding-layflat"/>` drawing the centre guide
- Frames cross the gutter freely, so no per-half logic is needed
- Layouts live in a separate theme (`Layouts <size>`, code `<size>-layouts`) and are
  referenced from the clean-named design theme (`<size>`, code `<size>`) by
  `layout_id`. **The clean-named theme is the one published to the collection.**
- Cover sets are often commented out of the definition entirely — for leather
  albums no cover artwork is produced at all. Check before touching cover geometry
- Every export seen has been image-only. `<text>` in a **layout** is still unproven
- **Gutters between frames are absolute.** Preserve them in mm; do not scale them
- Vertical bands may be clean fractions of page height rather than clean inch
  values. Check before assuming the band vocabulary is needed — when the bands are
  fractions, `margin` and a proportional rule agree on every target whose
  `min(fx, fy)` lands on `fy`

## Canvases and wall art — PROVEN

Three canvas products retargeted, including a 62-size range built from one seed.
The `<ipage>` question below is closed.

### A canvas is four numbers

Print area `W x H`, bleed `b`, mirror depth `m` where `m <= b`. The remainder
`b - m` prints white.

```
artboard = (W + 2b) x (H + 2b)
```

| layout | `<image>` size | `<image>` position | extra |
|---|---|---|---|
| `gallery` | `(W + 2m) x (H + 2m)` | `(b - m, b - m)` | — |
| `mirror`  | `(W + 2m) x (H + 2m)` | `(b - m, b - m)` | `borderwrap="m"` |
| `color`   | `W x H`               | `(b, b)`           | whole wrap takes the chosen colour |

`borderwrap` is the mirrored band measured **inward from the image element's own
edge**, in mm:

```
print area  =  image element  -  2 x borderwrap
```

Verified on three seeds: `15.5 - 2(1.75) = 12`, `17 - 2(2.5) = 12`, `12 - 2(2) = 8`.

**The mirror is not a fulfillment transformation.** `fulfillment_transformations`
is empty on every canvas seen. It lives entirely in the layout element.

**Consequence: canvases have no aspect-change cost.** One image element per layout
and no multi-frame grid, so the constraint in `geometry.md` — that frame shape,
grid adjacency and page fill cannot all survive an aspect change — does not apply.
Portrait to landscape is arithmetic. No band vocabulary is needed.

**Never invent the wrap depth.** Three labs, three conventions: 1.75 with no white
band, 2.00 with no white band, 3.00 with 2.5 mirrored and 0.5 white. A lab asked
about "wrap size" may answer with stretcher-bar thickness instead, which is a
different number. Ask, and ask specifically.

### `<ipage>` — DERIVED

```xml
<ipage crop="true" edit="true" template="cover" zoom="39.024390243902"
       left="-20.618556701031" top="0" width="84.666666666667" height="84.666666666667"
       x="21.166666666667" y="21.166666666667" shadow_opacity="0.3"
       shadow_ox="2.54" shadow_oy="2.54" shadow_stdev="2.54"/>
```

- `template="cover"` — a **by-name** reference to another template in the same theme
- `width` / `height` / `x` / `y` — the frame on the host page
- `shadow_*` — drop shadow in millimetres

```
cover(box, X)  =  max( box_w / X_w ,  box_h / X_h )

zoom  =  ( cover(box, print_area) / cover(box, page)  -  1 ) x 100
```

`crop="true"` means **cover, not fit**. At `zoom=0` the referenced page is scaled to
cover the box; `zoom` is the extra scale that makes the *print area* cover it
instead, pushing bleed and wrap outside to be cropped.

Confirmed to twelve decimals on two independent products:

| sample | box | page | print area | zoom |
|---|---|---|---|---|
| canvas 12x12, bleed 1.75 | square | 15.5 sq | 12 sq | `29.166666666667` |
| 5x7 layflat album cover | 84.667 sq | 307.975 x 180.975 | 257.175 x 130.175 | `39.024390243902` |

The album cover is the discriminating sample — box, page and print area all have
different aspects, and only the cover-over-cover form reproduces its stored value.
A fit-based reading gives 136.58; fit-of-print gives -29.6. That also resolves the
old `84.667 / 0.39024 = 216.96` dead end: the baseline was the cover-fit of the
whole page, not a dimension of the page itself.

**Do not use the simpler-looking `max` over axes of `page / print_area`.** It fits
both samples by coincidence — one is all-square, the other has a square box — and
diverges as soon as the box carries the print-area aspect and the page does not. On
a 16x20 it gives 37.5 where the answer is 30.

**`zoom` does not vary with box size.** Four ipages of four different box sizes in
one export carry the identical value.

**`left` / `top` are the pan offset for a cross-aspect box.** Their exact scale is
still underived and it does not block anything: build every box to the print-area
aspect and both stay `0`. An un-zoomed ipage — one showing the whole artboard —
takes the **page** aspect instead.

### Preview pages

Typical canvas theme: `canvas`, `preview-zoomx1.5`, `preview`, `preview-clean`,
`preview-full`, `preview-backup`. The `preview:` boolean on the template record says
which are live.

**Room-scene pages** composite the canvas onto a photographed wall. The box is
**hand-placed per variant** — the box-to-scene ratio differs between variants and
the vertical centres sit at different scene fractions, so it is not derived. On a
bleed-only change it must not move. On a size change, hold the wall scale
(`box_w / print_area_w`, constant per scene) and the box centre.

**Full-page pages** (`preview-clean`, `preview-full`) are product renders, not
scenes. Fit the aspect into the seed's window, centred. `preview-clean` takes the
**print-area** aspect. `preview-full`'s outer ipage takes the **page** aspect and
carries no zoom; its inner ipage is `outer x print_area / page`, recentred, with
zoom; the translucent `<shape>` tracks the outer box; the four `wrap` labels sit a
fixed inset inside the artboard edge. `preview-backup` has no ipage — leave it.

The scene assets are square and aspect-agnostic, so any canvas shape composites
onto them. Capacity is set by the furniture, not the plate — see
`canvas-ranges.md` for measuring it and for the scene-switching rule.

### Wrap variants

Wrap type is a `multiple_choice` variant whose values each carry one
`element_substitution` of `substitution_type: layout`, `element_name: canvas`, and
`content` set to a layout **name** (`mirror` / `gallery` / `color`). Because the
reference is by name, it is portable across a whole size range with no remapping.
A colour-wrap value typically triggers a `color` child variant for the picker.

Watch for a value pointing at the wrong layout — one build had `Digital Wrap`
substituting `mirror`, so it produced output identical to `Mirror Wrap`.

## Adding a family

Record: the page types, whether pages are spreads or singles, where layouts live
and how they are referenced, which extra reference types appear, what must never be
auto-changed, and anything not yet derived. State unknowns plainly rather than
guessing — a wrong guess in this area reaches the press.

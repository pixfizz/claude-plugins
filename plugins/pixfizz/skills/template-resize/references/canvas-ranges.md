# Range builds — one seed to a whole size list

For a batch: one seed export plus a list of sizes becomes an importable template
per size. Proven at 5 sizes (album), 62 sizes (canvas, twice).

Everything geometric is derived; everything commercial is supplied. Nothing is
guessed.

## Read the seed before asking anything

The seed answers most of the intake. Ask only about what it cannot tell you —
asking eleven questions when the seed answers eight wastes the user's time, and
guessing the other three is worse.

| | where in the seed |
|---|---|
| bleed `b` | `<definition>` `<page type="canvas" bleed="...">` |
| mirror depth `m` | `borderwrap` on the `mirror` layout's `<image>`, in mm |
| white remainder | `b - m`; zero when the image element fills the artboard |
| template / product category | root `category`, `products[0].category` |
| code and name convention | root `code`, product `code`, theme `code`, root `name` |
| orientation vocabulary | `products[0].custom.orientation` |
| style token | `products[0].custom.style` — **note string vs list** |
| variant structure | `products[0].variant_types` — codes, values, defaults, controls |
| which values carry a price | non-empty `price` on a `variant_value` |
| preview flags | `preview:` boolean per template record |
| scene wall scale | room-scene ipage `width / print_area_w` |
| scene centres | ipage `x + width/2`, `y + height/2` |

## Must be supplied

1. **The size list**, as print area, with an orientation label per row. Confirm the
   convention is width-first.
2. **Base price per size.**
3. **Per-size variant uplifts**, and exactly which values carry them. Flat uplifts
   (backing, hangers) stay constant — confirm which are which.
4. **Both category strings** if they are changing.
5. **Which size is the seed**, and whether it is reissued in place or left alone.

## Ask only when the seed is silent

- **Mirror depth when the bleed is changing.** A seed with `m = b` and a new bleed
  of 2" could mean `m = 2`, or `m = 1.5` with a half-inch white staple edge. **This
  decides what reaches the press. Always ask.**
- **Orientation tokens** when the size list says Portrait/Landscape but the seed
  says Vertical/Horizontal. Use the seed's vocabulary and say so.
- **Style token** when the bleed changes and the seed carries one.
- **Preview strategy** when the range is much larger than the seed — below.
- **Media payload** — light archives or full.

## Preview capacity and the scene-switching rule

Measure the furniture line by edge-detecting the background plate rather than
guessing, then hold a page margin. For the standard desk scene:

| scene | wall scale | furniture line | usable box | max print |
|---|---|---|---|---|
| `preview-zoomx1.5` | 5.364031 mm/in | y = 214.3 mm | 242 x 155.9 mm | 45.1 x 29.1 in |
| `preview` (1:1) | 4.456140 mm/in | y = 202.1 mm | 242 x 190.3 mm | 54.3 x 42.7 in |

Centres: `preview` (127, 106.947368421052) · `preview-zoomx1.5` (127,
83.961111111111). Furniture line 0.7957 of scene height.

**Switch scene, do not shrink.** Keep a size on `preview-zoomx1.5` while it fits;
otherwise move the live `preview:` flag to `preview`, which shows more wall.
Compute both boxes correctly regardless — only the flag moves. Shrink the wall
scale only when even the wider scene cannot hold it, and report every size that was
shrunk with its percentage.

## Audit the supplied data before building

Run these and report. **Do not change the numbers.**

- **Dominance.** A strictly larger product must not cost less, or carry a smaller
  uplift, than a smaller one. Real supplied pricing has failed this repeatedly,
  traceable to a material-consumed column with a bad row.
- **Reconciliation.** Where the source has both a base and a combined figure, check
  `base + uplift == combined`. This is what proves the right column was read.
- **Coverage.** Every size matches a row, allowing for the source listing one
  orientation per pair.
- **Orientation labels** consistent with the dimensions.
- Sizes in the pricing source not in the range, and vice versa.

## Scripts

```bash
python3 scripts/build_range.py  config.json
python3 scripts/verify_range.py config.json
```

`scripts/config.example.json` is a real 62-size canvas run — three variant types,
per-size uplift, in-place reissue of the seed size — verified to reproduce shipped
output exactly. Copy it and edit rather than writing one from scratch.

`verify_range.py` is not advisory. On real runs it caught a dangling `layout_id`,
an id filter scoped by magnitude instead of by the media maps, and a
code-uniqueness assumption that was wrong.

## Delivery

One zip of per-size archives, a manifest CSV (name, size, orientation, price,
uplift, codes, category, live preview page, wall scale, id behaviour), a
contact-sheet PNG of every preview, and a build record written to the project.

Scene plates are typically 15 MB per export and identical across the range —
omitting `images/` takes a 62-size delivery from 950 MB to 205 kB. See
`import-behaviour.md` before promising that works.

## Report

Name every value taken from the seed rather than asked about, every size whose wall
scale was reduced, every preview reassigned, every field left at the seed's value
because it was ambiguous, and anything in the supplied data that looks wrong.

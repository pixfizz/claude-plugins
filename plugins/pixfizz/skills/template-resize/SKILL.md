---
name: template-resize
description: Use when resizing, retargeting, cloning or deriving a Pixfizz design product to a different size, or when generating a whole size range from one seed export — a photo book, album, canvas wrap, wall product, print or any template with pages. Triggers on "resize this template", "turn the 8x8 into a 10x10", "make a 5x7 from the 4x6", "the layouts are the wrong size", "derive the other sizes", "build the rest of the range", "here is the seed and the size list", or any design theme export (__print_theme.yml) or template export (__print_product.yml) supplied with a target size or a list of sizes. Also use when layout artwork renders crammed into a corner of the page with dead space, when a full-bleed spread shows a hairline white edge at trim, when a canvas preview shows a sliver of the mirrored wrap, when layouts in the picker do not match the page they are applied to, or when a design's pages carry different geometry from the layouts they reference.
---

# Pixfizz Template Resize

## Overview

Derive a Pixfizz design product at a new size by rewriting the geometry in its
export, rather than rebuilding it by hand. Two export kinds are handled:

| Export | Root file | Contains |
|---|---|---|
| **Design theme** (`Design > Export`) | `__print_theme.yml` | one theme: page stubs plus `layouts[]` |
| **Template** (`Template > Export`) | `__print_product.yml` | the whole product: definition XML, product attributes, variants, template options, and every print theme |

Both are gzipped tars carrying `assets/ fonts/ glb_files/ images/ pdfs/`. Repackage
with those directories present even when empty — the importer expects them.

Two modes:

- **One target size** — phases 1 to 5 below.
- **A whole size list from one seed** — same geometry, driven from a config.
  See `references/canvas-ranges.md` and use `scripts/build_range.py`. Proven at
  5 sizes (album) and 62 sizes (canvas, twice).

Work through the phases in order. Do not skip the proof sheet.

## Phase 1 — Read the export before touching it

Never assume the shape. Unpack and report:

```bash
tar xzf EXPORT.tar.gz -C work/
python3 scripts/pxload.py            # tolerant loader; Pixfizz emits Ruby YAML tags
```

Establish and state back to the user:

- which export kind this is, and the ids of every template, theme, product and layout
- the **element census** — anything other than `<image>` changes the job
- every page size present, and which are stale leftovers from an earlier size
- the reference graph: `layout_id`, `db:` image references, `target_element_name`,
  `<ipage template="...">`, and whether each resolves

`references/export-formats.md` has the full field shapes and the reference graph.

**On a range build, the seed also answers most of the intake** — bleed, wrap depth,
categories, variant structure, naming and orientation vocabulary. Read it first and
only ask about what it cannot tell you. Checklist in `references/canvas-ranges.md`.

**Stop and flag, do not silently fix:**

- `<text>` in a **layout** — font scaling is unproven; ask before touching it.
  `<text>` inside a *preview* page (scene labels, scale-reference groups) is part
  of the mockup: pass it through untouched and do not warn on it
- dangling references — a `layout_id` or `target_element_name` pointing at nothing.
  A `layout_id` that survived a previous import is dangling by default; see
  `references/import-behaviour.md`
- a design page whose frames differ from the layout it references (applying a
  layout copies it and nothing re-syncs)

`<ipage>` is no longer a stop — the relationship is derived. See
`references/product-families.md`.

## Phase 2 — Establish the geometry

Get the target size from `19_XML_TEMPLATE_REFERENCE.md` and the client spec, never
by guessing:

```
spread XML width/height  =  the OUTPUT dimensions, bleed included
```

A square-page album gives a 2:1 spread (8x8 → 16 x 8 in → 406.4 x 203.2 mm). A
canvas is `(W + 2b) x (H + 2b)`. `references/geometry.md` carries the spread
arithmetic and the numeric gotchas; `references/product-families.md` carries the
canvas model and the `<ipage>` formula.

**The declared `<page>` canvas is not evidence of the authored grid.** It has been
observed stale and prematurely correct. Always derive the grid from the frames.
`resize_layouts.py` does this with two independent detectors and refuses when they
disagree.

**Never invent a wrap depth, a category, a price or a style token.** Ask.

## Phase 3 — Resize

### Design theme export

```bash
python3 scripts/resize_layouts.py work/__print_theme.yml --target 508x254 --out work/new.yml
```

### Template export, one size

```bash
python3 scripts/retarget_template.py work/__print_product.yml --out work/new.yml \
  --from-spread 203.2x152.4 --to-spread 254x177.8 \
  --from-inch 8.000x6.000 --to-inch 10.000x7.000 \
  --sync-pages --rename "4x6=5x7"
```

Text-surgical: only the `layout:` and `data:` nodes change, so Ruby YAML tags, key
order and untouched fields survive exactly.

### A whole range

```bash
python3 scripts/build_range.py  config.json      # copy scripts/config.example.json
python3 scripts/verify_range.py config.json
```

**Before renaming, grep the whole file for the old string** and confirm every hit
is a field you intend to change. Names can be load-bearing — a pricing formula or
Liquid snippet may reference an attribute code.

### When the aspect ratio changes

For **multi-frame layouts**, frame shape, grid adjacency and page fill cannot all
be preserved — arithmetic, not a tooling limit. Default to `margin`, keep gutters
absolute, say plainly which cost was paid, show the proof sheet, and offer the
band-vocabulary override in `references/geometry.md`. Never apply `stretch` without
explicit instruction.

For **canvases there is no cost at all** — one image element per layout, so
portrait to landscape is arithmetic and no band vocabulary is needed.

## Phase 4 — Verify

Every time:

```bash
python3 scripts/verify_layouts.py work/orig.yml work/new.yml --source WxH --target WxH
python3 scripts/proof_layouts.py work/new.yml work/proof.png --title "..." \
        --compare work/orig.yml --src WxH
```

`verify_layouts.py` checks geometry exactness, bounds, metadata drift, element
census, aspect preservation, and **edge landing** — a frame on the page edge must
land on it exactly or a full-bleed spread ships with a hairline white trim edge.

For a range, `verify_range.py` adds the per-size commerce, variant, ipage, id and
code checks. **Its failures are not advisory** — on real runs it caught a dangling
`layout_id`, an id filter scoped by magnitude instead of by the media maps, and a
code-uniqueness assumption that was wrong.

**Then look at the proof sheet.** The numeric checks pass happily on a
self-consistently wrong grid; the picture is what catches it.

**Audit supplied pricing without changing it.** Check that a strictly larger
product never costs less or carries a smaller uplift, and that any base-plus-uplift
reconciles against the source's own combined figure. Report the bad rows and ship
the numbers as given.

## Phase 5 — Package and hand over

```bash
mkdir -p pkg/{assets,fonts,glb_files,images,pdfs} && cp -a work/assets/. pkg/assets/ 2>/dev/null
cp work/new.yml pkg/__print_product.yml       # or __print_theme.yml
cd pkg && tar czf ../NAME.tar.gz ./assets ./fonts ./glb_files ./images ./pdfs ./__print_*.yml
```

Confirm the tar entry list matches the source, so no image or asset was dropped.
Name the file after the rule used when an aspect change was involved
(`...-RESIZED-margin.tar.gz`) so it stays traceable.

**Ids — read `references/import-behaviour.md` before writing the handover.** The
short version, corrected 24 Aug 2026: **template import creates new records and
does not remap `layout_id`**, so a template's page comes back dangling and must be
repaired. Id preservation was proven for *design themes* only and does not extend
to templates. Do not promise overwrite semantics from keeping ids on a template.

The clone-in-admin workflow is still the safe habit for design themes:

1. the user clones the product to the new size in admin
2. exports that clone
3. this skill rewrites the clone
4. the user re-imports over it

Never tell the user to import a retargeted export over a seed they cannot afford
to lose.

## Report

State, in this order: what changed, what was deliberately left alone and why, what
is dangling or pre-existing-broken, and which decisions are the user's. Include the
margin table for aspect changes, and for a range the manifest plus every size whose
preview was reassigned or whose wall scale was reduced. Flag stale page sizes
rather than guessing — particularly covers, where the correct size depends on the
album family and a wrong guess sends a wrong-size PDF to the press.

## Scripts

- `scripts/pxload.py` — YAML loader tolerant of Pixfizz's Ruby/ActiveSupport tags
- `scripts/pxgeom.py` — shared geometry: grid detection, the transform rules, formatting
- `scripts/resize_layouts.py` — resize a design theme's layouts
- `scripts/retarget_template.py` — retarget a whole template export
- `scripts/verify_layouts.py` — the checks that must pass before shipping
- `scripts/proof_layouts.py` — contact sheet, optionally source-vs-result
- `scripts/build_range.py` — a whole size range from one seed, config-driven
- `scripts/verify_range.py` — per-size geometry, commerce, variants, ids and codes
- `scripts/config.example.json` — a real canvas run, trimmed; copy and edit

## References

- `references/export-formats.md` — field shapes, the reference graph, what links to what
- `references/geometry.md` — spread arithmetic, size table, the transform rules, gotchas
- `references/product-families.md` — books and canvases, both proven; the `<ipage>` formula
- `references/canvas-ranges.md` — range intake, preview capacity, data audit, delivery
- `references/import-behaviour.md` — what import actually does to ids, codes and media

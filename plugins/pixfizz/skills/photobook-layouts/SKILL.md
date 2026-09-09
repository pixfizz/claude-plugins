---
name: photobook-layouts
description: Use when adding, designing or generating layouts for a Pixfizz design theme - the photo frame arrangements a customer picks from in the Design Tool. Triggers on "add new layouts", "create photo book layouts", "we need more layout options", "fill the blank layouts", "generate a layout set", "more one-photo and two-photo layouts", "the layout picker is too thin", "design some collage arrangements", or any design theme export (__print_theme.yml) supplied with empty layouts or a request for more arrangements. Also use when layouts are untagged and the picker has lost its photo-count grouping, when a new theme has only a handful of arrangements, or when someone asks for layouts modelled on a competitor's or a reference set of thumbnails. This is the layout-CREATION skill; use template-resize instead when existing layouts are the wrong size for their page.
---

# Pixfizz Photo Book Layouts

## Overview

Add layouts to a design theme by writing frames into an exported
`__print_theme.yml` and re-importing it, rather than dragging boxes in admin
forty times.

A **layout** is a named arrangement of placeholder image frames on a page. The
Design Tool shows them in a picker, grouped by the `tags` facet, and applying
one copies its frames onto the customer's page. Layouts live in `layouts[]`, a
sibling of `templates[]` in the theme export, and carry `layout: true`.

**This skill creates layouts. `template-resize` rescales existing ones.** If the
arrangements are right but the page size is wrong, that is the other skill.

## The workflow that avoids the id problem

Do not invent layout ids and do not ship blank ones.

> Whether a blank or invented `id:` creates a new layout record is **not
> verified**. Id preservation making an import overwrite **is** verified for
> design themes (not for templates - see `references/layout-anatomy.md`).

So the safe sequence, and the one to ask the user for:

1. **The user creates N empty layouts in admin** (Design > Layouts > New,
   saved without frames) and tags each one if they want to control the mix.
2. **The user exports the theme.** Every blank now carries a real platform id.
3. **This skill writes frames into those blanks** and leaves every id, `number`,
   `name` and `usage_flags` untouched.
4. **The user re-imports.** It overwrites those exact records.

Tell the user how many blanks to make before they start. Aim for a round number
per photo-count group - six to eight each across 1, 2, 3, 4 and 5+ is a full
picker without padding.

## Phase 1 - Read the export before touching it

```bash
tar xzf EXPORT.tar.gz -C work/
python3 scripts/fill_layouts.py --in EXPORT.tar.gz --dry-run
```

State back to the user, and do not proceed until these are agreed:

| | |
|---|---|
| Page size | derived from the frames, not the declared `<page>` canvas |
| Gutter and margin | derived from the layouts already there |
| Existing layouts | how many, and what shape each one is |
| Existing tag strings | the exact vocabulary in use |
| Blank layouts | how many are waiting to be filled |

**Enumerate what is already in the theme before adding to it.** The fill script
skips any archetype whose frame geometry matches a layout already present, and
reports how many it dropped. A picker with the same 2-up twice looks broken.

**Read the tag strings off the theme; never invent them.** One seed used
`1 photo`, `2 photos`, `3 photos`, `5+ photos` - note the singular, and note
that `5+` is the catch-all with no `5 photos` string. A tag that does not match
the existing vocabulary silently creates a new picker group of one.

## Phase 2 - Establish the grid

`scripts/pxgrid.py:derive()` reports its evidence rather than asserting a
result. Check it.

- **Page size** comes from a full-bleed frame if there is one, otherwise the
  mode of `min_edge + max_extent`. The declared `<page>` canvas is observed
  stale in both directions and is not evidence.
- **Gutter** is the mode of the positive gap between horizontally adjacent
  frames. Almost always 6.35 mm (0.25 in).
- **Margin** is the mode of each layout's own smallest non-zero left edge.
  Taking the global minimum instead picks whichever single layout is tightest,
  which is not the house margin.

Override with `--margin` / `--gutter` when the derivation disagrees with what
the user knows. Do not silently accept a derived margin that only one layout
votes for.

## Phase 3 - Fill

```bash
python3 scripts/fill_layouts.py --in EXPORT.tar.gz --out FILLED.tar.gz
python3 scripts/fill_layouts.py --in EXPORT.tar.gz --out FILLED.tar.gz --groups 1,2
```

The library in `scripts/layout_library.py` holds 45 archetypes, 9 per group,
each a pure function of the page - so the same set works on a square album page,
a 2:1 spread, or a landscape print. `--groups` narrows it when the user only
wants, say, more one- and two-photo options.

Blanks are filled in library order, balanced across groups when there are fewer
blanks than archetypes. Adding an archetype is a few lines - see
`references/design-rules.md` for what makes one worth adding.

**The YAML is patched as text, not round-tripped.** Everything outside the blank
`data:` and `tags:` keys stays byte-identical, so the diff is reviewable and a
naive re-emit cannot reflow the other layouts or drop a Ruby-tagged scalar.

## Phase 4 - Verify

```bash
python3 scripts/verify_layouts.py --before EXPORT.tar.gz --after FILLED.tar.gz
python3 scripts/proof_sheet.py --in FILLED.tar.gz --compare EXPORT.tar.gz --out proof.png
```

`verify_layouts.py` fails the run on any of:

- a top-level key changed outside `layouts[]`
- layout ids or their order changed - the import would stop overwriting
- an already-populated layout modified
- `<page>` attributes changed
- XML that does not parse, a frame outside the trim, a non-positive frame
- a filled layout left untagged
- `left`/`top` not zero, or `edit`/`placeholder` missing
- **a trim edge landing a hairline off** - `253.99999` against a `254` page is a
  white line down the trim of every full-bleed print and no proof sheet shows it

It warns, without failing, on overlapping frames and on non-`<image>` elements.

**The proof sheet renders from the archive's own XML, never from the spec that
generated it.** Rendering the spec proves the spec, not the file that will be
imported. Show it to the user before they import - vetoing a layout on a
contact sheet costs nothing, undoing an import costs a restore.

Read the proof sheet yourself before sending it. Look for frames that overlap,
rows that sit off-centre, and any arrangement that duplicates another.

## Phase 5 - Package and hand over

The archive must keep the five media directories - `assets/ fonts/ glb_files/
images/ pdfs/` - present even when empty, `./`-prefixed member paths, and the
same member order as the source. `fill_layouts.py` reproduces the source's
member list exactly; do not repack by hand.

Hand over:

- the `.tar.gz`, one per theme, never split
- the proof sheet PNG
- the derived grid, in mm and inches
- the count filled, per tag
- what was deliberately skipped: duplicate archetypes, blanks left over

Say plainly that the import overwrites the blank records it was built from, and
that any layout already carrying frames was not touched.

## Design rules

Full detail in `references/design-rules.md`. The short version:

- **Cover the counts.** A picker weighted to 4-photo grids sends everyone to the
  same page. Six to eight per group across 1, 2, 3, 4 and 5+ is the target.
- **Spread the 5+ group.** It is a catch-all, so give it 5, 6, 7, 8, 9, 10 and
  12-frame options rather than five dense grids.
- **Roughly 70/30 aligned to asymmetric** unless the user says otherwise. All
  grids is dull; all scatter is unusable.
- **Never duplicate a shape already in the theme.**
- **One gutter for the whole set.** Mixed gutters read as a mistake.

## Scripts

| Script | Does |
|---|---|
| `scripts/fill_layouts.py` | derive the grid, fill blanks, repack. `--dry-run` first |
| `scripts/verify_layouts.py` | before/after assertions; exits non-zero on failure |
| `scripts/proof_sheet.py` | contact sheet from the archive's own XML |
| `scripts/layout_library.py` | the 45 archetypes; add to this, not to callers |
| `scripts/pxgrid.py` | `Page` geometry helpers, `fmt()`, grid derivation |
| `scripts/pxload.py` | tolerant YAML loader; Pixfizz emits Ruby tags |

`pxload.py` is duplicated verbatim in the `template-resize` skill deliberately, so each
skill stands alone. If the two are ever merged, share it and the numeric
conventions in `pxgrid.py`.

## References

- `references/layout-anatomy.md` - the export format, element conventions,
  tags, ids and what import actually does
- `references/design-rules.md` - grid vocabulary, the archetype catalogue, and
  how to add one

## Report

Close with what was verified and how:

- verified by reading the file: derived grid, existing layouts, tag vocabulary
- verified by script: the `verify_layouts.py` assertions, named
- **not verified**: that the import landed. Only the user can confirm that.
  Ask them to check the layout count in admin after importing, and say so.

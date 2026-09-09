# Import behaviour — what the platform actually does

## Template import creates new records and does not remap `layout_id`

**Proven 24 Aug 2026, and it corrects an earlier inference.**

A template exported from one site with generated ids in the `1.10e9` block was
imported into another. The re-export came back with native ids (`355307779+`) on
every template and layout — but its `canvas` page still carried
`layout_id="1100000010"`, the old generated id. The reference dangles.

Two consequences:

1. **Id preservation was proven for design themes and does NOT extend to
   templates.** Do not promise overwrite semantics from keeping ids on a template.
   Renumbering into per-size blocks is still worth doing so nothing collides, but
   it is belt-and-braces, not the mechanism.
2. **Any exported template whose page carries a `layout_id` comes back dangling.**
   Always repair it: point the page at the local layout whose materialised frames
   it actually matches. Compare frame geometry, do not assume — a `canvas` page
   matching `gallery` while the default wrap variant is `mirror` is normal and
   correct.

The clone-in-admin workflow is still the safe one for **design themes**, and is
still a sensible habit for templates, but the reason has changed: it is about
having a known-good record to overwrite, not about id preservation.

## Codes

Template `code` and product `code` are deliberately **the same string** in every
seed seen; the theme code differs (`canvas-8x8-2.00` vs `canvas8x8-2.00`). Check
uniqueness **across** templates, never within one — checking within will report
every file as a duplicate.

Re-importing an archive whose `code` already exists is untested. Assume it
duplicates rather than updates.

## Media

Image and asset ids are shared across sites in practice — the same scene-plate ids
appear on unrelated storefronts. **Never renumber media ids.** The maps must keep
pointing at the existing library records so the import reuses them instead of
uploading another copy of a 15 MB plate per size.

Omitting `images/` from the archive while keeping `__image_map` has worked in
practice. It is not formally proven. Ship one full archive alongside as a control
and say so in the handover.

## Materialised layout copies go stale

A page carries both a `layout_id` **and** a materialised copy of the layout's
elements. Editing the layout afterwards leaves the page stale — found live on a
real product. Always compare the page's frames against its referenced layout and
report a mismatch rather than silently re-syncing.

## Stale stubs propagate through every clone

Design-theme and album exports carry `preview`, `spread` and `cover` page stubs at
wrong sizes, sometimes colliding on `number`, sometimes with dangling `layout_id`s.
Leave them alone and report them. **Never auto-fix a cover** — the correct size is
family-specific and a wrong guess sends a wrong-size PDF to the press.

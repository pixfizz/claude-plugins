# Layout anatomy - the design theme export

Verified by reading two real exports from a 10x10 album theme (Aug 2026).

## Where layouts live

```yaml
id: 208384
name: Layouts Seed
code: seed
templates:            # page stubs, one per page type
- id: 355494374
  name: preview
  number: 0
  data: |
    <?xml version="1.0" encoding="UTF-8"?>
    <page width="127.0" height="127.0" version="2"/>
  layout: false
layouts:              # the layout library - a SIBLING of templates[], not nested
- id: 355494387
  name: page
  print_book_id:
  number: 3
  data: |-
    <?xml version="1.0" encoding="UTF-8"?><page height="254" name="page" pages="" version="2" width="254"><image edit="true" height="101.6" left="0" placeholder="true" top="0" width="101.6" x="22.225" y="76.2"/>
    <image edit="true" height="101.6" left="0" placeholder="true" top="0" width="101.6" x="130.175" y="76.2"/></page>
  layout: true
  usage_flags: 3
  custom: {}
  tags:
  - 2 photos
design_options: []
```

An **empty** layout is the same block with a bare `<page ...></page>` and
`tags: []`. That is what admin writes when you save a new layout with no frames,
and it is what this skill fills.

## Element conventions

```xml
<image edit="true" height="101.6" left="0" placeholder="true" top="0" width="101.6" x="22.225" y="76.2"/>
```

- **`left` and `top` are on every element and are always `0`. They are NOT the
  position.** `x`/`y` are.
- **`x` and `y` are omitted entirely when zero.** Parse them as defaulting to 0;
  insert the attribute only for a non-zero value. A full-bleed frame therefore
  has neither.
- Attribute order as emitted: `edit height left placeholder top width x y`.
- `edit="true" placeholder="true"` is what makes the frame a customer-fillable
  photo slot. Both are required.
- **Coordinates are always millimetres**, regardless of any `unit=` in the
  template definition.
- Elements may legitimately be negative and overhang the page on cover artwork.
  Bounds-check interior pages only.

## Page attributes on a layout

`<page height name pages version width>`. Copy them through unchanged.

`pages` is a comma list naming which page templates the layout is offered on
(`page01,page03,page05`). **An empty `pages=""` means all pages** - one seed was
deliberately cleared to that. Never rewrite this attribute on the user's behalf;
it decides where the layout appears in the picker.

## Tags

`tags` is the photo-count facet the Design Tool groups the picker by. It is a
list of strings and **must survive any rewrite or the picker loses its
grouping**.

Observed vocabulary on a real theme:

```
1 photo   2 photos   3 photos   4 photos   5+ photos
```

Singular for one. `5+ photos` is the catch-all - a 16-frame layout carries it.
There is no `5 photos` string. **Read the strings off the theme rather than
generating them**; a tag that does not match creates a picker group of one and
looks like a bug.

## number

Display order in the picker. Preserve it. Filling a blank does not change where
it appears.

## Ids and what import does

- **Id preservation makes a design-theme import overwrite the same records.**
  Verified for design themes.
- **It does not extend to templates** (`__print_product.yml`), where import
  creates new records and does not remap `layout_id`. See the `template-resize`
  skill's `references/import-behaviour.md`.
- **Whether a blank or invented layout `id:` creates a new record is NOT
  verified.** Blank `id:` is documented as accepted at template, template-option
  and print-theme level; nobody has proven it at layout level. Do not rely on it.
  Have the user create the blanks in admin instead.
- Re-importing a theme whose `code` already exists is untested. Assume the
  clone-in-admin, export, rewrite, re-import-over-it workflow.

## Materialised copies go stale

A design page carries both a `layout_id` reference **and** a materialised copy
of the layout's frames. Editing the layout afterwards leaves already-built pages
stale. Adding new layouts is safe - nothing references them yet - but say so if
the user asks why an existing page did not change.

## Archive shape

```
./assets/  ./fonts/  ./glb_files/  ./images/  ./pdfs/     (present even when empty)
./__print_theme.yml
```

gzipped tar, `./`-prefixed member paths, owner `pixfizz`. The importer expects
the media directories. Reproduce the source's member list and order.

## Stale page stubs

`preview` (127 x 127), `spread` (254 x 127) and `cover` (307.975 x 180.975) ride
along through every clone at 5x5-era sizes. **Leave them alone and report them.**
Never auto-fix a cover - the correct size is album-family specific and a wrong
guess sends a wrong-size PDF to the press.

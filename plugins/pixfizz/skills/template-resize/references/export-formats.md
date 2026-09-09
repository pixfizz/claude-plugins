# Pixfizz export formats and the reference graph

Verified against six design-theme exports and one full template export
(August 2026).

## Design theme export — `__print_theme.yml`

```yaml
id: 208007
name: Layouts 8x8
code: layouts-8x8
templates:            # page stubs, one per page type, usually empty of elements
- id: 354858041
  name: preview
  number: 0
  data: |
    <?xml version="1.0" encoding="UTF-8"?>
    <page width="127.0" height="127.0" version="2"/>
  layout: false
  usage_flags: 3
  preview: false
layouts:              # the layout library
- id: 354858054
  name: spread-layout
  print_book_id:
  number: 9
  data: |
    <?xml version="1.0" encoding="UTF-8"?>
    <page height="180.975" name="spread-layout" pages="" version="2" width="307.975">
      <image edit="true" height="114.3" left="0" placeholder="true" top="0" width="165.1" x="6.35" y="6.35"/>
    </page>
  layout: true
  usage_flags: 3
  custom: {}
  tags:
  - 2 photos
design_options: []
```

- `layouts[]` is a **sibling of `templates[]`**, not nested. Layout entries carry
  `layout: true`, template entries `layout: false`.
- `tags` is the photo-count facet the Design Tool groups the picker by. It is a
  list and must survive any rewrite or the picker loses its grouping.
- `number` is display order in the picker. Preserve it.
- **`left` and `top` are on every element and are always 0. They are NOT the
  position.** `x`/`y` are, and they are **omitted entirely when zero** — parse them
  as defaulting to 0, and insert the attribute when writing a non-zero value back.
- Coordinates are **always millimetres**, regardless of `unit=` in the definition.
- Keep the YAML block-scalar style (`data: |`). A naive round-trip reflows these
  into one-line strings; it still imports but the diff becomes unreadable.

## Template export — `__print_product.yml`

A superset. Top-level keys that matter:

| Key | Contains |
|---|---|
| `layout` | the `<definition>` XML as an escaped scalar — page sizes in **inches** (whatever `unit=` says), bleed, margin, hinge, the `<map>` spine ladder, `<set>` structure |
| `print_themes[]` | every theme, each with its own `templates[]` and `layouts[]` |
| `template_options[]` | imprint/foil/text options; `target_element_name` binds one to a page element |
| `products[]` | the storefront product: `code`, `name`, `custom{}` flags, `variant_types[]` |
| `max_pages` / `min_pages` / `page_increments` | duplicated outside the XML |
| `__image_map` / `__asset_map` / `__pdf_map` / `__font_map` | id → original filename for the tar payload |

Ruby tags such as `!ruby/object:ActiveSupport::TimeWithZone` appear on timestamps.
`scripts/pxload.py` handles them; plain `yaml.safe_load` throws.

## The reference graph

Everything below is a link that a rename or resize can break.

### Layout → design page

A design page references a layout by `layout_id` **on the `<page>` element**, and
the layout's frames are **copied into the page** with `layout="true"` added:

```xml
<page height="152.4" layout_id="355064753" name="spread01" width="203.2" version="2">
  <image edit="true" height="91.44" layout="true" left="0" placeholder="true" top="0"
         width="193.04" x="5.08" y="30.48"/>
</page>
```

Two consequences:

1. **The copy does not re-sync.** Editing a layout after it has been applied leaves
   the design page on the old geometry. This has been seen live in production — a
   4x6 product whose pages carried superseded values while its layouts theme was
   correct. Always compare, and offer to re-sync (`--sync-pages`).
2. A `layout_id` can dangle. One was found pointing at an id present in no theme in
   the export. Report it; do not invent a target.

### Option → page element

`template_options[].target_element_name` matches an element's `name` attribute.
In the sample, `cover-line-1`, `cover-line-2` and `spine-line` had **no matching
element anywhere** — the imprint options targeted nothing. Check, report, do not
silently create elements.

### Element → stored file

`src="db:205046441"` and `mask="db:205046442"` resolve through `__image_map`.
Preserve every `db:` reference exactly and confirm the tar payload still carries
the same ids after repackaging.

### Inline page → template

`<ipage template="cover" zoom="39.02" left="-20.62" top="0" .../>` embeds another
template's page as a live preview. See `product-families.md`.

## Round-trip behaviour

- Keeping ids makes an import **overwrite** the existing record rather than create
  a new one. Proven on design themes; assume the same for templates.
- Full coordinate precision survives export → import → export. Values such as
  `15.599773371056` were observed returning byte-identical.
- Pixfizz's own inch→mm conversion carries float noise: real files contain
  `609.5999999999999` and `304.79999999999995`. **Compare with a tolerance, never
  by string equality.**

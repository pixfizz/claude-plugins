---
name: xml-templates
description: "XML template definitions for Pixfizz design products — the production specification behind every design product. Use this skill whenever creating, editing, reviewing or debugging an XML template definition: definition attributes, page dimensions, bleed, margin and safe area, snap points, gutters, sets, growing spines, layflat spreads, PDF layers, separate-file and separate-page fulfillment, set captions, and page-count rules. Trigger for any mention of 'XML template', 'template definition', 'definition tag', 'page set', 'bleed', 'safe area', 'growing spine', 'binding map', 'separate layer', 'output-name', 'trimbox', 'uncounted pages', or a production file that is the wrong size, blank, duplicated, or missing pages. Also trigger when setting up a new design product, a photobook, calendar, canvas, greeting card, photo print or custom design tool product."
---

# Pixfizz XML Template Reference

The XML template defines the **production specification** for a design product: what file
production receives, at what size, at what resolution, in how many parts. Page layouts and page
structure are configured in the Design admin — the XML controls production output behaviour only.

Authoritative source: `19_XML_TEMPLATE_REFERENCE.md` in the Pixfizz knowledge base
(github.com/pixfizz/pixfizz-knowledge). Calendars and planners have their own vocabulary —
`foreachdate`, `<dategen>`, date sequences — in `23_XML_CALENDAR_REFERENCE.md`. Load that one for
any dated product; the rules here still apply underneath it.

## Read the geometry correctly — the three that get misread

These three cost the most, because each is intuitive in the wrong direction.

- **`width` and `height` are the pre-trimmed production size. Bleed is NOT added on top.** The
  values you write are what production receives.
- **`bleed` is a virtual guide.** It shows the end user where the page will be trimmed and has
  **no effect on the artwork output size**. It accepts asymmetric values in
  `top bottom left right` order: `bleed="10 20 10 25"`.
- **`margin` is the safe area, measured inward from the bleed line**, not from the page edge. With
  no bleed set, it is measured from the page edge. `margin="0"` explicitly disables the guide.

`snap` follows from those: default snap points are page edge and centre; with bleed and no margin
it snaps at the bleed; with a margin it ignores bleed and uses the margin. **If any snap values
are defined at all, elements snap exclusively to those values** — a partial list is a trap.

## `<definition>` attributes

| Attribute | Meaning |
|---|---|
| `unit` | Unit system for every dimension. `inch` or `mm`. One system per product. |
| `dpi` | Target resolution for production output |
| `output` | `pdf` or `jpeg` |
| `minimum-dpi` | Minimum acceptable image resolution; drives the quality warning in the Design Tool |
| `pages` | Starting page count on a new project. **Required for cut print products, set to `1`.** |
| `min` | Minimum page count the user cannot go below |
| `add` | Increment by which pages are added |
| `max` | Maximum total page count |
| `trimbox` | `true` embeds PDF trimbox metadata — for prepress workflows that need it |

## `<set>` attributes

A `<set>` groups one or more `<page>` elements. Five attributes, each defaulting to "on" when
omitted:

| Attribute | Effect when set |
|---|---|
| `count="false"` | Excludes the set from the product page count. Standard for covers. |
| `grow="true"` | This is the set used when the user adds pages. **Only one set should carry it.** |
| `fulfillment="false"` | Excludes the set from production artwork generation |
| `editor="false"` | Hides the set from the end user in the Design Tool |
| `preview="true"` | Designates the set as the project preview — the cart and saved-projects thumbnail |

The hidden preview set is a standard pattern and worth copying:

```xml
<set fulfillment="false" editor="false" preview="true">
	<page type="preview" bleed="0" width="10" height="10" />
</set>
```

## Page parameters worth knowing

- **`type`** refers to the name of the Page in the Design — it is a reference, not a label.
- **`output-name`** controls grouping. Pages sharing an `output-name` are grouped into one
  multi-page PDF. This is how a photobook keeps `Cover` separate from `Pages`.
- **`hinge`** renders the spine hinge line and shifts the alignment centre. Cover only, with a
  binding map.
- **`gutter`** hides artwork from the user in the area between pages, so content is not lost in
  the binding.
- **Comma-separated `type` in a `grow="true"` set cycles.** `type="page01,page02"` uses `page01`
  on the first addition and `page02` on the second, then repeats. Only meaningful inside a grow
  set.

## Filters

**Growing spine.** Nest inside the cover `<page>`; the `map` attribute must match a `<map name>`
elsewhere in the definition. Keys are inclusive ranges in `..` notation.

```xml
<page type="cover" ... hinge="0.2">
	<filter type="binding" map="binding" />
</page>

<map name="binding">
	<val key="24..37">0.35</val>
	<val key="38..73">0.35</val>
	<val key="74..93">0.39</val>
</map>
```

**Layflat spread.** `<filter type="binding-layflat" />` draws a centre guide on a spread and makes
alignment aids work within each half independently.

## PDF layers

Defined once at template level; elements are then assigned to layers in the admin design tool,
Photoshop-style.

```xml
<layers>
	<layer name="Barcode" />
	<layer name="Cutmarks" visibility="fulfillment" separate-file="true" />
</layers>
```

- `visibility`: `on` (default), `off`, or `fulfillment` — visible in production files, hidden in
  the Design Tool and on previews.
- `separate-file="true"` writes the layer to its own file, named `{base_name}_{layer_name}.{ext}`
  unless `filename` overrides it. `filename` supports `%prod_code%`, `%order_code%`, `%barcode%`.
  Give two layers the same `filename` to combine them into one file.
- `separate-page="true"` appends the layer's pages to the back of the main PDF instead. A 3-page
  product with a separate-page Foil layer fulfills as a 6-page PDF.

**Blank pages in the layer output is the common defect.** By default *every* page generates output
for a separate layer, even pages carrying no elements from it. Restrict it per page:

```xml
<page type="page1" ... separate-layers="Foil">   <!-- only Foil -->
<page type="page2" ... separate-layers="">       <!-- none -->
```

## Set captions

```xml
<captions>
	<left>Page {{n}}</left>
	<right>Page {{n}}</right>
</captions>
```

`{{n}}` is the sequential page number at runtime. Use left/right for spreads, `<center>` for
single-page sets, or plain words ("Front", "Back") where numbering would confuse.

## Product archetypes

Start from the closest of these rather than from an empty file. Full annotated examples are in the
KB reference.

| Product | Shape |
|---|---|
| **Photo prints** | `pages="1"`, `add="1"`, high `max`, `output="jpeg"`, `bleed="0"`, one set with `count="true" grow="true"` |
| **Canvas** | Large bleed for the wrap (e.g. `1.25`), `margin="0"`, design-aid layers off, cutmarks at `visibility="fulfillment"`, hidden preview set |
| **Photobook** | `pages`/`min`/`max`/`add`, `trimbox="true"`, binding map for the spine, cover set `count="false"`, grow set with cycling page types, `output-name` splitting Cover from Pages |
| **Greeting card** | Two hidden preview sets (only one `preview="true"`), two visible sets with word captions, no grow |
| **Custom design tool product** | **Exactly one set containing one page**, `fulfillment="false"`, geometry declared but nominal for variable-size products |

## Custom design tool products are a special case

When a browser-based custom tool builds the print file itself, the definition exists purely to
**declare the specification** — the tool reads it rather than carrying its own copy.

- **Exactly one set, one page.** `template.width` returns the *first* page, so a leading preview
  set hands the tool the wrong number.
- **`fulfillment="false"` on the set**, or every orderline gets a blank rendered file sized to the
  production page — fully transparent, which file explorers draw as a black square.
- **`dpi` and `minimum-dpi` are read by the tool, never hardcoded in its asset.** A baked-in DPI
  constant cannot be changed per lab and silently overrides what the product declares.
- Liquid exposes `template.width`, `template.height`, `template.dpi`, `template.minimum_dpi`.
  **`bleed` and `unit` are not exposed.**
- On variable-size products — stickers, gang sheets, banners, custom size prints — `width` and
  `height` are **nominal and must not be used as a constraint**. A product carrying a 5.75 x 6.25
  page while producing a 12 x 72 sheet is normal.

## Page-count rules

- **Booklets (stapled or coil-bound) must have a page count divisible by 4.** The design tool
  auto-detects page count on upload and warns on bleed or divisibility errors.
- **Old softcover templates can carry a page-count ghost bug** — corrupted page-count metadata
  lets customers add or delete pages beyond the defined limits. No server-side fix yet. Mitigation
  is to copy the customer's project onto a fresh template and reshare. Build new softcover
  products on current templates.
- Remember downstream: `pages` in a pricing formula counts uncounted pages too. Any set marked
  `count="false"` still lands in `pages`, which is why book pricing uses
  `(pages - uncounted_pages)`.

## FTP fulfillment behaviour

- **`originals/` vs `/originals/`** — the leading slash matters. Relative puts files in a
  subfolder inside the per-order folder; absolute puts them in a top-level folder at the FTP root.
- **Original customer uploads are not sent by default.** Only generated production files go. A
  fulfillment template named exactly `_additional_files.json` (leading underscore included) is
  required to include them. The payload schema is environment-specific — ask the platform team.
- **Every custom field value inserted into a JSON job ticket needs `| escape_json`.** A value
  containing a quote, backslash or newline otherwise produces invalid JSON and the job ticket
  fails, sometimes silently.
- **The job ticket folder must be named exactly `Job Tickets`**, that capitalisation, or FTP
  routing fails.

## Before delivering a definition

- [ ] One measurement system for the whole product
- [ ] Exactly one `grow="true"` set, if the product grows at all
- [ ] Preview set hidden from editor and excluded from fulfillment
- [ ] `output-name` grouping produces the file split production expects
- [ ] Separate layers restricted with `separate-layers` so no blank pages ship
- [ ] For a custom tool product: one set, one page, `fulfillment="false"`
- [ ] Booklet page counts divisible by 4
- [ ] A real order placed through to the delivered fulfillment package, not just a proof

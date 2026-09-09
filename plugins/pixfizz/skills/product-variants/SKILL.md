---
name: product-variants
description: Creating and debugging Pixfizz product variants and template options - the choices a customer makes on a product page. Use when adding a size, finish, paper, wrap, backing, quantity tier, imprint line, upload slot or any other selectable choice to a product; when deciding whether something belongs on the Product Attribute as a variant or on the Template as an option; when a choice does not appear, appears twice, cannot be changed, shows the wrong price, or renders as the wrong control; when building a conditional choice that only appears after another one is picked; or when an options or variants archive fails to import. Trigger for any mention of 'variant', 'variant type', 'variant value', 'template option', 'option type', 'multiple choice', 'value_type', 'trigger value', 'child option', 'selector', 'swatch', 'toggle', 'quick quantity', 'element substitution', 'default value', 'hide from cart', or a product page where a choice is missing, stuck, unpriced or ugly.
---

# Pixfizz Variants and Template Options

## Overview

A variant and a template option are the **same mechanism** attached to different
objects. Both are an `OptionType` with a list of `OptionValue`s. Which object you
hang it on decides who inherits it and where the price lives.

Two authority levels run through this skill and they are marked throughout:

- **Platform** — Pixfizz CMS behaviour. True on every site.
- **Shopper** — how the Shopper template renders it. Not true of a custom
  storefront or the Shopify path.

## 1. Variant or template option — settle this first (platform)

| | Variant | Template option |
|---|---|---|
| Lives on | Product Attribute | Template (or Design) |
| Is for | commercial choices that affect price — size, finish, backing | production-level choices — imprint text, foil, an upload the press needs |
| Inherited by | that one product | every Product Attribute sharing the Template |
| Rendered from | `product.variants` | `design.template_options` |

The split exists to avoid redundancy when several Product Attributes share one
Template. **Common production choices go on the Template once; commercial choices
go on each Product Attribute.**

Two consequences worth stating out loud before building:

- **A static product cannot carry template options.** Static Product Attributes have
  no Template link. If the choice has to be a template option, the product has to be
  a design product.
- Putting a priced choice on the Template pushes that price onto every product
  sharing it. That is occasionally what you want and usually not.

## 2. The seven types (platform)

The admin dropdown offers seven. In Liquid and in an export they appear as:

| Type | Value in export / Liquid | Needs |
|---|---|---|
| Multiple Choice | `multiple_choice` | a list of values; this is the default rendering path |
| Text | `text` | optional `placeholder`, `min_length`, `max_length`, `pattern` |
| Number | `number` | `min`, `max`, `step`, and see the unresolved item at the bottom of this file |
| Color | `color` | a `color_palette`, or it falls back to a raw colour input |
| Font | `font` | a `font_palette` |
| Image Upload | `image_upload` | optional `crop_aspect_ratio`, `target_element_names` |
| File Upload | `file_upload` | optional `accept` |

**Only `multiple_choice` has values.** `option_type.values` is `nil` on every other
type, so anything that needs a price per choice must be `multiple_choice`.

`default_value` is meaningful on number, color and font only. `placeholder` on text
and number. `target_element_names` on text and image_upload — that is how a text
option gets printed into a named element on the page.

**A text option caps around 2 KB.** Anything larger belongs in a `file_upload`
carrying a JSON file. *(Observed on real builds; the exact cap is not documented.)*

## 3. Children and triggers (platform)

An option can have children, and a child appears only when the parent's
`trigger_value` is chosen. `option_type.trigger_value` is the `OptionValue` that
reveals it, and is `nil` on anything that is not a child.

This is how a colour-wrap choice reveals a colour picker only when the customer
picks "Colour", and how a size choice reveals a size-specific sub-choice. Shopper
renders children recursively, so nesting works to any depth — but each level is
another decision on the page, so keep it to one.

**A required upload behind a trigger kills Add to Cart.** If a child `file_upload`
is marked required and its parent value is not selected, the form can be
unsatisfiable while looking complete. Do not mark a triggered upload required
unless the trigger value is also the default.

## 4. How Shopper renders them (Shopper)

Multiple Choice is the default path and renders as radio tiles. Everything else
renders by type — unless `option.custom.selector` overrides it:

| `custom.selector` | Applies to | Renders as |
|---|---|---|
| `textarea` | text | a 4-row textarea instead of a single line |
| `color` | multiple_choice | radio swatch tiles, colour read from each `value.custom.hex` |
| `checkbox` | multiple_choice | a checkbox; the **first value** is the checked state |
| `dropdown` | multiple_choice | a `<select>`, showing `value.custom.price_label` or the formatted `value.price` |
| `dropdown` | color with a palette | a scrollable list of swatch + colour name |
| `slider` | multiple_choice | a range input labelled from a code-to-name map |
| `quick-quantity` | multiple_choice | a grid of numeric inputs, one per value |
| `toggle` | multiple_choice with **exactly 2** values | a CSS-only animated switch |

`quick-quantity` is the one to reach for when a customer buys several sizes or
finishes at once, instead of adding a line item per combination.

`toggle` falls back to normal radio rendering if the value count is not exactly
two, so it cannot break the form. Mark one of the two as default or the initial
state is unpredictable. It is **not wired into the cart snippet**, where a 2-value
option falls back to a `<select>`.

Other custom fields that change behaviour: `custom.hidden` (hidden entirely),
`custom.kiosk_mode_only` (shown only in kiosk mode), `custom.multi_upload_group`
(grouped multi-image upload), `custom.accept` (upload constraints),
`custom.toggle_hide_labels` (bare switch, toggle only), and `custom.custom_script`
(injects a snippet — real, and the mounting point for custom design tools).

**Custom fields are site-specific and do not inherit parent to child.** Set them on
the site the option actually lives on.

**In the cart, rendering is simplified**: text becomes a plain input, everything
else becomes a `<select>`. Children and triggers still work. A selector that only
exists in `product/px-options` will not be there.

## 5. Pricing (platform)

**The price goes on the variant *value*, never on the variant type and never on the
product.** The product carries the base; each value carries its own delta or
formula. This is the single most common mistake in this area.

Three rules that follow from it:

- **Ranges must cover the whole quantity span with no gaps.** `.find` returns nil
  outside a range and `.last` then raises `NoMethodError`, which takes out the whole
  product page, not just the price.
- **Priced values are per-unit, then multiplied by quantity.** A flat fee on a value
  is charged once per unit, so a fee that should be charged once needs the product
  forced to quantity 1.
- A value with no price is free and displays as no delta. That is the right shape
  for a choice that only changes production, not cost.

For the formula grammar itself, use the `pricing-formulas` skill in this plugin.
This skill covers where the formula lives; that one covers what it says.

**Shopper display note:** `dropdown` shows the price delta next to each value.
`toggle` does not - if a toggle value carries a price, put it in the value name or
use `dropdown` instead.

## 6. Element substitutions — a value that changes the artwork (platform)

A value can carry an `element_substitution` that swaps something on the page when it
is selected. The useful form is `substitution_type: layout` with an
`element_name` and a `content` naming the **layout to substitute in**.

**Name-based substitutions are portable; id-based ones are not.** A substitution
that names a layout survives being copied to another size, another product, or a
whole generated range, because the name resolves at render. Anything keyed on an id
has to be remapped every time. Always author these by name.

`option_type.has_element_substitutions` is true when the option or any of its
children carries one, which is the quick way to find them on an existing site.

## 7. Building them by export rather than by hand (platform)

For more than a handful of values, or the same set across many products, exporting,
editing and re-importing beats clicking. The traps below are all real and all
silent — each one has shipped at least once.

- **The field is `value_type`, not `type`.** The export does not use the Liquid name.
- **`hidden`, `read_only` and `hide_from_cart` live inside `custom`**, not at the top
  level. Set at the top level they are ignored, and nothing warns you.
- **Unset booleans export as quoted strings.** An unset boolean comes out as
  `'false'`, and a non-empty string is truthy, so it imports as **true**. Re-check
  every boolean after any import.
- **Quote any string that contains a comma or consists only of digits**, and disable
  YAML alias generation, or repeated values collapse into anchors.
- **`read_only: true` renders a display chip plus a hidden input.** Anything trying
  to write that option silently no-ops. Never set it on an option a script or a
  custom tool writes.
- **`hide_from_cart: true` on every file upload**, or the customer sees `db:374` in
  their cart.
- **`target_element_name` can point at nothing.** An imprint option bound to an
  element name that exists on no page imports cleanly and does nothing. Check the
  binding; do not invent the element.
- **An option type that no reference export contains is unvalidated.** The
  diff-against-a-real-export habit cannot catch a presence validation on a field no
  sample has ever carried. Before generating one, create a minimal option of that
  type by hand in admin, export it, and diff against that.

**Re-importing does not update, it duplicates.** The admin assigns new ids on import
and appends `-1`, `-2` to both the **code and the name** on a collision. Because the
suffix lands on the code, a silent duplicate import breaks any Liquid or collection
path referencing that code. Correcting a bad import means deleting the old object
first, and checking for `-1` suffixes after any batch.

## 8. The single-value pill (Shopper)

A variant type with exactly one value is auto-selected, so it picks up the theme's
selected state and renders as a large dark pill that looks interactive but cannot be
changed. Four fixed specifications become four stacked blocks of roughly 190 px,
which pushes quantity and Add to cart below the fold.

This hits any product whose specification is fixed per SKU, which is most
web-to-print. If the value is fixed, either do not make it a variant at all, or
style the single-value case down to a static specification line. The value columns
are light-DOM children of `px-option-selector`, whose shadow root is only a `<slot>`,
so `style/custom.css` reaches them normally — no `::part()` needed.

## 9. Before you ship

- Right object: commercial on the Product Attribute, production on the Template.
- Every priced choice is `multiple_choice`, and the price is on the **value**.
- Quantity ranges are gap-free across the whole span.
- One value is marked default on every choice the customer should not have to make.
- Booleans re-checked after import, not assumed.
- Every `target_element_name` resolves to a real element.
- The cart shows what the customer chose, and does not show `db:` ids.
- Tested on a staging site with a real add-to-cart, not just a product page load.

## Unresolved — do not state either side as fact

**Number options and `default_value` carry a contradiction that has not been
settled.** The importer rejects a `number` option with a blank `default_value`:
*"Validation failed: Default value can't be blank"*. But a separate finding, from
live use, records that a number option carrying a default fails add-to-cart with
*"value is a required field"*, including in point of sale.

Both cannot stand unqualified. The possibilities are that the add-to-cart failure
was observed on admin-created options and admin permits what the importer does not;
that the add-to-cart failure had another cause; or that both are true and the type
is import-hostile. Until someone imports a number option and takes one order through
the cart, say so rather than picking a side.

---
name: liquid-patterns
description: Pixfizz-specific Liquid templating rules, patterns, and known pitfalls for
  Shopper storefront development. Use this skill whenever writing, reviewing, or debugging
  any Liquid, HTML, or CSS for a Pixfizz Shopper site — including snippets, sections,
  custom type loops, option rendering, JS re-injection, CSS delivery, and redirect config.
  Trigger for any Shopper template work even if the user does not explicitly mention Liquid
  — if they are working on a snippet, a page, a CSS file, or a CMS block, this skill
  applies. Always check this skill before suggesting any Liquid filter, sort pattern,
  JS injection method, or CSS placement approach. After completing significant template
  work, flag any newly discovered patterns or pitfalls for addition to this skill.
---

# Pixfizz Liquid Patterns — Shopper Storefront Reference

## Skill Evolution

After completing significant template work, flag new patterns, gotchas, or filter behaviours
worth capturing. Confirm with user before treating as established guidance.

---

## Code Governance (Non-Negotiable)

These rules apply to every piece of code delivered to a Pixfizz Shopper site. Full detail is in
`01_CODE_GOVERNANCE_UPDATED.md` in the Pixfizz knowledge base (github.com/pixfizz/pixfizz-knowledge).

- **Bootstrap 4.6** — not 5. Use 4.6 utility classes and components.
- **Hard tabs** — not spaces.
- **`currency` filter** — never `money`.
- **`asset_url` conventions** — use Pixfizz conventions for image URLs.
- **Block boundaries** — all code blocks must have `{% comment %}===== START: ... ====={% endcomment %}` and matching END markers.
- **Full block replacement** — always return the complete updated block. Never return partial edits or ask the user to merge fragments.
- **Code change output scale** — small/targeted edits → numbered find/replace instructions. Larger structural changes → full block. Never default to full blocks for minor edits.
- **CSS/Liquid split** — CSS goes in `style/custom.css` only. Never write CSS inline in Liquid/HTML snippets.
- **Shared snippet contract** — if a snippet is used across multiple live sites, do not remove existing variables, IDs, or JS hooks. Add defensively. Breaking a shared snippet can affect many production sites simultaneously.

---

## CSS Delivery

- The CSS page lives at `/site/custom.css` and is loaded via `<link>` in `html.head`.
- **All custom CSS goes in `style/custom.css`** — the per-site stub snippet.
- `request.path` inside `style/custom.css` always resolves to `/site/custom.css` (a
  separate HTTP request). It cannot be used for page-specific logic in that file.
- For path-specific inline styles, use `integrations/custom-body-scripts` instead.
- CSS scoping: always scope custom rules to a page-specific parent class. Never use
  generic selectors like `.card` without a scoped parent — cross-page side effects are
  common and hard to debug.

---

## Sort and Filter Rules

### The fundamental rule
`sort` only works reliably on `Paginate` objects — collections returned directly from
the platform (e.g. `website.custom_types[...]`, `user.orders`). It does **not** work
reliably on plain arrays built via `push`. Nested dot-notation keys (`'custom.my_field'`)
fail silently on push-built arrays — no error, unpredictable order.

**Rule: always apply `sort` at initial collection assignment. Never on a push-built array.**

### Correct sort + filter pattern
When you need to both sort and filter a Custom Type collection:

```liquid
{% assign all_items = website.custom_types['my_type'] | sort: 'custom.my_date_field' | reverse | page_size: 9999 %}
{% assign filtered_items = '' | split: ',' %}

{% for item in all_items %}
  {% if item.custom.some_condition %}
    {% assign filtered_items = filtered_items | push: item %}
  {% endif %}
{% endfor %}

{% for item in filtered_items %}
  {# filtered_items is already sorted — insertion order preserved from all_items #}
{% endfor %}
```

The `sort` executes in the database. Push inserts items in that pre-sorted order.
`filtered_items` inherits the sort without needing a second `sort` call.

### Date fields
Date fields used as sort keys must be ISO 8601 format (`YYYY-MM-DD`) for both `sort`
and string comparison (`<=`, `>=`) to work correctly.

### `service_position` field
All records must have this field populated. Records with nil values sort unpredictably.
Use high numbers (e.g. `99`) for items intended to appear last.

---

## JS Re-injection: `style onload` Pattern

### When to use
Any JS that must run on both initial page load and every subsequent AJAX re-injection.
Examples: checkout snippets inside `async: true` forms, snippets that re-render on
delivery option switches, any snippet where `<script>` tags are not reliably re-executing.

`<script>` tags inside AJAX-injected HTML do not re-execute. `style onload` fires on
every DOM insertion.

### Correct pattern
```liquid
{% capture my_init_script %}
(function() {
	var savedValue = '{{ some_liquid_var | escape }}';

	// setup and event listeners here

	// Always call init directly — DOMContentLoaded does not re-fire on AJAX:
	initMyThing();
})();
{% endcapture %}

<style onload="{{ my_init_script | escape }}"></style>
```

### Critical rules
- `{% capture %}` and `<style onload>` blocks must sit **outside** any `<script>` tag.
  Placing them inside a `<script>` block causes a syntax error and silently breaks all
  JS on the page.
- Always include a **direct call** to the init function at the end of the IIFE.
  `DOMContentLoaded` alone is not sufficient for AJAX re-injection.
- Use `removeEventListener` before `addEventListener` on elements that persist across
  re-injections, to avoid stacking duplicate handlers.
- Bake Liquid server values into the IIFE via `{{ variable | escape }}`.

### `onload = null` anti-pattern — never use
Setting `styleElement.onload = null` inside the handler cancels all future firings after
the first. Symptom: works on first load, stops responding after any re-injection.
Fix: use a plain IIFE, no arrow function wrapper, no `onload = null`.

### Once-per-load guard (`window.__flag`)
For logic that must fire only once per full page load (not on every re-injection):

```liquid
{% capture px_once_init %}
(function() {
	if (window.__pxMyThingShown) return;
	window.__pxMyThingShown = true;
	// logic here
})();
{% endcapture %}
<style onload="{{ px_once_init | escape }}"></style>
```

Use a flag name specific to the feature. Guard must be the **first line** of the IIFE.

### `sessionStorage` variant
For guards that must persist across page navigations within the same tab session:

```javascript
(function() {
	if (sessionStorage.getItem('pxMyThingShown')) return;
	sessionStorage.setItem('pxMyThingShown', '1');
	// logic here
})();
```

Use `sessionStorage` when `window.__flag` is cleared too early (on full page reload).

### When to use a plain `<script>` instead
Logic that should run **once** on full page load and does not need to survive AJAX
re-injection (e.g. postcode lookup, checkbox validation) belongs in a standard `<script>`
with `DOMContentLoaded`.

---

## Nested Forms Pitfall

The Shopper checkout page wraps everything in an outer `cart_update` form. Any
`address_create` or `address_update` form nested inside it is silently dropped by the
browser — only the outermost form processes on submit.

Symptom: address form Save button does nothing, no network request fires.
Fix: replace inline nested forms with redirect links to standalone address pages.

---

## Key Liquid Filters (Pixfizz-specific)

| Filter | Notes |
|---|---|
| `currency` | Always use this. Never `money`. Respects website currency config. |
| `sort` | Works on Paginate objects only. Fails silently on push arrays. |
| `where` | Works on Paginate objects. Supports `'custom.field', 'value'` and drill-down. |
| `push` | Adds one item to an array. Push-built arrays cannot be reliably re-sorted. |
| `page_size` | Sets page size on a Paginate object. Use `page_size: 9999` to fetch all. |
| `thumbnail_url` | Returns thumbnail URL from an Image object. Default 250px. |
| `cms_url` | Returns URL to a CMS page, collection, or product. |
| `preview_url` | Returns preview URL for a Project. Email use requires `share:` code. |
| `design_tool_url` | Returns editor URL for a Project. |
| `asset_url` | Use Pixfizz conventions. `cdn: false` for email image src. |
| `t` | Translation filter. Supports `ns:` and `locale:` params. |
| `parse_json` | Parses a JSON string into a Liquid object. |
| `escape_json` | Escapes a string for use inside JSON. Still requires surrounding quotes. |

---

## Key Objects Quick Reference

| Object | Notes |
|---|---|
| `website.custom_types['type']` | Returns Paginate collection of Custom Type instances |
| `request.path` | In `style/custom.css` always resolves to `/site/custom.css` |
| `request.params` | Access query params: `request.params.key` or `request.params['key']` |
| `cart.orderlines` | Loop with `{% for orderline in cart.orderlines %}` |
| `design.template_options` | Paginate collection of published top-level option types |
| `form.values` | Submitted field values inside a `{% form %}` block |

---

## Option / Variant Rendering

### `option.type` values
`text`, `number`, `color`, `font`, `image_upload`, `file_upload`, plus Multiple Choice
(the default rendered as radio buttons unless overridden by `option.custom.selector`).

### `option.custom.selector` overrides
| Selector | Renders as |
|---|---|
| `textarea` | `<textarea rows="4">` (for text options) |
| `color` | Radio buttons with SVG swatch tiles; uses `value.custom.hex` |
| `checkbox` | `<input type="checkbox">` using first value |
| `dropdown` | `<select>` with optional price labels |
| `slider` | `<input type="range">` |
| `quick-quantity` | Grid of numeric inputs per value (matrix purchasing) |

### Key option flags to check when debugging
- `option.custom.kiosk_mode_only` — only shown in kiosk mode
- `option.custom.hidden` — completely hidden
- `option.trigger_value` + `option.children` — conditional display / nesting
- `option.has_pricing` / `option.has_element_substitutions` — controls component flags
- `option.custom.multi_upload_group` — groups multiple upload options into one experience

---

## Snippet Conventions

- Snippets are rendered via `{% snippet 'snippet-name', param: value %}`.
- If a snippet is not found, an error is thrown unless `fallback_content: ''` is provided.
- **Home page custom content**: goes in `website/homepage` snippet. Requires the
  "Custom snippet (website/homepage) for home page" checkbox ticked in Admin → Storefront Settings.
  Both snippet and checkbox are required.
- **Kiosk-only options**: check `option.custom.kiosk_mode_only` via `helpers/is-kiosk-mode`.

## Component Notes

- **`px-project-preview` shadow DOM**: internal image is in shadow DOM. Style via
  `px-project-preview::part(img)` — `height: 100%` on the component element has no effect.
- **`px-image-upload`**: sources vary (`local galleries qr`). Supports crop aspect ratio,
  minimum DPI, accept types, and image adjustment flags from admin checklist.

---

## Hero Background Overlays

Do not use `background-blend-mode: multiply` with `bg-dark`. Use a semi-transparent
`rgba` overlay `<div>` with `position: absolute` instead:

```html
<div style="position: absolute; inset: 0; background: rgba(0,0,0,0.35); z-index: 1;"></div>
```

Starting point: `rgba(0,0,0,0.35)`. Adjust alpha to taste. Hero container must be
`position: relative`. Text content must have higher `z-index` than the overlay.

---

## Megamenu (style3 nav)

Full-width card dropdowns require `position-static` on the parent
`<li class="nav-item dropdown">`. Without it, Bootstrap sizes the dropdown to the nav
label width, collapsing text vertically.

---

## Redirects

Pixfizz redirect format: JSON array of arrays with regex patterns.

```json
[["^/old-path/?$", "/new-path"]]
```

- Start anchor `^`, optional trailing slash `/?`, end anchor `$`.
- System paths (cart, checkout, account, order-confirmation) do not need redirects.

---

## Dawn (Shopify) Integration Notes

When working on Shopify + Pixfizz sites using Dawn theme:

- Dawn overwrites `innerHTML` of elements with class `product-form__add-button` after
  variant changes. Fix: rename the Pixfizz button class to `pixfizz-launch-btn` so
  Dawn's update logic does not target it.
- Pixfizz editor iframe constraint: `style/custom.css` cannot reach editor-internal
  elements (`.px-header`, `.px-cart-button`) — the editor runs inside an iframe.

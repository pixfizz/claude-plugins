---
name: shopify-integration
description: "The Shopify + Pixfizz deployment path, where Shopify owns storefront, cart and checkout and Pixfizz owns personalization and order orchestration. Use this skill whenever working on a Shopify store connected to Pixfizz: metafield setup, product linking, integration types, the theme snippets, the Personalize button, cart previews and addon rows, quantity handlers, order webhooks, static product ingestion, or draft order flows. Trigger for any mention of 'Shopify', 'Dawn theme', 'metafield', 'pixfizz.product_sku', 'integration_type', 'Personalize button', 'cart preview', 'addon product', 'order webhook', 'line item property', or a Shopify cart or order that is not behaving. Also trigger when scoping or onboarding a client onto the Shopify path rather than Full Pixfizz."
---

# Shopify + Pixfizz Integration

Shopify owns storefront, cart, checkout and payment. Pixfizz owns personalization, project
storage, and production and order orchestration.

Authoritative source: `60_SHOPIFY_INTEGRATION.md` in the Pixfizz knowledge base
(github.com/pixfizz/pixfizz-knowledge). Buy Now / Personalize Later draft order flows are in
`62_SHOPIFY_BUY_NOW_PERSONALIZE_LATER.md`. This skill is the working procedure and the fault
index; those files carry the full snippet listings.

## Architecture in one pass

- Pixfizz runs on a **subdomain of the Shopify store's own domain** — `create.myprintshop.com`.
  It must be a custom hostname, **not** the default `*.pixfizz.com` subdomain. Half the
  "Pixfizz is not defined" reports trace back to this.
- `api.js` loads from the Pixfizz host into every Shopify page and provides the
  `Pixfizz.Shopify.*` methods every snippet uses.
- Customer identity passes from Shopify to Pixfizz as an MD5 hash of customer ID and email,
  signed with a shared secret from Pixfizz superadmin API Settings.
- Order paid in Shopify → webhook → Pixfizz marks the order **Confirmed**. Order fulfilled in
  Shopify → optional second webhook → **Shipped**.

## Product linking — get this right first

| Product shape | Where the SKU goes |
|---|---|
| **Without** Shopify variations | `pixfizz.product_sku` on the **product** |
| **With** Shopify variations | `pixfizz.product_sku` on **each variant**. Product level is fallback only |

`pixfizz.integration_type` always sits on the product. SKU format is `theme-code:product-code`,
no spaces, no typos. Shopify's "Track QTY" must be **disabled**. For photo prints, set
`pixfizz.adjust_cart_qty` to `false`.

**Edit ID-mapping CSVs in a plain-text editor, never Excel.** Excel silently reformats long
numeric Shopify IDs into scientific notation and corrupts the mapping.

## Integration types

Set on `pixfizz.integration_type`; defaults to `editor` when blank.

| Value | Behaviour |
|---|---|
| `editor` | Straight into the Pixfizz editor. Default. Photo books, full customisation |
| `options-to-editor` | Options first (e.g. calendar start month), then the editor |
| `options-to-cart` | Live preview modal, options and preview, no full editor. Notebooks, simpler products |
| `photo-prints` | The photo prints flow. Quantity is set inside Pixfizz, not the Shopify cart |

## Cart item properties

Pixfizz sets these line item properties; they drive every cart-page behaviour. The underscore
prefix hides them from customer display, and the cart template filters them via
`property_first_char != '_'`.

| Property | Meaning |
|---|---|
| `_pixfizz_project_id` | The Pixfizz project. Present on every personalized item |
| `_pixfizz_addon` | On addon lines; its value is the parent's `_pixfizz_project_id` |
| `_pixfizz_unit_quantity` | Per-unit quantity of an addon, used to scale it with the parent |

## The five theme snippets

All are rendered by `{% render %}` from the product template and cart page.

| Snippet | Where | Does |
|---|---|---|
| `pixfizz-setup` | `theme.liquid`, before `</head>` | Loads `api.js`, passes signed customer identity |
| `pixfizz-launch-product-handler` | Product page, in the button's `onclick` | Maps variant IDs to Pixfizz SKUs and addons, calls `launchProduct` |
| `pixfizz-orderline-preview-handler` | Cart, immediately after the `<img>` in `cart-item__image-container` | Swaps the static image for a live project preview |
| `pixfizz-edit-orderline-handler` | Cart | Edit routing back into the editor |
| `pixfizz-orderline-quantity-handler` | Cart quantity `<input>` onchange | Keeps addon quantities in step with the parent |

The launch handler's `form = document.querySelector('form[action*="/cart/add"]')` selector is
Dawn-shaped and may need adjusting on other themes. The preview handler uses `<style onload>` so
it re-fires on cart AJAX injection — the same pattern as the rest of the platform, and for the
same reason.

## Order sync

- **Payment webhook, required.** Event: **Order payment** — not Order creation. JSON. URL
  `https://<pixfizz-host>/webhooks/shopify/orders`.
- **Fulfillment webhook, optional.** Event: Fulfillment Creation. Same endpoint pattern.
- After creating the webhook in Shopify (Settings → Notifications), copy the signing secret into
  Pixfizz superadmin → Website → API Settings → Shopify Signing Secret.
- Pushing a status change into Pixfizz from Shopify Flow or any external automation uses HTTP
  **PUT**, not POST.
- A synced project with no owner is assigned to the account that placed the order.
- **All** Shopify line item properties are now captured into the Pixfizz orderline's `options`,
  not only the Pixfizz-specific ones.

## Static (non-personalized) products

Stores selling frames, film and accessories alongside personalized products can route every line
item into the Pixfizz order.

1. Create a `pixfizz.static_product_code` text metafield on Products, and optionally on Variants.
2. Create matching static products in Pixfizz whose `code` equals the metafield value.
3. Inject a hidden `_pixfizz_static_product` line item property in the product form. Variant-level
   metafield first, product-level as fallback — the same precedence as `product_sku`.
4. The payment webhook reads the property and creates the orderline.

Dawn v14 puts this in `snippets/buy-buttons.liquid`, inside the product form. Other themes differ.

**Two failure modes worth knowing before you debug this:**

- **An options or bundle app can break ingestion silently.** If such an app expands one cart line
  into a bundle parent plus component lines, all stamped with the same `_pixfizz_static_product`,
  the webhook does not create an order from that grouped shape and the static orderline never
  lands. A plain single-variant product ingests fine. Check for a bundle app before suspecting the
  metafield.
- **Duplicate `const line` declarations.** If the injection snippet loops qualifying lines in
  Liquid and declares `const line` once per line in the same script scope, two static-product lines
  in one cart produce a syntax error. Inline the values into the pushed object instead.

## Fault index

| Symptom | Cause to check first |
|---|---|
| `Pixfizz is not defined` | `pixfizz-setup` not in `theme.liquid` before `</head>`, or the host is `*.pixfizz.com` instead of the custom subdomain |
| No project preview in cart | Handler not immediately after the `<img>`; `_pixfizz_project_id` missing; snippet placed inside a `<script>` tag so it does not re-fire after AJAX |
| Edit link not firing on image click | The `<a>` needs `style="z-index:1;"` — the image container otherwise sits above it and swallows the click |
| Addon quantities not following the parent | Quantity handler missing from the drawer cart or other quantity controls, not just the main cart; `_pixfizz_unit_quantity` absent |
| Quantity selector showing on photo prints | `pixfizz.adjust_cart_qty` must be boolean **False**, not the string `"false"` — the template checks `.value == false` |
| Addon rows rendering independently | The `_pixfizz_addon` `{% continue %}` guard must be at the very top of the cart loop, before the `<tr>` opens |
| Orders not confirming after payment | Webhook on "Order creation" instead of "Order payment"; signing secret mismatch; host mismatch in the URL |
| "Personalize" reverts to "Add to cart" after a variant change | Dawn's Section Rendering API overwrites `innerHTML` of `product-form__add-button`. Rename the class to something like `pixfizz-launch-btn` |
| Customer gets two order emails | Both systems are notifying. Blank the redundant Pixfizz templates for lifecycle events Shopify already covers |
| Static products not landing in Pixfizz | Bundle/options app restructuring the line; property name mismatch; no matching static product `code` |

## Scoping notes

- **Third-party option apps have their own limits.** Globo Product Options caps variant counts and
  complex setups can exceed it. Fall back to Shopify core variants, or move option selection to a
  Pixfizz Shopper frontend instead of the Shopify product page.
- **Theme matters.** Documented cart work targets Dawn; Focal/Maestrooo and Horizon differ, and
  JSON-template themes differ from Liquid-template themes for variable pages. Confirm the theme
  and its version before quoting cart work.
- **Buy Now / Personalize Later** is a separate draft-order flow with its own compatibility
  constraints — check `62_...` before promising it on a given theme.
- Pixfizz CSS cannot reach editor-internal elements; the editor runs inside an iframe.

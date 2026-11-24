---
name: price-cards
description: "px_rates price cards: the JSON on a Pixfizz product that prices custom size, document and booklet products the same way on the website, in OrderHub and at the POS. Use when creating a product priced by size (prints, canvas, banners, magnets, vinyl, foam board, coroplast, any substrate), making a counter-only product that staff order in OrderHub but customers never see on the website, adding a material to an existing custom size product, changing rates, or when OrderHub or the website says a product is not set up or cannot be priced. Trigger for 'px_rates', 'price card', 'rate card', 'priced by area', 'per square foot', 'per square inch', 'custom size', 'counter product', 'OrderHub only', 'POS only', 'hidden product', 'engine', or a px_ product with a wrong or missing price."
---

# px_rates price cards

A price card is a JSON value in the product custom field `px_rates`. One engine (`pricing.js`)
reads it on the website, in OrderHub and at the POS, so a size priced at the counter and the same
size bought online always cost the same. There is no Ruby formula on these products.

Platform-level rule (Pixfizz CMS and OrderHub). Authoritative reference: `30_PRICING_ENGINE.md`
and `45_ORDERHUB.md` in github.com/pixfizz/pixfizz-knowledge. Never invent a rate: rates come
from the lab owner. If one is missing, ask for it; do not guess.

## Hard rules

1. **Rates change by editing `px_rates` only.** Never add a Ruby price formula, a variant value
   price or a product price to a `px_` product. OrderHub cannot evaluate Ruby, so a formula
   breaks counter pricing even when the website cart looks right.
2. **Every card carries `"engine"`.** No engine key = refused. Use `"engine": 4` on a
   counter-only product. On a product that is **on the website**, use the number the product
   already has unless Pixfizz tells you otherwise: the website tool bundles its own copy of the
   engine and refuses a card whose number is higher than its copy (the product page then shows
   the product as not set up). If that happens, put the number back.
3. **Codes must match exactly.** Each `stocks[].code` equals a value code of the `px_stock`
   variant. Each extra's value key equals a value code of its variant. A mismatch gives the
   reason `order-line` and no price.
4. **The engine does not check sizes.** Minimum and maximum width and length are the `min` and
   `max` on the `px_width_in` and `px_height_in` variants. Set them on every product.
5. **Live site.** Show the lab owner the card (old and new) and wait for a clear go before
   writing it. After writing, read the product back and confirm the card matches.

## Card format: mode `area` (anything sold by size)

```json
{"name":"<product name>","mode":"area","engine":4,"card_version":"<date and who confirmed the rates>","currency":"USD","unit":"sq_ft","tiering":"whole","stocks":[{"code":"magnet","label":"Magnet","tiers":[{"rate":11}]}],"extras":[]}
```

- `unit`: `sq_in` (default) or `sq_ft`. Width and height always arrive in inches; the unit only
  sets what a rate is per.
- `stocks[]`: one entry per material. `tiers[]` are bands in the card unit: `{"to": 4, "rate": 12}`
  then `{"rate": 10}`. `to` is exclusive and the last band has no `to`. One band with no `to` =
  one flat rate.
- `tiering`: `whole` charges the whole area at the rate of the band it lands in (bigger sizes
  can come out cheaper at a band edge, say so to the owner). `graduated` (default) charges each
  slice of area at its own band's rate.
- Optional per stock: `min` (minimum charge per item) and `base` (fixed amount per item, added
  before the minimum).
- `extras[]` (optional), each tied to a variant:
  `{"variant":"px_grommets","label":"Grommets","values":{"none":{},"corners":{"grommet":0.75}}}`.
  A value can carry `each` (per item), `rate` with optional `min` (per area unit), `lin_ft` with
  `edge` (`long`, `short`, `both`, `perimeter`), or `grommet` (per grommet).
- Rounding: whole cents, half up.

Worked check, `sq_ft`, one band at 11: 12 x 24 in = 288 sq in = 2 sq ft = 22.00. 24 x 36 in =
6 sq ft = 66.00. Always work three sizes by hand like this and show them to the owner.

## The variants a px_ product needs

| Code | Type | Purpose |
|---|---|---|
| `px_width_in` | number | Width in inches. Set `min` and `max`. |
| `px_height_in` | number | Height in inches (label it "Length (in)" for roll goods, keep the code). Set `min` and `max`. |
| `px_stock` | multiple choice | One value per material; value code = stock `code`. |
| `px_price` | number, hidden, `pos_hidden` true | Carries the computed unit price. |

Plus one variant per extra (`px_grommets`, `px_hanging`, `px_depth`, `px_edge`, `px_edgecolor`)
only if the product sells it. Never rename these codes.

## Recipe A: add a material to an existing counter-only product

Use when the new material has the same size limits and extras as the product.

1. Read the product (Pixfizz connector `product_get`). Note the card and the `px_stock` values.
2. Add the value to `px_stock` in admin (Products, the product, the Material variant, add value).
   Code: short, lowercase, no spaces, for example `foam-316`.
3. Add the matching entry to `stocks[]` in the card, same code. Update `card_version`.
4. Show the owner the old and new card and three hand-worked prices. On a go, write the card
   (connector `product_update` on `custom.px_rates`, then `apply_change`) and read it back.
5. Test at the till (below).

## Recipe B: a new counter-only product

Use when the size limits or extras differ from every existing product.

1. In admin, Templates screen, export an existing counter-only custom size product from the same
   site. Its `__print_product.yml` carries the variants, the card and the template options.
2. In the export, change: template `name` and `code`; product `code` and `name`; theme `name`,
   `code` and `url_path`; the XML page size (largest size, in inches).
3. Replace `px_rates` (under `products[].custom.px_rates`) with the new card, `"engine": 4`.
4. Set `min` and `max` on `px_width_in` and `px_height_in`.
5. `px_stock` values: one per material, code = stock code. Remove any extra variant the
   product does not sell, and remove it from `extras[]`.
6. Leave the template options as they are in a counter-only export. If you started from a
   **website** product instead, remove the website-only options `px_mount` and `px_place`, keep
   `px_print_file`, `px_original`, `px_spec` and `px_preview`.
7. Product custom `hide_from_search: true`. Import on the Templates screen. **Do not publish the
   template to any collection**: that keeps it off the website.
8. Read the new product back with the connector: code, name, card, min/max, material values,
   `hide_from_search`.
9. Test at the till (below).

Never delete and re-import a product to change its rates or materials: edit the card and the
variant values in place.

## Test at the till

1. In OrderHub, refresh the product catalog so the new product or material appears.
2. Start a custom order, pick the product, type a width and length, pick the material.
3. The price must equal your hand-worked price for three sizes. Try one size over the maximum
   and note whether the till blocks it.
4. Report each result to the owner. If the product is missing or shows no price, send Pixfizz
   support the product id, the size and what OrderHub showed.

## When a card is refused

| Reason | Meaning |
|---|---|
| `no-card` | `px_rates` is empty or not valid JSON |
| `bad-engine` | `"engine"` missing or not a number |
| `engine` | the card needs a newer engine than the website tool or OrderHub has |
| `mode` | `mode` is not one the engine knows |
| `unpriced` / `not-priced` | a material or size has no band that covers it |
| `order-line` | a variant value code does not match a stock or extra code |
| `bad-unit` | `unit` is not one the engine knows |

## What needs Pixfizz

- Website custom size tools (the customer-facing size builder) and their landing pages.
- Raising `"engine"` above 4, or a card mode other than `area` on a new kind of product.
- OrderHub not listing a product, or not pricing a card that passes every check above.

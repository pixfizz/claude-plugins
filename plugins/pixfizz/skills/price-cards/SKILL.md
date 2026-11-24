---
name: price-cards
description: "px_rates price cards: the JSON on a Pixfizz product that prices custom size, document and booklet products the same way on the website, in OrderHub and at the POS. Use when creating a product priced by size (prints, canvas, banners, magnets, vinyl, foam board, coroplast, any substrate), setting or changing booklet rates (per page, paper, color, staple or coil binding, covers), making a counter-only product that staff order in OrderHub but customers never see on the website, adding a material to an existing custom size product, changing rates, or when OrderHub or the website says a product is not set up or cannot be priced. Trigger for 'px_rates', 'price card', 'rate card', 'priced by area', 'per square foot', 'per square inch', 'booklet price', 'per page price', 'custom size', 'counter product', 'OrderHub only', 'POS only', 'hidden product', 'engine', or a px_ product with a wrong or missing price."
---

# px_rates price cards

A price card is a JSON value in the product custom field `px_rates`. One engine (`pricing.js`)
reads it on the website, in OrderHub and at the POS, so a size priced at the counter and the same
size bought online always cost the same. There is no Ruby formula on these products.

Platform-level rule (Pixfizz CMS and OrderHub). Authoritative reference: `33_PX_RATES_PRICE_CARDS.md`
(card format for every mode, engine rules, check list), `30_PRICING_ENGINE.md` and `45_ORDERHUB.md`
in github.com/pixfizz/pixfizz-knowledge.

## Which engine runs where (24 Nov 2026)

| Mode | What it prices | Website | OrderHub and POS |
|---|---|---|---|
| `area` | custom sizes, counter products | yes | yes (engine 4) |
| `booklet` | booklets: per page or per sheet, papers, covers, bindings | yes | yes (engine 4) |
| `flat` | documents and copies | yes | yes (engine 4) |
| `prints`, `forms`, `sheet` | Flat Prints, NCR forms, stickers | yes | not yet: needs engine 5, not installed in OrderHub yet |

A product in a mode OrderHub cannot price sells on the website but cannot be keyed in at the till. Never invent a rate: rates come
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
3. **Codes and names must match.** Each `stocks[].code` equals a value code of the `px_stock`
   variant, and its `label` equals that value's name. Each extra's value key equals a value code
   of its variant, and **each extra value carries a `"label"` equal to the value's name** when the
   name differs from the code (`"2ft":{"grommet":0.75,"label":"Every 2 ft"}`). OrderHub matches
   the order line by code or name; a value it cannot match gives `order-line` and no price at the
   till, even though the website prices it. Booklet and document choices (paper, color, binding)
   are matched by their `label`, so keep labels identical to what the product shows.
4. **The engine does not check sizes.** Minimum and maximum width and length are the `min` and
   `max` on the `px_width_in` and `px_height_in` variants. Set them on every product.
5. **Live site.** Show the lab owner the card (old and new) and wait for a clear go before
   writing it. After writing, read the product back and confirm the card matches.

## Card format: mode `area` (anything sold by size)

```json
{"name":"<product name>","mode":"area","engine":4,"card_version":"<date and who confirmed the rates>","currency":"USD","unit":"sq_ft","tiering":"whole","stocks":[{"code":"magnet","label":"Magnet","tiers":[{"rate":11}]}],"extras":[]}
```

- `unit`: `sq_in` (default) or `sq_ft` (`"engine": 1` is enough), or `sq_cm` / `sq_m` (need
  `"engine": 2` or higher). Width and height arrive in inches (or mm on metric lines); the unit
  only sets what a rate is per.
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

## Card format: mode `booklet`

Two shapes. Read the product's current card first and keep its shape.

**Simple booklet** (`"engine": 3`; `interior.rate_per` is `"page"`, has `bindings`, no `cover`):
price per booklet = pages x page rate + binding price.

```json
{"name":"Booklets 5.5 x 8.5","mode":"booklet","engine":3,"trim":{"w":5.5,"h":8.5,"label":"5.5 x 8.5 in"},"bleed":0.125,"printable_margin_in":0,"binding":{"code":"booklet","label":"Booklet","multiple_of":4,"min_pages":4,"pages_per_sheet":4},"overrun":{"pct":0},"interior":{"rate_per":"page","colors":[{"code":"bw","label":"Black & White","desc":"..."},{"code":"color","label":"Full Color","desc":"..."}],"print":{"bw":[{"min":1,"max":9999999,"rate":0.14}],"color":[{"min":1,"max":9999999,"rate":0.24}]},"papers":[{"code":"regular","label":"Regular (20 lb.)","desc":"..."},{"code":"gloss100","label":"Gloss (100 lb.)","desc":"...","print":{"bw":[{"min":1,"max":9999999,"rate":0.18}],"color":[{"min":1,"max":9999999,"rate":0.28}]}}]},"bindings":[{"code":"staple","label":"Staple Binding","desc":"...","bands":[{"min":1,"max":9999999,"price":0}]},{"code":"coil","label":"Coil Binding","desc":"...","bands":[{"min":1,"max":4,"price":3.75},{"min":5,"max":9,"price":3.0},{"min":10,"max":24,"price":2.63},{"min":25,"max":9999999,"price":1.88}]}],"volume_steps":[1,5,10,25,50,100],"defaults":{"int_color":"bw","int_paper":"regular","binding":"staple","copies":1,"blank_at":"obc"}}
```

- Page rate: `interior.print.<color>`, or the paper's own `print.<color>` when the paper has one.
  Bands (`min`, `max`, `rate`) count **all pages in the job** (pages x copies), so extra rows can
  lower the rate for big jobs.
- Binding: `bindings[].bands` (`min`, `max`, `price`) per booklet, counted on **copies**. 0 = included.
- Pages round up to `multiple_of` (4); the padded count is priced.
- Example rates are illustrative. Worked check: 24 pages, 10 copies, Full Color, Gloss, Coil =
  24 x 0.28 + 2.63 = 9.35 a booklet, 93.50 total.

**Saddle stitch with covers** (`"engine": 2`; has `cover.prints` and `bindery`): inside pages at a
rate per sheet (4 pages) counted on sheets in the whole run, a separate cover priced per cover by
cover paper and print, stitching per booklet counted on sheets per booklet, optional overrun.
Full field list: `33_PX_RATES_PRICE_CARDS.md` section 4b. With a separate cover, an 8-page
booklet has 1 stitching sheet, so the `bindery` table must start at 1 if that size is sold.

**Bands in booklet cards** start at 1, run on with no gaps (`next min = previous max + 1`) and end
high (9999999). A count outside every row has no price.

## Documents (`flat`) and other modes

Start from the product's current card and change rates only. Keep every `code`, `label` and the
card's shape; field lists are in `33_PX_RATES_PRICE_CARDS.md`.

## The variants a px_ product needs (area)

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

## Paste a card the owner prepared

1. Check it is one valid JSON object with `"mode"` and `"engine"`.
2. Read the product with the connector and compare every material, paper, color, binding and
   extra in the card with the product's variant values (codes and names, rule 3).
3. Work three real jobs by hand and show them.
4. Owner pastes it into the product attribute's `px_rates` field (or you write it on their go),
   saves, checks the product page shows the same price, then syncs OrderHub and tests at the till.

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
| `order-line` | a variant value on the order line matches no code or label on the card (often an extra value with no `label`) |
| `bad-unit` | `unit` is not one the engine knows |

## What needs Pixfizz

- Website custom size tools (the customer-facing size builder) and their landing pages.
- Raising `"engine"` above what the website tool and OrderHub run.
- A new kind of product (a mode or shape no product on the site uses yet).
- OrderHub not listing a product, or not pricing a card that passes every check above.

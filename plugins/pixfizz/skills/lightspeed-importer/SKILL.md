---
name: lightspeed-importer
description: Use when converting a Lightspeed or Vend POS CSV export (products, variants, or inventory) into a Pixfizz Static Product Importer CSV, or when preparing Lightspeed product data for bulk upload to a Pixfizz storefront. Triggers on Lightspeed exports containing handle, sku, variant_option, retail_price, and track_inventory columns.
---

# Lightspeed to Pixfizz Importer

## Overview

Lightspeed (Vend) exports one row per variant and per pricing tier. The Pixfizz Static Product Importer wants one row per product, with a single price, plus optional variants and Ruby pricing formulas added afterwards. This skill converts the former into the latter with `convert.py`, then guides the few decisions a script cannot safely make alone.

## The one rule that is not negotiable

If a product's Lightspeed rows have `track_inventory` set to true, that product MUST be imported as one row per SKU, never grouped into a single product with variants. Pixfizz can only hold inventory on a top-level product, not on a variant, so grouping an inventory-tracked product silently loses its per-SKU stock. The script enforces this automatically. Do not override it.

## Workflow

1. Run the converter:
   ```bash
   python3 convert.py INPUT.csv --out-dir pixfizz_out
   ```
   Add `--category "Your Category"` to set one Pixfizz category for every row. Without it, the Lightspeed `product_category` is used.

2. Read `pixfizz_out/conversion_report.txt` first. It states how each product was handled and lists anything needing review.

3. Confirm the judgement calls with the user before importing (see next section).

4. Upload `pixfizz_out/pixfizz_import.csv` in Pixfizz: Custom Admin, Tools, Static Product Importer. Pick the target collection.

5. After import, for any grouped product, open `pixfizz_out/pricing_formulas.txt` and paste the base pricing formula into the product, and each variant delta into the matching variant value price field.

## What to confirm with the user (do not assume)

The script makes safe defaults and flags them. Always confirm:

- **Which non-quantity dimension stays a variant, and which collapses.** Example: a print product may have both a sided option (keep as a variant) and a paper-weight option. The script keeps all of them and reports the base value it chose for each (for example `Paper=Husky, config=Single Sided`). Ask the user whether each should be a variant, or collapsed away.
- **The base value choices** the report lists. The base price and code come from the first value of each non-quantity dimension. Confirm that is the intended base.
- **Sparse variant matrices.** When colour and size are separate variants but only some combinations are real SKUs, the storefront will offer combinations that do not exist. The report flags this. Decide whether to restrict combinations or allow all.
- **Negative source values.** Negative stock is clamped to 0 and flagged. Negative base prices are flagged as possible discount or adjustment rows rather than real products.

## Column mapping

| Pixfizz column | Source |
|---|---|
| name | Lightspeed `name`, plus variant values when per-SKU |
| code | `sku` (the base/lowest-tier SKU when grouped) |
| price | `retail_price` (lowest quantity tier, base options, when grouped) |
| category | `product_category`, or the `--category` override |
| track_inventory | `track_inventory` |
| current_inventory | `inventory_*` outlet column, negatives clamped to 0 |
| tax_exempt | always false (Lightspeed "Default Tax" means taxable) |
| description, asset_image_name, fulfillment_code, min_quantity, max_quantity | left blank for the user to fill |

## Pixfizz pricing formula rules

Grouped products with quantity tiers get a Ruby formula in this exact idiom:

```ruby
{1..99=>0.35, 100..499=>0.30, 500..999=>0.25, 1000..50000=>0.20}.find { |range, unit_price| range.include?(quantity) }.last
```

- Keys are inclusive integer ranges, values are per-unit prices. The engine multiplies the result by quantity.
- The top range uses a high finite cap (50000). Never use `Float::INFINITY` or an endless range like `1000..`, both break the Pixfizz pricing engine.
- A double-sided or other variant uplift is a separate delta formula on the variant value, in the same idiom, or a flat number when the uplift is constant.

## Common mistakes

| Mistake | Fix |
|---|---|
| Grouping an inventory-tracked product | Never. One row per SKU. The script enforces this. |
| Using `Float::INFINITY` for the top tier | Use a finite cap like 50000. |
| Assuming column positions | Lightspeed shifts the variant_option columns between products. The script reads by column name, not position. |
| Treating a non-size dimension as price-driving | Only fold the real quantity-tier dimension into the formula. Other dimensions are variants. |
| Importing before confirming base values | Read the report and confirm the flagged base choices first. |

## Outputs

- `pixfizz_import.csv` ready to upload.
- `pricing_formulas.txt` base formulas and variant deltas for grouped products.
- `conversion_report.txt` decisions and review flags.

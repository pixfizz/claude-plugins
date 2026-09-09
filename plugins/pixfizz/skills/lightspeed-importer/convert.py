#!/usr/bin/env python3
"""
Convert a Lightspeed (Vend) retail CSV export into a Pixfizz Static Product
Importer CSV.

Hard rule: any product whose Lightspeed rows have track_inventory = true (1) is
emitted one row PER SKU, never grouped. Pixfizz can only hold inventory on a
top-level product, not on a variant, so grouping an inventory-tracked product
would lose its per-SKU stock.

Products without inventory tracking are grouped to one product per handle. If a
quantity-tier dimension is present (values like <99, 100+, 1000+), its tiers are
turned into a Ruby pricing formula and any other dimensions become variants with
computed price deltas.

Outputs (into --out-dir, default ./pixfizz_out):
  pixfizz_import.csv      ready to upload to the Static Product Importer
  pricing_formulas.txt    Ruby formulas + variant deltas for grouped products
  conversion_report.txt   decisions made and anything needing human review

Usage:
  python3 convert.py INPUT.csv [--out-dir DIR] [--category NAME]

--category overrides the Pixfizz category for every row. If omitted, the
Lightspeed product_category is used.
"""

import csv
import os
import re
import sys
import argparse
from collections import OrderedDict

PIXFIZZ_COLS = ["name", "code", "price", "description", "category",
                "asset_image_name", "fulfillment_code", "track_inventory",
                "current_inventory", "tax_exempt", "min_quantity", "max_quantity"]

TOP_CAP = 50000          # top-tier range cap. NEVER use Float::INFINITY or endless ranges - they break the Pixfizz engine.
TIER_LT = re.compile(r"^<\s*([\d,]+)$")     # "<99", "<50"
TIER_GE = re.compile(r"^([\d,]+)\s*\+$")    # "100+", "1,000+"


def read_lightspeed(path):
    """Read a Lightspeed export, tolerating its doubled line endings."""
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [r for r in reader if any(c.strip() for c in r)]
    idx = {name: i for i, name in enumerate(header)}

    def col(*names, prefix=None):
        for n in names:
            if n in idx:
                return idx[n]
        if prefix:
            for name, i in idx.items():
                if name.startswith(prefix):
                    return i
        return None

    cmap = {
        "handle": col("handle"),
        "sku": col("sku"),
        "name": col("name"),
        "category": col("product_category"),
        "retail": col("retail_price"),
        "track": col("track_inventory"),
        "inv": col("inventory_Main_Outlet", prefix="inventory_"),
        "tax": col("outlet_tax_Main_Outlet", prefix="outlet_tax_"),
        "o1n": col("variant_option_one_name"), "o1v": col("variant_option_one_value"),
        "o2n": col("variant_option_two_name"), "o2v": col("variant_option_two_value"),
        "o3n": col("variant_option_three_name"), "o3v": col("variant_option_three_value"),
    }
    return rows, cmap


def get(row, cmap, key, default=""):
    i = cmap.get(key)
    if i is None or i >= len(row):
        return default
    return row[i]


def truthy(v):
    return str(v).strip().lower() in ("1", "true", "yes")


def fnum(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def f2(x):
    return "%.2f" % x


def clamp_int(v):
    try:
        return str(max(0, int(float(v))))
    except (TypeError, ValueError):
        return ""


def variant_values(row, cmap):
    return [v for v in (get(row, cmap, "o1v"), get(row, cmap, "o2v"), get(row, cmap, "o3v")) if v.strip()]


def dimensions(rows, cmap):
    """Ordered map of dimension name -> ordered list of distinct values."""
    dims = OrderedDict()
    for row in rows:
        for nk, vk in (("o1n", "o1v"), ("o2n", "o2v"), ("o3n", "o3v")):
            name = get(row, cmap, nk).strip()
            val = get(row, cmap, vk).strip()
            if name:
                dims.setdefault(name, [])
                if val and val not in dims[name]:
                    dims[name].append(val)
    return dims


def tier_lb(label):
    """Lower bound for a tier label. '<N' -> 0 (base), 'N+' -> N."""
    label = label.strip()
    m = TIER_GE.match(label)
    if m:
        return int(m.group(1).replace(",", ""))
    if TIER_LT.match(label):
        return 0
    return None


def is_tier_value(v):
    return bool(TIER_LT.match(v.strip()) or TIER_GE.match(v.strip()))


def find_quantity_dim(dims):
    """Return the dimension name that holds quantity tiers, or None."""
    for name, values in dims.items():
        if "quant" in name.lower() or "price" in name.lower():
            if any(is_tier_value(v) for v in values):
                return name
        tierish = sum(1 for v in values if is_tier_value(v))
        if values and tierish >= max(1, len(values) * 0.5):
            return name
    return None


def dim_value_of(row, cmap, dim_name):
    for nk, vk in (("o1n", "o1v"), ("o2n", "o2v"), ("o3n", "o3v")):
        if get(row, cmap, nk).strip() == dim_name:
            return get(row, cmap, vk).strip()
    return ""


def range_hash(tiers):
    """tiers: {lb: price}, lb 0 = base. Build contiguous integer ranges -> .find idiom."""
    lbs = sorted(tiers.keys())
    parts = []
    for j, lb in enumerate(lbs):
        start = 1 if lb == 0 else lb
        end = str(lbs[j + 1] - 1) if j < len(lbs) - 1 else str(TOP_CAP)
        parts.append("%s..%s=>%s" % (start, end, f2(tiers[lb])))
    return "{" + ", ".join(parts) + "}.find { |range, unit_price| range.include?(quantity) }.last"


def convert(path, out_dir, category_override=None):
    rows, cmap = read_lightspeed(path)
    handles = OrderedDict()
    for row in rows:
        handles.setdefault(get(row, cmap, "handle"), []).append(row)

    import_rows = []
    formula_blocks = []
    report = []

    for handle, hrows in handles.items():
        pname = get(hrows[0], cmap, "name")
        cat = category_override or get(hrows[0], cmap, "category") or ""
        inv_tracked = any(truthy(get(r, cmap, "track")) for r in hrows)
        dims = dimensions(hrows, cmap)
        tax_exempt = "false"  # Lightspeed "Default Tax" means taxable

        # ---- RULE: inventory-tracked -> one row per SKU, never grouped ----
        if inv_tracked:
            clamped = 0
            for r in hrows:
                raw = fnum(get(r, cmap, "inv"))
                if raw is not None and raw < 0:
                    clamped += 1
                vals = variant_values(r, cmap)
                nm = pname + (" - " + " ".join(vals) if vals else "")
                import_rows.append([nm, get(r, cmap, "sku"), f2(fnum(get(r, cmap, "retail")) or 0),
                                    "", cat, "", "", "true", clamp_int(get(r, cmap, "inv")), tax_exempt, "", ""])
            note = "%s: inventory-tracked -> %d rows, one per SKU (no grouping)." % (pname, len(hrows))
            if clamped:
                note += " %d SKU(s) had negative stock in the source, clamped to 0 - verify real counts." % clamped
            report.append(note)
            continue

        qdim = find_quantity_dim(dims)
        non_qty = [d for d in dims if d != qdim]

        # ---- Grouped with quantity tiers -> base price + Ruby formula ----
        if qdim:
            base_combo = {d: dims[d][0] for d in non_qty}  # first value of each other dim

            def matches_base(r):
                return all(dim_value_of(r, cmap, d) == base_combo[d] for d in non_qty)

            base_tiers, base_code, base_lb = {}, None, 10 ** 9
            for r in hrows:
                if not matches_base(r):
                    continue
                lb = tier_lb(dim_value_of(r, cmap, qdim))
                if lb is None:
                    continue
                price = fnum(get(r, cmap, "retail"))
                base_tiers[lb] = price
                if lb < base_lb:
                    base_lb, base_code = lb, get(r, cmap, "sku")

            base_price = base_tiers.get(0, min(base_tiers.values()) if base_tiers else 0)
            import_rows.append([pname, base_code, f2(base_price), "", cat, "", "", "false", "", tax_exempt, "", ""])
            if base_price is not None and base_price < 0:
                report.append("%s: WARNING base price is negative (%s) - review this product, it may be a discount/adjustment row not a real product." % (pname, f2(base_price)))

            block = ["%s   (code %s)" % (pname, base_code), "-" * 56,
                     "BASE pricing formula:", range_hash(base_tiers), ""]
            combo_note = ", ".join("%s=%s" % (d, base_combo[d]) for d in non_qty) or "no other options"
            block.append("Base combination: %s" % combo_note)

            # variant deltas: vary one non-qty dim, hold others at base
            for d in non_qty:
                for v in dims[d][1:]:
                    delta = {}
                    for r in hrows:
                        if dim_value_of(r, cmap, d) != v:
                            continue
                        if not all(dim_value_of(r, cmap, o) == base_combo[o] for o in non_qty if o != d):
                            continue
                        lb = tier_lb(dim_value_of(r, cmap, qdim))
                        if lb is None or lb not in base_tiers:
                            continue
                        delta[lb] = round((fnum(get(r, cmap, "retail")) or 0) - base_tiers[lb], 2)
                    if not delta:
                        continue
                    if len(set(delta.values())) == 1:
                        block.append('Variant "%s = %s" delta: %s' % (d, v, f2(next(iter(delta.values())))))
                    else:
                        block.append('Variant "%s = %s" delta:' % (d, v))
                        block.append(range_hash(delta))
            formula_blocks.append("\n".join(block))
            report.append("%s: grouped, quantity dim '%s', other dims %s -> formula generated. CONFIRM base value choices: %s."
                           % (pname, qdim, non_qty or "none", combo_note))
            continue

        # ---- Not inventory-tracked, no quantity dim -> group, price by dim deltas ----
        priced = [(r, fnum(get(r, cmap, "retail")) or 0) for r in hrows]
        base_row, base_price = min(priced, key=lambda x: x[1])
        import_rows.append([pname, get(base_row, cmap, "sku"), f2(base_price), "", cat, "", "", "false", "", tax_exempt, "", ""])
        if base_price < 0:
            report.append("%s: WARNING base price is negative (%s) - review, may be a discount/adjustment row." % (pname, f2(base_price)))
        if len(hrows) > 1:
            block = ["%s   (code %s, base %s)" % (pname, get(base_row, cmap, "sku"), f2(base_price)),
                     "-" * 56, "No quantity tiers. Set these as variant price adjustments (flat amounts):"]
            base_vals = variant_values(base_row, cmap)
            for r, price in priced:
                vals = variant_values(r, cmap)
                if vals == base_vals:
                    continue
                block.append('  %s : +%s' % (" / ".join(vals), f2(price - base_price)))
            formula_blocks.append("\n".join(block))
            report.append("%s: grouped, no quantity tiers -> %d variant price deltas. CHECK for option combinations that are not real SKUs (sparse matrix)."
                           % (pname, len(hrows) - 1))
        else:
            report.append("%s: single product, no variants." % pname)

    os.makedirs(out_dir, exist_ok=True)
    imp_path = os.path.join(out_dir, "pixfizz_import.csv")
    with open(imp_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(PIXFIZZ_COLS)
        w.writerows(import_rows)

    fpath = os.path.join(out_dir, "pricing_formulas.txt")
    with open(fpath, "w") as f:
        if formula_blocks:
            f.write("PIXFIZZ PRICING - paste into each product after import.\n")
            f.write("Quantity formulas go in the product pricing formula field; variant\n")
            f.write("deltas go in each variant value price field.\n")
            f.write("Top tier capped at %d (never Float::INFINITY or endless ranges).\n" % TOP_CAP)
            f.write("=" * 64 + "\n\n")
            f.write("\n\n" + ("=" * 64) + "\n\n".join([""] + formula_blocks) + "\n")
        else:
            f.write("No pricing formulas needed (all products are inventory-tracked per-SKU or single-price).\n")

    rpath = os.path.join(out_dir, "conversion_report.txt")
    with open(rpath, "w") as f:
        f.write("CONVERSION REPORT\n" + "=" * 64 + "\n")
        f.write("Products in: %d   Rows out: %d\n\n" % (len(handles), len(import_rows)))
        for line in report:
            f.write("- " + line + "\n")

    return imp_path, fpath, rpath, len(handles), len(import_rows)


def main():
    ap = argparse.ArgumentParser(description="Convert Lightspeed CSV to Pixfizz Static Product Importer CSV.")
    ap.add_argument("input", help="Lightspeed export CSV")
    ap.add_argument("--out-dir", default="pixfizz_out")
    ap.add_argument("--category", default=None, help="Override Pixfizz category for all rows")
    args = ap.parse_args()
    if not os.path.exists(args.input):
        sys.exit("Input file not found: %s" % args.input)
    imp, fpath, rpath, np, nr = convert(args.input, args.out_dir, args.category)
    print("Wrote %s (%d products in, %d rows out)" % (imp, np, nr))
    print("Wrote %s" % fpath)
    print("Wrote %s" % rpath)


if __name__ == "__main__":
    main()

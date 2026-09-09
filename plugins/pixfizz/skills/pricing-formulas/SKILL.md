---
name: pricing-formulas
description: "Ruby pricing formulas, price variables, automatic discounts and extra fees on the Pixfizz platform. Use this skill whenever writing, reviewing, debugging or explaining any price on a Pixfizz product — product attribute pricing formulas, variant and option price adjustments, quantity or volume breaks, per-page book pricing, photo print pricing, cart-level automatic discounts, and Liquid-based extra fees. Trigger for any mention of 'pricing formula', 'price ladder', 'quantity break', 'volume discount', 'tiered pricing', 'price variable', 'surcharge', 'rush fee', 'minimum order fee', 'automatic discount', 'extra fee', or a price that is wrong, doubled, or not applying. Also trigger whenever a formula contains quantity, units, pages, or cut_print_quantity, even if the user does not call it a pricing question."
---

# Pixfizz Pricing Formulas

Ruby expressions evaluated in context that must return a numeric price. Used for product
pricing and for option/variant pricing.

Authoritative source: `30_PRICING_ENGINE.md` in the Pixfizz knowledge base
(github.com/pixfizz/pixfizz-knowledge). This skill is the working procedure; that file is the
reference. Never invent a rate or a pattern — if the required idiom is not here or there, say so
and ask.

## The four questions to settle before writing anything

Answer these in order. Most wrong prices trace back to one of them being assumed rather than
asked.

1. **Is this a photo print (cut print)?** If yes, the quantity variable is `cut_print_quantity`,
   always, with no exceptions. If no, `cut_print_quantity` must never appear in the formula.
2. **Per orderline or across the cart?** `quantity` counts within one orderline.
   `units` accumulates across every orderline for that product in the cart. A customer who adds
   one yard sign, goes back, and adds another gets two first-unit prices under `quantity` and one
   combined ladder under `units`. This is a commercial decision, not a default.
3. **Does the product have uncounted pages?** If it is a book or any multi-page product, use
   `(pages - uncounted_pages)`, never raw `pages`. See the trap below.
4. **Where does this formula live?** Product Attribute (Products → the product → the specific
   size/variant → Pricing Formula), or on a variant **value**, or as a cart-level Automatic
   Discount or Extra Fee. These behave differently and are not interchangeable.

## Hard rules

- **The formula returns a per-unit price. The platform multiplies by quantity.** Returning a
  total squares the price. When the natural expression is a total, divide by quantity at the end.
- **Ranges must cover the full ordered span with no gaps.** `.find` returns nil outside them and
  `.last` then raises `NoMethodError`, which breaks the product page, not just the price. A gap is
  silent until somebody orders into it.
- **Use a finite top cap.** Never `Float::INFINITY`, never an endless range like `1000..`. Both
  break the pricing engine. `1000..50000` is the idiom.
- **Force float division.** `2.0`, not `2`. Integer division silently rounds and the error is
  small enough to survive review.
- **Keep formulas basic.** Established patterns run reliably; clever Ruby gets unpredictable.
- **Never invent rates.** Ship the ladder with zeros and say so. A product priced at 0.00 is
  obviously not ready; a product priced at a plausible invention reaches a customer.
- **Run the formula in real Ruby before handing it over**, including its failure modes — an order
  below the lowest range, above the highest, and exactly on a boundary.

## Canonical patterns

**Tiered unit price** — the workhorse. Returns per-unit; the engine multiplies.

```ruby
{1..99=>2.04, 100..149=>1.44, 150..50000=>1.20}.find { |range, unit_price| range.include?(quantity) }.last
```

**Photo prints** — same shape, but the variable is fixed and the pattern multiplies explicitly
because cut print quantity is not the orderline quantity.

```ruby
{1..10=>0.59, 11..49=>0.49, 50..249=>0.44, 250..499=>0.39, 500..2000=>0.35}.find { |range,unit_price| range.include?(cut_print_quantity) }.last * cut_print_quantity
```

**Linear:** `0.85 * cut_print_quantity`

**Base plus incremental pages** — note the subtraction, see the trap below.

```ruby
19.99 + ((pages - uncounted_pages) - 16) / 2.0 * 0.50
```

**Volume discount across the cart** — uses `units`, so separate orderlines accumulate.

```ruby
{1..1=>8.00, 2..5=>6.50, 6..10=>6.00, 11..20=>5.75, 21..50=>4.80, 51..1000=>4.15}.find { |range,unit_price| range.include?(units)}.last
```

**Volume discount combined with per-page pricing:**

```ruby
{1..1=>(19.99 + (pages-16)/2 * 0.50), 2..5=>(18.99 + (pages-16)/2 * 0.45), 6..10=>(17.99 + (pages-16)/2 * 0.40)}.find { |range,unit_price| range.include?(units)}.last
```

**Threshold plus blocks of pages:** `49 + ([0, pages - 50].max / 4)`

**Sheet-based production:** `10 + (((pages - 12.0) / 12.0).ceil) * 8`

**First unit dearer, each additional cheaper** — a total expression, so it divides out:

```ruby
(25 + ([0, quantity - 1].max * 15.0)) / quantity
```

**A number option carrying the price directly.** A `number` template option with `value` as its
pricing formula makes the entered number the price. This is how a custom design tool prices
continuous geometry — area, per-foot, free sizes — without enumerating a variant ladder.

```ruby
value
value * 3
value * {1..99=>1.0, 100..499=>0.9, 500..50000=>0.82}.find { |range, mult| range.include?(quantity) }.last
```

Division of labour: the tool writes the **quantity-1 unit price**, the formula owns quantity.
Writing an already-tiered price double-discounts and looks plausible in the cart. Writing a
finished total freezes the price so the cart stepper stops re-pricing. Ship the option with **no
default value** — a number option with a default fails add-to-cart with "value is a required
field", including in point of sale.

## Traps

**`pages` includes uncounted pages.** It counts every page in the project, including pages in XML
sets marked `count="false"` — covers, preview pages. Book pricing on raw `pages` overcharges,
because it counts more "extra" pages than the customer added. Always `(pages - uncounted_pages)`
for interior-page pricing. Applies to base+incremental, threshold+blocks, sheet-based, and
volume+per-page alike.

**Negative variant adjustments are not supported.** The platform does not price negative extras
or negative variant adjustments. Two workarounds:

- The variant formula editor rejects a **leading minus sign** outright. Multiply by `-1` at the
  end instead: `(base_price * tier_1) * -1` works where `-(base_price * tier_1)` errors.
- For a genuine discount variant, invert the model: lower the product base price to the discounted
  value and add a positive surcharge to the "standard" variant. Rush +20% is natural (rush is the
  surcharge); delay −10% needs the inversion (delayed becomes the base). Label them in
  customer-facing terms and never expose the inverted mechanics to the client.
- The supported way to add a conditional surcharge at cart level is an **Extra Fee**, below.

**Whether the platform sums two priced variants on one product is untested.** Do not assert it.
Either test it with a real order line, or fold the surcharge into a single priced variant.

**Photo enhancement add-ons charge per image, not per print quantity.** The standard behaviour of
multiplying the option price by quantity is wrong here; the formula must flatten the multiplier.
The canonical snippet is not locked in the reference — confirm against the live site before
reusing.

## Cart-level pricing: Automatic Discounts and Extra Fees

Both are platform-level, configured in Main Admin, and both take a **Liquid** formula (not Ruby)
with full cart and user context. Automatic Discounts subtract; Extra Fees add. Both return a
numeric **amount** in site currency, not a percentage — the formula does the percentage maths
itself. If no branch matches and the formula returns nothing, nothing is applied.

Context available: `cart.orderlines`, `cart.orderlines_total`, `cart.promocode_code`, `user.*`,
standard Liquid filters.

```liquid
{%- if cart.orderlines_total >= 250 %}
    orderlines_total * 0.20
{%- elsif cart.orderlines_total >= 150 %}
    orderlines_total * 0.15
{%- endif %}
```

**Property-name trap:** it is `cart.promocode_code`, not `cart.promocode`. The short form is not a
valid Cart property, resolves to nil, and is falsy — so a guard written as
`{%- unless cart.promocode -%}` never blocks and the discount stacks on top of a promo code.

Extra Fees live under **Shipping → Extra Fees**, each with a code, a name and a formula. Canonical
uses: a minimum-order handling fee, an oversize shipping surcharge, or a per-duplicate-orderline
charge using the seen-string + `contains` idiom to count distinct products across
`cart.orderlines`. Note the KB flags the orderline-iteration specifics as pending live
confirmation — verify on the first test order rather than assuming.

## Price Variables

Admin-defined numeric constants, available by name inside formulas, used to centralise pricing
inputs across products and options. `whitelabel` is a Price Variable, not a system variable.
They can be bulk exported and imported, including across sites, which is the right tool for
onboarding scoping with hundreds of variables or replicating a pricing setup between sites.

## Before handing a formula over

- [ ] Right quantity variable for the product type — `cut_print_quantity` only on photo prints
- [ ] `quantity` vs `units` chosen deliberately and stated to the client
- [ ] `(pages - uncounted_pages)` wherever page count drives price
- [ ] Ranges gap-free across `min_units` to `max_units`, finite top cap
- [ ] Returns per-unit, not a total
- [ ] Float division forced where any division happens
- [ ] Executed in real Ruby, including below-range, above-range and boundary cases
- [ ] Rates confirmed by the client, never invented

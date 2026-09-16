---
name: seasonal-campaign
description: Plan and build a seasonal or promotional campaign on a Pixfizz storefront - the offer (automatic discount or promo code), the landing page, order cutoff messaging, banners, and the test and switch-off plan. Use for holiday, Black Friday, Mother's Day, Father's Day, Valentine's, graduation, back-to-school or any dated sale; for gift bundles ('buy 3, save 10%'), spend thresholds, first-order or customer-group offers, influencer and email codes, single-use codes, free shipping promotions, and deciding whether offers may stack. Trigger for 'campaign', 'promotion', 'sale', 'promo code', 'discount code', 'coupon', 'voucher code', 'automatic discount', 'bundle offer', 'gift guide', 'order by date', 'holiday cutoff', 'countdown', 'free shipping over', or a discount that is not applying or is applying twice.
---

# Pixfizz Seasonal Campaigns

A campaign is four things built in order: **the offer, the page, the deadline, the switch-off.**
Most campaign faults come from the last two being forgotten.

Pair with `pricing-formulas` for formula syntax, `storefront-copy` for the words,
`shopper-ux` for the page layout, and `storefront-audit` to check the result live.

**Commercial decisions belong to the store owner.** The discount level, who qualifies, whether
offers stack, and the shipping cutoff dates are business choices. Ask for them; never pick them.

## Step 1 - The brief

Get these answered before building anything:

- [ ] Occasion, start date and time, end date and time, and the store's time zone
- [ ] The offer, in one sentence a customer would understand
- [ ] Which products or collections are in and out
- [ ] Who qualifies: everyone, a customer group, first-time buyers, code holders
- [ ] **Stacking:** may this offer combine with promo codes? with other automatic discounts?
- [ ] Last order dates per shipping method and for in-store pickup, from the store's own
      production times and carrier schedule. Never invent carrier dates
- [ ] Where it appears: homepage, banner, landing page, email, social
- [ ] Who switches it off, and when

## Step 2 - Choose the mechanism

Pixfizz has two discount mechanisms, both under **Main Admin -> Marketing**. Platform-level.

| Need | Use |
|---|---|
| Discount everyone sees with no code | **Automatic discount** |
| Bundles, "any 3 from this collection", tiered spend, customer groups, cart field conditions | **Automatic discount** |
| A code for an influencer, email list or partner, so you can see which channel sold | **Promo code** |
| One-off codes for a comped order or a service recovery | **Promo code**, Single Use |
| A batch of unique codes | **Promo code**, Single Use with copies, or CSV import |
| Buy-one-get-one or X-for-Y | **Promo code** (built-in rule types) |
| Free or reduced shipping | **Promo code** ("shipping is deducted") |
| Hard start and end dates set in admin | **Promo code** (automatic discounts have no date fields) |

Default to an automatic discount. It is more flexible, applies itself, and nobody has to find
or type a code.

### Automatic discounts - how they behave

Fields: **Name, Code, Combines, Formula.** Verified in admin and against the help article.

- **The formula runs as Liquid first, and its output is evaluated as a pricing expression.**
  It must produce a **positive amount** in store currency. Zero, blank or negative applies nothing.
- **Pricing variables:** `orderlines_total` and `orderlines_discount` (the promo code discount
  on order lines). No `quantity`, `units` or `pages` - this is cart level.
- **Liquid objects:** `cart` (restricted), `user`, `website`. Working cart properties include
  `cart.orderlines_total`, `cart.orderlines_discount`, `cart.promocode_code`, `cart.orderlines`,
  `cart.custom`, `cart.address`, `cart.shipping_option`. **Not usable:** `cart.total`,
  `cart.shipping`, `cart.discount`, `cart.shipping_discount`, `cart.tax`.
- **It discounts order lines only**, never shipping or fees, and is capped at the order line total.
- **It stacks with promo codes by default.** To stop that, guard the formula with
  `cart.promocode_code == blank`. The property is `promocode_code`; `cart.promocode` does not
  exist, is always empty, and a guard written with it never blocks.
- **Automatic discounts do not combine with each other by default.** When several qualify, only
  the single largest applies. Tick **Combines** on the ones allowed to add together; the platform
  then picks the best total among combinable ones, or a larger non-combinable one if that wins.
- **Calculation order:** order lines -> promo codes -> automatic discounts -> extra fees ->
  shipping -> tax. Extra fee formulas can read `auto_discount` and `cart.auto_discounts`.
- **No start or end date.** A dated offer must check the date inside the formula, and still
  needs a calendar reminder to remove it.

### Promo codes - what the admin offers

Verified in admin. **Multiple Use** or **Single Use** (single use has a Copies count).

- Code, name, starts at, expires at (in the store's time zone)
- **When:** a user buys any product / a specific product / a product from a category
- **Then:** amount per product; percentage per product; shipping deducted; whole cart discount;
  two-for-one; grouped two-for-one; X-for-Y; grouped X-for-Y
- **And:** optionally also deduct shipping or apply a whole cart discount
- **From/To:** all products / specific products / specific product categories
- **Limits:** discount applied a maximum number of times; spend exceeds an amount; limited to a
  total number of customer uses
- The rule is stored as JSON in the Code box. Bulk codes import from CSV; usage exports as a
  CSV report.

## Step 3 - Build the offer

### Dated window (automatic discount)

```liquid
{%- assign today = 'now' | date: '%Y%m%d' | plus: 0 -%}
{%- if today >= 20261127 and today <= 20261201 and cart.promocode_code == blank -%}
	orderlines_total * 0.15
{%- endif -%}
```

The time zone `'now'` is evaluated in is **not verified**. Start the window a day early or
confirm with a test on the boundary day, and say so in the handover.

### Spend more, save more

```liquid
{%- if cart.orderlines_total >= 200 -%}
	orderlines_total * 0.15
{%- elsif cart.orderlines_total >= 100 -%}
	orderlines_total * 0.10
{%- elsif cart.orderlines_total >= 50 -%}
	orderlines_total * 0.05
{%- endif -%}
```

### Customer group

```liquid
{%- if user.category == 'wholesale' -%}
	orderlines_total * 0.2
{%- endif -%}
```

### Gift bundle: any 3 different products from a set, save 10%

Tag each product in the set with a **product custom field** (for example `gift_bundle`, text)
rather than listing product codes in the formula. The tag survives renames and new products join
the set without a formula edit. The custom field must be created on the site first.

```liquid
{%- assign seen = '|' -%}
{%- assign count = 0 -%}
{%- assign set_total = 0 -%}
{%- for line in cart.orderlines -%}
	{%- assign tag = line.product.custom.gift_bundle | downcase | strip -%}
	{%- if tag == 'book-lovers' -%}
		{%- assign set_total = set_total | plus: line.price -%}
		{%- assign key = '|' | append: line.product.id | append: '|' -%}
		{%- unless seen contains key -%}
			{%- assign seen = seen | append: line.product.id | append: '|' -%}
			{%- assign count = count | plus: 1 -%}
		{%- endunless -%}
	{%- endif -%}
{%- endfor -%}
{%- if count >= 3 and cart.promocode_code == blank -%}
	{{ set_total }} * 10 / 100.0
{%- endif -%}
```

- Counts **different** products; two of the same mug count once. Wrapping ids in `|` stops
  product 1 matching inside product 11.
- The collection page decides what is **shown**; the tag decides what is **discounted**. Every
  product in the collection needs the tag, or it shows and does not count.
- **Not verified on a live order:** that `line.product.custom.*` resolves inside an automatic
  discount, and whether `line.price` is the line total or already net of other discounts.
  Prove both with the test matrix before launch.

## Step 4 - The page and the deadline

- **Landing page.** On a Shopper child site, create a `pages` Custom Type instance
  (Website -> Custom Types -> Pages) with a `page_path` that no real page uses; the page is
  served at `/site/<page_path>`. Fill `page_title` and `page_description` - they become the
  search title and description. The offer's products come from a collection, which can be
  hidden from the menu.
- **Say the offer and the condition in the first screen.** "Pick any 3, save 10%, no code
  needed" beats "Bundle and save". Use `storefront-copy`.
- **Cutoff messaging** comes from the store's dates, per shipping method, and switches itself
  over when a date passes, using the same `'now' | date` comparison as above. Show the next
  cutoff that still applies, not the whole table.
- **After the last shipping date,** swap the message to what still works: in-store pickup,
  gift vouchers, digital delivery.
- **Banners.** Shopper keeps site-wide promotion text in the `website/sitewide-promotion` and
  `website/current-promotions` snippets where the template reads them. Check the template
  version before relying on either.
- **Tell the shopper what they have.** If a cart message shows the bundle progress, drive it
  from the same tag and threshold as the formula, and keep the two numbers in step.

## Step 5 - Test before launch

Place these in the cart and read the discount line each time:

- [ ] Qualifying cart: discount appears, correct amount
- [ ] One item short of qualifying: no discount
- [ ] Qualify, then remove an item: discount disappears
- [ ] Duplicates of one product (bundle offers): counted once
- [ ] A promo code applied: the offer steps aside or stacks, exactly as the owner decided
- [ ] Two automatic discounts qualifying together: the expected one wins, or they combine
- [ ] Before the start and after the end (or the boundary day): nothing applies
- [ ] A customer outside the group (group offers): nothing applies
- [ ] Shipping and fees are untouched by an automatic discount
- [ ] The landing page loads live, with its title, description and products

Use a staging or test site where one exists. Remove test carts afterwards.

## Step 6 - Switch-off

- [ ] Delete or disable each automatic discount the day after the end, even if dated in the formula
- [ ] Promo codes expire on their own; check for any that were created without an end date
- [ ] Remove or replace the banner and cutoff messaging
- [ ] Hide the campaign collection from the menu, or redirect the landing page to an evergreen page
- [ ] Export the promo code CSV report for the owner's records

## Diagnosis: "the discount is not applying" / "it applied twice"

1. **Is the formula output positive?** A branch that matches nothing outputs nothing.
2. **Is another automatic discount larger?** Without Combines, only the largest one applies.
3. **Is the promo code guard spelled `cart.promocode_code`?**
4. **Does the formula use a cart property that does not work** (`cart.total`, `cart.discount`,
   `cart.shipping`, `cart.tax`)?
5. **Bundle offers: is every product tagged, with the exact tag value?**
6. **Applied twice:** an automatic discount and a promo code for the same offer are stacking,
   which is the default. Add the guard, or remove one of them.
7. **Dated offers:** is the store's time zone moving the boundary by a day?

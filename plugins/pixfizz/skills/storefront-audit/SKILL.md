---
name: storefront-audit
description: Health check of a live Pixfizz storefront - broken menu links, empty collections, products with no price or image, a dead Add to Cart, a custom tool mounted twice, missing SEO titles, a noindex left on or a sitemap that was never generated. Use when checking a store before launch, after an import or a template change, when a customer reports that something on the site is broken, or on a routine health pass. Trigger for 'audit my site', 'health check', 'is my store ready', 'check my storefront', 'what is broken on my site', 'pre-launch check', 'broken links', 'add to cart does nothing', 'page not found in my menu', or any request to review a live Shopper or Shopify + Pixfizz store rather than a file. Works on the live URL, read-only.
---

# Pixfizz Storefront Health Check

A read-only pass over a **live** storefront that returns a pass/fail list with the evidence for
each line. It checks the site the customer sees, not a file, a backup or a local preview.

Pair with `storefront-launch` for what to fix in which order, `shopper-ux` for conversion
quality, and `liquid-patterns` or `product-variants` once a fault is located.

## Ground rules

- **Read-only.** Do not save anything in admin, do not submit forms, do not place an order.
  An add-to-cart or checkout test is a separate step that needs the owner's explicit OK, and
  should run on a staging or test site where one exists.
- **The live page is the only evidence.** A template file that looks right proves the file, not
  the site. Every finding names the URL it was measured on.
- **Label every line.** *Verified live*, *not verified*, or *not checked*. A check that did not
  run is never reported as a pass.
- **Count what ran.** End the report with how many pages were fetched and how many were
  product pages. "No problems" on three pages is not a clean site.
- **A hidden browser tab can lie about layout.** Chrome freezes CSS transitions in a background
  tab, so a width or position read there may be the pre-transition value. Do not report a layout
  defect from a hidden tab. Status codes, text and attributes are safe.
- **Do not guess a fix for a commercial setting** (prices, discounts, shipping rates). Report
  what the page shows and leave the decision with the store owner.

## Tooling

Run the checks **inside a browser tab on the storefront's own domain.** Same-origin `fetch()`
from the page reads every other page on the site without navigating, and the page's DOM gives
you prices and form state that a plain HTTP fetch cannot. A cloud shell often cannot reach the
store at all.

Establish first:

1. **The URL** and whether the site is **live or pre-launch.** Several checks invert: a
   `noindex` is correct before launch and a serious fault after it.
2. **The deployment model.** Full Pixfizz (Shopper) or Shopify + Pixfizz. Everything below is
   written for Shopper; the Shopify notes are at the end.
3. **Which Shopper generation.** Shopper 24 runs Bootstrap 4.6; Shopper v2 runs Bootstrap 5.
   Read it from the page (step 1) rather than asking.

## Step 1 - Site-level checks (homepage)

```js
const out = {};
out.title = document.title;
out.description = document.querySelector('meta[name=description]')?.content || '';
out.robots = document.querySelector('meta[name=robots]')?.content || '';
out.canonical = document.querySelector('link[rel=canonical]')?.href || '';
out.bootstrap = window.bootstrap?.Tooltip?.VERSION || window.jQuery?.fn?.tooltip?.Constructor?.VERSION || 'unknown';
out.gtm = !!document.querySelector('script[src*="googletagmanager.com"]');
for (const p of ['/robots.txt', '/sitemap.xml']) {
	const r = await fetch(p);
	out[p] = { status: r.status, type: r.headers.get('content-type') };
}
out.footerLinksSitemap = !!document.querySelector('a[href*="sitemap.xml"]');
out
```

| Check | Pass | Fail means |
|---|---|---|
| `robots` meta | `noindex` **before** launch, absent **after** | Live site hidden from Google, or a pre-launch site being indexed |
| `/sitemap.xml` | 200 with XML | 404 = the site crawl has never run. Admin -> Website Crawls. Worse if the footer links to it |
| Title / description | Real brand text | Blank description, or a placeholder like "My Brand" |
| Canonical | On the store's own domain | Pointing at another host |
| Bootstrap | Major version matches the Shopper generation (4.x on Shopper 24, 5.x on v2). Compare the major number only: the bundled minor can differ, and a Shopper 24 site has reported 4.4.1 | Components written for the other generation will not behave |

**Shopper admin trap (template-level).** On Shopper v2 the manage-admin "hide from search"
toggle has been seen writing a different checklist key from the one the page head reads. Trust
the rendered `robots` meta, never the toggle.

## Step 2 - Discover the pages

Do not rely on `/sitemap.xml`; on many stores it does not exist yet. Collect the site's own
links from the rendered homepage, which includes the header menu, megamenu and footer:

```js
const urls = [...new Set([...document.querySelectorAll('a[href^="/site"]')]
	.map(a => a.getAttribute('href').split('#')[0].split('?')[0]))];
urls
```

Add any URLs the owner names. For a large catalog, add the product links found on each
collection page in step 3, and cap the run at a stated number (say 150 pages) rather than
silently truncating.

## Step 3 - Status and content of every page

```js
const rows = [];
for (const u of urls) {
	const r = await fetch(u);
	const d = new DOMParser().parseFromString(await r.text(), 'text/html');
	rows.push({
		u,
		status: r.status,
		title: d.title,
		description: !!d.querySelector('meta[name=description]')?.content,
		comingSoon: /coming soon/i.test(d.body.innerText),
		options: d.querySelectorAll('px-option').length,
		priceEls: d.querySelectorAll('px-product-price').length,
		cta: [...d.querySelectorAll('button[name=editor]')].map(b => b.value).join('|'),
		toolRoots: d.querySelectorAll('[data-product-seen]').length,
	});
}
rows
```

Reading the rows:

- **`status: 404` on a menu link** is a broken menu item. Shopper returns a real 404 status for
  a missing page, so this is reliable. Report every one with the menu it came from. A menu
  pointing at a collection that was never created is the common cause before launch.
- **`comingSoon: true` on a collection** is an empty collection: the page renders but has no
  products. Verified on Shopper 24; other templates may word it differently, so confirm by eye
  on the first one.
- **`priceEls > 0`** marks a product page. Carry those URLs into step 4.
- **Missing description** on product and collection pages is an SEO finding, low severity.
- **Relative menu links.** A menu link written without its leading slash works from the homepage
  and breaks one level down. If a link works from `/site` and 404s from a sub-page, grep the
  navigation snippets for `href="` values that do not start with `/`.

## Step 4 - Product pages

Open each product page **in the tab** (not via fetch), because prices and form validity only
exist after the page's scripts run. Then:

```js
const btn = document.querySelector('button[name=editor]');
const form = btn?.form;
({
	prices: [...document.querySelectorAll('px-product-price')]
		.map(p => (p.shadowRoot?.textContent || p.textContent || '').trim()),
	cta: btn ? { value: btn.value, text: btn.innerText.trim(), disabled: btn.disabled } : null,
	invalid: form ? [...form.elements].filter(e => e.willValidate && !e.checkValidity()).map(e => {
		const o = e.closest('px-option');
		return { name: e.name, optionHidden: o ? getComputedStyle(o).display === 'none' : null, msg: e.validationMessage };
	}) : null,
	brokenImages: [...document.images].filter(i => i.complete && i.src && i.naturalWidth === 0).map(i => i.src),
	toolRoots: document.querySelectorAll('[data-product-seen]').length,
})
```

| Check | Fail means |
|---|---|
| Any price reads `$0.00` or blank | Price not set on the variant values, or a formula returning nothing |
| Price read from `textContent` is empty | Not a fault: `px-product-price` renders into a **shadow root**. Read `shadowRoot`, as above |
| `invalid` lists a control whose `optionHidden` is `true` | **Dead Add to Cart.** A required upload option behind a trigger keeps its error while hidden, so the form can never submit and the shopper sees nothing. Fix: make those upload options not required. See `product-variants` |
| `invalid` lists visible controls only | Normal until the shopper fills them in |
| `toolRoots` is 2 or more | A custom design tool is **mounted twice** - usually a stray `custom_script` on a second template option. Remove the duplicate |
| `cta.value` is not `add-to-cart` on a product that should add straight to the cart | The product or collection is missing its add-to-cart flag, so the button opens the standard editor |
| `brokenImages` not empty | An image asset name that does not exist on this site |

**Console errors are usually noise.** A `gtag is not defined` error on load says nothing about a
dead Add to Cart. Check form validity first.

## Step 5 - Cart and checkout (with permission only)

- `/site/cart` returns 200: safe to check without permission.
- An add-to-cart test changes the cart and, on a Pixfizz site, can create saved projects. Ask
  first. On a design product, add one item, confirm the line appears with a preview and the
  expected price, then remove it.
- Never place an order on a live store as part of an audit.

## Step 6 - Report

Open with the counts, then failures ranked by what they cost the store:

1. **Blocks a sale** - dead Add to Cart, a $0.00 price, checkout unreachable.
2. **Blocks discovery** - `noindex` on a live site, broken menu links, empty collections in the menu.
3. **Hurts trust or SEO** - broken images, missing titles and descriptions, no sitemap.
4. **Cosmetic.**

Each line: what is wrong, the URL, the evidence (the value you read), the verification label
and the fix or the skill that owns the fix. Close with what was **not** checked and why.

## Shopify + Pixfizz stores

Storefront, cart and checkout belong to Shopify, so steps 1 to 3 apply with Shopify's URL
structure (`/products/`, `/collections/`). On product pages, check the Personalize button is
present and survives a variant change, and that personalized items show their preview in the
cart. The fault index in `shopify-integration` covers the common symptoms.

## Before reporting the site as healthy

- [ ] Live or pre-launch established, and the `noindex` result judged against it
- [ ] Every menu link fetched, with its status
- [ ] Every product page opened in the tab, not just fetched
- [ ] Page counts stated
- [ ] Every line labelled verified live, not verified, or not checked

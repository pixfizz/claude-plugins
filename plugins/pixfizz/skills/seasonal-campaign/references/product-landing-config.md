# Product landing pages: `product-landing/config` (Shopper 24)

Template-level reference. Shopper 24 renders configurable landing pages (holiday, gifts,
seasonal campaigns) with one engine that every child site already inherits:
`product-landing/landing`, its script and the product-landing CSS. A site never edits the
engine. It supplies two things:

1. **The config**: its own override of the snippet `product-landing/config`, a JSON object
   with one key per landing page.
2. **A Pages instance** per landing page, whose content renders the engine.

Observed on live sites: the config key matches the page path (a page at `/site/holiday` reads
the `holiday` key, `/site/gifts` reads `gifts`). Keep them the same.

## The one rule: add your key, never replace the others

`product-landing/config` holds every landing page on the site. If the site already overrides
it, open the override and add the new key next to the existing ones. Pasting a file that holds
only your key deletes every other landing page on the site. If the site has no override yet,
override the snippet in admin (Website, Snippets, find `product-landing/config`, Override
Snippet). A new override can start empty, so make sure it holds the complete JSON. Validate the JSON before saving.

## Page object

```json
{
  "holiday": {
    "theme": { ... },
    "breadcrumbs": [ { "label": "Home", "url": "/" }, { "label": "Holiday" } ],
    "blocks": [ { "type": "hero", ... }, { "type": "faq", ... } ]
  }
}
```

**theme** keys: `page`, `deep`, `surface`, `surface_2`, `ink`, `muted`, `faint`, `line`,
`accent`, `accent_hover`, `accent_ink`, `wall` (colors), `radius` (e.g. `"16px"`),
`heading_font`, `mono_font` (CSS font stacks).

**blocks** render top to bottom in array order. Most blocks take `tone`: `page`, `deep` or
`ink` (which theme color the section sits on), and an optional `id`, which becomes the
section's anchor, so a menu link can jump straight to it. `buttons` is always a list of
`{ "label", "url" }`.

## Block types and their keys

Only keys seen in working configs are listed.

| type | keys |
|---|---|
| `snow` | `count`, `seconds` (0 = keeps falling) |
| `countdown` | `tone`, `eyebrow`, `target` (ISO local time, e.g. `2026-12-25T00:00:00`), `timezone_offset` (e.g. `-05:00`), `deadlines` [`label`, `show` (display text), `date` (ISO)], `next_label`, `all_label`, `after_text`, `buttons` |
| `hero` | `image`, `image_alt`, `image_width`, `image_height`, `image_ratio`, `focus_x`, `focus_y`, `focus_x_desktop` (0 to 1), `eyebrow`, `title`, `text`, `buttons`, `chips` (list of short strings) |
| `facts` | `items` [`value`, `label`] |
| `spin` | `id`, `tone`, `store_key` (browser storage key, change it per campaign), `eyebrow`, `title`, `text`, `button`, `list_label`, `slices` [`label`, `short`, `color`, `ink`, `weight`, `code`, `detail`, `url`], `email` {`enabled`, `klaviyo_company`, `klaviyo_list`, `label`, `note`}, `shop_label`, `fine_print` |
| `doors` | `id`, `tone`, `eyebrow`, `title`, `text`, `all_label`, `items` [`teaser`, `title`, `price_label`, `image`, `image_alt`, `url`] (12 doors, or 8) |
| `recipients` | `id`, `tone`, `eyebrow`, `title`, `text`, `tabs` [`label`, `image`, `image_alt`, `title`, `text`, `picks` [`name`, `price`, `price_label`, `image`, `url`, `image_alt`], `url`, `link_label`] |
| `split` | `id`, `tone`, `image_side` (`right`; omit for the default side), `image`, `image_alt`, `image_width`, `image_height`, `eyebrow`, `title`, `text`, `bullets` (list of strings), `buttons` |
| `giftbox` | `id`, `tone`, `eyebrow`, `title`, `text`, `closed`, `open` (two images), `image_alt`, `button`, `again`, `hint`, `tease_title`, `tease_text`, `ideas` [`tag`, `title`, `text`, `price_label`, `image`, `image_alt`, `url`, `cta`] |
| `budget` | `tone`, `eyebrow`, `title`, `text`, `steps` (list of numbers), `default`, `slider_label`, `count_many` (use `[n]` for the count), `count_one`, `items` [`name`, `price`, `price_label`, `image`, `url`, `image_alt`], `note` |
| `offer` | `id`, `tone`, `eyebrow`, `title`, `text`, `threshold` (number), `gift` {`name`, `value`, `image`, `image_alt`}, `try_title`, `left_text`, `done_text`, `items` (as budget), `buttons`, `fine_print` |
| `steps` | `tone`, `eyebrow`, `title`, `items` [`title`, `text`], `buttons` |
| `faq` | `tone`, `eyebrow`, `title`, `items` [`q`, `a`] |
| `cta` | `image`, `image_alt`, `eyebrow`, `title`, `text`, `buttons`, `contact` [`label`, `url`] |
| `faqschema` | `name`, `description` (outputs FAQ structured data for the page's `faq` block) |

## Wire every promise to something real

- **Prices.** `price` and `price_label` are display text the config holds; they do not read
  the product. Set them to the site's own prices, or set `price_label` to `""`. The store owner
  decides prices.
- **Spin codes.** Every `code` on a `spin` slice must exist as a promo code on the site, or
  remove the `spin` block.
- **Spend threshold.** The `offer` block only shows progress toward `threshold`. The gift
  itself needs an Automatic Discount on the site (see the main skill), or remove the block.
- **Dates.** `countdown` `target` and `deadlines`, and any FAQ answer that repeats them, must
  match the store's real order-by dates.
- **Links.** Every `url` points at a product, collection or landing page that exists on this
  site. Remove the door, pick or tile for anything the site does not sell.

## Images

Upload images in admin (Website, Assets) and reference them by file name in the config
(`"image": "lg-hol-hero.avif"`). Use one prefix per kit (for example `lg-` for landing images)
so names do not collide with existing assets. Use WebP or AVIF, sized for the slot. A name that
does not exist on the site renders as an empty image with no error, so check every image on the
live page.

## The Pages instance

Custom Types, Pages (the type id differs per site), new instance:

- `page_path`: the config key, e.g. `holiday` (the page is then `/site/holiday`)
- `page_title`, `page_description`: SEO title and description
- `page_content`: `{% snippet 'product-landing/landing' %}`. Extra page-only markup (for
  example a custom section with its own small script) can follow that line in the same field
  and travels with the page.

Then add the page to the menu, and check it live at phone, tablet and desktop widths: no
sideways scroll, sections aligned with the header and footer, every image loaded, no console
errors.

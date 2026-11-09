# Pixfizz plugins for Claude

Claude skills for Pixfizz customers and partners. Install once and Claude knows how the Pixfizz
platform actually behaves - the Liquid rules, the pricing engine, XML template geometry, the
Shopify integration, and the order things have to be done in.

Full setup walkthrough, including which Claude product to use and how to connect it:
**[aisetup.pixfizz.com](https://aisetup.pixfizz.com)**

## Install

**Claude desktop app (Cowork)**

Customize → Plugins → Add marketplace → `pixfizz/claude-plugins`, then install **Pixfizz Storefront**.

**Claude Code, in a terminal**

```
/plugin marketplace add pixfizz/claude-plugins
/plugin install pixfizz@pixfizz
```

The two plugin systems are separate and do not sync. If you use both, install in both.

## Plugins

| Plugin | Version | What it covers |
|---|---|---|
| **Pixfizz Storefront** (`pixfizz`) | 0.7.0 | Liquid and templates, pricing formulas, variants and template options, XML product templates, template resizing, Shopify + Pixfizz, conversion UX, storefront copy, photo book layouts, Lightspeed/Vend import, setup and launch sequencing, live site health checks, fulfillment setup, seasonal campaigns and holiday landing pages, your own designs in the studios (PSD or PDF to Pixfizz designs) |

Run `/pixfizz:help` after installing for a menu of everything with example prompts.

## What these skills are

Working procedure, not reference documentation. Each one carries the rules that stop you breaking
your own site, and points at the file in the public knowledge base that carries the full detail:
**[github.com/pixfizz/pixfizz-knowledge](https://github.com/pixfizz/pixfizz-knowledge)**.

They cover platform behaviour and implementation patterns. They do not cover Pixfizz pricing,
packaging or commercial terms - ask your Pixfizz contact for anything commercial.

## Changelog

- **0.7.0** - New `studio-designs` skill and `/pixfizz:designs`: bring your own designs into a
  Pixfizz studio or design product from a layered PSD or a finished PDF. Reads photo windows and
  live text, builds a design import from a real export of your template, and covers the routes the
  studios offer today: Greeting Card Studio store designs, the Business Cards site designs file,
  Calendar Studio, and the design tool for everything else. Ships four scripts. Also: XML text
  rules (kerning in points, shrink headroom, 32-character font names, no `unit` reads as mm, preview
  sets added late), redirects on `/site/` paths and `redirect_to`, product page filter rows,
  scoping CSS on platform components, the `extra_pages` price trap and discount rounding,
  post-import checks (fulfillment code, stale custom values), the social sharing image, account
  v2 flags, Shopify metafield namespace and the photo-prints launch branch.
- **0.6.0** - Holiday and seasonal landing pages: new `product-landing/config` reference (block
  types and keys, the Pages instance, wiring prices, codes and dates). Health check: read raw
  HTML before reporting schema or H1s, custom-domain sites on the `.pixfizz.com` host, dead
  sign-in and modal triggers, stale stored health results. Launch: a backup import replaces
  the whole child site, new child overrides start empty, ask for the backup without assets.
  Liquid: `asset_url` on a missing asset renders empty. Copy: no design counts, a simpler
  storefront hero.

## Support

- Help articles: [help.pixfizz.com](https://help.pixfizz.com)
- Video walkthroughs: [videos.pixfizz.com](https://videos.pixfizz.com)
- Anything else: support@pixfizz.com

Corrections and gaps in these skills are welcome - open an issue or mail support@pixfizz.com.

---

© Pixfizz Ltd. Provided for use with the Pixfizz platform.

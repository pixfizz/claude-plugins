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
| **Pixfizz Storefront** (`pixfizz`) | 0.4.0 | Liquid and templates, pricing formulas, variants and template options, XML product templates, template resizing, Shopify + Pixfizz, conversion UX, storefront copy, photo book layouts, Lightspeed/Vend import, setup and launch sequencing |

Run `/pixfizz:help` after installing for a menu of everything with example prompts.

## What these skills are

Working procedure, not reference documentation. Each one carries the rules that stop you breaking
your own site, and points at the file in the public knowledge base that carries the full detail:
**[github.com/pixfizz/pixfizz-knowledge](https://github.com/pixfizz/pixfizz-knowledge)**.

They cover platform behaviour and implementation patterns. They do not cover Pixfizz pricing,
packaging or commercial terms - ask your Pixfizz contact for anything commercial.

## Support

- Help articles: [help.pixfizz.com](https://help.pixfizz.com)
- Video walkthroughs: [videos.pixfizz.com](https://videos.pixfizz.com)
- Anything else: support@pixfizz.com

Corrections and gaps in these skills are welcome - open an issue or mail support@pixfizz.com.

---

© Pixfizz Ltd. Provided for use with the Pixfizz platform.

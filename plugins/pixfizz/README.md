# Pixfizz Storefront

Claude skills for building and improving a Pixfizz Shopper storefront.

Install:

```
/plugin marketplace add pixfizz/claude-plugins
/plugin install pixfizz@pixfizz
```

`/plugin` works in a local Claude Code terminal session. In the Claude desktop app, add the
same marketplace under Customize → Plugins → Add marketplace. See
[aisetup.pixfizz.com](https://aisetup.pixfizz.com) for the full walkthrough.

## Skills

**`liquid-patterns`** — the templating rules for Shopper. Code governance (Bootstrap 4.6, hard
tabs, `currency` not `money`, block boundaries), CSS delivery, the sort-and-filter rule that
catches most people out, the `style onload` pattern for JS that must survive AJAX re-injection,
option and variant rendering, redirects, and Dawn integration notes for Shopify + Pixfizz sites.

**`shopper-ux`** — conversion framework for storefront pages. Core principles, then
vertical-specific guidance for photo labs (including kiosk mode), photo gifting brands, and
school/sports photography. Ends with a review checklist for full page audits.

**`storefront-copy`** — hero sections, headlines, CTAs, social proof placement, page structure
frameworks, and a common-mistakes checklist to run before any copy ships.

**`pricing-formulas`** — Ruby pricing formulas and the traps that make prices silently wrong: the
per-unit rule, gap-free ranges, finite caps, `cut_print_quantity` on photo prints only, `quantity`
vs `units`, and `(pages - uncounted_pages)` for book pricing. Also covers cart-level Automatic
Discounts and Extra Fees, and the negative-variant workaround.

**`xml-templates`** — the production specification for a design product. Definition and set
attributes, the three geometry values that get misread (width, bleed, margin), PDF layers and
separate-file output, product archetypes, and the FTP fulfillment rules.

**`shopify-integration`** — the Shopify + Pixfizz path: metafields and SKU precedence, integration
types, the five theme snippets, cart item properties, order webhooks, static product ingestion,
and a fault index covering the symptoms that come up most.

**`lightspeed-importer`** — converts a Lightspeed or Vend CSV export into a Pixfizz Static
Product Importer CSV, with the pricing formula idiom the pricing engine actually accepts. Ships
`convert.py`.

**`photobook-layouts`** — creates the frame arrangements customers pick from in the Design Tool.
Writes layouts straight into an exported `__print_theme.yml` instead of dragging boxes in admin
forty times: 45 archetypes derived from the page geometry, tags read off the theme so the picker
keeps its photo-count grouping, duplicate shapes dropped, and a verifier that asserts id and
order preservation before you re-import. Ships six Python scripts including a proof-sheet
renderer.

**`storefront-launch`** — what to have ready and what order to do it in. Deployment models,
the Full Pixfizz and Shopify + Pixfizz phase sequences, the blocker per phase, the Shopper CMS
backup format and snippet-override encoding, the 14 order notification templates, vertical notes
for photo labs, school/sports and gifting, and a pre-launch checklist.

**`product-variants`** — the choices a customer makes on a product page. Which object a choice
belongs on (commercial variants on the Product Attribute, production options on the Template),
the seven option types and what each needs, children and triggers, the Shopper selector
overrides, where a price actually lives, element substitutions that survive being copied, and
the export traps that fail silently — `value_type` not `type`, booleans that import as their
opposite, and a re-import that duplicates rather than updates.

**`template-resize`** — derive a design product at a new size by rewriting the geometry in its
export instead of rebuilding it by hand. Handles a design theme or a full template export, one
target size or a whole size list from one seed, with per-size pricing and variant carry-through,
a proof sheet per size and a verifier. Proven at 5 sizes and twice at 62.

## Commands

| Command | Does |
|---|---|
| `/pixfizz:help` | Menu of everything here, with example prompts |
| `/pixfizz:liquid` | Template work using the Pixfizz Liquid rules |
| `/pixfizz:ux` | Conversion review of a page or flow |
| `/pixfizz:copy` | Write or review storefront copy |
| `/pixfizz:pricing` | Write, review or debug a pricing formula |
| `/pixfizz:xml` | Create or debug an XML template definition |
| `/pixfizz:shopify` | Shopify + Pixfizz setup or fault |
| `/pixfizz:import` | Lightspeed/Vend CSV to Pixfizz import |
| `/pixfizz:layouts` | Create or fill photo book layouts in a design theme |
| `/pixfizz:launch` | Plan or troubleshoot a storefront setup and launch |
| `/pixfizz:variants` | Create, review or debug variants and template options |
| `/pixfizz:resize` | Resize a template, or build a whole size range from one seed |

Skills also fire automatically when the work matches — the commands are shortcuts, not the only
way in.

## Going deeper

These skills are the working procedure. The full platform reference lives in the public knowledge
base at github.com/pixfizz/pixfizz-knowledge — each skill names the file that carries the detail
it summarises.

## Scope

These skills describe platform behaviour and implementation patterns. They do not cover
pricing, packaging or commercial terms — ask your Pixfizz contact for anything commercial.

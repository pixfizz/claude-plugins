---
name: storefront-launch
description: Getting a Pixfizz storefront configured and live - what to prepare, what order to do it in, and what blocks each phase. Use when setting up a new Pixfizz store, planning or reviewing a launch sequence, working out which deployment model applies (Full Pixfizz, Shopify + Pixfizz, Custom API or Marketplace), standing a site up from a Shopper CMS backup, reading or writing backup .tar files and snippet overrides, configuring order notification emails, or checking a store is ready to go live. Trigger for any question about store setup, launch sequencing, what needs to be ready before a phase can start, why a phase has stalled, or the pre-launch checklist. Also trigger for photo lab, school/sports photography or photo gifting stores where the vertical changes the setup order.
---

# Pixfizz Storefront Launch

## Deployment Model — Establish First

Before any setup work, confirm which deployment model applies. It determines which phases are
in scope and which system owns each part of the stack.

| Model | Storefront | Checkout | Personalisation | Production |
|---|---|---|---|---|
| Full Pixfizz | Pixfizz (Shopper) | Pixfizz | Pixfizz | Pixfizz |
| Shopify + Pixfizz | Shopify | Shopify | Pixfizz | Pixfizz |
| Custom API | Your own platform | Your own platform | Pixfizz | Pixfizz |
| Marketplace | Marketplace | Marketplace | Pixfizz | Pixfizz |

Shopper-specific onboarding (phases below) applies to **Full Pixfizz** deployments only.
For Shopify + Pixfizz, substitute the Shopify-specific phase sequence.

---

## What to Have Ready Before Starting

Have all of the following in hand before setup work begins. Missing items stall specific phases.

**Always required**
- Brand assets: logo (SVG or high-res PNG preferred), brand colours (hex), fonts
- Product catalog: categories, product names, variants, pricing structure
- Sample product images for personalisation testing
- Payment gateway credentials (Full Pixfizz) or confirmation of Shopify payment setup

**Required depending on model**
- Shipping rate structure (Full Pixfizz — needed for Phase 3)
- Shopify admin access (Shopify + Pixfizz — needed from Phase 1)
- CNAME / DNS access for custom domain setup
- Stripe account details (if Stripe is the payment gateway)

**Nice to have early**
- Existing product photography / lifestyle imagery
- Any existing store URL or legacy platform to reference for navigation structure
- Brand guidelines document if available

---

## Full Pixfizz — Launch Phase Sequence

A typical Full Pixfizz build runs 25-40 tasks across 5-6 phases, tracked in myPixfizz.

### Phase 1: Store Foundations
_Needs brand assets in place before it can start._

- Select and configure Shopper theme
- Upload logo and configure brand colours in style snippets
- Set up custom domain and SSL
- Build primary navigation structure
- Configure homepage (sections, hero, featured products)
- Set announcement bar, footer content

**Blockers:** Logo, colours, domain/DNS access, and a rough navigation structure.

### Phase 2: Product Setup
_Longest phase. Can run in parallel with Phase 1 if assets are ready._

- Define product categories and collection structure
- Create product templates (XML) for each product type
- Create design templates and configure personalization options
- Set up product variants (size, finish, quantity tiers, etc.)
- Configure pricing rules per product
- Upload product imagery

**Blockers:** Complete product catalog, pricing structure, and product images.
Pricing must be fully confirmed before launch — changes after go-live cause friction.

### Phase 3: Checkout Configuration
- Connect payment gateway (Stripe typical)
- Configure shipping rules and rates
- Set up tax handling
- Configure order confirmation and notification emails (14 templates available)
- Set minimum order amounts if required

**Blockers:** Payment gateway credentials, shipping rate structure, tax registration info.

### Phase 4: Production Setup
- Verify artwork generation for each product template
- Test production file output and confirm format matches lab/production requirements
- Confirm OrderHub job creation per product type
- Validate production file downloads

**Blockers:** Production specs from the lab or print supplier. Must know file format, colour
profile, bleed/trim requirements per product before this phase can complete.

### Phase 5: Launch Readiness
- Place test orders across all product types
- Validate full order lifecycle end-to-end
- Confirm payment capture and production routing
- Soft launch (restricted access or staff only)
- Fix any issues found in soft launch
- Full launch

**Note:** Do not skip the test orders. Issues found here are far cheaper than issues
found by live customers.

---

## Shopper Backup Format and New-Site Stand-Up (Reference)

Applies to Full Pixfizz (Shopper) sites. A CMS backup is a `.tar` of the site's CMS
content. Use this when standing a site up from an exported backup, or when reading a
reference site to copy structure.

### Backup .tar structure

| Path | Holds |
|---|---|
| `layouts/` | Layout wrappers, one file per layout |
| `pages/` | Real CMS pages, one file per page |
| `snippets/` | Everything else: theme tokens, checklist flags, nav, sections, homepage content |
| `asset_files/` | The actual binary assets (images), original filename kept |
| `assets/` | One `.yml` metadata sidecar per asset, named `<filename>.yml`, paired 1:1 with `asset_files` |

**A child-site backup contains only child-level overrides.** Everything not overridden
(most Shopper snippets, parent layouts, the icon library) is inherited from the Shopper
parent and is NOT in the tar. A small file count is normal, not a broken or partial export.

### File format

Every layout, page, and snippet is YAML frontmatter followed by a body:

```
---
name: style/color-primary        (real path, WITH slashes)
description: 
renderer_type: 1
---
#0d6efd                          (value or markup)
```

- `name:` carries the slash path. This is what the platform uses to resolve the snippet.
- `renderer_type: 1` = snippet. `renderer_type: 0` = page or layout. Layouts also carry a `default:` field.
- Token snippets (colours, sizes) are a single raw value in the body.

### Snippet filename encoding

Nested snippet paths flatten to filenames using double underscores:

| Snippet path | Filename in `snippets/` |
|---|---|
| `style/color-primary` | `style__color-primary` |
| `style/custom.css` | `style__custom.css` |
| `admin/checklist/font-body` | `admin__checklist__font-body` |
| `website/homepage` | `website__homepage` |
| `navigation/megamenu/gifts` | `navigation__megamenu__gifts` |

When creating a new override file, the filename uses `__` and the `name:` frontmatter uses
`/`. Both must agree.

### The layout is what loads the storefront (critical)

A working Shopper layout uses Pixfizz macro tags, not hand-written HTML:

```
<px:setup>
<html>
<head>
	<px:javascripts />
	<px:stylesheets />
</head>
<body>
	<px:content />
</body>
</html>
</px:setup>
```

`<px:stylesheets />` injects the full theme CSS stack including `/site/custom.css`.
`<px:javascripts />` injects the JS stack. `<px:content />` injects the page or home content.

**Gotcha:** a freshly created site can ship with a `main` layout that is bare hand-written
HTML with none of these tags. That site renders with no theme, no CSS, no fonts, and no
Bootstrap. Replacing that layout with the px-tag version above restores the entire
pipeline. This is the first thing to check on any site that renders as nothing.

### Home page wiring

Three pieces, all required together:
- `pages/__home` uses `layout_name: main` (the px-tag layout).
- `admin/checklist/custom-home-page` set to `TRUE` switches on custom home content.
- `website/homepage` holds the homepage markup (Bootstrap 4.6, `{{ 'file.jpg' | asset_url }}`
  images, `{% snippet 'icons/x.svg' %}` icons).

### Theme tokens

Colours, radii, and body font size are one-value snippets the CSS delivery page reads.
Retheming a site is setting these values. Common ones: `style/color-primary`,
`style/color-background`, `style/color-highlight`, `style/color-highlight-light`,
`style/btn-border-radius`, `style/btn-pill-border-radius`, `style/text-input-border-radius`,
`style/body-font-size`.

### Fonts

- `admin/checklist/font-body` accepts a built-in name (`lato`, `open-sans`, `avenir`) or `custom`.
- For `custom`, set `style/custom-body-font` to the font-family string, and load the web font
  (Google Fonts `<link>` via `integrations/custom-links`, which is a child override).
- Heading/display fonts have no built-in snippet. Wire them in `style/custom.css`. The custom
  CSS page loads after the theme CSS, so heading font-family wins without `!important`.

### Assets

- Reference in Liquid as `{{ 'name.jpg' | asset_url }}`.
- Binary lives in `asset_files/name.jpg`; metadata sidecar in `assets/name.jpg.yml`.
- On a live site, upload via Main Admin, Website, Assets. Both entries appear on the next export.

### Nav override

The active two-row nav is `navigation/style3`. Links are defined in a
`{% capture navigation_links %}` block, each `<li class="nav-item position-static">`.
Override nav by editing that capture block. `position-static` is required for full-width
megamenu dropdowns.

### Watch for stray snippets

Real backups can carry test or stray snippets. Ignore anything that is not a known Shopper path.

### Header logo and navigation (include in the FIRST tar pass)

Wire the brand into the header as part of the initial build, not as a follow-up:

- **Logo**: override `header/logo` by swapping ONLY the asset name in the parent's exact
  pattern: `<img src="{{ 'logo-file.svg' | asset_url }}" alt="{% snippet 'website/title' %} logo" class="navbar-brand-logo">`.
  CRITICAL: do NOT add an anchor (the navigation snippets already wrap this in `<a>`;
  nesting anchors makes the browser split the DOM and the mobile logo escapes its
  `d-lg-none` wrapper, leaking onto desktop). Do NOT add inline sizing; keep the
  `navbar-brand-logo` class, which is sized by the theme.
- **Logo sizing**: `header/logo-height-desktop` (parent default 52px) and
  `header/logo-height-mobile` are one-value snippets. Override to suit the mark.
- **Do NOT style `.nav-logo`**: in `navigation/style3` that anchor is an empty, unstyled
  legacy element. Painting a CSS background into it duplicates the real centered desktop
  logo, which is rendered by an absolutely-positioned div also calling `header/logo`.
- **Navigation, order matters** (known failure mode when skipped): FIRST set or confirm
  `admin/checklist/header-logo-position`, which takes ONLY `CENTER` or `LEFT`. CENTER
  renders `navigation/style3`, LEFT renders `navigation/style1`. THEN edit only the
  matching snippet's `{% capture navigation_links %}` block, each link as
  `<li class="nav-item position-static">` (required for full-width megamenus). Never edit
  a nav style the flag does not select; the edit silently does nothing and wastes a cycle.
- **Favicon**: upload as an asset named exactly `favicon.png`, a transparent PNG, square
  ratio, max 192x192px. No snippet or admin setting needed; the platform picks it up by name.
- The logo asset binaries (plus `.yml` sidecars) go in the same tar.

### Standing up a new Shopper site from a backup

**Import gotcha (verified in production):** tar imports do not reliably apply
`admin/checklist/*` flag values. A checklist snippet can be present in the tar with the
correct value and still not take effect. After every import, verify all checklist flags
(especially `custom-home-page`) in the admin UI and set them manually if needed.

Order of operations for a fresh child site:

1. Confirm the site is a Shopper child (inherits the parent template). If not, that is the
   first fix and may need platform help.
2. Ensure `layouts/main` is the px-tag version. Replace it if it is bare HTML.
3. Set `admin/checklist/custom-home-page` to `TRUE`.
4. Set theme token snippets (colours, radii) to the brand palette.
5. Set `admin/checklist/font-body` to `custom`, add `style/custom-body-font`, the web-font
   `<link>`, and `style/body-font-size`.
6. Add brand foundations to `style/custom.css` (design tokens, heading font wiring, base type).
7. Override `header/logo`, add the desktop `.nav-logo` CSS, set `header/logo-height-mobile`,
   and override the active navigation snippet's links (see Header logo and navigation above).
8. Build `website/homepage` content.
9. Re-import the tar, verify checklist flags in admin, then confirm theme, fonts, logo, nav, and home render before building further.

---

## Shopify + Pixfizz — Launch Phase Sequence

### Phase 1: Shopify Store Access
- Grant Pixfizz collaborator admin access on the Shopify store
- Confirm Shopify plan and theme compatibility
- Review existing product catalog structure

### Phase 2: Pixfizz App Installation
- Install Pixfizz Shopify app
- Generate API credentials and connect systems
- Configure webhooks for order sync

### Phase 3: Product Synchronisation
- Map Shopify products to Pixfizz templates
- Configure personalisation options per product
- Map variants between Shopify and Pixfizz
- Validate pricing alignment between platforms

### Phase 4: Checkout Flow Validation
- Validate cart integration and personalisation data transfer
- Verify orders flow correctly from Shopify to Pixfizz
- Confirm order line item data is complete for production routing

### Phase 5: Production Verification
- Place test orders through Shopify
- Confirm artwork generation and OrderHub job creation
- Validate production routing for each product type

### Phase 6: Launch
- Validate full personalisation and checkout UX
- Confirm production output quality
- Enable products for public purchase

---

## Common Blockers by Phase

| Phase | Typical blocker |
|---|---|
| Phase 1 | Logo / brand assets not ready |
| Phase 2 | Product catalog incomplete or pricing not finalised |
| Phase 3 | Payment gateway credentials missing or gateway not yet set up |
| Phase 4 | Production specs not confirmed with lab/supplier |
| Phase 5 | Nobody available to approve test orders |

---

## Vertical-Specific Notes

### Photo Labs
- Confirm early whether kiosk mode is required — it affects storefront structure significantly
- Establish whether the lab offers in-store collection (affects checkout/shipping config)
- Film processing services (if offered) need separate product template setup
- Same-day or next-day collection messaging is a strong commercial differentiator — plan for it in Phase 1

### School / Sports Photography
- Access code / class lookup flow must be planned before navigation is built (Phase 1)
- Package tiers (print bundles vs single prints) must be fully defined before Phase 2
- Seasonal campaigns mean launch timing is critical — delay past peak season has real revenue impact

### Photo Gifting Brands
- Occasion-based navigation structure should be confirmed in Phase 1 before building nav
- Gift wrapping and delivery date options add complexity to Phase 3 — flag early

---

## Email Notification Templates

14 email templates are available, mapped to the order lifecycle. Configured in
Admin → Settings → Email Notifications. Each can be enabled or disabled individually.

**Order lifecycle:** Order Pending, Order Draft, Order Confirmed, Order Downloaded,
Order Manufactured, Order Shipped, Order Fulfilled, Order Error, Order Canceled,
Orderline Fulfilled.

**Other:** Cart Abandoned, User Signup, Password Reset, Sign-in Token Renewed.

Review and customise all active templates before launch — default content often references
generic Pixfizz copy that should be replaced with your own brand voice.

---

## Pre-Launch Checklist

- [ ] All product types have been test-ordered
- [ ] Payment capture confirmed (real test transaction, not test mode only)
- [ ] Production files generated and approved for each product type
- [ ] All 14 email templates reviewed - active ones customised for your brand
- [ ] Custom domain live with SSL confirmed
- [ ] Navigation and homepage signed off
- [ ] Retail pricing confirmed and validated against your own rate card
- [ ] Shipping rules tested with real address(es)
- [ ] Kiosk mode tested on intended hardware (if applicable)

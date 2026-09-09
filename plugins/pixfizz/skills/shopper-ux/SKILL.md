---
name: shopper-ux
description: "Conversion-focused UX and UI guidance for Pixfizz Shopper template sites. Use this skill whenever the user is working on any aspect of a Shopper-based storefront — reviewing layouts, designing pages or sections, critiquing component design, improving CTAs, planning information architecture, or evaluating any eCommerce flow within a Pixfizz site. Also trigger for any question about eCommerce UX in the context of photo labs, photo gifting, school photography, sports photography, or personalized print products on the Pixfizz platform. Always apply even if the user does not explicitly mention conversion — conversion is always the underlying goal. Trigger for kiosk interface work on any photo lab Shopper site."
---

# Pixfizz Shopper UX — Conversion Framework

## Living Document

This skill should be updated after any conversation where new UX patterns, vertical-specific
insights, or Shopper implementation decisions are established. After relevant sessions, suggest
an update to the appropriate section and confirm with the user before writing changes.

---

## Hard Constraints

All suggestions must be implementable within these boundaries:
- Bootstrap 4.6 (utility classes, grid, components) — the version the Shopper template ships with
- Liquid templating (Shopper CMS)
- HTML and CSS only — no custom JavaScript
- No assumptions about third-party scripts or plugins

Suggestions outside these constraints are still valid as directional input but must be clearly
flagged as "outside current scope — requires developer involvement" and not presented as the
primary recommendation.

---

## Core Conversion Principles

These apply across all Pixfizz Shopper verticals.

### 1. Reduce steps to the editor

The Pixfizz personalisation editor is the conversion engine. Every page and component should
move the customer closer to it. Audit any design for unnecessary steps between landing and
starting personalisation.

- Primary CTA on product pages: always action-oriented ("Start Creating", "Personalise Now",
  "Order Prints" — match the lab's language)
- Never bury the primary CTA below the fold on mobile
- Product cards in grids: CTA must be visible without hover on mobile

### 2. CTA hierarchy

Each page should have one dominant CTA. Secondary actions (share, save, compare, browse more)
must be visually subordinate. Never compete with the primary conversion action. If two actions
feel equal in weight, one of them is wrong.

### 3. Trust signals

Personalised products carry purchase anxiety — will it look right, will it arrive in time, will
the quality match expectations. Address this proactively and close to the point of decision:
- Quality reassurance near the CTA (print quality, material specs, "printed in our lab")
- Delivery or collection timeframes visible before checkout, ideally on the product page
- Social proof (reviews, order counts) placed close to the primary CTA, not only at page bottom

### 4. Mobile-first

Assume a significant portion of online traffic is mobile. Evaluate every layout at mobile
viewport first. Key checks:
- CTA reachable with thumb (bottom-anchored or high in viewport)
- Product imagery loads fast and fills width
- Personalisation preview is legible at small size
- Touch targets minimum 44px height

### 5. Imagery strategy

- Lead with lifestyle imagery (finished product in context) to trigger emotional purchase intent
- Follow with product detail (print quality, material close-up) to resolve doubt
- For personalised products: show realistic placeholder content in the product, never blank
- For photo labs: use imagery that reflects the local community and studio environment where
  possible — reinforces the physical presence as a trust signal

### 6. Pricing transparency

Show price early. Do not make customers click through to find it. For variable-price products
(size, format, quantity), show a "from £X" anchor price on the grid card. Minimum order amounts
should be surfaced at cart stage, not at checkout.

---

## Vertical-Specific Guidance

### Photo Labs (local / kiosk)

Photo lab customers are often local — ordering on an in-store kiosk, planning to collect in
person, or switching between both channels. This creates UX opportunities that most eCommerce
templates do not exploit.

**Online storefront**
- Prominently surface "Collect in Store" as a fulfilment option — treat it as a feature and
  competitive advantage, not just a delivery variant buried in checkout
- Show store location and hours in the header or a persistent banner for single-location labs
- "Ready in X hours" or same-day collection messaging is a strong conversion driver — surface
  it on the homepage and product pages, not only at checkout
- Reinforce physical presence as a trust signal: "Printed in our [City] lab", studio
  photography, staff imagery if available
- Repeat customers are common — consider whether a returning customer flow (reorder, continue
  editing) is surfaced accessibly

**Kiosk interface (Shopper kiosk mode)**

The Pixfizz Shopper kiosk mode is a distinct deployment (subdomain-based, e.g.
kiosk.sitename.com) designed for in-store touchscreen use. Key patterns established in
production:

- **Home screen**: Large task-selection tiles as the primary interface ("What would you like
  to do today?"). Two or three tiles maximum. Secondary "Browse all products" as a quiet text
  link — not a button — for customers who want to explore beyond the primary tasks.
- **Navigation model**: "Start Over" replaces conventional back/breadcrumb navigation. It
  should be persistent and clearly visible throughout the flow. No standard site nav bar.
- **Kiosk Active indicator**: A status pill (top right) confirms the session is in kiosk mode.
  Useful for staff to verify the correct mode is running.
- **Staff Access**: Present but visually tucked away (bottom left, low contrast). Not hidden,
  but not prominent — customers should not be drawn to it.
- **Order flow layout**: Split-panel on larger screens — photos/selections on the left,
  persistent pricing and options panel on the right. This allows customers to see the running
  total and make size/quantity decisions without scrolling.
- **Size and quantity selection**: Touch-friendly +/- stepper controls. Currently selected
  option highlighted in brand accent colour. Price per item shown inline with each option.
- **Touch targets**: All interactive elements must be comfortable for finger interaction.
  Minimum 44px, aim for 56px+ on primary actions.
- **Reduced cognitive load**: Fewer navigation options, fewer distractions, task-oriented
  language throughout. The kiosk customer is standing at a screen in a shop — they want to
  complete the task, not explore.
- **Minimum order**: Surface minimum order amount at cart, not at checkout. Kiosk customers
  may be ordering a single low-value print — clarity here prevents abandonment at the final
  step.

**Cross-channel considerations**
- A customer who starts online and collects in-store, or vice versa, should experience
  consistent branding and product framing across both touchpoints
- Kiosk UI and online storefront can share design language (colours, typography, product
  photography) even where layout differs significantly

**Product focus**
- Photo prints, photo books, canvas, framed prints tend to be the core lab offering
- Keep navigation shallow and product discovery fast — lab customers typically know what
  they want
- Film processing (where offered) should be a top-level category, not buried

### Photo Gifting Brands

- Occasion-led navigation works well (Birthday, Wedding, New Baby, etc.) — lead with the
  moment, not the product spec
- Emotional hooks drive purchase — hero content should centre the recipient and the occasion
- Gifting anxiety: delivery date guarantees and gift wrapping options should be prominent,
  not discovered at checkout
- Personalisation preview is especially important — "see it before you buy it" reduces
  abandonment significantly in this vertical
- Upsell opportunities are strong here — complementary products (cards, wrapping, extras)
  can be introduced post-personalisation without disrupting the primary flow

### School / Sports Photography

- Purchasers are parents, often on mobile, often time-pressured
- Access code or class/team lookup flows must be the hero element on the homepage — the
  entire page should orient around this action for seasonal campaigns
- Package selection (single print vs bundle vs digital) is the key conversion moment —
  present tiers with clear visual differentiation and a recommended/popular flag on the
  most valuable option
- Seasonal urgency is real — deadline messaging and countdown elements are appropriate and
  effective here; do not shy away from them
- Trust signal priority in this vertical: school/club branding and the photographer's name
  carry more weight than generic reviews

---

## Review Checklist

Use this section only when conducting a full UX audit of a page or flow. Do not surface in
routine design or component work.

- [ ] Is the primary CTA above the fold on mobile?
- [ ] Is there a clear single dominant action per page?
- [ ] Are trust signals (quality, delivery, reviews) near the CTA?
- [ ] Is pricing visible before the product detail page?
- [ ] Does the layout lead with lifestyle imagery?
- [ ] Are all suggestions implementable in Bootstrap 4.6 + Liquid + HTML/CSS?
- [ ] If photo lab vertical: is in-store/collection messaging surfaced early?
- [ ] If kiosk mode: is "Start Over" persistent, are touch targets sufficient, is the
      split-panel layout used for the order flow?
- [ ] If school/sports vertical: is the access/lookup flow the hero element?
- [ ] If gifting vertical: is occasion context and delivery reassurance prominent?

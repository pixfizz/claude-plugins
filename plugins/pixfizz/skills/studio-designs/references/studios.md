# Routes per studio

Sizes are in mm and include bleed unless a line says "trim". 1/8 in bleed is 3.175 mm. The seed export is the
authority for page names and sizes: if it disagrees with a table here, the seed wins and the build follows it.

## Design tool route (any design product)

The design opens in the Pixfizz design tool on the lab's own template. Works on any template with normal pages.

What the build writes on each page, bottom to top:

| Element | Name | Notes |
|---|---|---|
| White base, locked | `artwork_base` | Full page, so a transparent area never prints as nothing |
| Photo windows | `photo-1`, `photo-2`, ... | Placeholders in reading order (top to bottom, left to right). Rename freely: the design tool does not care, design options and studios do |
| Artwork, locked | `artwork_top` | The design with the windows cut out. Art drawn over a window in the source (a ribbon over a photo) stays over the photo |
| Live text | the names you set | One element per line, shrink to fit, 5% headroom |

Names that read well in the design tool and that the Greeting Card Studio library designs also use: `greeting`,
`name`, `line`, `line2`, `line3`, `note`, `sign`, `mono`. Use them unless the lab has its own convention.

If the lab wants a "change the photo" or "type your name" field on the product page (instead of opening the design
tool), that is a design option targeting the element by name. Add it in the admin after the import; the build does
not create options.

## Greeting Card Studio: store designs (the lab's own designs in the studio)

Studio 0.5.0 and later. The lab's own card designs sit in the studio next to the Pixfizz and MSP designs, priced from
the lab's own card products. Each store design keeps exactly the card type and orientation its template has.

**What a store design is**
- A design on the lab's **own** 5 x 7 in card template: folded (pages `front`, `outside`, `inside`, `back`) or flat
  two-sided (`front`, `back`). Portrait or landscape is read from the front page.
- The **front is one fixed picture**: one image named `cover`, the whole artwork with its bleed. No photo, no words
  to change. A flat PDF or PNG is ideal; for a PSD, put every front type layer in `bake`.
- **Back and inside** are plain white and carry only these elements:

| Page | Images | Text |
|---|---|---|
| Flat two-sided, `back` | `logo` or `back-image` (the customer's logo) | `sentiment` (message), `signature` (company or family name) |
| Folded, `back` | `back-image` | `back-message` |
| Folded, `inside` | `logo`, `photo` | `sentiment`, `signature` |

The build stops on any other name, or on artwork on the back or inside. Codes ending `-upload` are skipped by the
library (the studio's own "Your own design" replaces them).

**Page sizes on the 5 x 7 templates (with bleed)**

| Card | Page | Portrait | Landscape |
|---|---|---|---|
| Flat | `front`, `back` | 133.35 x 184.15 | 184.15 x 133.35 |
| Folded | `front`, `back` | 130.175 x 184.15 (no bleed on the fold side) | read from the seed |
| Folded | `inside` (open spread) | 260.35 x 184.15 | read from the seed |

`outside` (and any `finished` mockup page) is made of page references only; the build copies it from the seed.

**Steps**
1. Build each design with `build_design.py --profile gcs-store`, import it on the lab's card template, check it in the
   design tool.
2. Export the template (with its designs) from the admin and unpack it. Run:
   `python3 scripts/gcs_store_library.py <site tag> lib/ <unpacked template export> [more exports]`
   It writes `gcs-store-<tag>-designs.json`, a front picture per design (`.webp`), the sample logo and photo, and the
   fonts the templates use (`.woff2`) so the studio shows the print fonts.
3. Upload every file in `lib/` to the site's Assets. Read back each asset's URL.
4. Write `gcs-store-<tag>-files.json` as `{"v": "<date>", "files": {"<asset name>": "<asset url>", ...}}` with every
   file from step 2, upload it too, and read its URL.
5. Publish the designs to a collection (kept out of the menu).
6. Add to the studio page's settings (the page content holding `product/greeting-card-studio`):
   `gcs_store_collection: '<that collection>'`, `gcs_store_products: 'fold-p:<product id>,flat2-l:<product id>'`
   (one role per card product the designs sit on), `gcs_store_files: '<URL of the files index>'`. If those products
   name the paper or envelope variants differently, add `gcs_store_paper_variant` and `gcs_store_envelope_variant`.
   All three main settings or store designs stay off. Never an apostrophe in a value.
7. Open the studio: the designs show under their own occasion, in their own orientation only, at their product's
   price. Open one, add a logo, change the message, check the proof, add to cart.

**Store products and variants.** The studio sends only its own variants (paper, finish, corners, envelope and the
envelope printing ones). Any other variant on the store products (a proof or rush option) is not sent and, if it is
required, blocks Add to cart.

## Business Cards: site designs file

Business Cards 3.5.0 and later. The lab's designs are listed first in the design picker, before the shared designs.

**What a site design is**
- One design = a front and an optional back, each the card trim plus bleed (3.5 x 2 in card: 95.25 x 57.15 mm).
- The artwork is one image per side. Every text line is a field the customer types into (set `label` on a text in
  `layout.json` for the field label, `"fixed": true` for words that belong to the design).
- At most one photo window per side, named `photo` (the customer adds their photo with the standard crop). A window
  named `logo` is the logo slot: the customer's logo, an icon, or nothing (the order waits until they choose).
- Fonts load from Google Fonts: each font needs `"google": "Family:weight"` as well as a `file` for measuring.

**Steps**
1. One layout per design (`extract.py`), pages named `front` and `back`.
2. `python3 scripts/bc_site_designs.py --trim <W>x<H> --bleed 3.175 --safe 3.175 --tag <tag> --out build/ <layouts>`
   The trim must be the card's trim in mm (3.5 x 2 in = `88.9x50.8`). One file per card size: the tool refuses a
   file whose trim or bleed differs from the card, and never scales a design to another size.
3. Upload the JSON and every `.webp` to the site's Assets.
4. On the business card template's `px_mount`, add the two lines the script printed:
   `bc_designs_more_file: '...'` and `bc_designs_more_assets: '...'` (`bc_designs` must be `'true'`).
5. Open the product: the lab's designs come first. Open each, type a long name, add a logo, check the proof and the
   Finished view, add to cart. Check the console for "[business-cards]" errors (a refused file or a missing image
   says so there).

## Calendar Studio: copy a studio design and swap the art

The studio reads designs by code `<template code>-cs-<design>` from the collection in `cs_collection`, each with
pages `cover`, `image`, `calendar-month`, `back-cover` (wall) or `calendar-month` (desk), photo frames named
`photo`, `photo-2`, ..., a `caption` text on the photo layouts, a `cover-sub` text on the cover, and layouts named
`cs-photos-1`, `-2`, `-4` (and `-caption` versions) tagged `1 photo`, `2 photos`, `4 photos`. The month grids are
calendar elements that fill dates; a designer's PSD cannot recreate them.

So the route keeps everything the studio reads and only changes the look:
1. On the lab's calendar template, **Copy** an existing Calendar Studio design (the Copy button keeps the linked
   layouts; an export and re-import loses them).
2. Give the copy a code in the studio pattern (`<template code>-cs-<new design>`) and a name.
3. Read the designer's pages with `extract.py` (one per page role). Use each page's `-art.png` as the background
   image on the matching page of the copy, under the date grid and photo frames. Change fonts and colors of the
   month names and dates to match.
4. Keep every element name above. Publish the copy to the `cs_collection` collection and open it in the studio.

Not built yet: a script that swaps the art into a calendar design export automatically.

## Studios with no own-design intake yet

Photo Book Studio, Collage Studio, Puzzle Studio, Mug Studio, Pet Studio, Stationery Studio, the wall studios and
the T-shirt Studio show only the designs Pixfizz ships for them. Tell the lab so, and that the request is noted.
Where the product also exists as a normal design product, the design tool route works today.

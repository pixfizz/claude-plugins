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

The lab's own card designs sit in the studio next to the Pixfizz and MSP designs, on the lab's own card products and
at their prices. Each design keeps exactly the card type and orientation its template has (one card type, one
orientation, offered as such). There are two kinds; nearly every retail design is the first.

| Kind | Studio | Front | Back and inside | Builder |
|---|---|---|---|---|
| **Live front** | where set up (below) | photo windows and words live, art above or below the photos kept | photo windows and words live | `scripts/gcs_store_live.py` from design exports |
| Fixed front | 0.5.0+ | one finished picture (`cover`) | logo, photo and message by fixed names | `scripts/gcs_store_library.py` from a template export |

### Live front: which stores have it

As of 25 Nov 2026 the live front is in the studio file of the stores Pixfizz has set it up on. The shared studio file
other stores run does not have it yet, whatever its version number says. Ask Pixfizz support to confirm or add it for
the store before step 7 (Mount). Everything before that step can be done first.

### Live front: what the studio needs

A design qualifies when all of these hold. The builder checks each one and prints PROBLEMS for anything it cannot place.
- It sits on the lab's own **5 x 7 in card product**, flat two-sided (pages `front` and `back`) or folded (pages
  `outside` and `inside`). Any design code; MSP-origin designs the lab copied onto its own products qualify too.
- **Photo windows** are image elements with `placeholder="true"` OR a name starting with `placeholder`
  (case-insensitive, e.g. `Placeholder 3`). Anything else is art.
- **Words** are text elements with `edit="true"`. Text without it is part of the art. Words that must print untouched
  must not have `placeholder="true"` (such text never prints unless the customer's edit clears the flag).
- Art that only a template option puts on the page (a Color Theme or Greeting option that fills an image element with
  no source) is drawn from that option's default value; the builder says so per element.
- Up to 12 or more photo windows per face is fine; art drawn above a photo (a frame, a bow) is kept above it.

How the builder turns a design into the studio's format (the same method as the MSP designs):
- The art of each face is cut into **plates**: everything below the first live element, then the art between live
  elements, so art above a photo stays above it. All plates of a design go in one atlas image (`-a-<key>.webp`,
  `-t.webp` for small views).
- Photo windows and words stay live on top, at their exact boxes, rotation, font, size, color and alignment.
- A photo window with a **mask** (arch, circle) gets its mask as a small PNG (`-m-<hash>.png`).
- The site fonts the words use are shipped as `woff2`, cut to Latin characters so each stays well under 300 KB.
- The hand-off map (`map` in the library): for every live element its page, its name when unique on the page, and
  its box in page mm, written in the same pass as the studio keys, so they always match. At Add to cart the studio
  finds each element by name, else by box (within 3 mm).

Export quirks to know (seen in real exports, 20 Nov 2026):
- `left` and `top` on an image are its **crop offset inside the box, not its position**. A missing `x` or `y` is 0.
  Never read `left`/`top` as a position.
- Exports carry extra pages (`preview-front`, `preview-back`, `preview-both`, `backup`), not always flagged as
  previews. Only `front`, `back`, `outside` and `inside` are card faces.
- Several elements can share a name (or have none); the box fallback covers them.

### Live front: steps

1. **List the designs.** From the lab: which designs, on which products. Read the products' templates and variants
   with the Pixfizz connector (`product_get`). Note the product id per card type and orientation, e.g. flat
   portrait and flat landscape. Designs in other sizes (4 x 5.5, 6 x 8.5) wait: the studio prices one size.
2. **Export each design**: `admin.pixfizz.com/site/<site>/admin/print_theme/export_print_theme/<design id>` (one file
   per design, the file name starts with the site). Unpack each into its own folder.
3. **Build the library** (needs `pyyaml lxml pillow fonttools brotli`):
   `OCC=christmas OCC_NAME=Christmas MIN_UNITS=<product minimum> python3 scripts/gcs_store_live.py <tag> lib/ <export dirs>`
   Designs for several occasions in one library: add `OCC_MAP=<file>.json`, a JSON object of design id to occasion
   key (`christmas`, `hanukkah`, `newyear`, `seasons`, `faith`); designs not listed take `OCC`. A store whose studio
   does not sort store designs by occasion yet shows them all under `OCC`.
   `<tag>` is short and new per library (e.g. `vh`, `retail`): never reuse the tag of a fixed-front library on the
   same site. Read PROBLEMS: every line is something the customer would see wrong. Fix the design in the admin and
   export again; never edit the output.
4. **Look before uploading.** Open each front preview (`gcs-store-<tag>-<key>.webp`) next to the design in the admin.
5. **Upload** every file in `lib/` to the site's Assets (keep the names). Then write
   `gcs-store-<tag>-files.json` as `{"v": "<date>", "files": {"<asset name>": "<asset url>", ...}}` from the asset
   list (`assets_list` in the connector), upload it, read its URL. Every URL in the index is absolute
   (`https://...`): a relative `/fz/...` path belongs to one host and answers 403 from the storefront.
6. **Publish** the designs to one collection kept out of the menu (the studio reads it by name).
7. **Mount**: on the studio page (Pages, the instance holding `product/greeting-card-studio`) add
   `gcs_store_collection: '<collection>'`, `gcs_store_products: 'flat2-p:<id>,flat2-l:<id>'` (one entry per card type
   the designs sit on: `flat2-p`, `flat2-l`, `fold-p`, `fold-l`), `gcs_store_files: '<files index URL>'`. Add
   `gcs_store_paper_variant` / `gcs_store_envelope_variant` when those products name the variants differently.
   Test on a hidden page first. Never an apostrophe in a value.
8. **Check on the live page**, desktop and phone, every design:
   - the gallery tile shows "Flat · N photos" and the right price;
   - the front shows the art, a window per photo, the words; type a long family name;
   - add photos (all windows; the studio waits until every window has one), crop one, swap two;
   - back side, paper and quantity, envelopes, proof, Add to cart;
   - open the cart project in the design tool: every photo in its window, the typed words on the page, nothing moved;
   - generate the production PDF of a test order.
   Report each as checked or not verified.

### Live front: what it does not do yet
- Sizes other than 5 x 7 (4 x 5.5, 6 x 8.5) and switching between versions of one design ("linked layouts").
- Text on a curve or with mixed styles in one line shows as one plain style.
- A "Your logo" slot on a live design (logos are a fixed-front feature).

### Fixed front (corporate cards)

Studio 0.5.0 and later. Use only when the whole front is one finished picture and the back and inside carry a logo,
a photo and a message.

- A design on the lab's **own** 5 x 7 in card template: folded (pages `front`, `outside`, `inside`, `back`) or flat
  two-sided (`front`, `back`). Portrait or landscape is read from the front page.
- The **front is one fixed picture**: one image named `cover`, the whole artwork with its bleed. A flat PDF or PNG is
  ideal; for a PSD, put every front type layer in `bake`.
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
3. Upload, files index, collection and mount as in the live-front steps 5 to 8.

**Store products and variants (both kinds).** The studio sends only its own variants (paper, finish, corners,
envelope and the envelope printing ones). Any other variant on the store products (a proof, rush or size option) is
not sent and, if it is required, blocks Add to cart: make it optional with a default, or leave the product out.

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

## Calendar Studio: the lab's own calendar templates

Calendar Studio 0.6.0 and later (November 2026; live on one store when this was written, so test every step). The
lab's own calendars run in the studio as they are: its own products, templates, sizes, month grids, prices and
choices. Pixfizz switches this on per store in the studio page config (`"mode":"own"` in `#cs-config`). Your part is
to check the templates fit, send Pixfizz the list, and test.

**What each calendar needs**
- One design per product. A version with a cover is its own product next to the version without.
- The month page is the page type the template definition prints for the months. Read the definition with XML
  comments stripped: a template can keep older pages and commented-out cover sets that never reach a project.
- One photo window per month page: an image with `placeholder="true"`. Other images on the page (grid cell art)
  are kept as art and are never filled.
- A cover only where the definition prints one. A back cover is not shown or filled in the studio and prints as
  the template has it.
- Month names are drawn as the template's sample text has them (full, title case, or three letters).
- Holidays and personal dates are offered only on calendars whose month page has those calendar fields.

**Not offered in this mode:** the 1, 2 or 4 photo layouts, the caption line, date stickers, Colors, Monday-start
twins, the room view and the design tool link.

**What to send Pixfizz, per calendar:** product id and design id, wall or desk, the name and one line of text for
its card, the size label, the binding (`previews.md`), and the variant code of any extra choice the customer makes
(for example production time).

**Check on a hidden page before linking it,** desktop and phone, every calendar:
- its card shows the right name, size and price; the with-cover switch changes product and price;
- add photos: one per month (and the cover); Add to cart stays off while any page is empty;
- the extra choice changes the price and is on the cart line;
- open the cart project's pages: cover and 12 months filled, grid art untouched, back cover as the template;
- generate the production PDF of a test order: month names, holidays on the right days, page count.

To take a calendar out of the studio, remove its row from the studio collection; unticking Published on the row
does not hide it (0.6.1).

## Calendar Studio: copy a studio design and swap the art

For a lab that wants its own art on the studio's calendars (the studio's sizes, grids and photo layouts).

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

## Photo Book Studio: the lab's own books and cover designs

For a store that sells its own book lines (sizes, cover designs, prices) in the studio. Pixfizz switches this on per
store with the `collections` block of `#pbs-config` on the studio page (`28_TOOL_SETTINGS_REFERENCE.md`, Photo Book
Studio); do not write that block yourself. Your part is the designs.

**What the studio needs**
- Each book size is its own product on its own template. A cover design is one design per size on that template,
  published to the studio's design collection.
- Every design has its **Linked Layouts** (the page layouts and cover layouts designs). An import does not create
  the links: without them the studio has no layouts.
- Page books (pages `cover`, `page01`, `page02` ...) need `"layflat":"false"` in the block (studio 4.0.4+); the
  default is lay-flat spreads. Tell Pixfizz which the books are.
- On the cover, an image named `placeholder` with a sample photo is the customer's cover photo (studio 4.0.5+);
  any other image is fixed art. Editable text is the title the customer types.

**Adding a cover design**
1. On the book template, **Copy** a design that already works in the studio (Copy keeps the linked layouts), then
   give the copy its name and code.
2. Change the cover page only: the art, the title text, the photo window. Lay it out from that size's own cover
   page (spine and hinge differ per size), keeping the page tag and the spine and hinge elements.
3. Repeat per size. The same art is a separate design on every size.
4. Before publishing, read each design's cover page (`/v1/themes/<design id>.json?sitename=<site>`) and look at
   `/v1/themes/<design id>/preview.webp?hide_placeholders=false&height=900`: a copy that still shows the old cover
   is the usual miss.
5. Publish to the studio's design collection. Check in the studio: the cover in the gallery for every size, the
   cover photo, the title, the price in the store's own currency, Add to cart, and the production PDF of a test
   order (cover and spine).

Not built yet: a script that writes a cover onto every size from one design file.

## Studios with no own-design intake yet

Collage Studio, Puzzle Studio, Mug Studio, Pet Studio, Stationery Studio, the wall studios and
the T-shirt Studio show only the designs Pixfizz ships for them. Tell the lab so, and that the request is noted.
Where the product also exists as a normal design product, the design tool route works today.

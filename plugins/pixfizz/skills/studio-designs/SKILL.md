---
name: studio-designs
description: Use when a lab wants to bring, pull or import its own designs into a Pixfizz studio or design product - greeting cards, business cards, calendars, photo book covers - from a layered PSD, a finished flat file (PDF, AI, PNG, JPG) or designs already on its site, or wants to change how a design looks before the customer picks it (studio thumbnail, preview image, calendar spiral, a border instead of full bleed). Triggers on "add our own card designs", "pull our holiday cards into the Greeting Card Studio", "use our own calendars in Calendar Studio", "our own photo book covers", "convert this PSD into a Pixfizz design", "our own business card designs", "we bought these templates", "change the thumbnail of this design", "wrong spiral in the preview", "we cannot print full bleed", or any PSD, AI or print-ready PDF to sell as a personalizable product. Covers the route each studio offers today, designer file prep, building a design import from a real export, studio libraries, and where each thumbnail comes from.
---

# Pixfizz studio designs: bringing a lab's own designs in

A lab buys or commissions designs (holiday cards, birth announcements, business cards, calendars, book covers) and
wants its customers to personalize them on its Pixfizz store: add photos, change the words, order. This skill turns the
designer's file into something the platform and the studios can use, and says plainly where a studio cannot take it
yet.

If the ask is about how a design **looks before the customer picks it** (a gallery thumbnail, a preview image, the
spiral on a calendar, a border because the lab cannot print to the edge), read `references/previews.md` first: most
studio thumbnails are drawn from the design, not from an image you can swap.

Everything here is built from the lab's own files and one export from the lab's own site. Nothing is uploaded by
the scripts. The lab (or you, through the admin) imports and uploads, then checks the result in the design tool and
on the storefront before publishing.

## Step 1. Which product, which route

Ask which product the design is for, then pick the route from this table. Details per studio are in
`references/studios.md`; read the section for the route you pick before building anything.

| Product | Route today | What the customer gets |
|---|---|---|
| Any design product (cards, invitations, announcements, posters, anything with a template) | **Design tool route**: a design on the lab's own template | Opens in the Pixfizz design tool: photos into the windows, words edited in place |
| Greeting Card Studio, the lab's own card designs, with photo windows and words on the front (the usual case) | **Store designs, live front** (where the store's studio file has it, see Rules): the lab's designs on its own 5 x 7 flat two-sided or folded card products, plus a library built from the design exports | In the studio next to the Pixfizz designs: photos and words editable on the front, back and inside, the card's own price, paper and envelopes |
| Greeting Card Studio, a corporate card whose front is one finished picture | **Store designs, fixed front** (studio 0.5.0+) | Fixed front; logo, photo and message on the back and inside |
| Business Cards (3.5.0 and later) | **Site designs file**: one JSON plus images on the lab's assets | In the business card tool before the shared designs: the customer types their details, adds a logo or photo |
| Calendar Studio, the lab's own calendars as they are (own sizes, grids, products) | **Own calendar templates** (studio 0.6.0+, switched on by Pixfizz per store) | The lab's own calendars in the studio: a photo per month, its own prices and choices |
| Calendar Studio, the lab's art on the studio's calendars | **Copy a studio design** on the lab's own calendar template and swap the art | In the studio with the lab's art, month grids and photo layouts kept |
| Photo Book Studio, the lab's own book sizes and cover designs | **Own books** (switched on by Pixfizz per store): designs on the lab's own book templates | The lab's books and covers in the studio, at its own prices |
| Other studios (Collage, Puzzle, Mug, Pet, wall studios) | No own-design intake yet | Say so. Offer the design tool route where the product has a normal template |

If the lab wants a design in every card type (one-sided, two-sided, folded, portrait and landscape), each format
is its own design on its own template, and only a layered file can be reflowed into the others. A flat file stays
in the one format and orientation it was made in.

## Step 2. What kind of file

Ask which they have, and get the file before promising anything.

- **Layered file (PSD; AI or IDML exported to PSD with layers).** The best case. Background art, photo windows and
  live text are separate, so the customer can change every word and the design can be rebuilt in other formats.
- **Finished flat file (PDF, AI saved with PDF content, PNG, JPG).** Every word is part of the picture and stays as
  it is. Photo windows are found from the flat gray "your photo here" areas, or the lab says where they are. Good
  for designs where only the photo changes. For the Greeting Card Studio, designs that are already on the lab's
  site need no file at all: the design export is the source (`references/studios.md`).

What to ask the designer for is in `references/file-prep.md`: the page size with bleed, 300 dpi, RGB, the fonts
as files (and the right to use them on a website), one file per printed page, photo windows named or marked.

## Step 3. Get the seed export

Every build starts from a real export, never from a file typed by hand:

1. In the admin, open the template the design will go on
   (`admin.pixfizz.com/site/<site>/admin/print_theme/product/<template id>`) and export **one design** of that
   template (`.../admin/print_theme/export_print_theme/<design id>`): any design, or for a studio one already
   working in the studio. Unpack it.
2. That export decides the page names and sizes the new design must match. If the lab's file is a different size,
   stop and say so: resize the artwork, or pick the template that matches it. Never stretch.

For Business Cards there is no seed: the card size comes from the product (`bc_trim_w`, `bc_trim_h`, `bc_bleed` on
the business card mount).

## Step 4. Read the file

```
pip install psd-tools pymupdf scipy fonttools pillow pyyaml brotli
python3 scripts/extract.py spec.json out/
```

`spec.json` names the design and one source file per printed page (format in the script header). The script
writes `layout.json` (every measure in mm), the artwork per page with the photo windows cut out, a proof per page
with every window and text line outlined and named, and the fonts the file uses.

Show the lab the proofs. Then fix in the spec and run again until it is right:
- **Element names.** Every text line and photo window gets the name the route needs (`references/studios.md`).
  Lines the script could not name are printed as NAME THESE.
- **Headline lettering** that should stay part of the art goes in `bake` (it is then never editable).
- **Alignment** of each text line: left, center or right, as the designer set it.
- **Photo windows on a flat file** the script did not find: give their boxes in `windows`; `"none"` for a page
  with no photos.

Then set the fonts in `layout.json`: for each font a `file` (TTF or OTF). If the lab does not have the font, pick a
free look-alike (Google Fonts), set `"substitute": true` and the build sizes it to the original line width. Font
names must be 32 characters or fewer, or the import fails.

## Step 5. Build

| Route | Command |
|---|---|
| Design tool | `python3 scripts/build_design.py --seed <export> --layout out/ --out build/ --samples a.jpg,b.jpg` |
| Greeting Card Studio, designs already on the site | no build: export each design, then `scripts/gcs_store_live.py` (see `references/studios.md`) |
| Greeting Card Studio, a new design from a PSD | the design tool build first, import it on the card template, then the same as above |
| Greeting Card Studio, fixed-front corporate card | `--profile gcs-store`, then `scripts/gcs_store_library.py` |
| Business Cards site designs | `python3 scripts/bc_site_designs.py --trim 88.9x50.8 --tag <short site tag> --out build/ out1/ out2/ ...` |

The build stops on anything the platform would refuse or the studio would not read: a page name or size that does
not match the template, a name over 32 characters, a character the font cannot print, an element name the studio
does not know. Fix the cause; never edit the output by hand.

It writes the import file and a preview per page drawn from the same numbers. Show the previews next to the
designer's original before anything is imported.

## Step 6. Install and check

Give the lab numbered steps, one admin screen at a time. The usual set:

1. **Import the design**: on the template's page, **Import Design**, pick `IMPORT-design-<code>.tar.gz`. It always
   creates a new design. Read the design list afterwards: a design with the same name as an existing one arrives
   with `-1` added to its name (the code is unchanged). Imported designs have no preview image until one is set
   (`references/previews.md`). A design imported unpublished and without a SKU is not in the template page's
   design list: open it by its id instead of importing again.
2. **Open it in the design tool** and check every page against the preview: fonts, text position, photo windows,
   nothing cut at the trim. Add a photo to each window. Change each line of text to a long name and a short one.
3. **For a studio**: upload the library files to Assets and add the studio settings (`references/studios.md`).
4. **Publish** the design to its collection, then open it on the storefront as a customer would. Before publishing
   a batch, read what each design really holds (`https://<store>/v1/themes/<design id>.json?sitename=<site>` in a
   signed-in admin tab returns every page's XML): a design with the right name and the wrong pages is easy to miss.
5. **Proof before selling**: order one on a test account, or create a project and generate its production PDF, and
   check the print file (bleed, fonts embedded, photos at full resolution).

Report what was checked and how. Anything not checked on the live store is "not verified yet", never "done".

## Rules

- **Do not turn a lab away because its card has photos or words on the front.** The Greeting Card Studio takes such
  designs as store designs with a live front. As of 25 Nov 2026 that part is in the studio file of the stores Pixfizz
  has set it up on, not yet in the shared studio file every other store runs, and the version number does not tell
  you which (a store on a higher number can be without it). So: build the library, and before mounting it ask
  Pixfizz support to confirm the store's studio has store designs with a live front, or to add it. The library is
  used as built either way.
- **Words that must print are never placeholders.** A text element with `placeholder="true"` does not print, in the
  preview or the production file, unless the tool that fills it clears the flag. Keep the flag for prompt text
  ("enter your text here") only; a greeting that should print untouched ("Merry Christmas") must not carry it. After a
  test order, check an edited line and an untouched line in the production PDF.
- **The template definition and the design pages use the same names.** Every `<page type="X">` in the definition needs
  a design page named X. A mismatch imports without an error and then fails when a customer starts a project.

- Designs the lab supplies stay on the lab's site. Do not add the lab's logo, phone number or names as sample
  words in a design meant for its customers: use generic sample words ("The Smith Family", "Your Company").
- Colors: platform print files are RGB. A CMYK file is converted; soft pinks and greens can shift slightly from the
  designer's CMYK proof. Ask for RGB where the designer can supply it.
- Text boxes get about 5% headroom above and below the letters, so the platform's shrink-to-fit does not trim
  them one size down. Letter spacing (`kerning`) is in points.
- One style per text line: a superscript (the "th" in 10th) becomes plain text.
- A page with no background prints white. A design converted from a flat file always carries its own white base.
- Never change a studio's design codes, the studio settings or the product codes to fit a design. Build the design
  to the studio.
- Pricing, paper and quantity are the product's, not the design's. This skill does not set prices.

## References

- `references/studios.md`: each route in full, element names per studio, page sizes, studio settings
- `references/file-prep.md`: what to ask the designer for, and what each kind of file can become
- `references/previews.md`: where each thumbnail and preview comes from, and how to change it (border instead of
  full bleed, the calendar spiral, preview images)
- Platform detail: the Pixfizz knowledge base (github.com/pixfizz/pixfizz-knowledge), `19_XML_TEMPLATE_REFERENCE.md`
  for page elements, `28_TOOL_SETTINGS_REFERENCE.md` for every studio setting, `26_CUSTOM_DESIGN_TOOLS.md` for the
  studios

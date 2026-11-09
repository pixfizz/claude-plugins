---
name: studio-designs
description: Use when a lab wants to bring its own designs into a Pixfizz studio or design product - greeting cards, holiday cards, birth announcements, business cards, calendars - from a designer's layered file (PSD) or a finished flat file (PDF, AI, PNG, JPG). Triggers on "add our own card designs", "convert this PSD into a Pixfizz design", "put our designs in the Greeting Card Studio", "our own business card designs", "make our calendar designs work in Calendar Studio", "we bought these templates", "turn this PDF into a template", "can customers add their photo to our design", or any PSD, AI or print-ready PDF supplied with a request to sell it as a personalizable product. Covers which route each studio offers today, what to ask the designer for, reading the file into photo windows and live text, building a design import from a real export, the Greeting Card Studio store library and the Business Cards site designs file.
---

# Pixfizz studio designs: bringing a lab's own designs in

A lab buys or commissions designs (holiday cards, birth announcements, business cards, calendars) and wants its
customers to personalize them on its Pixfizz store: add photos, change the words, order. This skill turns the
designer's file into something the platform and the studios can use, and says plainly where a studio cannot take it
yet.

Everything here is built from the lab's own files and one export from the lab's own site. Nothing is uploaded by
the scripts. The lab (or you, through the admin) imports and uploads, then checks the result in the design tool and
on the storefront before publishing.

## Step 1. Which product, which route

Ask which product the design is for, then pick the route from this table. Details per studio are in
`references/studios.md`; read the section for the route you pick before building anything.

| Product | Route today | What the customer gets |
|---|---|---|
| Any design product (cards, invitations, announcements, posters, anything with a template) | **Design tool route**: a design on the lab's own template | Opens in the Pixfizz design tool: photos into the windows, words edited in place |
| Greeting Card Studio, a design whose front is finished art (no photo, no words to change on the front) | **Store designs**: designs on the lab's own 5 x 7 folded or flat two-sided card templates, plus a library file | In the studio next to the Pixfizz designs, fixed front, logo, photo and message on the back and inside |
| Greeting Card Studio, a design with photos or words on the front | Design tool route for now | The studio cannot show these yet; sell the design as its own card product |
| Business Cards (3.5.0 and later) | **Site designs file**: one JSON plus images on the lab's assets | In the business card tool before the shared designs: the customer types their details, adds a logo or photo |
| Calendar Studio | **Copy a studio design** on the lab's own calendar template and swap the art | In the studio with the lab's art, month grids and photo layouts kept |
| Other studios (Photo Book, Collage, Puzzle, Mug, Pet, wall studios) | No own-design intake yet | Say so. Offer the design tool route where the product has a normal template |

If the lab wants a design in every card type (one-sided, two-sided, folded, portrait and landscape), each format
is its own design on its own template, and only a layered file can be reflowed into the others. A flat file stays
in the one format and orientation it was made in.

## Step 2. What kind of file

Ask which they have, and get the file before promising anything.

- **Layered file (PSD; AI or IDML exported to PSD with layers).** The best case. Background art, photo windows and
  live text are separate, so the customer can change every word and the design can be rebuilt in other formats.
- **Finished flat file (PDF, AI saved with PDF content, PNG, JPG).** Every word is part of the picture and stays as
  it is. Photo windows are found from the flat gray "your photo here" areas, or the lab says where they are. Good
  for a studio front (the Greeting Card Studio store front is a fixed picture anyway) and for designs where only
  the photo changes.

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
| Greeting Card Studio store design | the same with `--profile gcs-store`, then `scripts/gcs_store_library.py` (see `references/studios.md`) |
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
   with `-1` added to its name (the code is unchanged). Imported designs have no preview image until one is set.
2. **Open it in the design tool** and check every page against the preview: fonts, text position, photo windows,
   nothing cut at the trim. Add a photo to each window. Change each line of text to a long name and a short one.
3. **For a studio**: upload the library files to Assets and add the studio settings (`references/studios.md`).
4. **Publish** the design to its collection, then open it on the storefront as a customer would.
5. **Proof before selling**: order one on a test account, or create a project and generate its production PDF, and
   check the print file (bleed, fonts embedded, photos at full resolution).

Report what was checked and how. Anything not checked on the live store is "not verified yet", never "done".

## Rules

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
- Platform detail: the Pixfizz knowledge base (github.com/pixfizz/pixfizz-knowledge), `19_XML_TEMPLATE_REFERENCE.md`
  for page elements, `28_TOOL_SETTINGS_REFERENCE.md` for every studio setting, `26_CUSTOM_DESIGN_TOOLS.md` for the
  studios

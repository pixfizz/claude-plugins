# Thumbnails and previews: what the customer sees before choosing

A lab asks to change "the thumbnail" of a design: the spiral is not the one it uses, it cannot print to the edge,
the sample does not look like its product. Before changing anything, find where that picture comes from. A studio
gallery is not a set of uploaded thumbnails: each studio draws its tiles from the design itself. A new image file
changes nothing there, and a changed design changes the tile, the studio view and the print together.

The rule for every surface: the picture shows what the lab will print. Never make a tile look better than the
product (edge to edge for a lab that prints with a border, a spiral the lab does not have).

As of 25 Nov 2026. Studios change often: when a studio's own settings reference (`28_TOOL_SETTINGS_REFERENCE.md`
in the Pixfizz knowledge base) disagrees with this page, the reference is newer.

## Where each picture comes from

| Where the customer sees it | The picture is | How to change it |
|---|---|---|
| Shop and collection pages, landing page cards, the Publish Products design picker | The design's **preview image** (an asset set on the design), or, with none set, a live drawing of the design's own page | Set a new preview image (below) |
| Greeting Card Studio gallery: Pixfizz and MSP designs | Drawn by the studio from the shared design library, with the studio's own sample photos | Not changeable per store today. See "When the picture cannot be changed" |
| Greeting Card Studio gallery: the store's own designs | Drawn from the store library built from the design exports (`studios.md`) | Change the design in the admin, export it again, rebuild and upload the library with a new `LIB_V` and a new `v` in the files index |
| Calendar Studio: gallery and every page | Drawn from the design's own pages. The spiral is a studio setting | Change the design (your own template or copy). Spiral: below |
| Photo Book Studio: standard book covers | Drawn by the studio | Not changeable per store today |
| Photo Book Studio: the store's own books | Drawn from the design's own cover page | Change the cover page of the design |
| Business Cards: the store's own designs | The side images in the site designs file | Rebuild the file (`studios.md`) |
| Cart, saved projects, order pages | Drawn from the customer's own project | Nothing to set |

Studios do not read the design's preview image. Setting one changes the shop pages and the admin picker, never a
studio gallery tile.

## Setting a design's preview image

1. Make the image from the real design, not from a mockup: open
   `https://<store>/v1/themes/<design id>/preview.webp?hide_placeholders=false&height=900` for a plain render of
   the design page, or take the tile as the studio draws it. Generic sample words and photos, no customer's own.
2. Save it as WebP, about 1000 px on the long edge, under 300 KB. Upload it to the site's Assets.
3. On the design page (`admin.pixfizz.com/site/<site>/admin/print_theme/theme/<design id>`), **Choose Asset
   Image**, pick the file, save. One image can serve the same design in every size.
4. Open the shop or collection page as a customer and check the card. An imported design has no preview image
   until this is done.

On a store that takes its designs from the Pixfizz Templates library, the designs belong to the library: their
preview images are the same for every store and are not set per store.

## The common asks

**"We cannot print to the edge."** The thumbnail is not the thing to change: the design is. On the lab's own
template (or its own copy of the design), move the background art and the photo windows inside a white border as
wide as the lab's unprintable margin, on every page. The studio tile, the studio view and the print file then all
show the border. Then make a new preview image from the changed design for the shop pages. For designs the lab
cannot edit (the shared library), see below.

**"Our spiral is different."** Calendar Studio draws the binding itself. The studio page config (`#cs-config`
on the studio's page) takes `"coil":"wireo"` for a silver twin-loop wire hung from a punched hole; without it the
studio draws its standard coil. The wire strip is drawn for the calendar's page width and needs its strip images
on the site: if the calendar shows no binding after the change, ask Pixfizz for the strips for that width. Other
bindings (a colored coil, binding on another edge) are not available yet: say so and pass the request to Pixfizz.
A binding painted into a design's own artwork is changed in the design.

**"The sample photos are not our style."** The sample photos in the studio tiles belong to the studio and are
the same on every store. On the lab's own designs (store designs, own calendars, own book covers) the sample is
the design's own placeholder image: change it in the design.

**"The tile shows a size or format we do not sell."** A tile is there because the design is in the studio's
collection. Take the design out of that collection (its row, not only the Published tick: Calendar Studio 0.6.1
still lists a design whose row is unticked).

## When the picture cannot be changed

For Pixfizz and MSP designs in the Greeting Card Studio and the standard Photo Book Studio covers, a store cannot
change how a tile is drawn. Say so plainly, then offer what works today:
- take the designs that do not fit the lab's printing out of the studio collection;
- bring the lab's own version in by the own-design route for that studio (`studios.md`), where the tile follows
  the design;
- pass the request to Pixfizz support with the store, the studio and one example.

Never work around it with CSS on the tile, an image laid over the gallery, or a changed copy of a studio file.

## Check

After any change, on the live page, desktop and phone: the tile, the opened design, and one proof or production
PDF, all three showing the same edges and binding. The Greeting Card Studio keeps its design list for 15 minutes:
add `?gcs_nocache=1` to the page link to see a change at once. Report each as checked or not verified.

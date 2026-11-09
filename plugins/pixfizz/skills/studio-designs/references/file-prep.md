# Preparing a design file

## What to ask the designer for

Send this list to the lab (or their designer) before converting anything:

1. **The page size of the product, with bleed.** For a 5 x 7 in card: 5.25 x 7.25 in (133.35 x 184.15 mm) per side.
   For a 3.5 x 2 in business card: 3.75 x 2.25 in. Take it from the template, not from memory.
2. **300 dpi** at that size.
3. **RGB.** Platform print files are RGB; a CMYK file is converted and soft colors can shift a little.
4. **One file per printed page** (front, back, inside), or a PDF with one page per printed page.
5. **Fonts as files** (TTF or OTF), with the right to use them for customer personalization on a website. If the
   lab cannot share a font, a free look-alike is used and sized to the original line width.
6. **Photo windows marked**: in a PSD, a smart object or a layer named "photo" or "put image here" clipped to the
   window shape; in a flat file, a flat mid-gray box where each photo goes.
7. **Words the customer changes as live text** (a type layer per block), and headline lettering that stays as part
   of the art named so it is clear (or converted to a shape).
8. **Safe area**: nothing important closer than 1/8 in (3.175 mm) to the trim.

## What each kind of file can become

| File | Photos | Words | Other formats (folded from flat, landscape from portrait) |
|---|---|---|---|
| Layered PSD | Yes, from smart objects or marked layers | Live, one element per line | Possible by rebuilding the layout; flag what cannot reflow |
| AI or IDML | Export to PSD with layers first | Live after export | As PSD |
| Print-ready PDF | Yes, from gray boxes or given boxes | Fixed (part of the art) | No: one format and orientation only |
| PNG or JPG | As PDF | Fixed | No |
| Canva or Figma | Export a PDF per page (flat), or ask the designer for a layered PSD | Fixed unless layered | As the export |

## Things that catch people out

- **Photos in tilted or shaped windows** (a gift box, a polaroid at an angle): the photo is a rectangle placed
  under the artwork; the artwork's cut-out gives the shape. The customer sees the shape, the crop works on the
  rectangle.
- **Overlay designs** (one full-page picture with transparent holes over the photos) cannot be turned into another
  orientation by moving frames: the art has to be recomposed.
- **Script fonts** often have no stored size in a PSD; the build sizes the line from the lettering and says so.
- **Superscripts and mixed styles in one line** become one style per line.
- **Text in all caps by style** (not typed in capitals) comes through as capitals; the customer's own words follow
  what they type.
- **A page with no background prints white**, never transparent.
- **Font names longer than 32 characters fail the import.** Shorten the name in `layout.json`.

---
name: fulfillment-setup
description: How finished orders reach production on Pixfizz - fulfillment destinations (FTP or HTTP), filename and directory templates, output format and color profile, JSON or XML job tickets, sending the customer's original files with _additional_files.json, custom design tool print files, and OrderHub. Use when specifying what a lab or print partner needs to receive, reviewing or writing a fulfillment template, or diagnosing production files that are missing, misnamed, in the wrong folder, duplicated or unreadable. Trigger for 'fulfillment', 'fulfilment', 'FTP', 'job ticket', 'production file', 'print file', 'hot folder', '_additional_files', 'original files', 'filename template', 'order folder', 'OrderHub', 'files not arriving', 'refulfill', or a production system that cannot find or read what Pixfizz sent.
---

# Pixfizz Fulfillment Setup

Where production files go after an order is placed, what they are called, and what travels with
them. Platform-level throughout unless marked otherwise.

Authoritative source: `31_FULFILLMENT_ENGINE.md` and `32_ORDER_LIFECYCLE.md` in the Pixfizz
knowledge base (github.com/pixfizz/pixfizz-knowledge). For the production specification of the
file itself (size, bleed, layers, which sets render), use `xml-templates`.

## Who does what

- **Fulfillment destinations and their templates are configured by Pixfizz** in the platform's
  Super Admin. A store owner cannot edit them from Main Admin.
- **The store or lab owns the specification**: where files must land, what they must be called,
  what the production system reads. This skill helps write that specification precisely and
  check the result.
- **Each orderline carries a fulfillment code** that decides which destination receives it.
  One site can route different products to different destinations.

So the useful output of this skill is usually one of: a spec to send to Pixfizz, a template
reviewed line by line, or a diagnosis of a delivered order.

## The chain

1. Order confirmed and paid.
2. Artwork generated for each orderline from its template definition.
3. Files, plus any job ticket and additional files, delivered to the destination (FTP or HTTP).
4. The production system picks them up: OrderHub Desktop, a press hot folder, or the lab's
   own software. OrderHub Desktop polls, downloads, and reports status back
   (Downloaded -> Manufactured), which moves the order on.

A failure at any step looks the same from the shop floor: "the files never came". Work down the
chain in order (see Diagnosis).

## What to specify before setup

Have every one of these answered in writing before a destination is built. Most delays in
production setup are one of these being guessed.

- [ ] Delivery: FTP (host, user, folder) or HTTP (endpoint URL, content type, parameters, auth)
- [ ] File format per product: PDF, JPEG or PNG
- [ ] Color profile: sRGB or AdobeRGB
- [ ] One file per order line, or one file per page (single page output)
- [ ] Photo prints: one file per copy, or one file with a quantity (multiple cut print copies)
- [ ] Folder structure and file naming the production system expects, with a real example
- [ ] Whether a job ticket is needed, in what format (JSON or XML), with a sample the system accepts
- [ ] Whether the customer's original uploaded files must be sent as well
- [ ] Bleed, trim and size per product (this belongs in the XML template, not here)

## Destination settings

| Setting | Notes |
|---|---|
| Type | FTP or HTTP |
| FTP host, user, password, directory | Directory is the root under which order folders are created |
| WebService URL, content type, parameter name, fixed parameters | HTTP delivery only |
| Format | pdf, jpeg, png |
| Filename template | Liquid. Names each production file, and may include a folder path |
| Directory template | Liquid. Names the per-order folder |
| Single page output | One file per page instead of one per line |
| Multiple cut print copies | Separate copies for cut-print workflows |
| Color profile | sRGB or AdobeRGB |

Staff-only settings also exist (FTP TLS flags, delivery callback, image enhancement, split by
orderline). Ask Pixfizz if a production system needs one of them.

## Filename and directory templates

Variables seen in working templates: `order.code`, `order.id`, `orderline.id`,
`orderline.product.code`, `orderline.barcode`, `print_quantity`, `page_output_name`,
`layer_output_name`, `format`.

A clean reference pattern, one folder per order line with quantity and page in the name:

```liquid
{{ order.code }}_{{ orderline.id }}/{{ order.code }}_{{ orderline.id }}_Q{{ print_quantity }}_{{ page_output_name }}{% if layer_output_name %}_{{ layer_output_name }}{% endif %}.{{ format }}
```

with a directory template of `{{ order.code }}_{{ order.id }}`.

Rules:

- **`layer_output_name` only exists for separate-layer output.** Guard it with `if`, as above,
  or ordinary files get a trailing underscore.
- **A leading slash changes the meaning.** `originals/` is a subfolder inside the order folder.
  `/originals/` is a folder at the FTP root, outside every order. Both are valid, neither errors.
- **Change every template that writes to the same structure together.** Updating the filename
  template but not `_additional_files.json` puts production files in one place and originals
  in another.
- **Keep folder names identical across every site on the same FTP.** `Job Tickets` on one site
  and `job-tickets` on another fails silently. Where job tickets route through a `Job Tickets`
  folder, use exactly that capitalization.

## Fulfillment templates

Extra files written alongside the production files. Each template has a file name, an
extension, a body (Liquid), "Description in Dir" (write it inside the order folder) and "Skip
if empty". A blank file name has been seen listed as `%order_code%`, meaning the file is named
after the order code (read from the admin list, not verified from a delivered file).

**Every custom value inside a JSON string must go through `| escape_json`.** A customer note
containing a quote, backslash or line break otherwise produces invalid JSON, and the job ticket
fails, sometimes silently. Never assume a value is safe.

**Comma guard.** JSON arrays built in loops need a flag so the first item has no leading comma:

```liquid
{%- assign first = true -%}
{%- for line in order.orderlines -%}
	{%- unless first -%},{%- endunless -%}
	{ "jobId": "{{ line.id }}" }
	{%- assign first = false -%}
{%- endfor -%}
```

### A JSON job ticket (OrderHub shape)

```liquid
{
	"orderId": "{{ order.id }}",
	"orderNumber": "{{ order.code }}",
	"jobs": [
	{%- for line in order.orderlines %}
		{
			"jobId": "{{ line.id }}",
			"images": [
			{%- assign first = true -%}
			{%- for file in line.generated_files %}
				{%- unless first %},{% endunless %}
				{
					"filename": "{{ file.filename }}",
					"size": "{% if line.product.custom.lab_size != blank %}{{ line.product.custom.lab_size }}{% else %}None{% endif %}",
					"quantity": {% unless line.is_cut_print %}{{ line.quantity }}{% else %}{{ file.quantity }}{% endunless %}
				}
				{%- assign first = false -%}
			{%- endfor %}
			]
		}{% unless forloop.last %},{% endunless %}
	{%- endfor %}
	]
}
```

- `line.generated_files` is what the platform rendered. It is **empty** for a product whose
  template sets carry `fulfillment="false"` (every custom design tool product), so those files
  must be declared another way (below).
- Photo prints: quantity comes from the file (`file.quantity`) because each image has its own
  count. Everything else uses the line quantity.
- `lab_size` is a product custom field used here to pass the production system's own size code.
  Custom fields are created per site, so it has to exist on the site before it can hold a value.

### Sending the customer's original files: `_additional_files.json`

**Original uploads are not sent by default.** Only rendered production files are. A template
named exactly `_additional_files.json` (file name `_additional_files`, extension `json`, leading
underscore included) tells the platform to copy more files. Its body must render a **JSON array
of `source` / `destination` pairs**; destination paths are relative to the destination folder:

```json
[
	{ "source": "https://...", "destination": "ORDER_LINE/original-files/1-photo.jpg" }
]
```

A working body covers four kinds of file per order line:

```liquid
[
{%- assign af_first = true -%}
{%- for line in orderlines -%}

	{%- comment %} 1. The customer's photos in the project {%- endcomment -%}
	{%- for image in line.project.images -%}
		{%- unless af_first -%},{%- endunless -%}
		{ "source": "{{ image.url | escape_json }}",
		  "destination": "{{ order.code }}_{{ line.id }}/original-files/{{ forloop.index }}-{{ image.filename | escape_json }}" }
		{%- assign af_first = false -%}
	{%- endfor -%}

	{%- comment %} 2. Print files written by a custom design tool: any upload option whose code contains _print_ {%- endcomment -%}
	{%- for opt in line.chosen_template_options -%}
		{%- if opt.template_option.type == "file_upload" and opt.template_option.code contains '_print_' and opt.uploaded_file.url != blank -%}
			{%- unless af_first -%},{%- endunless -%}
			{ "source": "{{ opt.uploaded_file.url | escape_json }}",
			  "destination": "{{ order.code }}/{{ line.product.code | escape_json }}.{{ order.code }}.Q{{ line.quantity }}.{{ line.barcode }}_design.pdf" }
			{%- assign af_first = false -%}
		{%- endif -%}
	{%- endfor -%}

	{%- comment %} 3. Other uploads on template options. Codes containing preview are cart thumbnails and never go to production {%- endcomment -%}
	{%- for opt in line.chosen_template_options -%}
		{%- if opt.template_option.type == "file_upload" and opt.uploaded_file.url != blank -%}
			{%- unless opt.template_option.code contains '_print_' or opt.template_option.code contains 'preview' -%}
				{%- unless af_first -%},{%- endunless -%}
				{ "source": "{{ opt.uploaded_file.url | escape_json }}",
				  "destination": "{{ order.code }}_{{ line.id }}/original-files/{{ opt.template_option.code }}-{{ opt.uploaded_file.filename | escape_json }}" }
				{%- assign af_first = false -%}
			{%- endunless -%}
		{%- endif -%}
	{%- endfor -%}

	{%- comment %} 4. Uploads on variants, same rule {%- endcomment -%}
	{%- for v in line.chosen_variants -%}
		{%- if v.variant.type == "file_upload" and v.uploaded_file.url != blank -%}
			{%- unless v.variant.code contains '_print_' or v.variant.code contains 'preview' -%}
				{%- unless af_first -%},{%- endunless -%}
				{ "source": "{{ v.uploaded_file.url | escape_json }}",
				  "destination": "{{ order.code }}_{{ line.id }}/original-files/{{ v.variant.code }}-{{ v.uploaded_file.filename | escape_json }}" }
				{%- assign af_first = false -%}
			{%- endunless -%}
		{%- endif -%}
	{%- endfor -%}

{%- endfor -%}
]
```

Why it is shaped this way:

- **Key on a code token, never on a list of codes.** Every custom tool names its print-file
  option with `_print_` in the code, so a new tool needs no template edit. A hard-coded list
  goes stale the day the next tool ships.
- **Exclude previews.** A tool that stores a cart thumbnail in an upload option will otherwise
  send that thumbnail to production next to the real artwork.
- **Bucket 2 does nothing until the option exists on the template.** A site where the tool's
  print option was never created sends nothing for that product, with no error. This is the
  usual reason the setup looks finished and is not.
- **The print-file path must match the job ticket exactly.** If the job ticket also lists custom
  tool print files, build the filename with the same expression in both templates.

**Not verified - test before relying on it:** a job ticket that also lists an
`originalFilename` for rendered files has to reproduce the numbering and names used in bucket 1.
The two loops run over different collections (`generated_files` and `project.images`), so the
paths only agree if both come out in the same order with the same names. Place one order with
several images and compare the ticket against the folder.

## Custom design tool products

A custom tool builds its own print file in the browser and uploads it into a template option.
The template's sets all carry `fulfillment="false"`, so **the platform renders nothing** for that
line. Everything production receives for it travels through `_additional_files.json` (and the
job ticket, if the production system needs it listed). No template, no file, and no error.

## Operational rules

- **Files on the Pixfizz FTP drop are deleted automatically after about a week.** The production
  system must collect them promptly; this is not an archive.
- **Force-refulfill** is available on the order in admin and re-sends an order's files. Use it
  after a destination or template fix, rather than asking the customer to reorder.
- **Cancelling an order in admin does not by itself stop transaction fees.** Send the order codes
  to your Pixfizz contact as well.

## Diagnosis: files missing, misnamed or unreadable

Work in this order and stop at the first failure.

1. **Did the order reach a fulfilled state?** Check the order status and history in admin.
   Unpaid or errored orders do not deliver.
2. **Were files generated?** Order line -> Generated Files. None on a design product means an
   artwork problem (see `xml-templates`). None on a custom tool product is normal: go to step 4.
3. **Is the fulfillment code the one you expect?** A line routed to a different destination
   delivers correctly to the wrong place.
4. **Custom tool line: is there an uploaded print file** on the `_print_` option of that line?
   No file means the tool did not upload, not a fulfillment fault.
5. **Did the templates render valid JSON?** A quote or line break in a customer note without
   `escape_json` breaks the whole ticket. Look for the unescaped value.
6. **Is the file in the folder you are looking in?** Check for a leading-slash path, a
   mismatched `Job Tickets` folder name, or a filename template changed without the matching
   `_additional_files.json` change.
7. **Did the production system collect it in time?** Files older than about a week are gone
   from the drop.
8. **Unreadable file?** Format and color profile against the spec, then size and bleed in the
   XML template.

Report each step as checked or not checked. Anything that needs a Super Admin view (template
bodies, destination settings) goes to Pixfizz with the order code and order line id.

## Before calling a destination ready

- [ ] Spec answered in writing (list above)
- [ ] One real test order per product type, including one custom tool product if the site has one
- [ ] Delivered folder compared file by file against the spec, not just "files arrived"
- [ ] Job ticket opened and parsed by the production system, not just by eye
- [ ] A test order with a quote and a line break in the customer note
- [ ] Original files present, cart thumbnails absent

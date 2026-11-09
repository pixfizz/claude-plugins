#!/usr/bin/env python3
"""Pixfizz studio-designs: step 1, read a lab's design file into a layout you can check before anything is built.

  python3 extract.py <spec.json> <out dir>

The spec names the design and one source file per printed page:
  {"code": "lab-xmas-gift-flat2-p", "name": "Gift Box",
   "pages": [{"name": "front", "file": "Christmas Card.psd", "mode": "layered"},
             {"name": "back",  "file": "Christmas Card back.pdf", "mode": "flat"}],
   "dpi": 300,                       optional, the source resolution (PSD: read from the file)
   "bake": ["Merry"],                optional, type layers that stay part of the artwork (headline lettering)
   "roles": {"The Smith Family": "signature", "Some layer#2": "line2"},   optional, element name per type layer (or layer#line)
   "align": {"The Smith Family": "center"},                               optional, left / center / right
   "windows": {"back": [[x0, y0, x1, y1], ...]},                          optional, photo windows in source px (flat files);
                                                                          "none" for a page with no photo windows
   "pdf_page": {"back": 0}}                                               optional, which PDF page

Two kinds of file:
  layered (PSD): smart objects and layers named like "put image here", "photo", "double click", "clipping mask" become
    photo windows; type layers become live text, one element per line; every other visible layer is artwork. Artwork
    drawn above a window in the file (a ribbon over a photo) stays above the photo.
  flat (PDF, AI saved with PDF content, PNG, JPG): the whole page is fixed artwork, words included. Photo windows come
    from "windows", or are found as flat neutral-gray placeholder areas.

Writes into <out dir>: layout.json (every measure in mm, page size including bleed), <page>-art.png (the artwork with the
photo windows cut out), <page>-proof.png (windows and text boxes outlined and named), fonts.txt (fonts the file uses).
Nothing is uploaded. Check the proof and fonts.txt, fix the spec, run again, then run build_design.py.
"""
import io, json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WINDOW_RE = re.compile(r'(put|place|insert|add|drop).*(image|photo|picture)|double click|^photo|^image ?\d*$|clipping mask', re.I)
# ---------------------------------------------------------------- PSD
def leaf_layers(psd):
    out = []
    def walk(group, hidden):
        for l in group:
            vis = l.visible and not hidden
            if l.is_group():
                skip = bool(re.search(r'crop ?marks?|guides?', l.name, re.I))
                walk(l, hidden or not l.visible or skip)
            else:
                out.append((l, vis))
    walk(psd, False)
    return out

def classify(psd, bake):
    leaves = leaf_layers(psd)
    W, H = psd.width, psd.height
    order = {id(l): i for i, (l, _) in enumerate(leaves)}
    windows, texts, art, clipped_to_window = [], [], [], set()
    for i, (l, vis) in enumerate(leaves):
        if not vis:
            continue
        x0, y0, x1, y1 = l.bbox
        if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H:
            continue  # crop marks and other off-canvas furniture
        if l.kind == 'type' and l.name not in bake and not any(l.name.startswith(b) for b in bake):
            texts.append(l); continue
        clip = getattr(l, 'clipping', False)
        if clip and windows and id(windows[-1]) == id(leaves[i - 1][0]) or (clip and i and id(leaves[i - 1][0]) in clipped_to_window):
            clipped_to_window.add(id(l)); continue  # "put image here" clipped onto its window base
        if l.kind == 'smartobject' or (l.kind in ('shape', 'pixel') and WINDOW_RE.search(l.name)):
            windows.append(l); clipped_to_window.add(id(l)); continue
        art.append(l)
    return leaves, order, windows, texts, art

def layer_alpha(l, W, H):
    """the layer's own coverage on the canvas (0..1 float)"""
    im = l.composite()
    a = np.zeros((H, W), np.float32)
    if im is None:
        return a
    im = im.convert('RGBA'); x0, y0 = l.bbox[0], l.bbox[1]
    la = np.asarray(im)[..., 3].astype(np.float32) / 255
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    w = min(la.shape[1] - sx0, W - dx0); h = min(la.shape[0] - sy0, H - dy0)
    if w > 0 and h > 0:
        a[dy0:dy0 + h, dx0:dx0 + w] = la[sy0:sy0 + h, sx0:sx0 + w]
    return a

def composite(psd, keep):
    ids = {id(l) for l in keep}
    def f(l):
        return l.is_group() or id(l) in ids
    im = psd.composite(layer_filter=f, force=True)
    return im.convert('RGBA').resize((psd.width, psd.height)) if im.size != (psd.width, psd.height) else im.convert('RGBA')

def ink_color(l, band=None):
    im = np.asarray(l.composite().convert('RGBA'))
    if band:
        im = im[band[0] - l.bbox[1]:band[1] - l.bbox[1]]
    im = im.reshape(-1, 4)
    im = im[im[:, 3] > 230]
    if not len(im):
        return '#000000'
    r, g, b = np.median(im[:, :3], axis=0).astype(int)
    return '#%02X%02X%02X' % (r, g, b)

def line_bands(l, nlines):
    """y ranges (canvas px) of each text line, from the layer's ink"""
    a = np.asarray(l.composite().convert('RGBA'))[..., 3] > 40
    rows = a.any(axis=1); bands, y = [], 0
    while y < len(rows):
        if rows[y]:
            s = y
            while y < len(rows) and rows[y]:
                y += 1
            bands.append([s, y])
        y += 1
    # merge small fragments (superscripts, descenders) into their neighbour until there are nlines bands
    while len(bands) > nlines:
        gaps = [bands[i + 1][0] - bands[i][1] for i in range(len(bands) - 1)]
        i = int(np.argmin(gaps)); bands[i] = [bands[i][0], bands[i + 1][1]]; del bands[i + 1]
    oy = l.bbox[1]
    return [(b[0] + oy, b[1] + oy) for b in bands]

def line_extent(l, band):
    a = np.asarray(l.composite().convert('RGBA'))[..., 3] > 40
    oy, ox = l.bbox[1], l.bbox[0]
    cols = a[band[0] - oy:band[1] - oy].any(axis=0)
    xs = np.where(cols)[0]
    return ox + xs[0], ox + xs[-1] + 1

def text_lines(l):
    ed = l.engine_dict; fs = [pstr(f['Name']) for f in l.resource_dict['FontSet']]
    txt = l.text.replace('\n', '\r')
    runs = ed['StyleRun']['RunArray']; lens = ed['StyleRun']['RunLengthArray']
    styles, pos = [], 0
    for r, k in zip(runs, lens):
        s = r['StyleSheet']['StyleSheetData']
        styles.append((pos, pos + k, s)); pos += k
    scale = l.transform[3] if l.transform else 1.0
    out, start = [], 0
    for line in txt.split('\r'):
        # the style of the line = the style covering most of its characters (superscript runs ignored)
        best = None
        for a, b, s in styles:
            ov = min(b, start + len(line)) - max(a, start)
            if ov > 0 and s.get('FontBaseline') is None and (best is None or ov > best[0]):
                best = (ov, s)
        s = best[1] if best else styles[0][2]
        caps = s.get('FontCaps') == 2
        fsz = s.get('FontSize')
        out.append(dict(text=re.sub(r' {2,}', ' ', line.upper() if caps else line), font=fs[s.get('Font', 0)], size_px=float(fsz) * scale if fsz else None,
                        tracking=float(s.get('Tracking', 0))))
        start += len(line) + 1
    return [x for x in out if x['text'].strip()]


def gray_mask(im):
    a = np.asarray(im).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    neutral = (abs(r - g) < 10) & (abs(g - b) < 12) & (r > 140) & (r < 200)
    return (neutral * 255).astype(np.uint8)

def detect_gray_windows(im, min_px=150):
    """flat neutral-gray placeholder areas (the usual 'your photo here' fill) -> boxes"""
    from scipy import ndimage
    g = gray_mask(im) > 0
    g = ndimage.binary_closing(g, iterations=6)
    g = ndimage.binary_fill_holes(g)
    lab, k = ndimage.label(g); boxes = []
    for sl in ndimage.find_objects(lab):
        y, x = sl
        if x.stop - x.start >= min_px and y.stop - y.start >= min_px:
            boxes.append((x.start, y.start, x.stop, y.stop))
    return boxes

# ---------------------------------------------------------------- shared
def reading_order(boxes):
    rowh = max(1, min(b[3] - b[1] for b in boxes) // 2) if boxes else 1
    return sorted(boxes, key=lambda b: ((b[1] + b[3]) // 2 // rowh, b[0]))


# ---------------------------------------------------------------- pages
def psd_page(path, page, spec):
    from psd_tools import PSDImage
    psd = PSDImage.open(path); W, H = psd.width, psd.height
    dpi = float(spec.get('dpi') or 0) or psd_dpi(psd)
    cm = int(getattr(psd.color_mode, 'value', psd.color_mode))
    if cm != 3:
        NOTES.append('%s: the file is %s, converted to RGB (platform PDFs are RGB; colors can shift slightly from the lab proof)'
                     % (page, {4: 'CMYK', 1: 'grayscale'}.get(cm, 'color mode %d' % cm)))
    bake = spec.get('bake', [])
    leaves, order, windows, texts, art = classify(psd, bake)
    first_win = min((order[id(w)] for w in windows), default=10 ** 9)
    below = [l for l in art if order[id(l)] < first_win]
    above = [l for l in art if order[id(l)] > first_win]
    base = composite(psd, below) if below else Image.new('RGBA', (W, H), (255, 255, 255, 255))
    hole = np.zeros((H, W), np.float32); boxes = []
    for w in windows:
        a = layer_alpha(w, W, H); hole = np.maximum(hole, a)
        ys, xs = np.where(a > 0.5)
        if len(xs): boxes.append((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    m = Image.fromarray((hole > 0.5).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))
    b = np.asarray(base).copy(); b[..., 3] = np.where(np.asarray(m) > 0, 0, b[..., 3]); top = Image.fromarray(b)
    if above:
        top = Image.alpha_composite(top, composite(psd, above))
    words = []
    roles, align_map = spec.get('roles', {}), spec.get('align', {})
    for l in texts:
        lines = text_lines(l)
        bands = line_bands(l, len(lines))
        for j, (ln, band) in enumerate(zip(lines, bands)):
            key = '%s#%d' % (l.name, j + 1)
            role = roles.get(key) or roles.get(l.name) or 'text-%d' % (len(words) + 1)
            x0, x1 = line_extent(l, band)
            if not ln['size_px']:
                ln['size_px'] = (band[1] - band[0]) * 1.05
                NOTES.append('%s: "%s" has no stored font size, sized from the lettering' % (page, ln['text']))
            words.append(dict(name=role, key=key, text=pstr(ln['text']), font=pstr(ln['font']), size_px=ln['size_px'], tracking=ln['tracking'],
                              color=ink_color(l, band), align=align_map.get(key) or align_map.get(l.name) or 'left',
                              ink=[int(x0), int(band[0]), int(x1), int(band[1])]))
    return W, H, dpi, top, boxes, words

def psd_dpi(psd):
    try:
        r = psd.image_resources.get_data(1005)
        return float(r.horizontal_res) if r else 300.0
    except Exception:
        return 300.0

def flat_page(path, page, spec):
    dpi = float(spec.get('dpi') or 300)
    if path.lower().endswith(('.pdf', '.ai')):
        import pymupdf as fitz
        d = fitz.open(path); pg = d[(spec.get('pdf_page') or {}).get(page, 0)]
        pix = pg.get_pixmap(dpi=int(round(dpi)), alpha=False); im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    else:
        im = Image.open(path)
        if im.info.get('dpi') and not spec.get('dpi'):
            dpi = float(im.info['dpi'][0])
        im = im.convert('RGB')
    W, H = im.size
    wins = (spec.get('windows') or {}).get(page)
    boxes = [] if wins == 'none' else ([tuple(b) for b in wins] if wins else detect_gray_windows(im))
    a = np.zeros((H, W), np.uint8)
    from scipy import ndimage
    g = ndimage.binary_fill_holes(ndimage.binary_closing(gray_mask(im) > 0, iterations=6))
    for x0, y0, x1, y1 in boxes:
        a[y0:y1, x0:x1] = 255
    if not wins:
        a = np.where(a > 0, g * 255, 0).astype(np.uint8)   # found windows: cut the gray shape, not its bounding box
    m = Image.fromarray(a).filter(ImageFilter.MaxFilter(7))
    t = np.asarray(im.convert('RGBA')).copy(); t[..., 3] = np.where(np.asarray(m) > 0, 0, 255)
    return W, H, dpi, Image.fromarray(t), boxes, []

def pstr(v):
    v = getattr(v, 'value', v)
    return str(v).strip("'") if not isinstance(v, str) else v

def r4(v):
    return round(float(v), 4)

NOTES = []
def main():
    spec_path, out = sys.argv[1], sys.argv[2]
    spec = json.load(open(spec_path, encoding='utf8'))
    base = os.path.dirname(os.path.abspath(spec_path))
    os.makedirs(out, exist_ok=True)
    layout = dict(code=spec['code'], name=spec['name'], description=spec.get('description', ''), pages=[], fonts={})
    fonts_seen = {}
    for pg in spec['pages']:
        path = pg['file'] if os.path.isabs(pg['file']) else os.path.join(base, pg['file'])
        mode = pg.get('mode') or ('layered' if path.lower().endswith('.psd') else 'flat')
        W, H, dpi, top, boxes, words = (psd_page if mode == 'layered' else flat_page)(path, pg['name'], spec)
        mm = 25.4 / dpi
        art_name = '%s-art.png' % pg['name']
        top.save(os.path.join(out, art_name), 'PNG', optimize=True)
        photos = [dict(name='photo-%d' % (i + 1), x=r4(x0 * mm), y=r4(y0 * mm), w=r4((x1 - x0) * mm), h=r4((y1 - y0) * mm))
                  for i, (x0, y0, x1, y1) in enumerate(reading_order(boxes))]
        texts = []
        for w in words:
            x0, y0, x1, y1 = w['ink']; size_mm = w['size_px'] * mm
            fonts_seen.setdefault(w['font'], []).append(w['text'])
            texts.append(dict(name=w['name'], source=w['key'], text=w['text'], font=w['font'], size=r4(size_mm), color=w['color'],
                              align=w['align'], kerning_pt=r4(w['tracking'] / 1000.0 * size_mm * 2.8346),
                              ink=dict(x=r4(x0 * mm), y=r4(y0 * mm), w=r4((x1 - x0) * mm), h=r4((y1 - y0) * mm))))
        layout['pages'].append(dict(name=pg['name'], mode=mode, w=r4(W * mm), h=r4(H * mm), dpi=dpi, art=art_name, photos=photos, texts=texts))
        # proof
        pr = Image.new('RGBA', (W, H), 'white'); pr = Image.alpha_composite(pr, top).convert('RGB'); d = ImageDraw.Draw(pr)
        lw = max(2, W // 400)
        for p in photos:
            b = [p['x'] / mm, p['y'] / mm, (p['x'] + p['w']) / mm, (p['y'] + p['h']) / mm]
            d.rectangle(b, outline=(0, 120, 255), width=lw); d.text((b[0] + 8, b[1] + 8), p['name'], fill=(0, 120, 255))
        for t in texts:
            i = t['ink']; b = [i['x'] / mm, i['y'] / mm, (i['x'] + i['w']) / mm, (i['y'] + i['h']) / mm]
            d.rectangle(b, outline=(230, 0, 120), width=lw); d.text((b[0], b[3] + 4), t['name'], fill=(230, 0, 120))
        pr.thumbnail((1600, 1600)); pr.save(os.path.join(out, '%s-proof.png' % pg['name']))
    for f, samples in fonts_seen.items():
        layout['fonts'][f] = dict(file=None, google=None, substitute=False, used_in=samples[:3])
    json.dump(layout, open(os.path.join(out, 'layout.json'), 'w'), indent=1, ensure_ascii=False)
    with open(os.path.join(out, 'fonts.txt'), 'w') as fh:
        for f, samples in fonts_seen.items():
            fh.write('%s\t%s\n' % (f, ' | '.join(samples[:3])))
    for p in layout['pages']:
        print('%s: %s, %.2f x %.2f mm at %g dpi, %d photo windows, %d text lines' % (p['name'], p['mode'], p['w'], p['h'], p['dpi'], len(p['photos']), len(p['texts'])))
    unnamed = [t['source'] for p in layout['pages'] for t in p['texts'] if t['name'].startswith('text-')]
    if unnamed: print('NAME THESE (spec "roles"):', '; '.join(unnamed))
    if fonts_seen: print('fonts used:', ', '.join(fonts_seen), '(set file or google for each in layout.json, see SKILL.md)')
    for n_ in NOTES: print('NOTE', n_)

if __name__ == '__main__':
    main()

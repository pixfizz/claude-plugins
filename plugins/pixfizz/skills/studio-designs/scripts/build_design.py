#!/usr/bin/env python3
"""Pixfizz studio-designs: step 2, build a design import file from a checked layout, on top of a real design export.

  python3 build_design.py --seed <design export dir> --layout <layout.json dir or file> --out <dir>
                          [--profile design-tool|gcs-store] [--samples a.jpg,b.jpg] [--keep-layouts]

--seed    an unpacked design export from the template the new design goes on (admin: the template's design list,
          Export on any design of that template). Its page names, page sizes, preview pages and file layout are kept;
          nothing is typed from scratch. Pages made only of page references (a folded card's outside, a "finished" mockup)
          are copied from the seed as they are.
--layout  the layout.json from extract.py, after you checked it: element names set, a font file for every font.
--profile design-tool (default): artwork_base (white, locked), photo windows as photo placeholders, artwork_top (the art
          with the windows cut out, locked), live text. Opens in the design tool.
          gcs-store: Greeting Card Studio store design. The front is one fixed picture named cover (no photos or words on it:
          bake the front type layers in extract.py); back and inside are white and carry only the studio's element names.
--samples sample photos for the photo windows (shown until the shopper adds their own). Without them the windows stay empty.

Writes <out>/IMPORT-design-<code>.tar.gz and <out>/<code>-preview-<page>.png (drawn from the same data as the tar).
Checks before writing: page names and sizes match the seed, every name 32 characters or fewer, every text glyph in its font,
element names allowed by the profile. A failed check stops the build and says what to fix.
"""
import argparse, io, json, os, re, sys, tarfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

PROFILES = {
    'gcs-store': {
        'front': {'images': {'cover'}, 'texts': set()},
        'back': {'images': {'back-image', 'logo'}, 'texts': {'back-message', 'sentiment', 'signature'}},
        'inside': {'images': {'logo', 'photo'}, 'texts': {'sentiment', 'signature'}},
    },
}
NEW_IMG, NEW_FONT = 1190000000, 1190900000

def n(v):
    return ('%.4f' % float(v)).rstrip('0').rstrip('.')

def die(msg):
    sys.exit('STOP: ' + msg)

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

# ---------------------------------------------------------------- seed (text surgery, never re-serialized)
TOP = re.compile(r'^([a-z_]+):', re.M)

def split_top(text):
    """top-level key -> raw chunk (key line included), in file order"""
    marks = [(m.start(), m.group(1)) for m in TOP.finditer(text)]
    out = []
    for i, (pos, key) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append((key, text[pos:end]))
    return out

def entries(chunk):
    """a list chunk ('templates:\\n- id: ...') -> raw entries"""
    body = chunk.split('\n', 1)[1] if '\n' in chunk else ''
    parts = re.split(r'(?m)^(?=- )', body)
    return [p for p in parts if p.startswith('- ')]

def entry_field(e, key):
    m = re.search(r'(?m)^  %s: ?(.*)$' % re.escape(key), e)
    return m.group(1).strip() if m else None

def entry_data(e):
    """the page XML of a template entry (block scalar or quoted scalar)"""
    m = re.search(r'(?ms)^  data: (\|-?|>-?)\n(.*?)(?=^  [a-z_]+:)', e)
    if m:
        lines = m.group(2).split('\n')
        ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
        return '\n'.join(l[ind:] for l in lines).strip()
    m = re.search(r'(?ms)^  data: (".*?")\n(?=  [a-z_]+:)', e)
    if m:
        return json.loads(m.group(1).replace('\\\n', '').replace('\n  ', ' '))
    die('could not read a page of the seed export')

def load_seed(path):
    p = os.path.join(path, '__print_theme.yml')
    if not os.path.exists(p):
        die('%s has no __print_theme.yml: export a DESIGN (not the template) from the target template and unpack it' % path)
    text = open(p, encoding='utf8').read()
    parts = split_top(text.lstrip('-\n'))
    seed = dict(path=path, parts=parts, pages=[])
    for key, chunk in parts:
        if key == 'templates':
            for e in entries(chunk):
                data = entry_data(e)
                root = ET.fromstring(data.encode('utf8') if data.startswith('<?xml') else data)
                kids = [c for c in root]
                composed = all(c.tag == 'ipage' or c.get('pdf_layer') == 'production' for c in kids) and kids
                seed['pages'].append(dict(name=entry_field(e, 'name'), raw=e, data=data, root=root,
                                          w=float(root.get('width')), h=float(root.get('height')),
                                          preview=entry_field(e, 'preview') == 'true', composed=bool(composed)))
    for key, chunk in parts:
        if key == '__image_map':
            seed['image_names'] = dict(re.findall(r"(?m)^  '(\d+)':\n    :original_filename: (.*)$", chunk))
        if key == '__font_map':
            seed['font_names'] = dict(re.findall(r"(?m)^  '(\d+)':\n    :name: (.*)$", chunk))
    seed.setdefault('image_names', {}); seed.setdefault('font_names', {})
    return seed

def refs(xml):
    return set(re.findall(r'src="db:(\d+)"', xml)), set(re.findall(r'font="(\d+)"', xml))

# ---------------------------------------------------------------- build
def text_box(t, page_w, font, scale, safe):
    """element box from the ink box: 1.3 x font size tall around the ink centre (5% headroom for shrink), wider than the ink"""
    ink = t['ink']; fs = t['size'] * scale
    if font.get('substitute'):
        # a look-alike font: size it so the line runs the same width as the original lettering
        ft = ImageFont.truetype(font['file'], 200)
        k = t.get('kerning_pt', 0) / 2.8346 / max(t['size'], 0.01) * 200
        tw = sum(ft.getlength(c) + k for c in t['text']) - k
        if tw > 0:
            fs = min(ink['w'] / tw * 200, t['size'] * 1.6)
    h = fs * 1.3
    cy = ink['y'] + ink['h'] / 2
    w = ink['w'] * 1.35
    if t['align'] == 'center':
        x = ink['x'] + ink['w'] / 2 - w / 2
    elif t['align'] == 'right':
        x = ink['x'] + ink['w'] - w
    else:
        x = ink['x']
    x = max(safe, x); w = min(w, page_w - safe - x)
    return fs, x, cy - h / 2, w, h

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', required=True); ap.add_argument('--layout', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--profile', default='design-tool'); ap.add_argument('--samples', default='')
    ap.add_argument('--keep-layouts', action='store_true'); ap.add_argument('--safe', type=float, default=6.35,
                    help='distance from the page edge text boxes must keep, mm (bleed + safe margin; default 1/8 + 1/8 in)')
    a = ap.parse_args()
    lp = a.layout if a.layout.endswith('.json') else os.path.join(a.layout, 'layout.json')
    L = json.load(open(lp, encoding='utf8')); ldir = os.path.dirname(os.path.abspath(lp))
    seed = load_seed(a.seed)
    prof = PROFILES.get(a.profile)
    if a.profile != 'design-tool' and not prof:
        die('unknown profile %s' % a.profile)

    # ---- checks
    for nm in [L['name'], L['code']]:
        if len(nm) > 32: die('"%s" is %d characters; names must be 32 or fewer' % (nm, len(nm)))
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', L['code']): die('code "%s": use lowercase letters, digits and dashes' % L['code'])
    lpages = {p['name']: p for p in L['pages']}
    build_pages = [p for p in seed['pages'] if not p['preview'] and not p['composed']]
    for sp in build_pages:
        lpg = lpages.get(sp['name'])
        if not lpg: die('the seed has a page "%s" the layout does not: add a source file for it' % sp['name'])
        if abs(lpg['w'] - sp['w']) > 0.6 or abs(lpg['h'] - sp['h']) > 0.6:
            die('page "%s" is %.2f x %.2f mm in your file and %.2f x %.2f mm on the template (both with bleed). '
                'Resize the artwork to the template, or pick the template that matches it.' % (sp['name'], lpg['w'], lpg['h'], sp['w'], sp['h']))
    extra = set(lpages) - {p['name'] for p in build_pages}
    if extra: die('the layout has page(s) %s that the template does not build: check the page names' % ', '.join(sorted(extra)))
    fonts = L.get('fonts', {})
    for fname, f in fonts.items():
        used = any(t['font'] == fname for p in L['pages'] for t in p['texts'])
        if not used: continue
        if not f.get('file'): die('font %s has no file: set fonts.%s.file to a TTF or OTF the lab is licensed to use' % (fname, fname))
        fp = f['file'] if os.path.isabs(f['file']) else os.path.join(ldir, f['file'])
        if not os.path.exists(fp): die('font file %s not found' % fp)
        f['file'] = fp
        f.setdefault('name', fname)
        if len(f['name']) > 32: die('font name "%s" is over 32 characters: the import fails. Set fonts.%s.name shorter' % (f['name'], fname))
        from fontTools.ttLib import TTFont
        cmap = TTFont(fp).getBestCmap()
        for p in L['pages']:
            for t in p['texts']:
                if t['font'] == fname:
                    miss = sorted({c for c in t['text'] if ord(c) not in cmap and c != ' '})
                    if miss: die('font %s has no glyph for %r in "%s"' % (fname, ''.join(miss), t['text']))
    if prof:
        for p in L['pages']:
            rule = prof.get(p['name'])
            if rule is None: continue
            if p['name'] == 'front' and (p['photos'] or p['texts']):
                die('a store design front is one fixed picture: put every front type layer in "bake" and give the front no photo '
                    'windows, or use --profile design-tool (the design opens in the design tool, not the studio)')
            bad = [ph['name'] for ph in p['photos'] if ph['name'] not in rule['images']] + \
                  [t['name'] for t in p['texts'] if t['name'] not in rule['texts']]
            if bad: die('page %s: element name(s) %s; the studio reads %s' % (p['name'], ', '.join(bad), ', '.join(sorted(rule['images'] | rule['texts']))))

    # ---- images and pages
    images, img_names = {}, {}
    def add_img(data, name):
        k = str(NEW_IMG + len(images) + 1); images[k] = data; img_names[k] = name; return k
    samples = [Image.open(s).convert('RGB') for s in a.samples.split(',') if s]
    fid = {}
    for fname, f in fonts.items():
        if not f.get('file'): continue
        same = [k for k, v in seed['font_names'].items() if v == f['name']]
        fid[fname] = same[0] if same else str(NEW_FONT + len(fid) + 1)
    new_xml, previews = {}, {}
    for sp in build_pages:
        p = lpages[sp['name']]; W, H = sp['w'], sp['h']
        art = Image.open(os.path.join(ldir, p['art'])).convert('RGBA')
        els = []
        if prof and p['name'] == 'front':
            flat = Image.alpha_composite(Image.new('RGBA', art.size, 'white'), art).convert('RGB')
            bio = io.BytesIO(); flat.save(bio, 'JPEG', quality=92); k = add_img(bio.getvalue(), '%s-cover.jpg' % L['code'])
            els.append('<image edit="true" name="cover" height="%s" left="0" pdf_layer="artwork" show_on_preview="true" src="db:%s" top="0" width="%s"/>' % (n(H), k, n(W)))
        else:
            if not prof:   # a store design back and inside stay plain (no background prints white); the studio reads only its own names
                bio = io.BytesIO(); Image.new('RGB', (64, 64), 'white').save(bio, 'JPEG', quality=95)
                k = add_img(bio.getvalue(), 'white.jpg')
                els.append('<image crop="false" edit="false" height="%s" left="0" move="false" name="artwork_base" replace="false" src="db:%s" stretch="true" top="0" width="%s"/>' % (n(H), k, n(W)))
            for i, ph in enumerate(p['photos']):
                src = ''
                if samples:
                    bio = io.BytesIO(); samples[i % len(samples)].save(bio, 'JPEG', quality=82)
                    src = ' src="db:%s"' % add_img(bio.getvalue(), '%s-%s-sample-%d.jpg' % (L['code'], p['name'], i + 1))
                els.append('<image edit="true" height="%s" left="0" name="%s" placeholder="true" show_on_preview="true"%s top="0" width="%s" x="%s" y="%s"/>'
                           % (n(ph['h']), esc(ph['name']), src, n(ph['w']), n(ph['x']), n(ph['y'])))
            ext = art.getextrema()
            plain = ext[3][1] == 0 or all(lo == 255 for lo, hi in ext[:3])
            if prof and not plain:
                die('page %s has artwork: a store design back and inside are plain white with the studio elements only' % p['name'])
            if not plain:
                bio = io.BytesIO(); art.save(bio, 'PNG', optimize=True)
                k = add_img(bio.getvalue(), '%s-%s-art.png' % (L['code'], p['name']))
                els.append('<image crop="false" edit="false" height="%s" left="0" move="false" name="artwork_top" replace="false" src="db:%s" stretch="true" top="0" width="%s"/>' % (n(H), k, n(W)))
        words = []
        for t in p['texts']:
            f = fonts[t['font']]
            fs, x, y, w, h = text_box(t, W, f, f.get('scale', 1.0), a.safe)
            kern = t.get('kerning_pt', 0) * fs / max(t['size'], 0.01)
            kk = ' kerning="%s"' % n(kern) if abs(kern) > 0.001 else ''
            els.append('<text align="%s" color="%s" edit="true" font="%s" fontsize="%s" height="%s"%s name="%s" shrink="true" valign="center" width="%s" x="%s" y="%s">%s</text>'
                       % (t['align'], t['color'], fid[t['font']], n(fs), n(h), kk, esc(t['name']), n(w), n(x), n(y), esc(t['text'])))
            words.append(dict(t=t, fs=fs, x=x, y=y, w=w, h=h, kern=kern, file=f['file']))
        new_xml[sp['name']] = ('<?xml version="1.0" encoding="UTF-8"?>\n<page height="%s" name="%s" pages="" version="2" width="%s">\n  ' % (n(H), sp['name'], n(W))
                               + '\n  '.join(els) + '\n</page>')
        previews[sp['name']] = (W, H, art, p, words, samples)

    # ---- YAML by surgery on the seed text
    out_parts = []
    kept_imgs, kept_fonts = set(), set()
    for key, chunk in seed['parts']:
        if key == 'id': chunk = 'id: \n'
        elif key == 'name': chunk = 'name: %s\n' % json.dumps(L['name'])
        elif key == 'code': chunk = 'code: %s\n' % L['code']
        elif key == 'description': chunk = 'description: %s\n' % json.dumps(L.get('description', ''))
        elif key in ('preview_img', 'source_id', 'preview_template_id'): chunk = '%s: \n' % key
        elif key == 'custom': chunk = 'custom:\n  url_path: %s\n  meta_title: %s\n' % (L['code'], json.dumps(L['name']))
        elif key == 'templates':
            ents = []
            for i, sp in enumerate(seed['pages']):
                if sp['name'] in new_xml:
                    data = '\n'.join('    ' + l for l in new_xml[sp['name']].split('\n'))
                    ents.append('- id: \n  name: %s\n  print_book_id: \n  number: %d\n  data: |\n%s\n  layout: false\n  usage_flags: 3\n  preview: %s\n'
                                % (sp['name'], i, data, 'true' if sp['preview'] else 'false'))
                else:
                    e = re.sub(r'^- id: \d*', '- id: ', sp['raw'], count=1)
                    ents.append(e if e.endswith('\n') else e + '\n')
                    im, fo = refs(sp['data']); kept_imgs |= im; kept_fonts |= fo
            chunk = 'templates:\n' + ''.join(ents)
        elif key == 'layouts':
            if a.keep_layouts:
                chunk = re.sub(r'(?m)^- id: \d+', '- id: ', chunk)
                chunk = re.sub(r'(?m)^  print_book_id: \d+', '  print_book_id: ', chunk)
                im, fo = refs(chunk); kept_imgs |= im; kept_fonts |= fo
            else:
                chunk = 'layouts: []\n'
        elif key == 'design_options': chunk = 'design_options: []\n'
        elif key == '__image_map':
            rows = [(k, seed['image_names'].get(k, k)) for k in sorted(kept_imgs)] + list(img_names.items())
            chunk = '__image_map:\n' + ''.join("  '%s':\n    :original_filename: %s\n" % (k, v) for k, v in rows) if rows else '__image_map: {}\n'
        elif key == '__font_map':
            rows = [(k, seed['font_names'][k]) for k in sorted(kept_fonts) if k in seed['font_names']]
            rows += [(fid[f], fonts[f]['name']) for f in fid if fid[f] not in dict(rows)]
            chunk = '__font_map:\n' + ''.join("  '%s':\n    :name: %s\n" % (k, v) for k, v in rows) if rows else '__font_map: {}\n'
        out_parts.append(chunk if chunk.endswith('\n') else chunk + '\n')
    yml = '---\n' + ''.join(out_parts)

    os.makedirs(a.out, exist_ok=True)
    tar_path = os.path.join(a.out, 'IMPORT-design-%s.tar.gz' % L['code'])
    with tarfile.open(tar_path, 'w:gz') as tf:
        def add(nm, data=None):
            ti = tarfile.TarInfo(nm); ti.mtime = 0
            if data is None: ti.type = tarfile.DIRTYPE; ti.mode = 0o755; tf.addfile(ti)
            else: ti.size = len(data); ti.mode = 0o644; tf.addfile(ti, io.BytesIO(data))
        for d in ('assets', 'fonts', 'glb_files', 'images', 'pdfs'): add('./' + d + '/')
        add('./__print_theme.yml', yml.encode('utf8'))
        for k in sorted(kept_imgs):
            sp_ = os.path.join(seed['path'], 'images', k)
            if os.path.exists(sp_): add('./images/' + k, open(sp_, 'rb').read())
        for k, data in images.items(): add('./images/' + k, data)
        done = set()
        for k in sorted(kept_fonts):
            sp_ = os.path.join(seed['path'], 'fonts', k)
            if os.path.exists(sp_): add('./fonts/' + k, open(sp_, 'rb').read()); done.add(k)
        for f, k in fid.items():
            if k not in done:
                sp_ = os.path.join(seed['path'], 'fonts', k)
                add('./fonts/' + k, open(sp_ if os.path.exists(sp_) else fonts[f]['file'], 'rb').read()); done.add(k)

    # ---- previews, drawn from the same numbers that went into the XML
    for name, (W, H, art, p, words, smp) in previews.items():
        k = art.width / W
        im = Image.new('RGBA', art.size, 'white')
        for i, ph in enumerate(p['photos']):
            if not smp: continue
            s = smp[i % len(smp)]; bw, bh = int(ph['w'] * k), int(ph['h'] * k)
            sc = max(bw / s.width, bh / s.height); s2 = s.resize((int(s.width * sc) + 1, int(s.height * sc) + 1))
            s2 = s2.crop(((s2.width - bw) // 2, (s2.height - bh) // 2, (s2.width - bw) // 2 + bw, (s2.height - bh) // 2 + bh))
            im.paste(s2, (int(ph['x'] * k), int(ph['y'] * k)))
        im = Image.alpha_composite(im, art); d = ImageDraw.Draw(im)
        for wd in words:
            t = wd['t']; ft = ImageFont.truetype(wd['file'], max(1, int(round(wd['fs'] * k))))
            kp = wd['kern'] / 72 * 25.4 * k
            ws = [ft.getlength(c) + kp for c in t['text']]; tw = sum(ws) - (kp if ws else 0)
            bx, by, bw, bh = wd['x'] * k, wd['y'] * k, wd['w'] * k, wd['h'] * k
            x = bx if t['align'] == 'left' else bx + bw - tw if t['align'] == 'right' else bx + (bw - tw) / 2
            for c, cw in zip(t['text'], ws):
                d.text((x, by + bh / 2), c, font=ft, fill=t['color'], anchor='lm'); x += cw
        im = im.convert('RGB'); im.thumbnail((1400, 1400))
        im.save(os.path.join(a.out, '%s-preview-%s.png' % (L['code'], name)))
    print('wrote', tar_path, '(%d KB)' % (os.path.getsize(tar_path) // 1024))
    print('pages built:', ', '.join(new_xml), '| copied from the seed:', ', '.join(sp['name'] for sp in seed['pages'] if sp['name'] not in new_xml) or 'none')

if __name__ == '__main__':
    main()

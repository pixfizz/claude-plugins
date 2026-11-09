#!/usr/bin/env python3
"""Pixfizz studio-designs: build the Greeting Card Studio "store designs" library for one site from that site's own card
template exports (Greeting Card Studio 0.5.0 and later).

A store's own designs sit in the studio next to the Pixfizz and MSP designs. Each keeps exactly what its template has: one card type and one orientation, a fixed front (the whole artwork is one
picture), and live logo, photo and words on the back and inside, found again at the hand-off by element name.

usage: python3 gcs_store_library.py <site tag> <out dir> <export dir> [<export dir> ...]
  site tag    short name used in every file name, e.g. abc  ->  gcs-store-abc-*
  export dir  an unpacked template export (__print_product.yml, images/, fonts/). The product decides the role:
              a template with pages front, outside, inside, back is folded (fold); front and back only is flat two-sided (flat2).
              Orientation from the front page: taller than wide = portrait. Designs whose code ends in -upload are skipped
              (the studio's Your own design replaces them).
Writes into <out dir>: gcs-store-<tag>-designs.json, gcs-store-<tag>-<key>.webp (front, 900 px short side), -t.webp (300 px),
gcs-store-<tag>-logo.webp (the templates' sample logo), gcs-store-<tag>-photo.webp (sample inside photo),
gcs-store-<tag>-f-<font id>.woff2 (the site fonts the templates use, so the studio shows the print fonts).
Upload all of them to the site's assets, then build gcs-store-<tag>-files.json {v, files:{name:url}} from the asset list and
put its URL in the mount (gcs_store_files)."""
import sys, re, json, os, hashlib, io
import yaml
from PIL import Image
import xml.etree.ElementTree as ET
from fontTools.ttLib import TTFont

class _L(yaml.SafeLoader): pass
def _any(loader, suffix, node):
    if isinstance(node, yaml.MappingNode): return loader.construct_mapping(node, deep=True)
    if isinstance(node, yaml.SequenceNode): return loader.construct_sequence(node, deep=True)
    return loader.construct_scalar(node)
_L.add_multi_constructor('!', _any)
def load(p): return yaml.load(open(p, encoding='utf8'), Loader=_L)

TAG, OUT, EXPORTS = sys.argv[1], sys.argv[2], sys.argv[3:]
VERSION = os.environ.get('LIB_V', '2026-10-26')
os.makedirs(OUT, exist_ok=True)
P = 'gcs-store-' + TAG + '-'
B = 3.175  # bleed, mm
KEYS = {'sentiment': 'cs_msg', 'signature': 'cs_sig', 'back-message': 'cs_bmsg'}
LOGO_NAMES = ('logo', 'back-image')
FONTS = {}   # font id -> family name
designs, samples = [], {}

def els(xml, ox, oy, W, H, texts, xbase=0, ybase=0, page=''):
    """live elements of one card face, boxes in percent of the trimmed face; nm = the element name the hand-off finds"""
    r = ET.fromstring(xml) if isinstance(xml, str) else xml
    out = []
    for e in r:
        n = e.get('name') or ''
        if e.tag not in ('image', 'text') or e.get('pdf_layer') == 'production': continue
        x = float(e.get('x', 0)) - xbase - ox; y = float(e.get('y', 0)) - ybase - oy
        w = float(e.get('width')); h = float(e.get('height'))
        box = dict(x=round(x / W * 100, 3), y=round(y / H * 100, 3), w=round(w / W * 100, 3), h=round(h / H * 100, 3))
        if e.tag == 'image':
            src = (e.get('src') or '').split(':')[-1]
            if n in LOGO_NAMES: out.append(dict(t='g', nm=n, pg=page, **box)); samples.setdefault('logo', set()).add(src)
            elif n == 'photo': out.append(dict(t='p', s='b0', nm=n, pg=page, **box)); samples.setdefault('photo', set()).add(src)
            else: sys.exit('unknown image element %r on %s' % (n, page))
        else:
            if n not in KEYS: sys.exit('unknown text element %r on %s' % (n, page))
            k = KEYS[n]; fid = e.get('font'); FONTS.setdefault(fid, None)
            out.append(dict(t='x', k=k, nm=n, pg=page, f='sf' + fid, sz=round(float(e.get('fontsize')) / W * 100, 3), c=e.get('color'),
                            al=e.get('align', 'center'), va=e.get('valign', 'center'), **box))
            texts[k] = e.text or ''
    return out

def webp(im, path, size, q):
    im.resize(size, Image.LANCZOS).save(path, 'WEBP', quality=q, method=6)

src_dir = {}
for ex in EXPORTS:
    y = load(os.path.join(ex, '__print_product.yml')); prod = y['products'][0]
    for fid, f in (y.get('__font_map') or {}).items(): FONTS.setdefault(str(fid), None); FONTS[str(fid)] = f.get(':name') or f.get('name')
    for t in y['print_themes']:
        if t['code'].endswith('-upload') or t.get('deleted'): continue
        pages = {p['name']: p['data'] for p in t['templates']}
        fr = ET.fromstring(pages['front']); pw, ph = float(fr.get('width')), float(fr.get('height'))
        o = 'portrait' if ph > pw else 'landscape'; W, H = (127, 177.8) if o == 'portrait' else (177.8, 127)
        fmt = 'folded' if 'inside' in pages else 'double'
        role = ('fold' if fmt == 'folded' else 'flat2') + '-' + o[0]
        key = re.sub(r'[^a-z0-9-]', '', t['code'].lower())
        texts = {}
        cov = [e for e in fr if e.tag == 'image' and e.get('name') == 'cover']
        if len(cov) != 1: sys.exit(t['code'] + ': the front needs exactly one image named cover')
        src = cov[0].get('src').split(':')[1]
        # the front page of a folded portrait card has no bleed at the fold (left edge)
        fx = 0 if (fmt == 'folded' and o == 'portrait') else B; fy = B
        im = Image.open(os.path.join(ex, 'images', src)).convert('RGB'); iw, ih = im.size
        c = im.crop((round(fx / pw * iw), round(fy / ph * ih), round((fx + W) / pw * iw), round((fy + H) / ph * ih)))
        webp(c, os.path.join(OUT, P + key + '.webp'), (900, 1260) if o == 'portrait' else (1260, 900), 80)
        webp(c, os.path.join(OUT, P + key + '-t.webp'), (300, 420) if o == 'portrait' else (420, 300), 78)
        d = dict(id='store-' + key, key=key, code=t['code'], theme=t['id'], role=role, product=prod['id'], formats=[fmt], orients=[o],
                 minUnits=int(prod.get('min_units') or 1), front=P + key)
        if fmt == 'double':
            d['back'] = els(pages['back'], B, B, W, H, texts, page='back')
        else:
            d['fold'] = els(pages['back'], B, B, W, H, texts, page='back')
            ins = ET.fromstring(pages['inside']); L, R = [], []
            for e in ins:
                if e.get('pdf_layer') == 'production': continue
                second = float(e.get('x', 0)) >= W + B if o == 'portrait' else float(e.get('y', 0)) >= H + B
                (R if second else L).append(e)
            def sub(lst, second):
                s = ET.Element('page'); [s.append(e) for e in lst]
                if o == 'portrait': return els(s, 0 if second else B, B, W, H, texts, xbase=W + B if second else 0, page='inside')
                return els(s, B, 0 if second else B, W, H, texts, ybase=H + B if second else 0, page='inside')
            d['inL'] = sub(L, False); d['inR'] = sub(R, True)
        d['name'] = re.sub(r'\s*(5x7|7x5)\s*(V|H|Flat)?\s*$', '', t['name']).strip()
        d['texts'] = texts
        designs.append(d); src_dir[key] = ex

# the sample logo and photo the templates carry (one each expected; the first is used)
def first_image(kind):
    for s in sorted(samples.get(kind, [])):
        for ex in EXPORTS:
            p = os.path.join(ex, 'images', s)
            if os.path.exists(p): return p
    return None
hs = {k: sorted({hashlib.sha256(open(os.path.join(ex, 'images', s), 'rb').read()).hexdigest()[:12] for s in samples.get(k, []) for ex in EXPORTS if os.path.exists(os.path.join(ex, 'images', s))}) for k in ('logo', 'photo')}
lg = first_image('logo'); logo = Image.open(lg).convert('RGBA'); logo.thumbnail((900, 900)); logo.save(os.path.join(OUT, P + 'logo.webp'), 'WEBP', lossless=True)
ph = first_image('photo')
if ph: im = Image.open(ph).convert('RGB'); im.thumbnail((1200, 1200)); im.save(os.path.join(OUT, P + 'photo.webp'), 'WEBP', quality=80)
fonts = {}
for fid, name in FONTS.items():
    srcf = next((os.path.join(ex, 'fonts', fid) for ex in EXPORTS if os.path.exists(os.path.join(ex, 'fonts', fid))), None)
    if not srcf: sys.exit('font %s (%s) is not in the exports' % (fid, name))
    f = TTFont(srcf); f.flavor = 'woff2'; f.save(os.path.join(OUT, P + 'f-' + fid + '.woff2'))
    fonts['sf' + fid] = dict(id=int(fid), name=name, file=P + 'f-' + fid + '.woff2')
lib = dict(v=VERSION, tag=TAG, designs=designs, fonts=fonts, logo=P + 'logo.webp', photo=P + 'photo.webp' if ph else None,
           labels=dict(cs_msg='Message', cs_sig='Company name', cs_bmsg='Back message'))
# optional: ready-made messages for the Message box (PHRASES=<file>.json, {"phrases": [{"t": text, "f": font key}]}); every font must be in the library
if os.environ.get('PHRASES'):
    lib['phrases'] = json.load(open(os.environ['PHRASES'], encoding='utf8'))['phrases']
    for p in lib['phrases']:
        if p['f'] not in fonts: sys.exit('phrase font %s is not in the library fonts %s' % (p['f'], sorted(fonts)))
open(os.path.join(OUT, P + 'designs.json'), 'w').write(json.dumps(lib, separators=(',', ':'), ensure_ascii=False))
print(len(designs), 'designs:', ', '.join(d['key'] + '(' + d['role'] + ')' for d in designs))
print('fonts:', {k: v['name'] for k, v in fonts.items()}, 'sample logo files', hs['logo'], 'sample photo files', hs['photo'])

#!/usr/bin/env python3
"""Greeting Card Studio 0.7.2: a store library of designs with a LIVE front (photo windows and words on the front), built from
the site's own design exports (admin > design > Export, export_print_theme/<id>). The MSP generator's method, one role per design:
the artwork becomes a plate atlas per design (art above a photo gets its own plate), photos and words stay live, and the
hand-off map (element name if unique on the page, else its box in page mm) is written in the same pass, so keys always match.

usage: gcs_store_live.py <site tag> <out dir> <export dir> [<export dir> ...]
  env  OCC=christmas  OCC_NAME=Christmas  MIN_UNITS=25  LIB_V=<date>  OCC_MAP=<json file {design id: occasion key}>
  export dir = one unpacked design export (__print_theme.yml or __print_product.yml, images/, fonts/)
Role from the pages: front + back = flat2, outside + inside = fold; orientation from the trimmed face.
Writes gcs-store-<tag>-designs.json, -a-<key>.webp / -a-<key>-t.webp (atlases), -<key>.webp / -<key>-t.webp (front preview),
-f-<font id>.woff2. Upload all to the site's assets, build gcs-store-<tag>-files.json {v, files:{name:url}}, mount gcs_store_files.
Checks every design and stops with the reason on anything it cannot place (see PROBLEMS at the end)."""
import sys, os, re, io, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(1, os.path.join(HERE, '..', 'msp'))
import yaml
from lxml import etree
from PIL import Image
from fontTools.ttLib import TTFont
import xrender as X

class _L(yaml.SafeLoader): pass
def _any(loader, suffix, node):
    if isinstance(node, yaml.MappingNode): return loader.construct_mapping(node, deep=True)
    if isinstance(node, yaml.SequenceNode): return loader.construct_sequence(node, deep=True)
    return loader.construct_scalar(node)
_L.add_multi_constructor('!', _any)

TAG, OUT, EXPORTS = sys.argv[1], sys.argv[2], sys.argv[3:]
P = 'gcs-store-' + TAG + '-'
B = 3.175; TW = 127.0; TH = 177.8
S = 640 / TW
THUMB_W = {'p': 260, 'l': 364}
os.makedirs(OUT, exist_ok=True)
FONTS = {}; PROBLEMS = []; designs = []
# 0.7.13: OCC_MAP=<json {theme id: occasion key}> gives each design its own occasion (christmas, hanukkah, newyear, seasons,
# faith: the studio chips, as the MSP designs use them). Designs not in the map take the library occasion (OCC).
OCCMAP = {str(k): v for k, v in json.load(open(os.environ['OCC_MAP'])).items()} if os.environ.get('OCC_MAP') else {}

def fv(e, k, d=0.0):
    try: return float(e.get(k)) if e.get(k) not in (None, '', 'false') else d
    except ValueError: return d

def norm(xml):
    """one page as lxml root: positions in x/y (some exports use left/top), score marks dropped"""
    if not isinstance(xml, str): xml = str(xml)
    r = etree.fromstring(xml.encode())
    for e in list(r):
        if (e.get('name') or '').lower() == 'score' or e.tag == 'score': r.remove(e); continue
        # left/top are the photo's crop offset inside its box, NOT its position; a missing x or y is 0 (seen in real exports, 20 Nov 2026)
        for k in ('x', 'y'):
            if e.get(k) is None: e.set(k, '0')
    return r

def is_live(e):
    nm = (e.get('name') or '').lower()
    if e.tag == 'image' and (e.get('placeholder') == 'true' or nm.startswith('placeholder')) and e.get('edit') != 'false': return 'p'
    if e.tag == 'text' and e.get('edit') == 'true': return 'x'
    return None

def load_export(ex):
    for n in ('__print_theme.yml', '__print_product.yml'):
        p = os.path.join(ex, n)
        if os.path.exists(p): y = yaml.load(open(p, encoding='utf8'), Loader=_L); break
    else: sys.exit(ex + ': no __print_theme.yml or __print_product.yml')
    themes = y.get('print_themes') or [y.get('print_theme') or y]
    fm = y.get('__font_map') or {}
    for fid, f in fm.items(): FONTS.setdefault(str(fid), (f.get(':name') or f.get('name') or str(fid), None))
    imgs = {fn: open(os.path.join(ex, 'images', fn), 'rb').read() for fn in os.listdir(os.path.join(ex, 'images'))} if os.path.isdir(os.path.join(ex, 'images')) else {}
    fonts = {}
    if os.path.isdir(os.path.join(ex, 'fonts')):
        for fid in os.listdir(os.path.join(ex, 'fonts')): fonts[fid] = os.path.join(ex, 'fonts', fid)
    return themes, imgs, fonts

def option_defaults(t):
    """Artwork that only a template option puts on the page (Color Theme, Greeting: an image element with no src that the
    option's default value fills by element substitution). {element name: image src} of each multiple-choice option's default value."""
    subs = {}
    for o in t.get('design_options') or []:
        vals = [v for v in (o.get('option_values') or []) if v.get('published') not in (False, 'false')]
        if not vals: continue
        dv = next((v for v in vals if v.get('default') in (True, 'true')), None)
        if dv is None: continue
        for s in dv.get('element_substitutions') or []:
            if s.get('substitution_type') == 'image' and s.get('element_name') and s.get('content'): subs.setdefault(s['element_name'], str(s['content']))
    return subs

def pages_of(t):
    out = {}
    subs = option_defaults(t)
    for p in t.get('templates') or []:
        if p.get('layout') in (True, 'true') or p.get('preview') in (True, 'true'): continue
        nm, data = p.get('name'), p.get('data')
        if nm not in ('front', 'back', 'outside', 'inside') or not data: continue   # preview-*, backup and option pages are not card faces
        if isinstance(data, str) and data.strip().startswith('"'): data = yaml.safe_load(data)
        r = norm(data)
        for e in r:
            if e.tag == 'image' and not e.get('src') and e.get('name') in subs and not is_live(e):
                e.set('src', subs[e.get('name')]); print('%s: %s on %s takes its option default %s' % (t.get('code'), e.get('name'), nm, subs[e.get('name')]))
        if nm in out:
            if len(list(r)) == 0: continue          # duplicate empty page (fold-p has a second empty outside)
            if len(list(out[nm])) == 0: out[nm] = r; continue
            PROBLEMS.append('%s: two non-empty pages named %s, the first is used' % (t.get('code'), nm)); continue
        out[nm] = r
    return out

def build_panel(root, ctx, page, x0, y0, pw, ph, turn, cells, keyp, texts, slots, mp, static_ph=False, tkp=None):
    W, H = fv(root, 'width'), fv(root, 'height')
    kids = list(root)
    order = sorted(range(len(kids)), key=lambda i: (fv(kids[i], 'z', 0), i))
    names = [(k.get('name') or '') for k in kids]
    def inside(e):
        x, y, w, h = fv(e, 'x'), fv(e, 'y'), fv(e, 'width'), fv(e, 'height')
        return x < x0 + pw and x + w > x0 and y < y0 + ph and y + h > y0
    def center_in(e):
        cx = fv(e, 'x') + fv(e, 'width') / 2; cy = fv(e, 'y') + fv(e, 'height') / 2
        return x0 <= cx < x0 + pw and y0 <= cy < y0 + ph
    els = []; group = []; first = [True]
    def flush():
        if not group and not first[0]: return
        r = etree.Element('page', width=str(W), height=str(H), version='2')
        if first[0] and root.get('bgcolor'): r.set('bgcolor', root.get('bgcolor'))
        for e in group: r.append(etree.fromstring(etree.tostring(e)))
        cv = X.render(etree.tostring(r), ctx, px_per_mm=S, show_placeholders=True, transparent=not first[0])
        crop = cv.crop((round(x0 * S), round(y0 * S), round(x0 * S) + round(pw * S), round(y0 * S) + round(ph * S)))
        if turn: crop = crop.rotate(180)
        cells.append(crop)
        els.append({'t': 'b', 'x': 0, 'y': 0, 'w': 100, 'h': 100, 'pi': len(cells) - 1})
        group.clear(); first[0] = False
    for i in order:
        e = kids[i]; lv = is_live(e)
        if lv == 'p' and static_ph: lv = None
        if lv and center_in(e):
            flush()
            gx, gy, w, h = fv(e, 'x'), fv(e, 'y'), fv(e, 'width'), fv(e, 'height')
            x, y, rot = gx - x0, gy - y0, fv(e, 'rotate')
            if turn: x, y, rot = pw - x - w, ph - y - h, (rot + 180) % 360
            if rot > 180: rot -= 360
            el = {'x': round(x / pw * 100, 3), 'y': round(y / ph * 100, 3), 'w': round(w / pw * 100, 3), 'h': round(h / ph * 100, 3)}
            if abs(rot) > 0.01: el['rot'] = round(rot, 2)
            nm = e.get('name') or ''
            m = {'t': lv, 'g': [round(gx, 3), round(gy, 3), round(w, 3), round(h, 3)]}
            if nm and names.count(nm) == 1: m['nm'] = nm
            if lv == 'p':
                k = keyp + str(len(slots)); slots.append(k); el.update(t='p', s=k); m['s'] = k
                bw = fv(e, 'border')
                if bw > 0 and e.get('border') != 'false': el['css'] = f"border:{bw / pw * 100:.3f}cqw solid {e.get('bordercolor') or '#ffffff'};box-sizing:border-box;"
                if fv(e, 'radius') > 0: el['r'] = round(fv(e, 'radius') / pw * 100, 3)
                mk = (e.get('mask') or '').replace('db:', '')
                if mk and mk in ctx.images:
                    mh = mask_file(ctx.images[mk])
                    el['css'] = el.get('css', '') + f"-webkit-mask:url(@m:{mh}) center/100% 100% no-repeat;mask:url(@m:{mh}) center/100% 100% no-repeat;"
                elif mk: PROBLEMS.append('%s: photo %s has a mask that is not in the export; shown as a plain rectangle' % (page, nm or k))
            else:
                fid = e.get('font', ''); FONTS.setdefault(fid, (fid, None))
                k = (tkp or keyp) + 't' + str(len(texts) + 1); m['k'] = k
                txt = ''.join(e.itertext())
                texts.append((k, txt, fv(e, 'fontsize', 4.233)))
                el.update(t='x', k=k, f='sf' + fid, sz=round(fv(e, 'fontsize', 4.233) / pw * 100, 3), c=(e.get('color') or '#000000'), al=e.get('align', 'left'))
                if e.get('valign') in ('top', 'bottom'): el['va'] = e.get('valign')
                if e.get('caps') == 'true': el['tt'] = 1
                if fv(e, 'kerning'): el['ls'] = round(fv(e, 'kerning') / fv(e, 'fontsize', 4.233), 3)
            mp.setdefault(page, []).append(m)
            els.append(el)
        elif not lv and inside(e):
            group.append(e)
    if group or first[0]: flush()
    return els

MASKS = {}
def mask_file(b):
    """a photo mask as a small alpha PNG (white where the photo shows), file gcs-store-<tag>-m-<hash>.png"""
    h = hashlib.sha1(b).hexdigest()[:10]
    if h not in MASKS:
        im = Image.open(io.BytesIO(b)).convert('RGBA'); a = im.getchannel('A')
        m = a if a.getextrema()[0] < 250 else im.convert('L')
        m.thumbnail((400, 400), Image.LANCZOS)
        out = Image.new('RGBA', m.size, (255, 255, 255, 0)); out.putalpha(m)
        out.save(os.path.join(OUT, P + 'm-' + h + '.png'), optimize=True); MASKS[h] = 1
    return h

def label_texts(texts):
    out = {}
    if not texts: return out
    big = max(texts, key=lambda t: t[2])[0]; n = 0
    for k, txt, sz in texts:
        low = txt.lower()
        if re.search(r'\bname', low) or 'family' in low: lab = 'Names'
        elif re.fullmatch(r'\s*(19|20)\d\d\s*', txt) or 'year' in low: lab = 'Year'
        elif k == big: lab = 'Greeting'
        else: n += 1; lab = 'Line ' + str(n) if n > 1 else 'Small line'
        out[k] = lab
    return out

def webp(im, path, w, q):
    h = round(im.height * w / im.width); im.convert('RGB').resize((w, h), Image.LANCZOS).save(path, 'WEBP', quality=q, method=6)

for ex in EXPORTS:
    themes, imgs, fonts = load_export(ex)
    ctx = X.Ctx(imgs, fonts, []); ctx.real = True; ctx.images = imgs
    for t in themes:
        code = str(t.get('code') or ''); name = str(t.get('name') or code)
        pg = pages_of(t)
        if 'front' in pg and 'back' in pg: fmt = 'flat2'; face = pg['front']; fw, fh = fv(face, 'width') - 2 * B, fv(face, 'height') - 2 * B
        elif 'outside' in pg and 'inside' in pg:
            fmt = 'fold'; face = pg['outside']; ow, oh = fv(face, 'width') - 2 * B, fv(face, 'height') - 2 * B
            fw, fh = (ow / 2, oh) if ow > oh else (ow, oh / 2)
        else: PROBLEMS.append('%s: pages %s are neither front+back nor outside+inside; left out' % (code, sorted(pg))); continue
        o = 'p' if fh > fw else 'l'; on = 'portrait' if o == 'p' else 'landscape'
        pw, ph = fw, fh
        if abs(pw * ph - TW * TH) > 60: PROBLEMS.append('%s: face %.1f x %.1f mm is not 5 x 7' % (code, pw, ph))
        key = re.sub(r'[^a-z0-9]+', '-', code.lower()).strip('-') or str(t.get('id'))
        cells = []; mp = {}
        ft, fs_ = [], []; bt, bs_ = [], []; it_, is_ = [], []; ot, os_ = [], []
        if fmt == 'flat2':
            front = build_panel(pg['front'], ctx, 'front', B, B, pw, ph, False, cells, 'f', ft, fs_, mp)
            back = build_panel(pg['back'], ctx, 'back', B, B, pw, ph, False, cells, 'b', bt, bs_, mp)
            nthumb = len(cells); fold, inL, inR = [], [], []
        else:
            side = o == 'p'
            fb = (B + pw, B, False) if side else (B, B + ph, False)       # front panel on the outside page
            ob = (B, B, False) if side else (B, B, True)                  # outside back (turned on a top-fold card)
            front = build_panel(pg['outside'], ctx, 'outside', fb[0], fb[1], pw, ph, fb[2], cells, 'f', ft, fs_, mp)
            fold = build_panel(pg['outside'], ctx, 'outside', ob[0], ob[1], pw, ph, ob[2], cells, 'o', ot, os_, mp, static_ph=True)
            nthumb = len(cells)
            ia, ib = ((B, B), (B + pw, B)) if side else ((B, B), (B, B + ph))
            inL = build_panel(pg['inside'], ctx, 'inside', ia[0], ia[1], pw, ph, False, cells, 'b', it_, is_, mp, tkp='i')
            inR = build_panel(pg['inside'], ctx, 'inside', ib[0], ib[1], pw, ph, False, cells, 'b', it_, is_, mp, tkp='i')
            back = []
        if not fs_ and not any(e['t'] == 'x' for e in front): PROBLEMS.append('%s: nothing live on the front (fixed-front design: use gen_store_lib.py)' % code)
        cw, ch = cells[0].size
        full = Image.new('RGBA', (cw, ch * len(cells)), (0, 0, 0, 0))
        for i, c in enumerate(cells): full.alpha_composite(c.convert('RGBA'), (0, i * ch))
        full.save(os.path.join(OUT, P + 'a-' + key + '.webp'), 'WEBP', quality=80, method=5)
        tw = THUMB_W[o]; th = round(ch * tw / cw)
        thumb = Image.new('RGBA', (tw, th * nthumb), (0, 0, 0, 0))
        for i in range(nthumb): thumb.alpha_composite(cells[i].convert('RGBA').resize((tw, th), Image.LANCZOS), (0, i * th))
        thumb.save(os.path.join(OUT, P + 'a-' + key + '-t.webp'), 'WEBP', quality=78, method=5)
        # the front preview: the whole face with its sample photos and words, as the template's own preview shows it
        fpg = pg['front'] if fmt == 'flat2' else pg['outside']
        cv = X.render(etree.tostring(fpg), ctx, px_per_mm=S, show_placeholders=True)
        fx0, fy0 = (B, B) if fmt == 'flat2' else (fb[0], fb[1])
        fim = cv.crop((round(fx0 * S), round(fy0 * S), round(fx0 * S) + round(pw * S), round(fy0 * S) + round(ph * S)))
        if fmt == 'fold' and fb[2]: fim = fim.rotate(180)
        webp(fim, os.path.join(OUT, P + key + '.webp'), 900 if o == 'p' else 1260, 80)
        webp(fim, os.path.join(OUT, P + key + '-t.webp'), 300 if o == 'p' else 420, 78)
        texts = {k: tx for k, tx, _ in ft + bt + it_ + ot}
        tl = dict(label_texts(ft)); tl.update({k: 'Back: ' + v for k, v in label_texts(bt + ot).items()}); tl.update({k: 'Inside: ' + v for k, v in label_texts(it_).items()})
        px = cells[0].convert('RGB').resize((1, 1), Image.LANCZOS).getpixel((0, 0)); cols = [e['c'] for e in front if e.get('t') == 'x']
        ink = cols[0] if cols else '#222222'
        lv = {'front': front, 'back': back, 'fold': fold, 'inL': inL, 'inR': inR,
              'n': {'front': len(fs_), 'back': len(bs_), 'inside': len(is_)}, 'pl': {'f': P + 'a-' + key, 'N': len(cells), 'T': nthumb},
              'tl': tl, 'texts': texts, 'pal': {'paper': '#%02x%02x%02x' % px, 'ink': ink, 'accent': cols[1] if len(cols) > 1 else ink, 'accent2': ink}}
        fmts = 'folded' if fmt == 'fold' else 'double'
        designs.append({'id': 'store-' + key, 'key': key, 'code': code, 'theme': t.get('id'), 'role': fmt + '-' + o, 'formats': [fmts], 'orients': [on],
                        'minUnits': int(os.environ.get('MIN_UNITS', '1')), 'front': P + key, 'name': re.sub(r'\s*(5x7|7x5)\s*(V|H|Flat)?\s*$', '', name).strip(),
                        'live': 1, 'lv': lv, 'map': mp, 'texts': texts})
        if str(t.get('id')) in OCCMAP: designs[-1]['occ'] = [OCCMAP[str(t.get('id'))]]   # one occasion per design
        print('%-40s %-7s front %d photo(s) %d text(s), %d plate(s)' % (code, fmt + '-' + o, len(fs_), len(ft), len(cells)))

fonts = {}
for fid, (name, _) in FONTS.items():
    if not fid: continue
    src = next((os.path.join(ex, 'fonts', fid) for ex in EXPORTS if os.path.exists(os.path.join(ex, 'fonts', fid))), None)
    if not src: PROBLEMS.append('font %s (%s) is not in the exports; the studio shows a fallback' % (fid, name)); continue
    f = TTFont(src)
    from fontTools import subset
    sub = subset.Subsetter(subset.Options(layout_features=['*'], name_IDs=['*'], notdef_outline=True, glyph_names=False))
    sub.populate(unicodes=list(range(0x20, 0x7f)) + list(range(0xa0, 0x180)) + [0x2013, 0x2014, 0x2018, 0x2019, 0x201c, 0x201d, 0x2022, 0x2026, 0x20ac, 0x2122])
    sub.subset(f)
    f.flavor = 'woff2'; f.save(os.path.join(OUT, P + 'f-' + fid + '.woff2'))
    try: fid_i = int(fid)
    except ValueError: fid_i = fid
    fonts['sf' + fid] = {'id': fid_i, 'name': name, 'file': P + 'f-' + fid + '.woff2'}
lib = {'v': os.environ.get('LIB_V', '2026-11-20'), 'tag': TAG, 'live': 1, 'designs': designs, 'fonts': fonts, 'logo': None, 'photo': None,
       'occasion': {'key': os.environ.get('OCC', 'christmas'), 'name': os.environ.get('OCC_NAME', 'Christmas')}, 'labels': {}}
open(os.path.join(OUT, P + 'designs.json'), 'w').write(json.dumps(lib, separators=(',', ':'), ensure_ascii=False))
print(len(designs), 'designs,', len(fonts), 'fonts')
print('PROBLEMS:\n' + ('\n'.join(PROBLEMS) or 'none'))

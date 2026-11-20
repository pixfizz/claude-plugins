"""Render a Pixfizz page XML (version 2) to PNG for review.
Covers what the MSP and GCS card designs use: page bgcolor, image (art + placeholders, border, rotate),
shape (rect, ellipse), text (font, fontsize mm, color, align, valign, kerning mm, leading, shrink, rotate).
Placeholders are filled with a sample photo (cover fit) so the review looks like a real card.
Not a production renderer: the platform's own preview and PDF are the reference."""
import io, re, math
from lxml import etree
from PIL import Image, ImageDraw, ImageFont, ImageColor

def col(c, default='#000000'):
    if not c or c in ('false', 'none', 'transparent'): return None if c else ImageColor.getrgb(default)
    try: return ImageColor.getrgb(c)
    except Exception: return ImageColor.getrgb(default)

def f(e, k, d=0.0):
    v = e.get(k)
    try: return float(v) if v not in (None, '', 'false') else d
    except ValueError: return d

class Ctx:
    def __init__(self, images, fonts, samples):
        self.images = images      # db id (str) -> bytes or PIL image
        self.fonts = fonts        # font id (str) -> path to ttf/otf
        self.samples = samples    # list of PIL images for placeholders
        self._cache = {}
        self.real = True
    def img(self, src):
        k = src.replace('db:', '')
        if k in self._cache: return self._cache[k]
        b = self.images.get(k)
        if b is None: return None
        im = b if isinstance(b, Image.Image) else Image.open(io.BytesIO(b))
        im = im.convert('RGBA'); self._cache[k] = im; return im

def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    r = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    x, y = (r.width - w) // 2, (r.height - h) // 2
    return r.crop((x, y, x + w, y + h))

def paste_rot(canvas, layer, x, y, rot):
    if rot:
        cx, cy = x + layer.width / 2, y + layer.height / 2
        layer = layer.rotate(-rot, expand=True, resample=Image.BICUBIC)
        x, y = cx - layer.width / 2, cy - layer.height / 2
    canvas.alpha_composite(layer, (round(x), round(y))) if x >= 0 and y >= 0 else _paste_any(canvas, layer, round(x), round(y))

def _paste_any(canvas, layer, x, y):
    tmp = Image.new('RGBA', canvas.size); tmp.paste(layer, (x, y), layer); canvas.alpha_composite(tmp)

def render(xml, ctx, px_per_mm=8, show_placeholders=True, mark=False, transparent=False):
    root = etree.fromstring(xml.encode() if isinstance(xml, str) else xml)
    W, H = f(root, 'width'), f(root, 'height')
    S = px_per_mm
    cv = Image.new('RGBA', (round(W * S), round(H * S)), (0, 0, 0, 0) if transparent else ((col(root.get('bgcolor')) if root.get('bgcolor') not in (None,'','false') else None) or (255, 255, 255)))
    ph_i = 0
    kids = list(root)
    order = sorted(range(len(kids)), key=lambda i: (f(kids[i], 'z', 0), i))
    for i in order:
        e = kids[i]; tag = e.tag
        x, y, w, h = f(e, 'x') * S, f(e, 'y') * S, f(e, 'width') * S, f(e, 'height') * S
        rot = f(e, 'rotate')
        if w < 1 or h < 1: continue
        if tag == 'shape':
            c = col(e.get('color'), '#000000')
            lay = Image.new('RGBA', (round(w), round(h)))
            d = ImageDraw.Draw(lay)
            if e.get('kind') == 'ellipse': d.ellipse((0, 0, lay.width - 1, lay.height - 1), fill=c)
            else: d.rectangle((0, 0, lay.width, lay.height), fill=c)
            paste_rot(cv, lay, x, y, rot)
        elif tag == 'image':
            is_ph = e.get('placeholder') == 'true'
            if is_ph:
                if not show_placeholders: continue
                own = ctx.img(e.get('src', '')) if getattr(ctx, 'real', False) and e.get('src') else None
                if own is None:
                    if not ctx.samples: continue
                    own = ctx.samples[ph_i % len(ctx.samples)]; ph_i += 1
                lay = cover(own.convert('RGBA'), round(w), round(h))
            else:
                im = ctx.img(e.get('src', ''))
                if im is None: continue
                lay = im.resize((round(w), round(h)), Image.LANCZOS) if e.get('crop') == 'false' or e.get('stretch') == 'true' else cover(im, round(w), round(h))
            rad = f(e, 'radius') * S
            if rad > 0:
                r = min(rad, lay.width / 2, lay.height / 2)
                m = Image.new('L', lay.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, lay.width - 1, lay.height - 1), radius=r, fill=255)
                from PIL import ImageChops
                lay.putalpha(ImageChops.multiply(lay.getchannel('A'), m))
            mk = e.get('mask')
            if mk and mk.startswith('db:'):
                m = ctx.img(mk)
                if m is not None:
                    m = m.resize(lay.size, Image.LANCZOS)
                    ma = m.getchannel('A') if m.getchannel('A').getextrema()[0] < 250 else m.convert('L')
                    from PIL import ImageChops
                    lay.putalpha(ImageChops.multiply(lay.getchannel('A'), ma))
            op = f(e, 'opacity', 1.0)
            if 0 <= op < 1:
                lay.putalpha(lay.getchannel('A').point(lambda v: round(v * op)))
            bw = f(e, 'border') * S
            if bw > 0 and e.get('border') != 'false':
                d = ImageDraw.Draw(lay); bc = col(e.get('bordercolor'), '#FFFFFF')
                for k in range(round(bw)): d.rectangle((k, k, lay.width - 1 - k, lay.height - 1 - k), outline=bc)
            paste_rot(cv, lay, x, y, rot)
            if mark and is_ph:
                d = ImageDraw.Draw(cv); d.rectangle((x, y, x + w, y + h), outline=(255, 0, 160), width=2)
        elif tag == 'text':
            draw_text(cv, e, ctx, x, y, w, h, S, rot)
    return cv

def draw_text(cv, e, ctx, x, y, w, h, S, rot):
    path = ctx.fonts.get(e.get('font', ''))
    size = f(e, 'fontsize', 4.233) * S
    txt = ''.join(e.itertext())
    if e.get('caps') == 'true': txt = txt.upper()
    paras = txt.rstrip('\n').split('\n')
    color = col(e.get('color'), '#000000')
    kern = f(e, 'kerning') * S
    lead = f(e, 'leading', 0)
    def font(sz):
        try: return ImageFont.truetype(path, max(1, round(sz))) if path else ImageFont.load_default(max(1, round(sz)))
        except Exception: return ImageFont.load_default(max(1, round(sz)))
    def lwid(ft, ln): return sum(ft.getlength(ch) for ch in ln) + kern * max(0, len(ln) - 1)
    def wrap(ft):
        out = []
        for p in paras:
            cur = ''
            for wd in p.split(' '):
                t = (cur + ' ' + wd) if cur else wd
                if cur and lwid(ft, t) > w and e.get('shrink') != 'true': out.append(cur); cur = wd
                else: cur = t
            out.append(cur)
        return out
    def measure(ft, sz):
        ls = wrap(ft)
        lh = sz * (1.2 + lead / 100.0) if lead else sz * 1.2
        return ls, [lwid(ft, l) for l in ls], lh
    sz = size; ft = font(sz); lines, lw, lh = measure(ft, sz)
    if e.get('shrink') == 'true':
        n = 0
        while (max(lw) > w + 1 or lh * len(lines) > h + 1) and n < 40:
            sz *= 0.95; ft = font(sz); lines, lw, lh = measure(ft, sz); n += 1
    lay = Image.new('RGBA', (max(1, round(w)), max(1, round(h))))
    d = ImageDraw.Draw(lay)
    tot = lh * len(lines)
    va = e.get('valign', 'top')
    y0 = (h - tot) / 2 if va == 'center' else (h - tot if va == 'bottom' else 0)
    al = e.get('align', 'left')
    asc, desc = ft.getmetrics()
    for k, ln in enumerate(lines):
        lx = (w - lw[k]) / 2 if al == 'center' else (w - lw[k] if al == 'right' else 0)
        ly = y0 + k * lh + (lh - (asc + desc)) / 2
        cx = lx
        for ch in ln:
            d.text((cx, ly), ch, font=ft, fill=color); cx += ft.getlength(ch) + kern
    paste_rot(cv, lay, x, y, rot)

#!/usr/bin/env python3
"""Build a full size range of Pixfizz templates from one seed export.

    python3 build_range.py config.json

Config (see config.example.json). Every geometric value is derived; every commercial
value comes from the config. Nothing is guessed.

Proven on: 5x7 layflat album -> 5 sizes; canvas 12x12 -> 62; canvas 8x8 -> 62.
"""
import re, os, io, sys, json, shutil, yaml

MM = 25.4

# ------------------------------------------------------------------ helpers
def fmt(v):
    if abs(v) < 1e-9: v = 0.0
    s = f"{v:.12f}".rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'

def cover(bw, bh, xw, xh): return max(bw / xw, bh / xh)

def zoom(bw, bh, Vw, Vh, Pw, Ph):
    """crop="true" is cover, not fit. See references/geometry.md section 2."""
    return (cover(bw, bh, Vw, Vh) / cover(bw, bh, Pw, Ph) - 1) * 100

def find_scalar(lines, i):
    m = re.match(r'^(\s*)([A-Za-z_]+): ?(.*)$', lines[i])
    indent, key, rest = m.group(1), m.group(2), m.group(3)
    j = i + 1
    while j < len(lines):
        if lines[j].strip() == '': j += 1; continue
        if len(lines[j]) - len(lines[j].lstrip()) > len(indent): j += 1
        else: break
    while j - 1 > i and lines[j - 1].strip() == '': j -= 1
    block = '\n'.join(l[len(indent):] if len(l) > len(indent) else l.strip()
                      for l in lines[i:j])
    style = rest.strip() if rest.strip() in ('|', '|-') else 'plain'
    return indent, key, style, yaml.safe_load(io.StringIO(block))[key], j

def emit(indent, key, style, value):
    st = style if style in ('|', '|-') else '|-'
    body = value[:-1] if (st == '|' and value.endswith('\n')) else value
    return [f'{indent}{key}: {st}'] + [f'{indent}  {l}' if l else '' for l in body.split('\n')]

def setattrs(tag, **kw):
    """Rewrite attribute values in place. Zero x/y are removed, never written."""
    for k, v in kw.items():
        s = fmt(v) if isinstance(v, float) else str(v)
        present = re.search(rf'\b{k}="[^"]*"', tag)
        if k in ('x', 'y') and isinstance(v, float) and abs(v) < 1e-12:
            if present: tag = re.sub(rf'\s*\b{k}="[^"]*"', '', tag)
            continue
        if present: tag = re.sub(rf'\b{k}="[^"]*"', f'{k}="{s}"', tag)
        elif tag.endswith('/>'): tag = tag[:-2].rstrip() + f' {k}="{s}"' + '/>'
    return tag


class Range:
    def __init__(self, cfg):
        self.c = cfg
        self.seed_dir = cfg['seed_dir']
        self.src = open(os.path.join(self.seed_dir, '__print_product.yml')).read()
        doc = yaml.safe_load(re.sub(r'!ruby/object:\S+', '', self.src))
        self.protected = set()
        for mp in ('__image_map', '__asset_map', '__font_map', '__pdf_map'):
            self.protected |= set(int(k) for k in (doc.get(mp) or {}))
        self.b = cfg['bleed']; self.m = cfg['mirror']
        self.PG = cfg.get('preview_page_mm', 254.0)
        self.WIN = cfg.get('window_mm', 228.6)
        self.marg = cfg.get('page_margin_mm', 6.0)
        self.scenes = {}
        for k, s in cfg['scenes'].items():
            line = cfg['furniture_line'] * s['scene_mm'] + s['offset_y_mm']
            self.scenes[k] = dict(s, maxh=2 * min(s['centre_y'] - self.marg, line - s['centre_y']),
                                  maxw=2 * (self.PG / 2 - self.marg))

    # -------- scene placement
    def scene_box(self, key, W, H):
        p = self.scenes[key]; s = p['mm_per_inch']
        fit = min(1.0, p['maxw'] / (W * s), p['maxh'] / (H * s))
        return W * s * fit, H * s * fit, self.PG / 2, p['centre_y'], fit

    def pick_page(self, W, H):
        for key in self.c['scene_preference']:
            if self.scene_box(key, W, H)[4] >= 1.0: return key, 1.0
        last = self.c['scene_preference'][-1]
        return last, self.scene_box(last, W, H)[4]

    # -------- page rewriting
    def rewrite(self, nm, xml, W, H):
        b, m = self.b, self.m
        Pw, Ph = (W + 2*b) * MM, (H + 2*b) * MM
        Vw, Vh = W * MM, H * MM
        Iw, Ih = (W + 2*m) * MM, (H + 2*m) * MM
        ins = (b - m) * MM

        if nm in self.c['production_pages']:
            xml = re.sub(r'(<page\b[^>]*?)\bwidth="[^"]*"',  rf'\1width="{fmt(Pw)}"',  xml)
            xml = re.sub(r'(<page\b[^>]*?)\bheight="[^"]*"', rf'\1height="{fmt(Ph)}"', xml)
            def img(mo):
                t = mo.group(0)
                if nm == 'color':
                    return setattrs(t, width=Vw, height=Vh, x=b*MM, y=b*MM)
                return setattrs(t, width=Iw, height=Ih, x=ins, y=ins,
                                **({'borderwrap': m*MM} if nm == 'mirror' else {}))
            return re.sub(r'<image\b[^>]*/>', img, xml)

        ips = list(re.finditer(r'<ipage\b[^>]*/>', xml))
        if not ips: return xml

        if nm in self.scenes:
            bw, bh, cx, cy, _ = self.scene_box(nm, W, H)
            new = setattrs(ips[0].group(0), width=bw, height=bh,
                           x=cx - bw/2, y=cy - bh/2, zoom=zoom(bw, bh, Vw, Vh, Pw, Ph))
            return xml[:ips[0].start()] + new + xml[ips[0].end():]

        if nm == self.c.get('clean_preview'):
            s = min(self.WIN / W, self.WIN / H); bw, bh = W * s, H * s
            new = setattrs(ips[0].group(0), width=bw, height=bh,
                           x=(self.PG-bw)/2, y=(self.PG-bh)/2, zoom=zoom(bw, bh, Vw, Vh, Pw, Ph))
            return xml[:ips[0].start()] + new + xml[ips[0].end():]

        if nm == self.c.get('full_preview'):
            s = min(self.WIN / (W + 2*b), self.WIN / (H + 2*b))
            ow, oh = (W + 2*b) * s, (H + 2*b) * s
            iw, ih = W * s, H * s
            ox, oy, ix, iy = (self.PG-ow)/2, (self.PG-oh)/2, (self.PG-iw)/2, (self.PG-ih)/2
            iz = zoom(iw, ih, Vw, Vh, Pw, Ph)
            out, off = xml, 0
            for k, mo in enumerate(ips):
                t = mo.group(0)
                new = (setattrs(t, width=ow, height=oh, x=ox, y=oy) if k == 0
                       else setattrs(t, width=iw, height=ih, x=ix, y=iy, zoom=iz))
                out = out[:mo.start()+off] + new + out[mo.end()+off:]; off += len(new) - len(t)
            sm = re.search(r'<shape\b[^>]*/>', out)
            if sm:
                new = setattrs(sm.group(0), width=ow, height=oh, x=ox, y=oy)
                out = out[:sm.start()] + new + out[sm.end():]
            inset = self.c.get('wrap_label_inset_mm', 12.7)
            edges = {None: ('y', oy+inset), '-180': ('y', oy+oh-inset),
                     '90': ('x', ox+ow-inset), '-90': ('x', ox+inset)}
            def lab(mo):
                t = mo.group(0)
                r = re.search(r'\brotate="([^"]+)"', t)
                axis, c = edges[r.group(1) if r else None]
                lw = float(re.search(r'\bwidth="([^"]+)"', t).group(1))
                lh = float(re.search(r'\bheight="([^"]+)"', t).group(1))
                return (setattrs(t, x=(self.PG-lw)/2, y=c-lh/2) if axis == 'y'
                        else setattrs(t, x=c-lw/2, y=(self.PG-lh)/2))
            return re.sub(r'<text\b[^>]*name="wrap"[^>]*>wrap</text>', lab, out)
        return xml

    # -------- one size
    def build(self, item, base):
        W, H = float(item['w']), float(item['h'])
        size = f'{W:g}x{H:g}'
        live, capfrac = self.pick_page(W, H)
        lines = self.src.split('\n')

        idmap, nxt = {}, (base or 0) + 1
        if base:
            for ln in lines:
                mo = re.match(r'^\s*(?:- )?id: (\d+)\s*$', ln)
                v = int(mo.group(1)) if mo else None
                if mo and v not in self.protected and v not in idmap:
                    idmap[v] = nxt; nxt += 1

        out, i, ctx = [], 0, None
        while i < len(lines):
            ln = lines[i]
            mo = re.match(r'^(\s*(?:- )?)id: (\d+)\s*$', ln)
            if mo and int(mo.group(2)) in idmap:
                out.append(f'{mo.group(1)}id: {idmap[int(mo.group(2))]}'); i += 1; continue
            mo = re.match(r'^\s*name: (\S.*)$', ln)
            if mo: ctx = mo.group(1).strip()
            if re.match(r'^\s*data: ', ln):
                ind, key, style, val, j = find_scalar(lines, i)
                val = re.sub(r'layout_id="(\d+)"',
                             lambda x: f'layout_id="{idmap[int(x.group(1))]}"'
                             if int(x.group(1)) in idmap else x.group(0), val)
                out.extend(emit(ind, key, style, self.rewrite(ctx, val, W, H))); i = j; continue
            mo = re.match(r'^(\s+)preview: (?:true|false)\s*$', ln)
            if mo and ctx in self.scenes:
                out.append(f'{mo.group(1)}preview: {"true" if ctx == live else "false"}')
                i += 1; continue
            if re.match(r'^layout: ', ln):
                ind, key, style, val, j = find_scalar(lines, i)
                val = re.sub(self.c['definition_page_pattern'],
                             lambda x: x.group(1) + f'width="{W+2*self.b:g}" height="{H+2*self.b:g}"',
                             val)
                for a, bb in self.c.get('definition_replacements', {}).items():
                    val = val.replace(a, bb)
                out.append('layout: ' + json.dumps(val)); i = j; continue
            out.append(ln); i += 1

        t = '\n'.join(out)

        # repair the layout_id the importer leaves dangling (see references/import-behaviour.md)
        d = yaml.safe_load(re.sub(r'!ruby/object:\S+', '', t))
        target = self.c.get('production_page_layout', 'gallery')
        gal = [l['id'] for l in d['print_themes'][0]['layouts'] if l['name'] == target]
        cur = re.search(r'layout_id="(\d+)"', t)
        if gal and cur and int(cur.group(1)) != gal[0]:
            t = t.replace(f'layout_id="{cur.group(1)}"', f'layout_id="{gal[0]}"')

        for a, bb in self.c['literal_replacements'].items():
            t = t.replace(a, bb.format(size=size, name=item['name'], W=f'{W:g}', H=f'{H:g}'))
        for pat, rep in self.c['regex_replacements'].items():
            t = re.sub(pat, rep.format(size=size, name=item['name'],
                                       W=f'{W:g}', H=f'{H:g}',
                                       orientation=item['orientation'],
                                       price=f"{item['price']:.2f}"), t, flags=re.M)
        for seed_lit, val in (item.get('variant_prices') or {}).items():
            n = len(re.findall(rf"^\s*price: '{re.escape(seed_lit)}'$", t, flags=re.M))
            if n != item.get('variant_price_count', {}).get(seed_lit, n):
                raise SystemExit(f'{size}: expected '
                                 f'{item["variant_price_count"][seed_lit]} price lines for '
                                 f'{seed_lit}, found {n}')
            t = re.sub(rf"^(\s*)price: '{re.escape(seed_lit)}'$",
                       rf"\1price: '{float(val):.2f}'", t, flags=re.M)
        return t, live, capfrac, len(idmap)


def main(path):
    cfg = json.load(open(path))
    r = Range(cfg)
    out = cfg['out_dir']
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    manifest = []
    for n, item in enumerate(cfg['sizes']):
        W, H = float(item['w']), float(item['h'])
        size = f'{W:g}x{H:g}'
        seedrow = item.get('in_place', False)
        base = None if seedrow else cfg['id_block_base'] + n * cfg.get('id_block_step', 1_000_000)
        text, live, capfrac, nid = r.build(item, base)
        d = os.path.join(out, size)
        for sub in cfg.get('copy_dirs', []):
            src = os.path.join(r.seed_dir, sub)
            if os.path.isdir(src): shutil.copytree(src, os.path.join(d, sub))
        for sub in cfg.get('empty_dirs', []):
            os.makedirs(os.path.join(d, sub), exist_ok=True)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, '__print_product.yml'), 'w').write(text)
        bw, bh, _, _, _ = r.scene_box(live, W, H)
        manifest.append(dict(name=item['name'], size=size, orientation=item['orientation'],
                             price=item['price'], artboard=f'{W+2*r.b:g} x {H+2*r.b:g} in',
                             live_preview=live, wall_scale_pct=round(capfrac*100, 1),
                             box=f'{bw:.2f} x {bh:.2f} mm', ids=nid, in_place=seedrow,
                             variant_prices=item.get('variant_prices')))
    json.dump(manifest, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    cap = [m for m in manifest if m['wall_scale_pct'] < 100]
    print(f'{len(manifest)} templates built into {out}')
    for k in cfg['scene_preference']:
        got = [m['size'] for m in manifest if m['live_preview'] == k]
        print(f'  live preview {k:20} {len(got):3}')
    if cap:
        print(f'  wall scale reduced: {[(m["size"], m["wall_scale_pct"]) for m in cap]}')
    inp = [m['size'] for m in manifest if m['in_place']]
    if inp: print(f'  in-place (source ids kept): {inp}')

if __name__ == '__main__':
    main(sys.argv[1])

#!/usr/bin/env python3
"""Verify a built range. Zero failures or it does not ship.

    python3 verify_range.py config.json

Implements references/verification.md. On real runs this has caught a dangling
layout_id, an id filter scoped by magnitude instead of by the media maps, and a
code-uniqueness assumption that was wrong.
"""
import re, os, sys, json, yaml

MM = 25.4

def load(p): return yaml.safe_load(re.sub(r'!ruby/object:\S+', '', open(p).read()))
def A(t, n, d=None):
    m = re.search(rf'\b{n}="([^"]*)"', t)
    return float(m.group(1)) if m else d
def cover(bw, bh, xw, xh): return max(bw / xw, bh / xh)

def main(path):
    cfg = json.load(open(path))
    seed = load(os.path.join(cfg['seed_dir'], '__print_product.yml'))
    out, marg = cfg['out_dir'], cfg.get('page_margin_mm', 6.0)
    PG = cfg.get('preview_page_mm', 254.0)
    b, m = cfg['bleed'], cfg['mirror']
    scenes = {}
    for k, s in cfg['scenes'].items():
        line = cfg['furniture_line'] * s['scene_mm'] + s['offset_y_mm']
        scenes[k] = dict(s, maxh=2*min(s['centre_y']-marg, line-s['centre_y']),
                         maxw=2*(PG/2-marg))
    fails, codes, allids = [], {}, {}
    def chk(c, msg):
        if not c: fails.append(msg)

    for item in cfg['sizes']:
        W, H = float(item['w']), float(item['h'])
        size = f'{W:g}x{H:g}'
        doc = load(os.path.join(out, size, '__print_product.yml'))
        Pw, Ph = (W+2*b)*MM, (H+2*b)*MM
        Vw, Vh = W*MM, H*MM
        Iw, Ih = (W+2*m)*MM, (H+2*m)*MM
        ins = (b-m)*MM
        th = doc['print_themes'][0]
        pr = doc['products'][0]
        lay = {l['name']: l['data'] for l in th['layouts']}
        tpl = {t['name']: t for t in th['templates']}

        # ---- definition
        d = doc['layout']
        chk(f'width="{W+2*b:g}" height="{H+2*b:g}"' in d, f'{size}: definition page')
        for frag in cfg.get('definition_must_contain', []):
            chk(frag in d, f'{size}: definition lost {frag!r}')

        # ---- commerce
        for field, want in (item.get('expect') or {}).items():
            got = doc
            for part in field.split('.'):
                got = got[int(part)] if part.isdigit() else got[part]
            chk(got == want, f'{size}: {field} is {got!r}, expected {want!r}')
        chk(pr['price'] == f"{item['price']:.2f}", f'{size}: price {pr["price"]}')
        chk(th['design_options'][0]['crop_aspect_ratio'] == f'{W:g}in/{H:g}in',
            f'{size}: crop_aspect_ratio')

        # ---- layouts
        model = {'gallery': (Iw, Ih, ins, ins, None),
                 'mirror':  (Iw, Ih, ins, ins, m*MM),
                 'color':   (Vw, Vh, b*MM, b*MM, None)}
        for nm, (ew, eh, ex, ey, bw_) in model.items():
            if nm not in lay: continue
            x = lay[nm]
            pt = re.search(r'<page\b[^>]*>', x).group(0)
            chk(abs(A(pt, 'width')-Pw) < 1e-9 and abs(A(pt, 'height')-Ph) < 1e-9,
                f'{size}/{nm}: page size')
            it = re.search(r'<image\b[^>]*/>', x).group(0)
            for k, v in (('width', ew), ('height', eh), ('x', ex), ('y', ey)):
                chk(abs(A(it, k, 0)-v) < 1e-9, f'{size}/{nm}: {k}')
            chk(abs(A(it, 'borderwrap', 0)-(bw_ or 0)) < 1e-9, f'{size}/{nm}: borderwrap')
            if bw_: chk(abs(A(it, 'width')-2*A(it, 'borderwrap')-Vw) < 1e-9,
                        f'{size}/{nm}: print-area identity')
            if abs(ex) < 1e-12:
                chk(A(it, 'x') is None and A(it, 'y') is None,
                    f'{size}/{nm}: zero x/y should be omitted')

        # ---- production page in sync with its layout
        prod = cfg.get('production_page')
        if prod and prod in tpl:
            f = lambda s: [tuple(re.findall(r'\b(?:x|y|width|height|borderwrap)="([^"]+)"', e))
                           for e in re.findall(r'<image\b[^>]*/>', s)]
            tgt = cfg.get('production_page_layout', 'gallery')
            chk(f(tpl[prod]['data']) == f(lay[tgt]),
                f'{size}: {prod} page out of sync with {tgt} layout')
            lid = re.search(r'layout_id="(\d+)"', tpl[prod]['data'])
            if lid:
                chk(int(lid.group(1)) in [l['id'] for l in th['layouts']],
                    f'{size}: dangling layout_id {lid.group(1)}')

        # ---- ipages
        for nm, t in tpl.items():
            for mo in re.finditer(r'<ipage\b[^>]*/>', t['data'] or ''):
                g = mo.group(0)
                bw, bh, z = A(g, 'width'), A(g, 'height'), A(g, 'zoom')
                chk(A(g, 'left', 0) == 0 and A(g, 'top', 0) == 0, f'{size}/{nm}: left/top')
                tgt = (Pw/Ph) if z is None else (Vw/Vh)
                chk(abs(bw/bh - tgt) < 1e-9, f'{size}/{nm}: ipage aspect')
                if z is not None:
                    exp = (cover(bw, bh, Vw, Vh)/cover(bw, bh, Pw, Ph) - 1)*100
                    chk(abs(z-exp) < 1e-9, f'{size}/{nm}: zoom {z} != {exp}')
                x, y = A(g, 'x', 0), A(g, 'y', 0)
                chk(x >= -1e-9 and y >= -1e-9 and x+bw <= PG+1e-9 and y+bh <= PG+1e-9,
                    f'{size}/{nm}: ipage off the preview page')
                if nm in scenes:
                    p = scenes[nm]
                    chk(bw <= p['maxw']+1e-9 and bh <= p['maxh']+1e-9,
                        f'{size}/{nm}: box exceeds usable wall')
                    chk(abs(x+bw/2-PG/2) < 1e-9 and abs(y+bh/2-p['centre_y']) < 1e-9,
                        f'{size}/{nm}: box centre moved')
        live = [n for n in scenes if tpl.get(n, {}).get('preview')]
        chk(len(live) == 1, f'{size}: {len(live)} live room-scene previews')
        fp = cfg.get('full_preview')
        if fp and fp in tpl:
            ip = re.findall(r'<ipage\b[^>]*/>', tpl[fp]['data'])
            if len(ip) >= 2:
                chk(abs(A(ip[1], 'width') - A(ip[0], 'width')*Vw/Pw) < 1e-9,
                    f'{size}: {fp} inner box')
            sh = re.search(r'<shape\b[^>]*/>', tpl[fp]['data'])
            if sh:
                chk(abs(A(sh.group(0), 'width')-A(ip[0], 'width')) < 1e-9,
                    f'{size}: {fp} shape vs outer ipage')

        # ---- variants
        vts = {v['code']: v for v in pr['variant_types']}
        spec = cfg.get('variants') or {}
        if spec:
            chk(set(vts) == set(spec), f'{size}: variant types {sorted(vts)}')
            laynames = {l['name'] for l in th['layouts']}
            for vcode, vspec in spec.items():
                if vcode not in vts: continue
                vt = vts[vcode]
                chk([v['code'] for v in vt['variant_values']] == vspec['values'],
                    f'{size}: {vcode} value codes')
                chk(sum(1 for v in vt['variant_values'] if v['default']) == 1,
                    f'{size}: {vcode} default count')
                chk(vt['required'] and vt['published'], f'{size}: {vcode} not required/published')
                for v in vt['variant_values']:
                    for es in v['element_substitutions']:
                        if es['substitution_type'] == 'layout':
                            chk(es['content'] in laynames,
                                f'{size}: {v["code"]} -> missing layout {es["content"]!r}')
                    want = vspec.get('prices', {}).get(v['code'])
                    if want == '@uplift':
                        u = list((item.get('variant_prices') or {}).values())[0]
                        chk(v['price'] == f'{float(u):.2f}',
                            f'{size}: {v["code"]} uplift {v["price"]!r}')
                    elif want is not None:
                        chk(v['price'] == want, f'{size}: {v["code"]} price {v["price"]!r}')

        # ---- ids and codes
        prot = set(int(k) for mp in ('__image_map', '__asset_map', '__font_map')
                   for k in (doc.get(mp) or {}))
        ids = []
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == 'id' and isinstance(v, int): ids.append(v)
                    walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk({k: v for k, v in doc.items() if not k.startswith('__')})
        new = [i for i in ids if i not in prot]
        chk(len(new) == len(set(new)), f'{size}: duplicate ids')
        chk(all(i < 2**31 - 1 for i in new), f'{size}: id over int32')
        if not item.get('in_place'):
            chk(all(i > 1_000_000_000 for i in new), f'{size}: id not renumbered')
        for i in new:
            if i in allids: fails.append(f'id {i} collides: {allids[i]} and {size}')
            allids[i] = size
        chk(doc['code'] == pr['code'], f'{size}: template/product code differ')
        for c in (doc['code'], th['code']):
            if c in codes: fails.append(f'code {c} used by both {codes[c]} and {size}')
            codes[c] = size

        # ---- structural parity
        scrub_keys = set(cfg.get('scrub_keys',
            ['id', 'data', 'layout', 'name', 'code', 'custom', 'category',
             'crop_aspect_ratio', 'price', 'preview']))
        def scrub(o):
            if isinstance(o, dict):
                return {k: ('' if k in scrub_keys else scrub(v)) for k, v in o.items()}
            if isinstance(o, list): return [scrub(v) for v in o]
            return o
        chk(scrub(seed) == scrub(doc), f'{size}: structural drift vs seed')

    print('\n'.join(fails[:60]) if fails else 'ALL CHECKS PASSED')
    print(f'{len(fails)} failures across {len(cfg["sizes"])} templates, '
          f'{len(allids)} distinct ids')
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))

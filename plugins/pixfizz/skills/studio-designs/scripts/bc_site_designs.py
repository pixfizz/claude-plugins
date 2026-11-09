#!/usr/bin/env python3
"""Pixfizz studio-designs: build a Business Cards "site designs" file (Business Cards 3.5.0 and later) from checked layouts.

  python3 bc_site_designs.py --trim 88.9x50.8 --bleed 3.175 --safe 3.175 --tag abc --out <dir> <layout dir> [<layout dir> ...]

One layout per card design, from extract.py, with pages named front and (optionally) back, each the trim plus bleed on every
side. In the layout:
  - photo windows: at most one per side, named photo (the customer adds one photo per card). A window named logo is the
    logo slot instead (the customer's logo, an icon, or nothing).
  - text lines: every line becomes a field the customer types into; set "label" on a text for the field label
    (default: the element name), and "fixed": true for words that are part of the design.
  - fonts: every font needs "file" (TTF or OTF, for measuring) and "google": "Family:weight" (the card tool loads
    Google Fonts only), for example "Lora:400".
  - optional per layout: "industry" (the picker group) and "blurb" (one line under the name).

Writes into <out>: business-cards-designs-<tag>.json and one WebP per design side (<tag>-<code>-f.webp, -b.webp).
Upload every file to the site's Assets, then set on the business card template's px_mount:
  bc_designs_more_file: 'business-cards-designs-<tag>.json'
  bc_designs_more_assets: '<every .webp name, separated by |>'
The script prints both lines. One file per card size: the tool refuses a file whose trim or bleed differs from the card.
"""
import argparse, json, os, re, sys
from PIL import Image, ImageFont

def die(m):
    sys.exit('STOP: ' + m)

def r3(v):
    return round(float(v), 3)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trim', required=True, help='WxH in mm, e.g. 88.9x50.8 (3.5 x 2 in)')
    ap.add_argument('--bleed', type=float, default=3.175); ap.add_argument('--safe', type=float, default=3.175)
    ap.add_argument('--tag', required=True); ap.add_argument('--out', required=True); ap.add_argument('layouts', nargs='+')
    a = ap.parse_args()
    TW, TH = (float(v) for v in a.trim.lower().split('x')); B = a.bleed
    if not re.fullmatch(r'[a-z0-9-]+', a.tag): die('tag: lowercase letters, digits and dashes')
    os.makedirs(a.out, exist_ok=True)
    designs, sprites, google, assets = [], {}, set(), []
    for ld in a.layouts:
        lp = ld if ld.endswith('.json') else os.path.join(ld, 'layout.json'); base = os.path.dirname(os.path.abspath(lp))
        L = json.load(open(lp, encoding='utf8'))
        pages = {p['name']: p for p in L['pages']}
        if 'front' not in pages: die('%s: no page named front' % lp)
        d = dict(code=L['code'], name=L['name'], ind=L.get('industry', 'Our designs'), blurb=L.get('blurb', ''))
        for side, key in (('front', 'f'), ('back', 'b')):
            p = pages.get(side)
            if not p:
                continue
            if abs(p['w'] - (TW + 2 * B)) > 0.6 or abs(p['h'] - (TH + 2 * B)) > 0.6:
                die('%s %s is %.2f x %.2f mm; this card is %.2f x %.2f mm with bleed' % (L['code'], side, p['w'], p['h'], TW + 2 * B, TH + 2 * B))
            art = Image.open(os.path.join(base, p['art'])).convert('RGBA')
            k = art.width / p['w']
            px = round((TW + 2 * B) * 300 / 25.4); art = art.resize((px, round(px * art.height / art.width)), Image.LANCZOS)
            sk = '%s-%s-%s' % (a.tag, L['code'], key); fn = sk + '.webp'
            art.save(os.path.join(a.out, fn), 'WEBP', quality=88, method=6); sprites[sk] = fn; assets.append(fn)
            img = '<image href="px:%s" x="%s" y="%s" width="%s" height="%s" preserveAspectRatio="none"/>' % (sk, r3(-B), r3(-B), r3(TW + 2 * B), r3(TH + 2 * B))
            sd = {}
            photos = [w for w in p['photos'] if w['name'] != 'logo']; logos = [w for w in p['photos'] if w['name'] == 'logo']
            if len(photos) > 1: die('%s %s: %d photo windows; a business card takes one photo per card' % (L['code'], side, len(photos)))
            if len(logos) > 1: die('%s %s: more than one logo window' % (L['code'], side))
            if photos:
                w = photos[0]
                sd['art'] = '<rect x="%s" y="%s" width="%s" height="%s" fill="#FFFFFF"/>' % (r3(-B), r3(-B), r3(TW + 2 * B), r3(TH + 2 * B))
                sd['ph'] = dict(x=r3(w['x'] - B), y=r3(w['y'] - B), w=r3(w['w']), h=r3(w['h']), sh='r', req=1, lab='Your photo')
                sd['ov'] = img
            else:
                sd['art'] = img
            if logos:
                w = logos[0]; sd['lg'] = dict(x=r3(w['x'] - B), y=r3(w['y'] - B), w=r3(w['w']), h=r3(w['h']), c=w.get('color', '#333333'), smp=1)
            txt = []
            for t in p['texts']:
                f = L['fonts'].get(t['font']) or {}
                if not f.get('file') or not f.get('google'):
                    die('font %s needs "file" and "google" ("Family:weight") in %s' % (t['font'], lp))
                fam, _, wt = f['google'].partition(':'); wt = int(wt or 400); google.add('%s:%d' % (fam, wt))
                fp = f['file'] if os.path.isabs(f['file']) else os.path.join(base, f['file'])
                size = t['size']; ink = t['ink']
                ft = ImageFont.truetype(fp, 400)
                bb = ft.getbbox(t['text'], anchor='ls')           # ink box relative to the baseline, at 400 px
                below = bb[3] / 400 * size                        # ink below the baseline, mm
                baseline = ink['y'] + ink['h'] - below
                y = baseline - size * 0.9                         # the tool: baseline = y + s * ((lh - 1) / 2 + 0.8), lh 1.2
                w = min(ink['w'] * 1.35, TW - 2 * a.safe)
                al = {'left': 'l', 'center': 'c', 'right': 'r'}[t['align']]
                x = ink['x'] if al == 'l' else ink['x'] + ink['w'] / 2 - w / 2 if al == 'c' else ink['x'] + ink['w'] - w
                x = max(B + a.safe, min(x, B + TW - a.safe - w))
                row = dict(x=r3(x - B), y=r3(y - B), w=r3(w), t=t['text'], f=fam, wt=wt, st='italic' if 'italic' in t['font'].lower() else 'normal',
                           s=round(size, 4), c=t['color'], a=al, lh=1.2, fit=1, lab=t.get('label') or t['name'])
                ls = t.get('kerning_pt', 0) / (size * 2.8346) if size else 0
                if abs(ls) > 0.001: row['ls'] = round(ls, 4)
                if t.get('fixed'): row['fx'] = 1
                txt.append(row)
            sd['txt'] = txt
            d[key] = sd
        if 'b' not in d:
            d['b'] = dict(art='<rect x="%s" y="%s" width="%s" height="%s" fill="#FFFFFF"/>' % (r3(-B), r3(-B), r3(TW + 2 * B), r3(TH + 2 * B)), txt=[])
        designs.append(d)
    fams = {}
    for g in google:
        fam, wt = g.split(':'); fams.setdefault(fam, set()).add(int(wt))
    fonts = [fam if ws == {400} else '%s:%s' % (fam, ','.join(str(w) for w in sorted(ws))) for fam, ws in sorted(fams.items())]
    out = dict(TW=TW, TH=TH, B=B, SAFE=a.safe, fonts=fonts, sprites=sprites, designs=designs)
    name = 'business-cards-designs-%s.json' % a.tag
    json.dump(out, open(os.path.join(a.out, name), 'w'), ensure_ascii=False, separators=(',', ':'))
    print('wrote', name, 'with', len(designs), 'designs and', len(assets), 'images')
    print("bc_designs_more_file: '%s'" % name)
    print("bc_designs_more_assets: '%s'" % '|'.join(assets))

if __name__ == '__main__':
    main()

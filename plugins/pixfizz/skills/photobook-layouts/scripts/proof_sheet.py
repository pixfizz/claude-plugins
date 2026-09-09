#!/usr/bin/env python3
"""Render a proof sheet of every layout in a design-theme export.

    python3 proof_sheet.py --in filled.tar.gz --out proof.png [--compare before.tar.gz]

Renders from the archive's own XML, never from the spec that generated it - so
it shows what will actually import. With --compare, layouts that already existed
in the earlier archive are drawn in blue and the new ones in grey.
"""
import argparse
import os
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pxload                                  # noqa: E402
from PIL import Image, ImageDraw, ImageFont    # noqa: E402

ORDER = ["1 photo", "2 photos", "3 photos", "4 photos", "5+ photos"]


def load(path):
    d = tempfile.mkdtemp()
    with tarfile.open(path) as t:
        t.extractall(d)
    return pxload.load(os.path.join(d, "__print_theme.yml"))


def font(sz, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf",
              "/System/Library/Fonts/Supplemental/DejaVuSans%s.ttf"):
        try:
            return ImageFont.truetype(p % ("-Bold" if bold else ""), sz)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", default="proof.png")
    ap.add_argument("--compare", help="earlier archive; its layouts are drawn in blue")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--tile", type=int, default=200)
    a = ap.parse_args()

    doc = load(a.src)
    old = set()
    if a.compare:
        old = {l["id"] for l in load(a.compare).get("layouts", [])
               if "<image" in (l.get("data") or "")}

    items = []
    for l in doc.get("layouts", []):
        if not l.get("layout"):
            continue
        root = ET.fromstring(l["data"])
        fr = [(float(e.get("x", 0)), float(e.get("y", 0)),
               float(e.get("width")), float(e.get("height")))
              for e in root if e.tag == "image"]
        items.append((l, fr, float(root.get("width")), float(root.get("height")),
                      l["id"] in old))
    if not items:
        sys.exit("no layouts in this archive")
    items.sort(key=lambda t: (ORDER.index((t[0].get("tags") or ["5+ photos"])[0])
                              if (t[0].get("tags") or ["5+ photos"])[0] in ORDER else 99,
                              not t[4]))

    S, GAP, LBL, MARG = a.tile, 32, 34, 30
    PW = max(t[2] for t in items); PH = max(t[3] for t in items)
    tw, th = (S, int(S * PH / PW)) if PW >= PH else (int(S * PW / PH), S)
    cols = a.cols
    rows = (len(items) + cols - 1) // cols
    W = MARG * 2 + cols * tw + (cols - 1) * GAP
    H = MARG + 46 + rows * (th + LBL + GAP)
    img = Image.new("RGB", (W, H), "#f4f4f4")
    d = ImageDraw.Draw(img)
    f, fb, fh = font(11), font(12, True), font(16, True)
    name = doc.get("name", "theme")
    d.text((MARG, 18), f"{name} - {len(items)} layouts - page "
                       f"{PW:g} x {PH:g} mm", fill="#111", font=fh)

    for i, (l, fr, pw, ph, isold) in enumerate(items):
        c, r = i % cols, i // cols
        ox = MARG + c * (tw + GAP); oy = MARG + 46 + r * (th + LBL + GAP)
        d.rectangle([ox - 1, oy - 1, ox + tw + 1, oy + th + 1],
                    fill="#fff", outline="#c0c0c0")
        fill, edge = ("#cddcf0", "#4a76b8") if isold else ("#c6c6c6", "#5f5f5f")
        kx, ky = tw / pw, th / ph
        for (x, y, w, h) in fr:
            d.rectangle([ox + x * kx, oy + y * ky,
                         ox + (x + w) * kx - 1, oy + (y + h) * ky - 1],
                        fill=fill, outline=edge)
        tag = (l.get("tags") or ["untagged"])[0]
        d.text((ox, oy + th + 6), f"#{l.get('number','?')}  {tag}",
               fill="#4a76b8" if isold else "#111", font=fb)
        d.text((ox, oy + th + 20),
               f"{len(fr)} frame{'s' if len(fr) != 1 else ''}"
               + ("  (pre-existing)" if isold else ""), fill="#777", font=f)
    img.save(a.out)
    print(f"wrote {a.out}  ({img.size[0]}x{img.size[1]}, {len(items)} tiles)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
proof_layouts.py THEME.yml OUT.png [--safe 6.35] [--title T] [--theme CODE]
                 [--compare ORIG.yml --src WxH]

Renders every layout so a wrong grid assumption is visible. The numeric checks in
verify_layouts.py pass happily on a self-consistently wrong grid; this is what
catches it. Always look at the sheet before shipping.

With --compare, renders source and result side by side and tints any frame whose
aspect changed.
"""
import sys, argparse
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import pxgeom as G
import pxload
from PIL import Image, ImageDraw, ImageFont

FILL = {"image": ("#bcbcbc", "#8f8f8f"), "text": ("#cfe0f5", "#6f9ad1"),
        "background": ("#efe6d8", "#c0ab8c"), "clipart": ("#dfe9d8", "#94b183"),
        "shape": ("#f0dede", "#c08f8f"), "ipage": ("#e6d9f2", "#9b7cc0")}
DISTORT = ("#e9b7b7", "#c08f8f")


def layouts_of(path, theme=None):
    d = pxload.load(path)
    if "layouts" in d and theme is None:
        return d["layouts"]
    for th in d.get("print_themes", []):
        if (theme is None or th["code"] == theme) and th.get("layouts"):
            return th["layouts"]
    sys.exit("no layouts found in %s" % path)


def fonts():
    try:
        p = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
        return (ImageFont.truetype(p + ".ttf", 15), ImageFont.truetype(p + "-Bold.ttf", 15),
                ImageFont.truetype(p + "-Bold.ttf", 22))
    except Exception:
        f = ImageFont.load_default(); return f, f, f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("theme_yml"); ap.add_argument("out")
    ap.add_argument("--safe", type=float, default=6.35)
    ap.add_argument("--title", default=""); ap.add_argument("--theme")
    ap.add_argument("--compare"); ap.add_argument("--src")
    a = ap.parse_args()

    L = layouts_of(a.theme_yml, a.theme)
    W, H = G.page_dims(L[0]["data"])
    cmpL = layouts_of(a.compare, a.theme) if a.compare else None
    SW, SH = (float(v) for v in a.src.lower().split("x")) if a.src else (W, H)

    PX = min(2.0, 1100.0 / max(W, SW))
    COLS = 1 if cmpL else 3
    PAD, LBL = 26, 30
    cellw = int(max(W, SW) * PX) + PAD * 2
    cellh = int(max(H, SH) * PX) + PAD * 2 + LBL
    ncol = COLS * (2 if cmpL else 1)
    rows = (len(L) + COLS - 1) // COLS
    TOP = 46 if a.title else 0
    img = Image.new("RGB", (cellw * ncol, cellh * rows + TOP), "#f4f5f7")
    d = ImageDraw.Draw(img)
    f, fb, ft = fonts()
    if a.title:
        d.text((PAD, 14), a.title, fill="#111", font=ft)

    def draw(ox, oy, pw, ph, xml, ref=None):
        d.rectangle([ox, oy, ox + pw * PX, oy + ph * PX], fill="white", outline="#b8bcc4")
        d.rectangle([ox + a.safe * PX, oy + a.safe * PX,
                     ox + (pw - a.safe) * PX, oy + (ph - a.safe) * PX], outline="#e8b4b4")
        d.line([ox + pw * PX / 2, oy, ox + pw * PX / 2, oy + ph * PX], fill="#d5d8dd")
        k = 0
        for tag, at in G.EL_RE.findall(xml):
            av = G.attrs(at)
            if "width" not in av: continue
            x, y = float(av.get("x", 0)), float(av.get("y", 0))
            w, h = float(av["width"]), float(av["height"])
            fc, oc = FILL.get(tag, ("#ddd", "#999"))
            if ref:
                rf = G.frames(ref)
                if k < len(rf) and abs((w / h) / (rf[k][2] / rf[k][3]) - 1) > 0.02:
                    fc, oc = DISTORT
            k += 1
            d.rectangle([ox + x * PX, oy + y * PX, ox + (x + w) * PX, oy + (y + h) * PX],
                        fill=fc, outline=oc)
        d.text((ox, oy + ph * PX + 5), "%.1f x %.1f mm  (%.4g x %.4g in)"
               % (pw, ph, pw / 25.4, ph / 25.4), fill="#666", font=f)

    for i, e in enumerate(L):
        pw, ph = G.page_dims(e["data"])
        r, c = i // COLS, i % COLS
        ox = c * cellw * (2 if cmpL else 1) + PAD
        oy = r * cellh + PAD + LBL + TOP
        d.text((ox, oy - LBL + 4), "%s  -  %s"
               % ((e.get("tags") or ["?"])[0], e.get("id")), fill="#222", font=fb)
        if cmpL:
            draw(ox, oy, SW, SH, cmpL[i]["data"])
            draw(ox + cellw, oy, pw, ph, e["data"], ref=cmpL[i]["data"])
        else:
            draw(ox, oy, pw, ph, e["data"])

    img.save(a.out)
    print(a.out, img.size)


if __name__ == "__main__":
    main()

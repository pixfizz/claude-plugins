#!/usr/bin/env python3
"""
pxgeom.py -- shared geometry for Pixfizz page XML.

Every coordinate in `templates[].data` and `layouts[].data` is millimetres,
regardless of what `unit=` says in the product definition.
"""
import re

PAGE_RE = re.compile(r'<page\b[^>]*?>')
EL_RE   = re.compile(r'<(image|text|background|clipart|shape|ipage)\b([^>]*?)/>')
ATTR_RE = re.compile(r'(\w[\w-]*)="([^"]*)"')

# `left` and `top` are present on every element and are always 0 -- they are NOT
# the position. `x`/`y` are, and they are omitted entirely when zero.
NEVER_SCALE = {"left", "top", "rotation", "rotate", "angle", "opacity",
               "zindex", "z-index", "order", "dpi", "version", "flip", "zoom"}


def fmt(v):
    """12dp then strip. Load-bearing: it makes non-terminating factors such as
    7/6 land exactly on the page edge instead of 711.19999999."""
    s = "%.12f" % v
    s = s.rstrip("0").rstrip(".")
    return s if s else "0"


def attrs(s):
    return dict(ATTR_RE.findall(s))


def page_dims(xml):
    m = PAGE_RE.search(xml)
    if not m:
        return None
    a = attrs(m.group(0))
    try:
        return float(a["width"]), float(a["height"])
    except (KeyError, ValueError):
        return None


def set_page(xml, W, H):
    def rep(m):
        s = m.group(0)
        s = re.sub(r'\bwidth="[^"]*"', 'width="%s"' % fmt(W), s)
        s = re.sub(r'\bheight="[^"]*"', 'height="%s"' % fmt(H), s)
        return s
    return PAGE_RE.sub(rep, xml, count=1)


def census(xml):
    out = {}
    for tag, _ in EL_RE.findall(xml):
        out[tag] = out.get(tag, 0) + 1
    return out


def frames(xml, include_ipage=False):
    """[(x, y, w, h), ...] in document order."""
    out = []
    for tag, at in EL_RE.findall(xml):
        if tag == "ipage" and not include_ipage:
            continue
        a = attrs(at)
        if "width" in a and "height" in a:
            out.append((float(a.get("x", 0)), float(a.get("y", 0)),
                        float(a["width"]), float(a["height"])))
    return out


def write_frames(xml, new):
    """Replace each element's x/y/width/height in document order. Inserts x/y
    when the source omitted them (they are omitted when zero)."""
    i = [0]
    def rep(m):
        tag, at = m.group(1), m.group(2)
        if tag == "ipage":
            return m.group(0)
        a = attrs(at)
        if "width" not in a or "height" not in a:
            return m.group(0)
        x, y, w, h = new[i[0]]; i[0] += 1
        out = m.group(0)
        for k, v in (("width", w), ("height", h)):
            out = re.sub(r'\b%s="[^"]*"' % k, '%s="%s"' % (k, fmt(v)), out)
        for k, v in (("x", x), ("y", y)):
            if re.search(r'\b%s="' % k, out):
                out = re.sub(r'\b%s="[^"]*"' % k, '%s="%s"' % (k, fmt(v)), out)
            elif abs(v) > 1e-12:
                out = out[:-2] + ' %s="%s"/>' % (k, fmt(v))
        return out
    return EL_RE.sub(rep, xml)


def detect_grid(all_frames):
    """
    The declared <page> canvas is NOT evidence of the authored grid. It has been
    observed stale (cover size) and prematurely correct (already the target while
    the frames were still on the source grid). Derive it from the frames instead,
    with two independent detectors that must agree.

    Returns (full_bleed_candidate, symmetry_candidate, width_votes, height_votes).
    """
    from collections import Counter
    bleed = None
    for fr in all_frames:
        if len(fr) == 1 and abs(fr[0][0]) < 1e-9 and abs(fr[0][1]) < 1e-9:
            c = (fr[0][2], fr[0][3])
            if bleed is None or c[0] * c[1] > bleed[0] * bleed[1]:
                bleed = c
    wc, hc = Counter(), Counter()
    for fr in all_frames:
        if not fr:
            continue
        wc[round(min(f[0] for f in fr) + max(f[0] + f[2] for f in fr), 6)] += 1
        hc[round(min(f[1] for f in fr) + max(f[1] + f[3] for f in fr), 6)] += 1
    sym = (wc.most_common(1)[0][0], hc.most_common(1)[0][0]) if wc else None
    return bleed, sym, wc, hc


def is_full_bleed(x, y, w, h, SW, SH):
    return w * h >= 0.99 * SW * SH and x <= 1e-9 and y <= 1e-9


def transform(fr, SW, SH, TW, TH, rule, recentre=True):
    """Map one layout's frames onto the target page. Returns a new frame list."""
    fx, fy = TW / SW, TH / SH
    if not fr:
        return fr

    if rule == "uniform":
        return [(x * fx, y * fy, w * fx, h * fy) for (x, y, w, h) in fr]

    if rule == "stretch":
        return [(0.0, 0.0, TW, TH) if is_full_bleed(x, y, w, h, SW, SH)
                else (x * fx, y * fy, w * fx, h * fy) for (x, y, w, h) in fr]

    if rule == "fit":
        s = min(fx, fy)
        ox, oy = (TW - SW * s) / 2.0, (TH - SH * s) / 2.0
        return [(0.0, 0.0, TW, TH) if is_full_bleed(x, y, w, h, SW, SH)
                else (ox + x * s, oy + y * s, w * s, h * s) for (x, y, w, h) in fr]

    if rule == "cell":
        out = []
        for (x, y, w, h) in fr:
            if is_full_bleed(x, y, w, h, SW, SH):
                out.append((0.0, 0.0, TW, TH)); continue
            cx, cy, cw, ch = x * fx, y * fy, w * fx, h * fy
            a = w / h
            if cw / ch > a: nh, nw = ch, a * ch
            else:           nw, nh = cw, cw / a
            out.append((cx + (cw - nw) / 2.0, cy + (ch - nh) / 2.0, nw, nh))
        return out

    if rule == "margin":
        s = min(fx, fy)
        L = min(f[0] for f in fr); T = min(f[1] for f in fr)
        R = SW - max(f[0] + f[2] for f in fr); B = SH - max(f[1] + f[3] for f in fr)
        nL, nR, nT, nB = L * s, R * s, T * s, B * s
        if recentre and abs(L - R) < 0.75: nL = nR = (nL + nR) / 2.0
        if recentre and abs(T - B) < 0.75: nT = nB = (nT + nB) / 2.0
        cw, ch = SW - L - R, SH - T - B
        gx = (TW - nL - nR) / cw if cw else 1.0
        gy = (TH - nT - nB) / ch if ch else 1.0
        out = []
        for (x, y, w, h) in fr:
            if is_full_bleed(x, y, w, h, SW, SH):
                out.append((0.0, 0.0, TW, TH))
            else:
                out.append((nL + (x - L) * gx, nT + (y - T) * gy, w * gx, h * gy))
        return out

    raise SystemExit("unknown rule: " + rule)


def margins(fr, W, H):
    return (min(f[0] for f in fr), W - max(f[0] + f[2] for f in fr),
            min(f[1] for f in fr), H - max(f[1] + f[3] for f in fr))

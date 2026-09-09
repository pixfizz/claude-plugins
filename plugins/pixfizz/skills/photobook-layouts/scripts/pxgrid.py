"""Page geometry and the shared numeric conventions for Pixfizz layouts.

Coordinates are always millimetres, regardless of the definition's unit=.
`left` and `top` are always 0 and are NOT the position; `x`/`y` are, and are
omitted from the XML entirely when zero.
"""
IN = 25.4


def fmt(v):
    """Format to 12 decimals then strip.

    Load-bearing. Without it a non-terminating factor leaves a full-bleed frame
    at 711.19999999 against a 711.2 page - a hairline white edge down the trim.
    """
    s = f"{v:.12f}".rstrip("0").rstrip(".")
    return s if s else "0"


class Page:
    """A layout page and its margin/gutter vocabulary, all in mm."""

    def __init__(self, w, h, gutter=0.25 * IN, margin=0.875 * IN, narrow=0.5 * IN):
        self.w, self.h = float(w), float(h)
        self.g, self.m, self.n = float(gutter), float(margin), float(narrow)

    # content box at the house margin
    @property
    def cw(self):
        return self.w - 2 * self.m

    @property
    def ch(self):
        return self.h - 2 * self.m

    # content box at the narrow margin
    @property
    def nw(self):
        return self.w - 2 * self.n

    @property
    def nh(self):
        return self.h - 2 * self.n

    @property
    def short(self):
        return min(self.w, self.h)

    def cx(self, w):
        """x that centres a block of width w."""
        return (self.w - w) / 2

    def cy(self, h):
        """y that centres a block of height h."""
        return (self.h - h) / 2

    def grid(self, cols, rows, x0, y0, w, h, g=None):
        g = self.g if g is None else g
        cw = (w - (cols - 1) * g) / cols
        ch = (h - (rows - 1) * g) / rows
        return [(x0 + c * (cw + g), y0 + r * (ch + g), cw, ch)
                for r in range(rows) for c in range(cols)]

    def row(self, n, x0, y0, w, h, g=None):
        return self.grid(n, 1, x0, y0, w, h, g)

    def col(self, n, x0, y0, w, h, g=None):
        return self.grid(1, n, x0, y0, w, h, g)

    def lh(self, w, ratio=1.5, cap=None):
        """Height of a ratio:1 landscape of width w, capped so it still fits."""
        cap = self.h if cap is None else cap
        return min(w / ratio, cap)

    def block(self, cols, rows, ratio=1.0, x0=None, w=None):
        """Largest cols x rows block of cells of aspect `ratio` (h/w) that fits
        the content box, centred both ways.

        Drives from width when the block is short enough, and from height when
        it is not - which is what keeps a 3x2 of squares inside a wide spread
        instead of running off the top and bottom.
        """
        x0 = self.m if x0 is None else x0
        w = self.cw if w is None else w
        cw = (w - (cols - 1) * self.g) / cols
        ch = cw * ratio
        bh = rows * ch + (rows - 1) * self.g
        if bh > self.ch:
            ch = (self.ch - (rows - 1) * self.g) / rows
            cw = ch / ratio
            w = cols * cw + (cols - 1) * self.g
            x0 = self.cx(w)
            bh = self.ch
        return self.grid(cols, rows, x0, self.cy(bh), w, bh)

    def band(self, cols, rows, h, x0=None, w=None):
        """A cols x rows block of total height h, centred vertically."""
        x0 = self.m if x0 is None else x0
        w = self.cw if w is None else w
        return self.grid(cols, rows, x0, self.cy(h), w, h)

    def cell_h(self, cols, w=None, ratio=1.0):
        """Height of a cell whose width comes from splitting w into cols."""
        w = self.cw if w is None else w
        return (w - (cols - 1) * self.g) / cols * ratio


def derive(theme_layouts):
    """Derive page size, gutter and margin from the layouts already in a theme.

    Never trust the declared <page> canvas - it is observed stale in both
    directions. Returns (w, h, gutter, margin, votes) with the evidence, so the
    caller can report it rather than silently assuming.
    """
    import xml.etree.ElementTree as ET
    from collections import Counter

    frames, pages = [], Counter()
    for l in theme_layouts:
        try:
            root = ET.fromstring(l["data"])
        except Exception:
            continue
        pages[(root.get("width"), root.get("height"))] += 1
        for el in root:
            if el.tag != "image":
                continue
            frames.append((float(el.get("x", 0)), float(el.get("y", 0)),
                           float(el.get("width")), float(el.get("height"))))
    if not frames:
        (pw, ph), _ = pages.most_common(1)[0]
        return float(pw), float(ph), 0.25 * IN, 0.875 * IN, {"source": "declared page only"}

    # detector 1: a frame anchored at the origin gives the grid directly
    bleed = [(w, h) for (x, y, w, h) in frames if abs(x) < 0.01 and abs(y) < 0.01]
    # detector 2: mode of min_edge + max_extent
    wv = Counter(round(x + (x + w), 6) for (x, y, w, h) in frames)
    hv = Counter(round(y + (y + h), 6) for (x, y, w, h) in frames)

    pw = max(bleed, key=lambda t: t[0])[0] if bleed else wv.most_common(1)[0][0]
    ph = max(bleed, key=lambda t: t[1])[1] if bleed else hv.most_common(1)[0][0]

    # gutter: most common positive gap between adjacent frame edges on a row
    gaps = Counter()
    xs = sorted(frames, key=lambda f: (round(f[1], 3), f[0]))
    for a, b in zip(xs, xs[1:]):
        if abs(a[1] - b[1]) < 0.01:
            gap = round(b[0] - (a[0] + a[2]), 4)
            if 0.5 < gap < 30:
                gaps[gap] += 1
    gutter = gaps.most_common(1)[0][0] if gaps else 0.25 * IN

    # margin: each layout votes once with its own smallest non-zero left edge,
    # and the mode wins. Taking the global minimum instead picks whichever single
    # layout happens to be the tightest, which is not the house margin.
    per_layout = []
    for l in theme_layouts:
        try:
            root = ET.fromstring(l["data"])
        except Exception:
            continue
        xs = [float(e.get("x", 0)) for e in root if e.tag == "image"]
        xs = [x for x in xs if x > 0.01]
        if xs:
            per_layout.append(round(min(xs), 4))
    mv = Counter(per_layout)
    margin = mv.most_common(1)[0][0] if mv else 0.875 * IN
    lefts = sorted(set(per_layout))

    votes = {"declared_page": dict(pages), "width_votes": wv.most_common(3),
             "height_votes": hv.most_common(3), "gutter_votes": gaps.most_common(3),
             "margin_votes": mv.most_common(3), "left_edges": lefts[:5], "full_bleed_frames": len(bleed)}
    return float(pw), float(ph), gutter, margin, votes

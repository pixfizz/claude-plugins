"""Layout archetypes, expressed as functions of the page so they work at any size.

Each entry is (group, name, fn) where group is the photo-count facet the Design
Tool picker groups by, and fn(Page) returns a list of (x, y, w, h) frames in mm.

Groups 1-4 hold exactly that many frames. Group 5 is the "5+" catch-all and
holds anything from 5 upward, deliberately spread across counts rather than
being all dense grids.

Adding an archetype: keep it a pure function of the Page so it survives a
different page size, and never hard-code a millimetre value that is not derived
from p.w, p.h, p.m, p.n or p.g.
"""

LIBRARY = []


def A(group, name, fn):
    LIBRARY.append((group, name, fn))


# --------------------------------------------------------------- 1 photo
A(1, "Landscape full-width",
  lambda p: [(0, p.cy(p.lh(p.w)), p.w, p.lh(p.w))])
A(1, "Square, narrow margin",
  lambda p: [(p.cx(p.short - 2 * p.n), p.cy(p.short - 2 * p.n),
              p.short - 2 * p.n, p.short - 2 * p.n)])
A(1, "Portrait, tall centred",
  lambda p: [(p.cx(min(p.nh / 1.5, p.nw)), p.n, min(p.nh / 1.5, p.nw), p.nh)])
A(1, "Landscape top, deep base",
  lambda p: [(p.m, p.m, p.cw, p.lh(p.cw, cap=p.ch * 0.7))])
A(1, "Full-bleed top, base band",
  lambda p: [(0, 0, p.w, p.h - p.h / 4)])
A(1, "Small square, upper left",
  lambda p: [(p.m, p.m, p.cw / 2, p.cw / 2)])
A(1, "Landscape, left bleed",
  lambda p: [(0, p.cy(p.h / 2), p.w * 0.75, p.h / 2)])
A(1, "Portrait, right bleed",
  lambda p: [(p.w - p.w * 0.6, 0, p.w * 0.6, p.h)])
A(1, "Small square, lower right",
  lambda p: [(p.w - p.m - p.cw / 2, p.h - p.m - p.cw / 2, p.cw / 2, p.cw / 2)])

# --------------------------------------------------------------- 2 photos
A(2, "Two portraits, full bleed", lambda p: p.row(2, 0, 0, p.w, p.h))
A(2, "Two landscapes stacked",    lambda p: p.col(2, p.m, p.m, p.cw, p.ch))
A(2, "Two portraits, centred pair",
  lambda p: p.row(2, p.m * 1.5, p.cy(p.ch * 2 / 3), p.w - 3 * p.m, p.ch * 2 / 3))
A(2, "Feature plus inset",
  lambda p: [(p.m, p.m, p.cw, p.lh(p.cw, cap=p.ch * 0.65)),
             (p.m + p.cw / 2 + p.g / 2, p.m + p.lh(p.cw, cap=p.ch * 0.65) + p.g,
              p.cw / 2 - p.g / 2, p.ch - p.lh(p.cw, cap=p.ch * 0.65) - p.g)])
A(2, "Bleed top, small below",
  lambda p: [(0, 0, p.w, p.h * 0.625),
             (p.cx(p.w / 2), p.h * 0.7, p.w / 2, p.h * 0.25)])
A(2, "Staggered pair",
  lambda p: [(p.m, p.n, p.cw * 0.45, p.ch * 0.62),
             (p.m + p.cw * 0.55, p.n + p.ch * 0.3, p.cw * 0.45, p.ch * 0.62)])
A(2, "Two squares, centred column",
  lambda p: p.col(2, p.cx((p.ch * 0.8 - p.g) / 2), p.cy(p.ch * 0.8),
                  (p.ch * 0.8 - p.g) / 2, p.ch * 0.8))
A(2, "Bleed left, inset right",
  lambda p: [(0, 0, p.w * 0.625, p.h),
             (p.w * 0.65, p.cy(p.h * 0.4), p.w - p.m - p.w * 0.65, p.h * 0.4)])
A(2, "Two stacked, unequal",
  lambda p: [(p.m, p.m, p.cw, p.ch * 0.62),
             (p.cx(p.cw * 0.6), p.m + p.ch * 0.62 + p.g,
              p.cw * 0.6, p.ch * 0.38 - p.g)])

# --------------------------------------------------------------- 3 photos
A(3, "Three stacked",               lambda p: p.col(3, p.m, p.m, p.cw, p.ch))
A(3, "Three portraits, row", lambda p: p.block(3, 1, ratio=1.5))
A(3, "Feature above, pair below",
  lambda p: [(p.m, p.m, p.cw, p.lh(p.cw, cap=p.ch * 0.65))]
            + p.row(2, p.m, p.m + p.lh(p.cw, cap=p.ch * 0.65) + p.g,
                    p.cw, p.ch - p.lh(p.cw, cap=p.ch * 0.65) - p.g))
A(3, "Pair above, feature below",
  lambda p: p.row(2, p.m, p.m, p.cw, (p.ch - p.g) / 2)
            + [(p.m, p.m + (p.ch - p.g) / 2 + p.g, p.cw, (p.ch - p.g) / 2)])
A(3, "Three portraits, full bleed",  lambda p: p.row(3, 0, 0, p.w, p.h))
A(3, "Feature left, stack right",
  lambda p: [(p.m, p.m, p.cw * 0.6, p.ch)]
            + p.col(2, p.m + p.cw * 0.6 + p.g, p.m, p.cw * 0.4 - p.g, p.ch))
A(3, "Stack left, feature right",
  lambda p: p.col(2, p.m, p.m, p.cw * 0.4 - p.g, p.ch)
            + [(p.m + p.cw * 0.4, p.m, p.cw * 0.6, p.ch)])
A(3, "Three squares, bleed band",
  lambda p: p.row(3, 0, p.cy(min((p.w - 2 * p.g) / 3, p.h)),
                  p.w, min((p.w - 2 * p.g) / 3, p.h)))
A(3, "Three cascading",
  lambda p: [(p.m + i * (p.cw - p.cw * 0.6) / 2,
              p.m + i * ((p.ch - 2 * p.g) / 3 + p.g),
              p.cw * 0.6, (p.ch - 2 * p.g) / 3) for i in range(3)])

# --------------------------------------------------------------- 4 photos
A(4, "Quad grid",       lambda p: p.grid(2, 2, p.m, p.m, p.cw, p.ch))
A(4, "Quad, full bleed", lambda p: p.grid(2, 2, 0, 0, p.w, p.h))
A(4, "Four across",     lambda p: p.block(4, 1, ratio=1.5))
A(4, "Four stacked, column",
  lambda p: p.col(4, p.cx(p.cw / 2), p.m, p.cw / 2, p.ch))
A(4, "Feature above, trio below",
  lambda p: [(p.m, p.m, p.cw, p.lh(p.cw, cap=p.ch * 0.65))]
            + p.row(3, p.m, p.m + p.lh(p.cw, cap=p.ch * 0.65) + p.g,
                    p.cw, p.ch - p.lh(p.cw, cap=p.ch * 0.65) - p.g))
A(4, "Feature left, trio right",
  lambda p: [(p.m, p.m, p.cw * 2 / 3, p.ch)]
            + p.col(3, p.m + p.cw * 2 / 3 + p.g, p.m, p.cw / 3 - p.g, p.ch))
A(4, "Trio above, feature below",
  lambda p: p.row(3, p.m, p.m, p.cw, p.ch - p.lh(p.cw, cap=p.ch * 0.65) - p.g)
            + [(p.m, p.m + p.ch - p.lh(p.cw, cap=p.ch * 0.65),
                p.cw, p.lh(p.cw, cap=p.ch * 0.65))])
A(4, "Quad band, side bleed",
  lambda p: p.grid(2, 2, 0, p.cy(p.h * 0.675), p.w, p.h * 0.675))
A(4, "Four, offset pairs",
  lambda p: p.col(2, p.m, p.m, (p.cw - p.g) / 2, p.ch * 0.82)
            + p.col(2, p.m + (p.cw + p.g) / 2, p.m + p.ch * 0.18,
                    (p.cw - p.g) / 2, p.ch * 0.82))

# --------------------------------------------------------------- 5+ photos
A(5, "Five, two above three",
  lambda p: p.row(2, p.m, p.m, p.cw, (p.ch - p.g) / 2)
            + p.row(3, p.m, p.m + (p.ch - p.g) / 2 + p.g, p.cw, (p.ch - p.g) / 2))
A(5, "Six square grid",      lambda p: p.block(3, 2))
A(5, "Seven, feature plus six",
  lambda p: [(p.m, p.m, p.cw, p.ch * 0.56)]
            + p.grid(3, 2, p.m, p.m + p.ch * 0.56 + p.g, p.cw, p.ch * 0.44 - p.g))
A(5, "Eight, two by four",  lambda p: p.grid(2, 4, p.m, p.m, p.cw, p.ch))
A(5, "Eight, four by two",   lambda p: p.block(4, 2, ratio=1.5))
A(5, "Nine grid",           lambda p: p.grid(3, 3, p.m, p.m, p.cw, p.ch))
A(5, "Ten, five by two",     lambda p: p.block(5, 2, ratio=1.5))
A(5, "Twelve grid",         lambda p: p.grid(3, 4, p.m, p.m, p.cw, p.ch))
A(5, "Sixteen grid",        lambda p: p.grid(4, 4, p.m, p.m, p.cw, p.ch))


def build(page, groups=None):
    """Materialise the library against a Page. Returns [(group, name, frames)]."""
    out = []
    for g, name, fn in LIBRARY:
        if groups and g not in groups:
            continue
        out.append((g, name, [tuple(round(v, 9) for v in f) for f in fn(page)]))
    return out


def counts():
    from collections import Counter
    return Counter(g for g, _, _ in LIBRARY)

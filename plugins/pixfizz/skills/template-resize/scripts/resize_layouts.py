#!/usr/bin/env python3
"""
resize_layouts.py -- resize the layouts[] of a DESIGN THEME export
(__print_theme.yml) onto a new page size.

  resize_layouts.py THEME.yml --target 508x254 [--source WxH] [--rule R] [--out F]

Sizes are millimetres. Omit --source to auto-detect from the frames (recommended:
it cross-checks two detectors and refuses when they disagree).

Rules
  auto     uniform when the aspect is unchanged, otherwise 'margin'  (default)
  uniform  single factor; only valid when the aspect is unchanged
  margin   scale all four content-bbox margins by min(fx,fy); frames fill the rest
  fit      uniform min(fx,fy), centred; nothing distorts, page under-fills
  stretch  independent axes; fills the page, distorts every frame
  cell     proportional cell remap with the frame's own aspect fitted inside

Text-surgical: only the layouts block is rewritten, so every other field, the
YAML block-scalar style and the element attribute order survive untouched.
"""
import re, sys, argparse
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import pxgeom as G


def split(txt):
    head, sep, rest = txt.partition("\nlayouts:\n")
    if not sep:
        sys.exit("ERROR: no 'layouts:' block -- is this a design-theme export?")
    body, sep2, tail = rest.partition("\ndesign_options:")
    if not sep2:
        sys.exit("ERROR: no 'design_options:' terminator after the layouts block.")
    return head, body, tail


def blocks(body):
    """Split the layouts body into per-layout line groups, keyed on <page."""
    out, cur = [], None
    for line in body.split("\n"):
        if line.strip().startswith("<page"):
            if cur is not None: out.append(cur)
            cur = []
        if cur is not None: cur.append(line)
        else: out.append([line]); out[-1].append(None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("theme")
    ap.add_argument("--target", required=True)
    ap.add_argument("--source")
    ap.add_argument("--rule", default="auto",
                    choices=["auto", "uniform", "margin", "fit", "stretch", "cell"])
    ap.add_argument("--out")
    ap.add_argument("--no-recentre", action="store_true",
                    help="keep the source's asymmetric row margins instead of equalising them")
    a = ap.parse_args()

    TW, TH = (float(v) for v in a.target.lower().split("x"))
    txt = open(a.theme).read()
    head, body, tail = split(txt)

    # ---- gather ---------------------------------------------------------------
    lines = body.split("\n")
    starts = [i for i, l in enumerate(lines) if l.strip().startswith("<page")]
    ends = starts[1:] + [len(lines)]
    groups = [(s, e, "\n".join(lines[s:e])) for s, e in zip(starts, ends)]
    all_fr = [G.frames(g[2]) for g in groups]

    cen = {}
    for g in groups:
        for k, v in G.census(g[2]).items(): cen[k] = cen.get(k, 0) + v
    print("layouts: %d   elements: %s" % (len(groups), cen or "none"))
    other = set(cen) - {"image"}
    if other:
        print("!! non-image elements present: %s" % ", ".join(sorted(other)))
        print("   Text/font scaling is UNPROVEN and <ipage> carries its own zoom and pan.")
        print("   Inspect the proof sheet before shipping; do not assume these scaled correctly.")

    # ---- source grid ----------------------------------------------------------
    bleed, sym, wc, hc = G.detect_grid(all_fr)
    print("detector A (full-bleed frame): %s" % (bleed,))
    print("detector B (margin symmetry) : %s   [w %s | h %s]"
          % (sym, wc.most_common(2), hc.most_common(2)))
    if a.source:
        SW, SH = (float(v) for v in a.source.lower().split("x"))
        print("source grid: %g x %g  (manual override)" % (SW, SH))
    else:
        if bleed and sym and (abs(bleed[0] - sym[0]) > 1e-6 or abs(bleed[1] - sym[1]) > 1e-6):
            sys.exit("ERROR: detectors disagree (%s vs %s). Pass --source explicitly." % (bleed, sym))
        if not (bleed or sym):
            sys.exit("ERROR: could not detect the source grid. Pass --source explicitly.")
        SW, SH = bleed or sym
        print("source grid: %g x %g  (auto-detected, detectors agree)" % (SW, SH))

    fx, fy = TW / SW, TH / SH
    uniform = abs(fx - fy) <= 1e-9
    rule = a.rule
    if rule == "auto":
        rule = "uniform" if uniform else "margin"
    if rule == "uniform" and not uniform:
        sys.exit("ERROR: aspect changes %.4f:1 -> %.4f:1; 'uniform' would distort every frame."
                 % (SW / SH, TW / TH))
    print("factors: x=%.10g y=%.10g   rule=%s" % (fx, fy, rule))
    if not uniform:
        print("!! ASPECT CHANGE %.4f:1 -> %.4f:1." % (SW / SH, TW / TH))
        print("   Frame shape, grid adjacency and page fill cannot all be preserved.")
        print("   Rule '%s' was applied; review the band table below and the proof sheet." % rule)

    # ---- transform ------------------------------------------------------------
    new_body = list(lines)
    bands = []
    for (s, e, xml), fr in zip(groups, all_fr):
        nf = G.transform(fr, SW, SH, TW, TH, rule, recentre=not a.no_recentre)
        out = G.set_page(G.write_frames(xml, nf), TW, TH)
        pad = len(lines[s]) - len(lines[s].lstrip())
        rep = out.split("\n")
        for i in range(s, e): new_body[i] = None
        new_body[s] = "\n".join(rep)
        if nf: bands.append(G.margins(nf, TW, TH))
    body2 = "\n".join(x for x in new_body if x is not None)

    dst = a.out or a.theme
    open(dst, "w").write(head + "\nlayouts:\n" + body2 + "\ndesign_options:" + tail)

    print("\n%-4s %-34s %s" % ("#", "margins L/R/T/B (mm)", "(inches)"))
    for i, (L, R, T, B) in enumerate(bands):
        print("%-4d %8.3f %8.3f %8.3f %8.3f      %.3f %.3f %.3f %.3f"
              % (i, L, R, T, B, L / 25.4, R / 25.4, T / 25.4, B / 25.4))
    print("\nwrote %s" % dst)
    if not uniform:
        print("\nIf the margins are not the clean values the design system uses, override the\n"
              "vertical band per layout -- see references/geometry.md, 'Band vocabulary'.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
verify_layouts.py ORIGINAL.yml RESCALED.yml --source WxH --target WxH [--rule R]

Every check that must pass before a resized export ships. Exits non-zero on failure.
Works on a design-theme export, or on either theme inside a template export via
--theme <code>.
"""
import sys, argparse
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import pxgeom as G
import pxload

TOL = 1e-9
EDGE_TOL = 1e-9


def layouts_of(path, theme=None):
    d = pxload.load(path)
    if "layouts" in d and theme is None:
        return d["layouts"]
    for th in d.get("print_themes", []):
        if theme is None or th["code"] == theme:
            if th.get("layouts"):
                return th["layouts"]
    sys.exit("no layouts found in %s" % path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("original"); ap.add_argument("rescaled")
    ap.add_argument("--source", required=True); ap.add_argument("--target", required=True)
    ap.add_argument("--rule", default="auto"); ap.add_argument("--theme")
    a = ap.parse_args()
    SW, SH = (float(v) for v in a.source.lower().split("x"))
    TW, TH = (float(v) for v in a.target.lower().split("x"))
    fx, fy = TW / SW, TH / SH
    uniform = abs(fx - fy) <= 1e-9
    rule = a.rule if a.rule != "auto" else ("uniform" if uniform else "margin")

    old = layouts_of(a.original, a.theme); new = layouts_of(a.rescaled, a.theme)
    errs, comps, distorted = [], 0, 0
    if len(old) != len(new):
        errs.append("layout count %d -> %d" % (len(old), len(new)))

    for o, n in zip(old, new):
        lid = o.get("id")
        # 1. metadata drift
        for k in ("id", "number", "name", "tags", "usage_flags"):
            if o.get(k) != n.get(k):
                errs.append("%s: '%s' drifted %r -> %r" % (lid, k, o.get(k), n.get(k)))
        # 2. canvas is the target, absolutely
        p = G.page_dims(n["data"])
        if not p or abs(p[0] - TW) > 1e-6 or abs(p[1] - TH) > 1e-6:
            errs.append("%s: canvas %s, expected %g x %g" % (lid, p, TW, TH))
        # 3. element tags and count preserved
        if G.census(o["data"]) != G.census(n["data"]):
            errs.append("%s: element census changed %s -> %s"
                        % (lid, G.census(o["data"]), G.census(n["data"])))
            continue
        of, nf = G.frames(o["data"]), G.frames(n["data"])
        exp = G.transform(of, SW, SH, TW, TH, rule)
        for i, (e, g, s) in enumerate(zip(exp, nf, of)):
            for j in range(4):
                comps += 1
                if abs(g[j] - e[j]) > TOL:
                    errs.append("%s el%d comp%d: %.12g != expected %.12g" % (lid, i, j, g[j], e[j]))
            # 4. bounds
            if g[0] < -TOL or g[1] < -TOL or g[0] + g[2] > TW + TOL or g[1] + g[3] > TH + TOL:
                errs.append("%s el%d out of bounds" % (lid, i))
            # 5. edge landing -- a frame on the page edge must land on it EXACTLY,
            #    or a full-bleed spread ships with a hairline white trim edge.
            for val, lim, nm in ((g[0], 0.0, "left"), (g[1], 0.0, "top"),
                                 (g[0] + g[2], TW, "right"), (g[1] + g[3], TH, "bottom")):
                if abs(val - lim) < 0.05 and abs(val - lim) > EDGE_TOL:
                    errs.append("%s el%d %s edge off by %.3e mm" % (lid, i, nm, abs(val - lim)))
            if abs((g[2] / g[3]) / (s[2] / s[3]) - 1) > 1e-9:
                distorted += 1

    print("layouts %d | components %d | rule %s | factors x%.10g y%.10g"
          % (len(new), comps, rule, fx, fy))
    print("frames whose aspect changed: %d%s" % (distorted,
          "  (expected 0 for a uniform rescale)" if uniform else "  (expected for an aspect change)"))
    if uniform and distorted:
        errs.append("uniform rescale must not change any frame aspect")
    if errs:
        print("\nFAILURES (%d):" % len(errs))
        for e in errs[:40]: print("  -", e)
        sys.exit(1)
    print("PASS: geometry exact, in bounds, edges land exactly, no metadata drift, census preserved.")


if __name__ == "__main__":
    main()

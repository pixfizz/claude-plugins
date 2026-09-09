#!/usr/bin/env python3
"""Verify a filled design-theme export against the one it was built from.

    python3 verify_layouts.py --before export.tar.gz --after filled.tar.gz

Exits non-zero on any failure. Run this before handing anything over.
"""
import argparse
import os
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pxload                                  # noqa: E402


def read(path):
    d = tempfile.mkdtemp()
    with tarfile.open(path) as t:
        names = t.getnames()
        t.extractall(d)
    return pxload.load(os.path.join(d, "__print_theme.yml")), names


def frames(data):
    return [(float(e.get("x", 0)), float(e.get("y", 0)),
             float(e.get("width")), float(e.get("height")))
            for e in ET.fromstring(data) if e.tag == "image"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--tol", type=float, default=0.01)
    a = ap.parse_args()
    A, an = read(a.before)
    B, bn = read(a.after)
    fail = []

    if an != bn:
        fail.append(f"archive members differ:\n  {an}\n  {bn}")

    for k in set(A) | set(B):
        if k == "layouts":
            continue
        if A.get(k) != B.get(k):
            fail.append(f"top-level key changed outside layouts[]: {k}")

    la, lb = A.get("layouts", []), B.get("layouts", [])
    if len(la) != len(lb):
        fail.append(f"layout count {len(la)} -> {len(lb)}")
    if [l["id"] for l in la] != [l["id"] for l in lb]:
        fail.append("layout ids or their order changed - an import would no "
                    "longer overwrite the same records")

    for x, y in zip(la, lb):
        for k in x:
            if k in ("data", "tags"):
                continue
            if x[k] != y[k]:
                fail.append(f"layout {x['id']}: key {k} changed")
        was_blank = "<image" not in (x.get("data") or "")
        if not was_blank:
            if x.get("data") != y.get("data") or x.get("tags") != y.get("tags"):
                fail.append(f"layout {x['id']} was already populated and was modified")
            continue

        try:
            root = ET.fromstring(y["data"])
        except Exception as ex:
            fail.append(f"layout {y['id']}: XML does not parse: {ex}")
            continue
        oldroot = ET.fromstring(x["data"])
        if root.attrib != oldroot.attrib:
            fail.append(f"layout {y['id']}: <page> attributes changed "
                        f"{oldroot.attrib} -> {root.attrib}")
        pw, ph = float(root.get("width")), float(root.get("height"))
        els = list(root)
        if not els:
            fail.append(f"layout {y['id']}: still empty")
        if not y.get("tags"):
            fail.append(f"layout {y['id']}: filled but untagged - the picker "
                        f"would lose its grouping")
        for e in els:
            if e.tag != "image":
                fail.append(f"layout {y['id']}: non-image element <{e.tag}> - "
                            f"text frames are unproven, check by hand")
                continue
            if e.get("left") != "0" or e.get("top") != "0":
                fail.append(f"layout {y['id']}: left/top must be 0")
            if e.get("edit") != "true" or e.get("placeholder") != "true":
                fail.append(f"layout {y['id']}: missing edit/placeholder")
            fx, fy = float(e.get("x", 0)), float(e.get("y", 0))
            fw, fh = float(e.get("width")), float(e.get("height"))
            if fw <= 0 or fh <= 0:
                fail.append(f"layout {y['id']}: non-positive frame {fw}x{fh}")
            if fx < -a.tol or fy < -a.tol or fx + fw > pw + a.tol or fy + fh > ph + a.tol:
                fail.append(f"layout {y['id']}: frame outside trim "
                            f"({fx},{fy},{fw},{fh}) on {pw}x{ph}")
            # a frame meant to reach the trim must land exactly, or it prints a
            # hairline white edge that no proof sheet will show
            for nm, v, lim in (("right", fx + fw, pw), ("bottom", fy + fh, ph)):
                if 0 < abs(v - lim) < a.tol:
                    fail.append(f"layout {y['id']}: {nm} edge {v!r} is a hairline "
                                f"off {lim} - rounding lost")

    # overlapping placeholders: legal, but almost never intended in a generated
    # layout and invisible on a proof sheet. Reported as a warning, not a failure.
    warn = []
    for y in lb:
        try:
            fr = frames(y["data"])
        except Exception:
            continue
        for i in range(len(fr)):
            for j in range(i + 1, len(fr)):
                ax, ay, aw, ah = fr[i]; bx, by, bw, bh = fr[j]
                ox = min(ax + aw, bx + bw) - max(ax, bx)
                oy = min(ay + ah, by + bh) - max(ay, by)
                if ox > a.tol and oy > a.tol:
                    warn.append(f"layout {y['id']}: frames {i} and {j} overlap by "
                                f"{ox:.2f} x {oy:.2f} mm")
                    break
            else:
                continue
            break

    n_filled = sum(1 for x in la if "<image" not in (x.get("data") or ""))
    if warn:
        print("WARNINGS\n" + "\n".join("  ! " + w for w in warn))
    if fail:
        print("FAILED\n" + "\n".join("  - " + f for f in fail))
        sys.exit(1)
    print(f"PASSED - {n_filled} layouts filled, {len(la)-n_filled} pre-existing "
          f"untouched, {len(la)} total, ids and order preserved")


if __name__ == "__main__":
    main()

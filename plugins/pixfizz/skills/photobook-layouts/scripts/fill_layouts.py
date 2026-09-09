#!/usr/bin/env python3
"""Fill the blank layouts in a Pixfizz design-theme export.

The workflow this supports: the user creates N empty layouts in admin and
exports the theme. Every blank carries a real platform id, so writing frames
into them and re-importing overwrites those records instead of relying on
blank-id behaviour that has never been proven for layouts.

    python3 fill_layouts.py --in export.tar.gz --out filled.tar.gz
    python3 fill_layouts.py --in export.tar.gz --dry-run

The YAML is patched as text, not round-tripped. Everything outside the blank
`data:` and `tags:` keys stays byte-identical, so the diff is reviewable and
nothing else in the file can be disturbed.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pxgrid import Page, fmt, derive          # noqa: E402
from layout_library import build              # noqa: E402
import pxload                                 # noqa: E402

TAGS = {1: "1 photo", 2: "2 photos", 3: "3 photos", 4: "4 photos", 5: "5+ photos"}

BLANK_RE = re.compile(
    r'^  data: <\?xml version="1\.0" encoding="UTF-8"\?><page (?P<attrs>[^>]*?)>\n'
    r'    (?P<cont>[^\n]*?)></page>\n', re.M)


def unpack(path, into):
    with tarfile.open(path) as t:
        members = t.getnames()
        t.extractall(into)
    yml = os.path.join(into, "__print_theme.yml")
    if not os.path.exists(yml):
        sys.exit("no __print_theme.yml in archive - is this a design theme export?")
    return yml, members


def split_layouts(text):
    """Split the file into (head, [layout blocks], tail).

    Driven off the `- id:` boundaries inside layouts[] rather than a regex over
    the whole file - two data-key spellings otherwise match the same block and
    every blank gets counted twice.
    """
    i0 = text.index("\nlayouts:\n")
    i1 = text.index("\ndesign_options:")
    head = text[:i0 + 1] + "layouts:\n"
    body = text[i0 + len("\nlayouts:\n"):i1 + 1]
    tail = text[i1 + 1:]
    blocks = [b for b in re.split(r"(?m)^(?=- id: )", body) if b.strip()]
    return head, blocks, tail


DATA_KEY = re.compile(r"(?m)^  data: (?:\|-?\n)?(?P<val>(?:.*\n)*?)(?=^  [a-z_]+:)")
PAGE_ATTRS = re.compile(r"<page ([^>]*)>")


def is_blank(block):
    return "<image" not in block


def page_attrs_of(block):
    m = PAGE_ATTRS.search(block)
    if not m:
        raise ValueError("layout block has no <page> tag")
    return " ".join(m.group(1).split())


def img(x, y, w, h):
    """One placeholder element in the platform's own attribute order.

    left/top are always 0 and are not the position. x/y carry the position and
    are omitted entirely when zero, matching what the platform emits.
    """
    a = (f'<image edit="true" height="{fmt(h)}" left="0" placeholder="true"'
         f' top="0" width="{fmt(w)}"')
    if abs(x) > 1e-9:
        a += f' x="{fmt(x)}"'
    if abs(y) > 1e-9:
        a += f' y="{fmt(y)}"'
    return a + "/>"


def data_key(page_attrs, frames):
    hdr = f'<?xml version="1.0" encoding="UTF-8"?><page {page_attrs}>'
    parts = [img(*f) for f in frames]
    body = parts[0] + "".join("\n" + p for p in parts[1:])
    return "  data: |-\n    " + (hdr + body + "</page>").replace("\n", "\n    ") + "\n"


def shape_key(frames):
    return tuple(sorted(tuple(round(v, 2) for v in f) for f in frames))


def select(candidates, n):
    """Pick n entries balanced across groups, preserving library order."""
    if n >= len(candidates):
        return candidates[:n]
    by = {}
    for c in candidates:
        by.setdefault(c[0], []).append(c)
    out, i = [], 0
    while len(out) < n:
        took = False
        for g in sorted(by):
            if i < len(by[g]) and len(out) < n:
                out.append(by[g][i]); took = True
        if not took:
            break
        i += 1
    order = {id(c): k for k, c in enumerate(candidates)}
    return sorted(out, key=lambda c: order[id(c)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--groups", default="1,2,3,4,5",
                    help="photo-count groups to draw from, e.g. 1,2,3")
    ap.add_argument("--margin", type=float, help="override derived margin, mm")
    ap.add_argument("--gutter", type=float, help="override derived gutter, mm")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not a.dry_run and not a.dst:
        sys.exit("--out is required unless --dry-run")

    work = tempfile.mkdtemp()
    yml, members = unpack(a.src, work)
    doc = pxload.load(yml)
    layouts = [l for l in doc.get("layouts", []) if l.get("layout")]

    populated = [l for l in layouts if "<image" in (l.get("data") or "")]
    w, h, gutter, margin, votes = derive(populated)
    if a.gutter: gutter = a.gutter
    if a.margin: margin = a.margin
    page = Page(w, h, gutter=gutter, margin=margin)

    print(f"page        {fmt(w)} x {fmt(h)} mm  ({w/25.4:.4g} x {h/25.4:.4g} in)")
    print(f"gutter      {fmt(gutter)} mm ({gutter/25.4:.4g} in)")
    print(f"margin      {fmt(margin)} mm ({margin/25.4:.4g} in)")
    print(f"evidence    {votes}")

    # tag vocabulary: read it off the theme, never invent it
    seen_tags = Counter(t for l in layouts for t in (l.get("tags") or []))
    print(f"existing    {len(populated)} populated, tags {dict(seen_tags)}")
    for g, t in TAGS.items():
        if seen_tags and t not in seen_tags and g <= max(
                [int(x[0]) for x in seen_tags if x[0].isdigit()] or [0]):
            print(f"note        theme has no '{t}' layout yet; using that string")

    text = open(yml).read()
    head, blocks, tail = split_layouts(text)
    blank_idx = [i for i, b in enumerate(blocks) if is_blank(b)]
    print(f"blanks      {len(blank_idx)} empty layouts to fill "
          f"(of {len(blocks)} in the theme)")
    if not blank_idx:
        sys.exit("nothing to do - no empty layouts in this export. Create them in "
                 "admin (Design > Layouts > New) and export again.")

    groups = {int(g) for g in a.groups.split(",")}
    existing_shapes = {shape_key([(float(e.get("x", 0)), float(e.get("y", 0)),
                                  float(e.get("width")), float(e.get("height")))
                                 for e in ET.fromstring(l["data"])])
                       for l in populated}
    allc = build(page, groups)
    cands = [c for c in allc if shape_key(c[2]) not in existing_shapes]
    if len(allc) - len(cands):
        print(f"skipped     {len(allc)-len(cands)} archetype(s) already in the theme")
    chosen = select(cands, len(blank_idx))
    if len(chosen) < len(blank_idx):
        print(f"WARNING     only {len(chosen)} distinct archetypes available for "
              f"{len(blank_idx)} blanks; {len(blank_idx)-len(chosen)} stay empty")

    for i, (g, name, frames) in zip(blank_idx, chosen):
        b = blocks[i]
        attrs = page_attrs_of(b)
        m = DATA_KEY.search(b)
        if not m:
            sys.exit(f"could not locate the data key in layout block {i}")
        b = b[:m.start()] + data_key(attrs, frames) + b[m.end():]
        if b.count("  tags: []\n") != 1:
            sys.exit(f"layout block {i}: expected exactly one empty tags key")
        b = b.replace("  tags: []\n", f"  tags:\n  - {TAGS[g]}\n", 1)
        assert "<image" in b and "  data: |-\n" in b
        blocks[i] = b
    text2 = head + "".join(blocks) + tail

    print()
    for i, (g, name, frames) in enumerate(chosen, 1):
        print(f"  {i:02d}  {TAGS[g]:<10} {len(frames):>2} frame(s)  {name}")

    if a.dry_run:
        print("\ndry run - nothing written")
        return

    open(yml, "w").write(text2)
    root = os.path.dirname(yml)
    with tarfile.open(a.dst, "w:gz") as t:
        for m in members:                       # same member order as the source
            t.add(os.path.join(root, m.lstrip("./")), arcname=m, recursive=False)
    print(f"\nwrote {a.dst}")
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Retarget a whole Pixfizz template export (__print_product.yml) to a new size:
resize the definition XML, both print themes, the layouts, re-sync the design pages
from the layouts they reference, and rename everything.

Text-surgical: only the `layout:` node and the `data:` nodes are rewritten, so Ruby
YAML tags, key order and every untouched field survive byte-identical.
"""
import re, sys, argparse, yaml
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import pxload
import pxgeom as G

PG = re.compile(r'<page\b[^>]*?>')
EL = re.compile(r'<(image|text|background|clipart|shape|ipage)\b([^>]*?)/>')
AT = re.compile(r'(\w[\w-]*)="([^"]*)"')

def fmt(v):
    s = "%.12f" % v
    s = s.rstrip("0").rstrip(".")
    return s if s else "0"

def near(a, b, tol=0.01):
    return abs(a - b) <= tol

def page_dims(xml):
    m = PG.search(xml)
    if not m: return None
    a = dict(AT.findall(m.group(0)))
    try: return float(a["width"]), float(a["height"])
    except KeyError: return None

def set_page(xml, W, H):
    def rep(m):
        s = m.group(0)
        s = re.sub(r'\bwidth="[^"]*"', 'width="%s"' % fmt(W), s)
        s = re.sub(r'\bheight="[^"]*"', 'height="%s"' % fmt(H), s)
        return s
    return PG.sub(rep, xml, count=1)

def frames(xml):
    out = []
    for tag, at in EL.findall(xml):
        if tag == "ipage": continue
        a = {k: v for k, v in AT.findall(at)}
        if "width" in a and "height" in a:
            out.append((float(a.get("x", 0)), float(a.get("y", 0)),
                        float(a["width"]), float(a["height"])))
    return out

def recompose(xml, SW, SH, TW, TH, recentre=True):
    """Rule 'margin': scale all four content-bbox margins by min(fx,fy); frames fill the rest."""
    fr = frames(xml)
    if not fr:
        return set_page(xml, TW, TH)
    s = min(TW / SW, TH / SH)
    L = min(f[0] for f in fr); T = min(f[1] for f in fr)
    R = SW - max(f[0] + f[2] for f in fr); B = SH - max(f[1] + f[3] for f in fr)
    nL, nR, nT, nB = L * s, R * s, T * s, B * s
    if recentre and abs(L - R) < 0.75: nL = nR = (nL + nR) / 2.0
    if recentre and abs(T - B) < 0.75: nT = nB = (nT + nB) / 2.0
    cw, ch = SW - L - R, SH - T - B
    gx = (TW - nL - nR) / cw if cw else 1.0
    gy = (TH - nT - nB) / ch if ch else 1.0
    i = [0]
    def rep(m):
        tag, at = m.group(1), m.group(2)
        if tag == "ipage": return m.group(0)
        a = dict(AT.findall(at))
        if "width" not in a or "height" not in a: return m.group(0)
        x, y, w, h = fr[i[0]]; i[0] += 1
        if w * h >= 0.99 * SW * SH and x <= 1e-9 and y <= 1e-9:
            nx, ny, nw, nh = 0.0, 0.0, TW, TH
        else:
            nx = nL + (x - L) * gx; ny = nT + (y - T) * gy
            nw = w * gx; nh = h * gy
        out = m.group(0)
        for k, v in (("width", nw), ("height", nh)):
            out = re.sub(r'\b%s="[^"]*"' % k, '%s="%s"' % (k, fmt(v)), out)
        for k, v in (("x", nx), ("y", ny)):
            if re.search(r'\b%s="' % k, out):
                out = re.sub(r'\b%s="[^"]*"' % k, '%s="%s"' % (k, fmt(v)), out)
            elif abs(v) > 1e-12:
                out = out[:-2] + ' %s="%s"/>' % (k, fmt(v))
        return out
    return set_page(EL.sub(rep, xml), TW, TH)

def sync_from_layout(page_xml, layout_xml):
    """Replace a design page's frames with the (already-resized) layout's frames."""
    head = PG.search(page_xml).group(0)
    els = []
    for tag, at in EL.findall(layout_xml):
        if tag == "ipage": continue
        a = dict(AT.findall(at))
        a["layout"] = "true"
        order = ["edit", "height", "layout", "left", "placeholder", "top", "width", "x", "y"]
        keys = [k for k in order if k in a] + [k for k in a if k not in order]
        els.append("<%s %s/>" % (tag, " ".join('%s="%s"' % (k, a[k]) for k in keys)))
    return '<?xml version="1.0" encoding="UTF-8"?>' + head + "\n".join(els) + "</page>"

def node_span(lines, i):
    """Extent of the YAML node whose key line is lines[i]."""
    indent = len(lines[i]) - len(lines[i].lstrip())
    j = i + 1
    while j < len(lines):
        ln = lines[j]
        if ln.strip() and (len(ln) - len(ln.lstrip())) <= indent: break
        j += 1
    return j

def block(indent, key, text):
    pad = " " * (indent + 2)
    body = "\n".join(pad + l for l in text.split("\n"))
    return "%s%s: |-\n%s" % (" " * indent, key, body)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("--out", required=True)
    ap.add_argument("--from-spread", required=True, help="source spread mm, WxH")
    ap.add_argument("--to-spread", required=True, help="target spread mm, WxH")
    ap.add_argument("--from-inch", required=True, help='definition page size, e.g. 8.000x6.000')
    ap.add_argument("--to-inch", required=True, help='e.g. 10.000x7.000')
    ap.add_argument("--rename", action="append", default=[], help="OLD=NEW, applied to names/codes")
    ap.add_argument("--sync-pages", action="store_true", help="rewrite design pages from their referenced layouts")
    ap.add_argument("--rule", default="margin", choices=["margin","uniform","fit","stretch","cell"])
    a = ap.parse_args()

    SW, SH = (float(v) for v in a.from_spread.lower().split("x"))
    TW, TH = (float(v) for v in a.to_spread.lower().split("x"))
    d = pxload.load(a.src)
    raw = open(a.src).read()
    lines = raw.split("\n")

    # --- collect the parsed data XMLs in file order -------------------------------
    ordered, layout_by_id = [], {}
    for th in d["print_themes"]:
        for t in (th.get("templates") or []):
            ordered.append(("tmpl", th["code"], t))
        for l in (th.get("layouts") or []):
            ordered.append(("layout", th["code"], l))
            layout_by_id[str(l["id"])] = l
    report = []

    # --- pass 1: transform layouts, remember the new XML --------------------------
    new_xml = {}
    for kind, thcode, node in ordered:
        xml = node["data"]
        dims = page_dims(xml)
        if kind == "layout":
            new_xml[id(node)] = recompose(xml, SW, SH, TW, TH)
            report.append(("layout %s" % node["id"], "recomposed %gx%g -> %gx%g" % (SW, SH, TW, TH)))
        else:
            if dims and near(dims[0], SW) and near(dims[1], SH):
                lid = dict(AT.findall(PG.search(xml).group(0))).get("layout_id")
                if a.sync_pages and lid and lid in layout_by_id:
                    src_layout = new_xml.get(id(layout_by_id[lid]))
                    if src_layout is None:
                        src_layout = recompose(layout_by_id[lid]["data"], SW, SH, TW, TH)
                        new_xml[id(layout_by_id[lid])] = src_layout
                    new_xml[id(node)] = sync_from_layout(set_page(xml, TW, TH), src_layout)
                    report.append(("%s/%s" % (thcode, node["name"]), "resized + re-synced from layout %s" % lid))
                else:
                    new_xml[id(node)] = recompose(xml, SW, SH, TW, TH)
                    report.append(("%s/%s" % (thcode, node["name"]), "resized %gx%g -> %gx%g" % (SW, SH, TW, TH)))
            else:
                new_xml[id(node)] = xml
                report.append(("%s/%s" % (thcode, node["name"]),
                               "LEFT ALONE (page %s) - not the source spread size" % (("%gx%g" % dims) if dims else "none")))

    # --- pass 2: splice data: nodes ----------------------------------------------
    out, i, k = [], 0, 0
    while i < len(lines):
        m = re.match(r'^(\s*)data:', lines[i])
        if m and k < len(ordered):
            j = node_span(lines, i)
            out.append(block(len(m.group(1)), "data", new_xml[id(ordered[k][2])]))
            k += 1; i = j; continue
        m2 = re.match(r'^layout:', lines[i])
        if m2:
            j = node_span(lines, i)
            defn = d["layout"]
            fw, fh = a.from_inch.lower().split("x"); tw_, th_ = a.to_inch.lower().split("x")
            before = defn
            defn = defn.replace('width="%s" height="%s"' % (fw, fh), 'width="%s" height="%s"' % (tw_, th_))
            n = before.count('width="%s" height="%s"' % (fw, fh))
            report.append(("definition XML", "%d page tags %s -> %s" % (n, a.from_inch, a.to_inch)))
            out.append("layout: " + yaml.dump(defn, default_style='"', width=10**6).rstrip().rstrip("\n"))
            i = j; continue
        out.append(lines[i]); i += 1
    txt = "\n".join(out)
    if k != len(ordered):
        sys.exit("ERROR: matched %d data nodes but parsed %d" % (k, len(ordered)))

    # --- pass 3: renames ----------------------------------------------------------
    for r in a.rename:
        old, new = r.split("=", 1)
        c = txt.count(old)
        txt = txt.replace(old, new)
        report.append(("rename", "%-26s -> %-26s  (%d occurrences)" % (repr(old), repr(new), c)))

    open(a.out, "w").write(txt)
    ipages = sum(len(re.findall(r"<ipage", (t.get("data") or "")))
                 for th in d["print_themes"] for t in (th.get("templates") or []))
    if ipages:
        report.append(("!! <ipage> ELEMENTS", "%d found - inline live previews. Their zoom/left/top were NOT"
                                              " rescaled; check every preview by eye." % ipages))
    print("%-26s %s" % ("WHAT", "ACTION"))
    for kk, vv in report: print("%-26s %s" % (kk, vv))
    print("\nwrote", a.out)

if __name__ == "__main__":
    main()

"""Analyze a planner PDF: structure, named destinations, link graph,
text spans (font/size/color/bbox), vector drawings, fonts.

Usage:
    python3 analyze.py <pdf> [--pages 0,1,2,70,71] [--links] [--text] [--drawings]
                        [--out report.json]

Used both for the reference planner (structure ground truth) and for the
user's redesigned template pages (design token extraction).
"""

from __future__ import annotations

import argparse
import collections
import json
import sys

import pymupdf


def font_inventory(doc):
    out = {}
    for pno in range(len(doc)):
        for f in doc.get_page_fonts(pno, full=True):
            xref, ext, ftype, basefont, name, enc = f[:6]
            out[basefont] = ftype
    return out


def named_destinations(doc):
    """Return dict name -> page number for all named destinations."""
    return doc.resolve_names()


def link_graph(doc, limit_pages=None):
    edges = []
    for pno in range(len(doc)):
        if limit_pages and pno not in limit_pages:
            continue
        page = doc[pno]
        for link in page.get_links():
            if link["kind"] == pymupdf.LINK_GOTO:
                dest = link.get("page", -1)
                edges.append({"from": pno, "to": dest, "rect": [round(v, 1) for v in link["from"]],
                              "named": link.get("nameddest", "") or link.get("name", "")})
            elif link["kind"] == pymupdf.LINK_NAMED:
                edges.append({"from": pno, "to": None, "rect": [round(v, 1) for v in link["from"]],
                              "named": link.get("nameddest", "") or link.get("name", "")})
    return edges


def span_dump(doc, pno):
    page = doc[pno]
    out = []
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                out.append({
                    "text": text[:60],
                    "font": span["font"],
                    "size": round(span["size"], 2),
                    "color": f"#{span['color']:06x}",
                    "bbox": [round(v, 1) for v in span["bbox"]],
                    "flags": span["flags"],
                })
    return out


def drawing_dump(doc, pno, max_items=400):
    page = doc[pno]
    out = []
    for d in page.get_drawings():
        fill = d.get("fill")
        stroke = d.get("color")
        w = d.get("width")
        item_kinds = collections.Counter(i[0] for i in d["items"])
        out.append({
            "type": d["type"],
            "rect": [round(v, 1) for v in d["rect"]],
            "fill": fill and [round(c, 3) for c in fill],
            "stroke": stroke and [round(c, 3) for c in stroke],
            "width": w,
            "items": dict(item_kinds),
            "n_items": len(d["items"]),
        })
        if len(out) >= max_items:
            break
    return out


def classify_page(doc, pno, named_by_page):
    """Classify a reference-planner page by its named destination + text."""
    page = doc[pno]
    text = page.get_text("text", sort=True)
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    targets = named_by_page.get(pno, [])
    return {"first_line": first_line[:80], "targets": targets}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", default="")
    ap.add_argument("--links", action="store_true")
    ap.add_argument("--text", action="store_true")
    ap.add_argument("--drawings", action="store_true")
    ap.add_argument("--fonts", action="store_true")
    ap.add_argument("--classify", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    print(f"pages: {len(doc)}  size: {doc[0].rect}")

    named = named_destinations(doc)
    print(f"named destinations: {len(named)}")
    named_by_page = collections.defaultdict(list)
    for name, info in named.items():
        named_by_page[info.get("page", -1)].append(name)

    report = {"n_pages": len(doc), "page_rect": list(doc[0].rect),
              "named_count": len(named)}

    if args.fonts:
        inv = font_inventory(doc)
        report["fonts"] = inv
        print("fonts:")
        for bf, t in sorted(inv.items()):
            print(f"  {t:10s} {bf}")

    if args.classify:
        cls = [classify_page(doc, p, named_by_page) for p in range(len(doc))]
        report["classification"] = cls

    if args.links:
        edges = link_graph(doc)
        report["n_links"] = len(edges)
        print(f"links: {len(edges)}")
        # summary: link count per page
        per = collections.Counter(e["from"] for e in edges)
        report["links_per_page"] = dict(sorted(per.items()))

    pages = [int(x) for x in args.pages.split(",") if x.strip() != ""] if args.pages else []
    if args.text and pages:
        report["spans"] = {p: span_dump(doc, p) for p in pages}
        for p in pages:
            print(f"--- page {p} text spans ---")
            for s in report["spans"][p][:60]:
                print(f"  {s['bbox']} {s['font'][:28]:28s} {s['size']:5.1f} {s['color']} {s['text']!r}")
    if args.drawings and pages:
        report["drawings"] = {p: drawing_dump(doc, p) for p in pages}
        for p in pages:
            print(f"--- page {p} drawings (first 40) ---")
            for d in report["drawings"][p][:40]:
                print(f"  {d['type']:2s} rect={d['rect']} fill={d['fill']} stroke={d['stroke']} w={d['width']} items={d['items']}")

    if args.out:
        with open(args.out, "w") as f:
            json.dump(report, f, indent=1, default=str)
        print("wrote", args.out)


if __name__ == "__main__":
    main()

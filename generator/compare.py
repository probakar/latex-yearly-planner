"""Quantitative visual comparison: generated vs reference planner.

For representative pages, extracts text spans from both PDFs and matches each
reference span to the nearest generated span with the same text, reporting
position deltas (dx, dy). A small median delta + high match rate = faithful
layout reproduction (fonts differ: STIX vs Latin Modern by design in the
baseline; final design will carry its own fonts).
"""

from __future__ import annotations

import argparse
import statistics

import pymupdf

PAGES = [0, 1, 2, 6, 18, 19, 71, 72, 435, 436, 801, 1166, 1169, 1282]


def spans(doc, pno):
    out = []
    for b in doc[pno].get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                t = s["text"].strip()
                if not t or s["font"].startswith("LCIRCLE"):
                    continue
                out.append((t, s["bbox"][0], s["bbox"][1], s["size"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--ref", default="../ref/reference_planner_2027.pdf")
    ap.add_argument("--pages", default="")
    ap.add_argument("--tol", type=float, default=6.0)
    args = ap.parse_args()

    mine = pymupdf.open(args.pdf)
    ref = pymupdf.open(args.ref)
    pages = [int(x) for x in args.pages.split(",") if x] or PAGES

    total_ref, total_matched, all_dx, all_dy = 0, 0, [], []
    for pno in pages:
        rs, ms = spans(ref, pno), spans(mine, pno)
        dxs, dys, matched = [], [], 0
        for t, x, y, size in rs:
            best = None
            for t2, x2, y2, s2 in ms:
                if t2 != t:
                    continue
                d = abs(x - x2) + abs(y - y2)
                if best is None or d < best[0]:
                    best = (d, x2 - x, y2 - y)
            if best and best[0] < 80:
                matched += 1
                dxs.append(best[1])
                dys.append(best[2])
        total_ref += len(rs)
        total_matched += matched
        all_dx += dxs
        all_dy += dys
        med_dx = statistics.median(dxs) if dxs else float("nan")
        med_dy = statistics.median(dys) if dys else float("nan")
        within = sum(1 for a, b in zip(dxs, dys) if abs(a) <= args.tol and abs(b) <= args.tol)
        print(f"p{pno:4d}: ref spans {len(rs):4d}, matched {matched:4d} "
              f"({100*matched/max(1,len(rs)):5.1f}%), med dx {med_dx:+6.1f} dy {med_dy:+6.1f}, "
              f"within ±{args.tol}pt: {within}/{matched}")

    print(f"\nTOTAL: {total_matched}/{total_ref} spans matched "
          f"({100*total_matched/max(1,total_ref):.1f}%)")
    if all_dx:
        print(f"median dx {statistics.median(all_dx):+.2f} pt, median dy {statistics.median(all_dy):+.2f} pt")
        print(f"95% |dx| <= {sorted(abs(x) for x in all_dx)[int(len(all_dx)*0.95)]:.1f} pt, "
              f"95% |dy| <= {sorted(abs(y) for y in all_dy)[int(len(all_dy)*0.95)]:.1f} pt")


if __name__ == "__main__":
    main()

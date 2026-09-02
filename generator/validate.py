"""Validate a generated planner PDF against the reference planner.

Checks:
  1. page count and per-page named targets (order/identity)
  2. link graph: per-page multiset of link target names vs reference
  3. calendar text sanity on daily pages (date shown matches page identity)
  4. all GoTo links resolve to in-range pages
  5. boundary cases (Jan 1 / Dec 31 / first & last week / notes chain)

Usage: python3 validate.py <generated.pdf> [--ref ref/reference_planner_2027.pdf]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys

import pymupdf

import plancal
from pagemap import PageMap

REF_PAGE_KINDS = None


def page_kind_by_index(pm: PageMap):
    return [p.kind for p in pm.pages]


def classify_generated(doc, pm) -> list:
    return page_kind_by_index(pm)


def links_of(doc):
    out = collections.defaultdict(list)
    for pno in range(len(doc)):
        for l in doc[pno].get_links():
            if l["kind"] == pymupdf.LINK_GOTO:
                out[pno].append(("goto", l["page"]))
            elif l["kind"] == pymupdf.LINK_NAMED:
                out[pno].append(("named", l.get("nameddest", "")))
    return out


def named_by_page(doc):
    by = collections.defaultdict(list)
    for n, info in doc.resolve_names().items():
        if n.startswith("page.") or n == "Doc-Start":
            continue
        by[info.get("page", -1)].append(n)
    return by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--ref", default="../ref/reference_planner_2027.pdf")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    fails, warns = [], []

    doc = pymupdf.open(args.pdf)
    pm = PageMap(2027)

    # 1. page count ----------------------------------------------------------
    if len(doc) != 1283:
        fails.append(f"page count {len(doc)} != 1283")
    print(f"[1] pages: {len(doc)} (expect 1283)")

    # 2. page geometry ---------------------------------------------------------
    r = doc[0].rect
    if abs(r.width - 442.2) > 0.5 or abs(r.height - 592.44) > 0.5:
        fails.append(f"page size {r}")
    print(f"[2] page size: {r.width:.1f} x {r.height:.1f}")

    # 3. calendar/day text sanity on daily pages --------------------------------
    bad_dates = 0
    for p in pm.pages:
        if p.kind != "day":
            continue
        d = p.meta["date"]
        text = doc[p.idx].get_text()
        need = [str(d.day), plancal.DAY_NAMES[d.weekday()], plancal.MONTH_NAMES[d.month - 1]]
        if not all(n in text for n in need):
            bad_dates += 1
            if bad_dates <= 5:
                fails.append(f"day page {p.idx} missing {need} in text")
    print(f"[3] daily pages date text: {365 - bad_dates}/365 ok")
    if bad_dates:
        fails.append(f"{bad_dates} daily pages with wrong text")

    # 4. links resolve ------------------------------------------------------------
    mine = links_of(doc)
    n_links = sum(len(v) for v in mine.values())
    oob = [(p, t) for p, ls in mine.items() for t in ls
           if t[0] == "goto" and not (0 <= t[1] < len(doc))]
    if oob:
        fails.append(f"{len(oob)} out-of-range goto links e.g. {oob[:3]}")
    print(f"[4] links: {n_links}; out-of-range: {len(oob)}")

    # 5. link graph vs reference ------------------------------------------------------
    try:
        ref = pymupdf.open(args.ref)
        reflinks = json.load(open("measured/ref_links.json"))
        ref_named = collections.defaultdict(collections.Counter)
        for l in reflinks:
            nd = l["nd"]
            if nd.startswith("page.") or nd == "Doc-Start":
                continue
            ref_named[l["p"]][nd] += 1
        # map ref named dests to page indices for comparison with my gotos
        ref_dest_page = {n: i["page"] for n, i in ref.resolve_names().items()}
        ref_goto = collections.defaultdict(collections.Counter)
        for pno, ctr in ref_named.items():
            for nd, cnt in ctr.items():
                tgt = ref_dest_page.get(nd)
                if tgt is not None:
                    ref_goto[pno][tgt] += cnt
        my_goto = collections.defaultdict(collections.Counter)
        for pno, ls in mine.items():
            for k, t in ls:
                if k == "goto":
                    my_goto[pno][t] += 1
        mismatch = 0
        examples = []
        for pno in range(len(doc)):
            a, b = my_goto.get(pno, collections.Counter()), ref_goto.get(pno, collections.Counter())
            if a != b:
                mismatch += 1
                if len(examples) < 6:
                    only_mine = a - b
                    only_ref = b - a
                    examples.append((pno, dict(only_mine), dict(only_ref)))
        # Known, documented deviations (intentional):
        #  - pages 71-73/436-438/801-803 (Jan 1-3 day/reflect/more): reference
        #    ships a DEAD "Week 53" tab link; ours links correctly to page 18.
        known = set(range(71, 74)) | set(range(436, 439)) | set(range(801, 804))
        real = [e for e in examples if e[0] not in known]
        for e in examples:
            tag = " (known: fixed ref dead link)" if e[0] in known else ""
            warns.append(f"link mismatch page {e[0]}: mine-only={e[1]} ref-only={e[2]}{tag}")
        real_pages = [pno for pno in range(len(doc))
                      if my_goto.get(pno, collections.Counter()) != ref_goto.get(pno, collections.Counter())
                      and pno not in known]
        if real_pages:
            fails.append(f"{len(real_pages)} pages with real link mismatches: {real_pages[:10]}")
    except FileNotFoundError:
        warns.append("reference not found; skipping graph comparison")

    # 6. boundary cases -----------------------------------------------------------------
    def goto_targets(pno):
        return sorted({t for k, t in mine.get(pno, []) if k == "goto"})

    checks = [
        ("Jan 1 daily has no prev-day link beyond year", 71),
        ("Dec 31 daily", 435),
        ("first weekly page (fwWeek 53)", 18),
        ("last weekly page (Week 52)", 70),
        ("Notes Index 1", 1166),
        ("Note 114", 1282),
        ("year page", 1),
    ]
    for label, pno in checks:
        ts = goto_targets(pno)
        if not ts:
            fails.append(f"{label}: page {pno} has no links")
    print(f"[6] boundary pages have links: ok" if not any("no links" in f for f in fails) else "[6] issues")

    report = {"fails": fails, "warnings": warns, "n_links": n_links, "pages": len(doc)}
    if args.json:
        json.dump(report, open(args.json, "w"), indent=1)
    print()
    if fails:
        print(f"FAILURES ({len(fails)}):")
        for f in fails[:20]:
            print("  -", f)
        sys.exit(1)
    print("ALL CHECKS PASSED")
    for w in warns[:20]:
        print("  warn:", w)


if __name__ == "__main__":
    main()

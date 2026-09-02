"""Build the complete planner PDF.

Pipeline:
  1. PageMap (structure + named targets)
  2. fonts (CM-like STIX via matplotlib; DejaVu for symbols)
  3. render every page via the active design's renderers
  4. resolve LinkOp targets -> page indices, insert GoTo link annotations
  5. save + build report (JSON) for validation

Usage:
  python3 build.py [--year 2027] [--out ../out/planner_2027.pdf] [--design olive]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import time

import pymupdf

import plancal
from draw import DotAssets
from plancal import MONTH_NAMES, MONTH_SHORT
from draw import Fonts, Painter, LinkOp, TextOp
from design import Design
from pagemap import PageMap

sys.path.insert(0, str(pathlib.Path(__file__).parent))


# ---------------------------------------------------------------------------
# font setup
# ---------------------------------------------------------------------------

def setup_fonts() -> Fonts:
    import matplotlib
    md = pathlib.Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    fonts = Fonts()
    fonts.register_file("main", md / "STIXGeneral.ttf")
    fonts.register_file("bold", md / "STIXGeneralBol.ttf")
    fonts.register_file("italic", md / "STIXGeneralItalic.ttf")
    # DejaVu has ⟨ ⟩ □ glyphs
    dv = pathlib.Path("/usr/share/fonts/truetype/dejavu")
    if (dv / "DejaVuSans.ttf").exists():
        fonts.register_file("dejavu", dv / "DejaVuSans.ttf")
        fonts.alias("sym", "dejavu")       # ⟨ ⟩ □ glyph coverage
        fonts.alias("sym-next", "dejavu")
    else:
        fonts.alias("sym", "main")
        fonts.alias("sym-next", "main")
    return fonts


# ---------------------------------------------------------------------------
# per-page context (headings, tabs, side-nav selection) — design independent
# ---------------------------------------------------------------------------

def week_of_day(pm, dd: dt.date):
    for w in pm.yweeks:
        if w[0] <= dd <= w[6]:
            return w
    raise KeyError(dd)


def page_context(pm: PageMap, page, fonts, design) -> dict:
    kind = page.kind
    ctx = {"fonts": fonts, "design": design, "pm": pm, "page": page}
    y = design.year
    import measured_geom as G

    def day_style_heading(dd, prefix, leaf):
        prev, nxt = dd - dt.timedelta(days=1), dd + dt.timedelta(days=1)
        size = G.HEAD_SIZES[kind]
        parts = []
        # Go Day.PrevExists/NextExists evaluate on the current day
        has_prev = dd.month > 1 or dd.day > 1
        has_next = dd.month < 12 or dd.day < 31
        if has_prev:
            parts.append(("\u27e8", size - 4.0, plancal.day_ref(prev, prefix), False, "sym"))
        numw = fonts.text_width(str(dd.day), "main", size)
        num_x = G.TEXT_X0 if not has_prev else G.TEXT_X0 + 20.5
        target = plancal.day_ref(dd) if leaf else None
        parts.append((str(dd.day), size, target, False, "main"))
        vline_x = num_x + numw + 6.1
        sub_x = vline_x + 10.5
        if has_next:
            parts.append(("\u27e9", size - 4.0, plancal.day_ref(nxt, prefix), False, "sym-next"))
        return parts, vline_x, sub_x, has_next

    if kind == "year":
        ctx["heading"] = [(str(y), G.HEAD_SIZES["year"], "Calendar", False, "main")]
        ctx["tabs"] = [("Calendar", "Calendar"), ("Notes", "Notes Index")]
        ctx["tab_selected"] = ["Calendar"]
        ctx["side_sel_month"] = None
        ctx["side_sel_quarters"] = []
    elif kind == "quarter":
        q = page.meta["quarter"]
        ctx["heading"] = [(f"Q{q}", G.HEAD_SIZES["quarter"], f"Q{q}", False, "main")]
        ctx["tabs"] = [("Calendar", "Calendar"), ("Notes", "Notes Index")]
        ctx["tab_selected"] = []
        ctx["side_sel_month"] = None
        ctx["side_sel_quarters"] = [q]
    elif kind == "month":
        m = page.meta["month"]
        ctx["heading"] = [(MONTH_NAMES[m - 1], G.HEAD_SIZES["month"],
                           MONTH_NAMES[m - 1], False, "main")]
        ctx["tabs"] = [("Calendar", "Calendar"), ("Notes", "Notes Index")]
        ctx["tab_selected"] = []
        ctx["side_sel_month"] = m
        ctx["side_sel_quarters"] = [plancal.quarter_of(m)]
    elif kind == "week":
        days = page.meta["days"]
        wn = plancal.week_number(days)
        size = G.HEAD_SIZES["week"]
        head = []
        if page.meta["prev_exists"]:
            head.append(("\u27e8", size - 1.83,
                         plancal.week_ref(plancal.prev_week_days(days), y), False, "sym"))
        head.append(("Week", size, plancal.week_ref(days, y), False, "main"))
        head.append((str(wn), size, None, False, "main"))
        if page.meta["next_exists"]:
            head.append(("\u27e9", size - 1.83,
                         plancal.week_ref(plancal.next_week_days(days), y), False, "sym"))
        ctx["heading"] = head
        ctx["tabs"] = [("Calendar", "Calendar"), ("Notes", "Notes Index")]
        ctx["tab_selected"] = []
        sel_m, sel_q = set(), set()
        for dd in days:
            if dd.year == y:
                sel_m.add(dd.month)
                sel_q.add(plancal.quarter_of(dd.month))
        ctx["side_sel_month"] = sorted(sel_m)
        ctx["side_sel_quarters"] = sorted(sel_q)
    elif kind in ("day", "reflect", "day_notes"):
        dd = page.meta["date"]
        prefix = {"day": "", "reflect": "Reflect", "day_notes": "More"}[kind]
        leaf = {"day": None, "reflect": "Reflect", "day_notes": "Notes"}[kind]
        head, vline_x, sub_x, has_next = day_style_heading(dd, prefix, leaf)
        ctx["heading"] = head
        ctx["vline_x"] = vline_x
        ctx["sub_x"] = sub_x
        ctx["sub_arrow"] = has_next
        ctx["heading_sub"] = MONTH_NAMES[dd.month - 1]
        ctx["heading_weekday"] = plancal.DAY_NAMES[dd.weekday()]
        wk = week_of_day(pm, dd)
        ctx["tabs"] = [(f"Week {plancal.week_number(wk)}", plancal.week_ref(wk, y)),
                       ("Calendar", "Calendar"), ("Notes", "Notes Index")]
        ctx["tab_selected"] = []
        ctx["side_sel_month"] = dd.month
        ctx["side_sel_quarters"] = [plancal.quarter_of(dd.month)]
        ctx["week_days"] = wk
    elif kind == "notes_index":
        i = page.meta["index"]
        size = G.HEAD_SIZES["notes_index"]
        head = []
        if i > 1:
            prev_t = "Notes Index" if i - 1 == 1 else f"Notes Index {i-1}"
            head.append(("\u27e8", size - 1.83, prev_t, False, "sym"))
        head.append(("Index Notes", size, page.target, False, "main"))
        if i < design.notes_index_pages:
            head.append(("\u27e9", size - 1.83, f"Notes Index {i+1}", False, "sym"))
        ctx["heading"] = head
        # reference: Notes tab on every notes-index page targets the FIRST
        # index page ("Notes Index"); selected state marks the current one.
        ctx["tabs"] = [("Calendar", "Calendar"), ("Notes", "Notes Index")]
        ctx["tab_selected"] = ["Notes"]
        ctx["side_sel_month"] = None
        ctx["side_sel_quarters"] = []
    elif kind == "note":
        n = page.meta["number"]
        ip = page.meta["indexpage"]
        ctx["heading"] = [(f"Note {n}", G.HEAD_SIZES["note"], page.target, False, "main")]
        ntgt = "Notes Index" if ip == 1 else f"Notes Index {ip}"
        ctx["tabs"] = [("Calendar", "Calendar"), ("Notes", ntgt)]
        ctx["tab_selected"] = []
        ctx["side_sel_month"] = None
        ctx["side_sel_quarters"] = []
    else:  # title
        ctx["heading"] = []
        ctx["tabs"] = []
    return ctx


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build(year: int = 2027, out: str = "out/planner_2027.pdf",
          design: Design = None, renderers=None, progress_every=200, limit=None) -> dict:
    design = design or Design(year=year)
    fonts = setup_fonts()
    pm = PageMap(year)

    if renderers is None:
        import render_olive as ro
        renderers = ro.RENDERERS

    pages = pm.pages if limit is None else pm.pages[:limit]

    doc = pymupdf.open()
    dot_assets = DotAssets()
    t0 = time.time()
    all_links: list[tuple[int, LinkOp]] = []
    all_deferred: list[tuple] = []

    for page in pages:
        ctx = page_context(pm, page, fonts, design)
        ctx["design"] = design
        pyp = doc.new_page(width=design.page_w, height=design.page_h)
        painter = Painter(pyp, fonts, dot_assets)
        painter.defer_dots = True
        ops = renderers[page.kind](design, ctx, page, pm)
        painter.execute(ops)
        all_deferred.extend(painter.deferred_dots)
        for lop in painter.links:
            all_links.append((page.idx, lop))
        if progress_every and page.idx % progress_every == 0:
            print(f"  rendered page {page.idx}/{len(pm.pages)} ({time.time()-t0:.0f}s)")

    print(f"rendered {len(pm.pages)} pages in {time.time()-t0:.0f}s")

    # stamp dot grids: first materialize every distinct size so the source
    # doc is final (pymupdf caches graft maps), then stamp.
    for _, dop in all_deferred:
        dot_assets.page_for(dop.cols, dop.rows, dop.color)
    for pno, dop in all_deferred:
        dot_assets.stamp(doc[pno], dop)
    print(f"stamped {len(all_deferred)} dot grids in {time.time()-t0:.0f}s")

    # ---- wire links -------------------------------------------------------
    wired, dead = 0, []
    for pno, lop in all_links:
        tgt_idx = pm.target_of(lop.target)
        if tgt_idx is None:
            dead.append((pno, lop.target, lop.note))
            continue
        if tgt_idx >= len(doc):
            continue  # limited/debug builds: target page not rendered
        page = doc[pno]
        page.insert_link({
            "kind": pymupdf.LINK_GOTO,
            "from": pymupdf.Rect(lop.x0, lop.y0, lop.x1, lop.y1),
            "page": tgt_idx,
            "to": pymupdf.Point(0, 0),
        })
        wired += 1
    print(f"links wired: {wired}; dead (no target): {len(dead)}")

    doc.set_metadata({
        "title": f"{year} Digital Planner",
        "author": "planner generator",
        "creator": "latex-yearly-planner (python renderer)",
    })
    outp = pathlib.Path(out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(outp), deflate=True, garbage=1)
    size = outp.stat().st_size
    print(f"saved {outp} ({size/1e6:.2f} MB)")

    report = {
        "year": year, "pages": len(pm.pages), "links_wired": wired,
        "dead_links": dead[:50], "n_dead": len(dead),
        "counts": pm.counts(), "out": str(outp), "size": size,
    }
    with open(outp.with_suffix(".buildreport.json"), "w") as f:
        json.dump(report, f, indent=1)
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2027)
    ap.add_argument("--out", default=None)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    out = args.out or f"out/planner_{args.year}.pdf"
    build(args.year, out, limit=args.limit)

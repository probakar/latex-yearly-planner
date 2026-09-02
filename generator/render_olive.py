"""Calibrated olive renderer — geometry measured from ref/reference_planner_2027.pdf.

Structure per page kind mirrors the reference exactly; coordinates come from
measured_geom.py. Dots are drawn as small filled circles matching the
LCIRCLE10 glyph pitch/size.
"""

from __future__ import annotations

import datetime as dt

import plancal
from plancal import MONTH_NAMES, MONTH_SHORT, DAY_NAMES
from draw import TextOp, LineOp, RectOp, DotGridOp, LinkOp
import measured_geom as G

# rule y per page kind (measured)
RULE_Y = {
    "year": G.HEAD_RULE_Y["B"], "notes_index": 37.5, "note": G.HEAD_RULE_Y["B"],
    "quarter": 36.6, "month": 36.8, "week": 37.6,
    "day": G.HEAD_RULE_Y["A"], "day_notes": G.HEAD_RULE_Y["A"], "reflect": 35.2,
}


def tab_pattern(kind):
    return "B" if kind in ("year", "notes_index", "note") else "A"


def dots(ops, x, y, cols, rows, color=G.LIGHT, dx=G.DOT_DX, r=G.DOT_R):
    ops.append(DotGridOp(x, y, dx, dx, r, color, cols, rows))


# ---------------------------------------------------------------------------
# header
# ---------------------------------------------------------------------------

def header_ops(d, ctx):
    kind = ctx["page"].kind
    ops = []
    fonts = ctx["fonts"]
    rule_y = RULE_Y[kind]
    pat = tab_pattern(kind)

    # -- tabs (right aligned) [Week N] | Calendar | Notes ----------------------
    tabs = ctx.get("tabs", [])
    sel = set(ctx.get("tab_selected", []))
    cells = []
    for text, target in tabs:
        tw = fonts.text_width(text, "main", G.TAB_SIZE)
        prefix = text.split(" ")[0] if text.startswith("Week") else text
        cw = G.TAB_CELL_W.get(prefix)
        if cw is None:
            cw = tw + 2 * G.TAB_PAD
        cells.append((text, target, tw, cw))
    total = sum(c[3] for c in cells)
    cx = G.TEXT_X1 - total
    cell_top = rule_y - (25.5 if pat == "A" else 22.6)
    cell_bot = cell_top + G.TAB_CELL_H
    for i, (text, target, tw, cw) in enumerate(cells):
        if i:
            ops.append(LineOp(cx - 0.2, cell_top, cx - 0.2, cell_bot, G.GRAY, G.RULE))
        if text in sel:
            ops.append(RectOp(cx, cell_top, cx + cw, cell_bot, fill=G.PRIMARY))
        color = G.WHITE if text in sel else G.PRIMARY
        ops.append(TextOp(cx + G.TAB_PAD, cell_top + 13.2, text, G.TAB_SIZE, color, "main"))
        ops.append(LinkOp(cx, cell_top, cx + cw, cell_bot, target, f"tab:{text}"))
        cx += cw

    # -- heading ---------------------------------------------------------------
    head = ctx.get("heading", [])
    x = G.TEXT_X0
    weekday = ctx.get("heading_weekday")
    deferred_arrow = None
    for text, size, target, bold, font in head:
        if font == "sym-next":
            deferred_arrow = (text, size, target)
            continue
        f = font if font != "sym" else "sym"
        if font == "sym":
            f = "sym"
        elif bold:
            f = "bold"
        else:
            f = font or "main"
        ops.append(TextOp(x, G.HEAD_BASELINE, text, size, G.PRIMARY, f))
        w = fonts.text_width(text, f, size)
        own = ctx["pm"].target_of(target) == ctx["page"].idx if target else False
        if target and not own:
            ops.append(LinkOp(x, max(0.3, G.HEAD_BASELINE - size * 0.8 - 1),
                              x + w + 2, G.HEAD_BASELINE + size * 0.2, target,
                              f"head:{text}"))
        x += w + 11.9

    # day-style two-row heading block (weekday bold / month name in sub column)
    sub = ctx.get("heading_sub")
    if sub:
        sub_x = ctx["sub_x"]
        wd = ctx.get("heading_weekday", "")
        ops.append(TextOp(sub_x, 15.9, wd, G.BODY, G.PRIMARY, "bold"))
        ops.append(TextOp(sub_x, G.DAY_HEAD_ROW2_BASE, sub, G.BODY, G.PRIMARY, "main"))
        ops.append(LineOp(ctx["vline_x"], G.HEAD_BASELINE - 18.2, ctx["vline_x"],
                          G.HEAD_BASELINE + 3.5, G.GRAY, G.RULE))
        if deferred_arrow:
            text, size, target = deferred_arrow
            ax = sub_x + max(fonts.text_width(wd, "bold", G.BODY),
                             fonts.text_width(sub, "main", G.BODY)) + 11.9
            ops.append(TextOp(ax, G.HEAD_BASELINE, text, size, G.PRIMARY, "sym"))
            w = fonts.text_width(text, "sym", size)
            ops.append(LinkOp(ax, max(0.3, G.HEAD_BASELINE - size * 0.8 - 1),
                              ax + w + 2, G.HEAD_BASELINE + size * 0.2, target,
                              f"head:{text}"))

    # -- thick rule --------------------------------------------------------------
    ops.append(LineOp(G.TEXT_X0, rule_y, G.TEXT_X1, rule_y, G.PRIMARY, G.RULE_THICK))

    # -- side nav -------------------------------------------------------------------
    ops += side_nav_ops(d, ctx, rule_y)
    return ops


def side_nav_ops(d, ctx, rule_y):
    ops = []
    fonts = ctx["fonts"]
    q_top = rule_y + 0.4
    m_top = q_top + 4 * G.SIDE_Q_CELL + G.SIDE_GAP
    sel_m = ctx.get("side_sel_month")
    if not isinstance(sel_m, list):
        sel_m = [sel_m] if sel_m else []
    sel_q = ctx.get("side_sel_quarters", [])

    def bar(top, entries, targets, selected, cell_h):
        out = []
        out.append(LineOp(G.SIDE_X0, top, G.SIDE_X1, top, G.GRAY, G.RULE))
        for i, (text, tgt) in enumerate(zip(entries, targets)):
            y0, y1 = top + i * cell_h, top + (i + 1) * cell_h
            is_sel = tgt in selected
            if is_sel:
                out.append(RectOp(G.SIDE_X0, y0, G.SIDE_X1, y1, fill=G.PRIMARY))
            w = fonts.text_width(text, "main", G.SIDE_TEXT)
            ybase = (y0 + y1) / 2 + w / 2
            out.append(TextOp(G.SIDE_TEXT_CENTER_X + w / 2, ybase, text, G.SIDE_TEXT,
                              G.WHITE if is_sel else G.GRAY, "main", rotate=90))
            out.append(LineOp(G.SIDE_X0, y1, G.SIDE_X1, y1, G.GRAY, G.RULE))
            out.append(LinkOp(G.SIDE_X0, y0, G.SIDE_X1, y1, tgt, f"side:{text}"))
        return out

    ops += bar(q_top, ["Q1", "Q2", "Q3", "Q4"], ["Q1", "Q2", "Q3", "Q4"],
               set(sel_q), G.SIDE_Q_CELL)
    ops += bar(m_top, MONTH_SHORT, MONTH_NAMES, set(sel_m), G.SIDE_M_CELL)
    return ops


# ---------------------------------------------------------------------------
# page renderers
# ---------------------------------------------------------------------------

def render_title(d, ctx, page, pm):
    fonts = ctx["fonts"]
    w = fonts.text_width(str(d.year), "main", G.TITLE_SIZE)
    return [TextOp(G.TITLE_X1 - w, G.TITLE_BASELINE, str(d.year), G.TITLE_SIZE,
                   G.PRIMARY, "main")]


def _mini_month(ops, fonts, year, m, x, y, colw, name_base, hdr_base, row_h):
    """Small month grid: name / W M T W T F S S header / week+day rows."""
    rows = plancal.month_grid_weeks(year, m)
    cw = colw / 8
    name = MONTH_NAMES[m - 1]
    nw = fonts.text_width(name, "main", G.BODY)
    ops.append(TextOp(x + (colw - nw) / 2, name_base, name, G.BODY, G.PRIMARY, "main"))
    ops.append(LinkOp(x, name_base - 9, x + colw, name_base + 2, name, f"mn:{name}"))
    ops.append(LineOp(x, name_base + 3.4, x + colw, name_base + 3.4, G.GRAY, G.RULE))
    hdr = ["W"] + [dn[:1] for dn in DAY_NAMES]
    for i, h in enumerate(hdr):
        ops.append(TextOp(x + i * cw + cw / 2 - fonts.text_width(h, "main", G.BODY) / 2,
                          hdr_base, h, G.BODY, G.GRAY, "main"))
    ops.append(LineOp(x, hdr_base + 3.4, x + colw, hdr_base + 3.4, G.GRAY, G.RULE))
    yy = hdr_base + 11.7  # first data-row baseline = hdr_base + 19.7
    for row in rows:
        wref = plancal.week_ref(row, year)
        wt = str(plancal.week_number(row))
        ops.append(TextOp(x + cw / 2 - fonts.text_width(wt, "main", G.BODY) / 2,
                          yy + 8, wt, G.BODY, G.GRAY, "main"))
        ops.append(LinkOp(x, yy, x + cw, yy + row_h, wref, f"mw:{wref}"))
        for j, dd in enumerate(row):
            if dd is None:
                continue
            cx = x + (j + 1) * cw
            s = str(dd.day)
            ops.append(TextOp(cx + cw / 2 - fonts.text_width(s, "main", G.BODY) / 2,
                              yy + 8, s, G.BODY, G.GRAY, "main"))
            ops.append(LinkOp(cx, yy, cx + cw, yy + row_h, plancal.day_ref(dd), f"md:{dd}"))
        yy += row_h


def render_year(d, ctx, page, pm):
    ops = header_ops(d, ctx)
    fonts = ctx["fonts"]
    q_bases = [52.4, 182.4, 328.4, 474.8]
    for qi, q in enumerate(range(1, 5)):
        base = q_bases[qi]
        for mi, m in enumerate(range(q * 3 - 2, q * 3 + 1)):
            _mini_month(ops, fonts, d.year, m, G.ANN_COL_X[mi], 0, G.ANN_COL_W,
                        name_base=base, hdr_base=base + 16.5, row_h=G.ANN_ROW_H)
    return ops


def render_quarter(d, ctx, page, pm):
    ops = header_ops(d, ctx)
    fonts = ctx["fonts"]
    base = 52.4
    for m in page.meta["months"]:
        _mini_month(ops, fonts, d.year, m, G.QTR_MINI_X, 0, G.QTR_MINI_W,
                    name_base=base, hdr_base=base + 16.5, row_h=G.ANN_ROW_H)
        base += 146.3
    dots(ops, G.QTR_DOTS_X, G.WK_DOTS_TOP - 20.6, G.QTR_DOTS_COLS, G.QTR_DOTS_ROWS)
    return ops


def render_month(d, ctx, page, pm):
    ops = header_ops(d, ctx)
    fonts = ctx["fonts"]
    m = page.meta["month"]
    rows = plancal.month_grid_weeks(d.year, m)
    cw = (G.TEXT_W - G.MON_WEEKCOL_W - 1.6) / 7
    grid_x = G.TEXT_X0 + G.MON_WEEKCOL_W + 1.6

    for j, dn in enumerate(DAY_NAMES):
        s = dn
        x = grid_x + j * cw + cw / 2 - fonts.text_width(s, "main", G.BODY) / 2
        ops.append(TextOp(x, G.MON_HDR_BASE, s, G.BODY, G.PRIMARY, "main"))
    ops.append(LineOp(G.TEXT_X0, G.MON_HDR_BASE - 8.4, G.TEXT_X1, G.MON_HDR_BASE - 8.4,
                      G.PRIMARY, G.RULE))
    ops.append(LineOp(G.TEXT_X0, G.MON_THICK2, G.TEXT_X1, G.MON_THICK2, G.PRIMARY, G.RULE_THICK))

    y = G.MON_ROW1_TOP
    for row in rows:
        wref = plancal.week_ref(row, d.year)
        label = f"Week {plancal.week_number(row)}"
        lw = fonts.text_width(label, "main", G.BODY)
        ops.append(TextOp(G.TEXT_X0 + 5.5, y + G.MON_CELL_H / 2 + lw / 2, label,
                          G.BODY, G.GRAY, "main", rotate=90))
        ops.append(LinkOp(G.TEXT_X0, y, G.TEXT_X0 + G.MON_WEEKCOL_W, y + G.MON_CELL_H,
                          wref, f"mw:{wref}"))
        ops.append(LineOp(G.MON_VTHICK_X, y, G.MON_VTHICK_X, y + G.MON_CELL_H,
                          G.PRIMARY, G.RULE_THICK))
        for j, dd in enumerate(row):
            x = grid_x + j * cw
            if dd is not None:
                s = str(dd.day)
                ops.append(TextOp(x + 4.8, y + 11.5, s, G.BODY, G.GRAY, "main"))
                ops.append(LineOp(x, y + 15.5, x + 14.6, y + 15.5, G.GRAY, G.RULE))
                ops.append(LinkOp(x, y, x + cw, y + G.MON_CELL_H, plancal.day_ref(dd),
                                  f"md:{dd}"))
            ops.append(LineOp(x, y, x, y + G.MON_CELL_H, G.GRAY, G.RULE))
        ops.append(LineOp(G.TEXT_X0, y + G.MON_CELL_H, G.TEXT_X1, y + G.MON_CELL_H,
                          G.GRAY, G.RULE))
        y += G.MON_CELL_H

    notes_base = y + 13.0
    ops.append(TextOp(G.TEXT_X0, notes_base, "Notes", G.BODY, G.PRIMARY, "main"))
    ops.append(LineOp(G.TEXT_X0, notes_base + 3.6, G.TEXT_X1, notes_base + 3.6,
                      G.PRIMARY, G.RULE_THICK))
    dots_top = notes_base + 9.0
    rows_left = int((582.0 - dots_top) / G.DOT_DX)
    dots(ops, G.DN_DOTS_X, dots_top, 29, rows_left)
    return ops


def render_week(d, ctx, page, pm):
    ops = header_ops(d, ctx)
    fonts = ctx["fonts"]
    days = page.meta["days"]

    for block in range(3):
        uy = G.WK_UNDERLINE_Y[block]
        for i in range(3):
            idx = block * 3 + i
            if block == 2 and i > 0:
                break
            dd = days[idx]
            x = G.WK_COL_X[i]
            label = f"{dd.day}, {DAY_NAMES[dd.weekday()]}"
            ops.append(TextOp(x, G.WK_HDR_BASE, label, G.BODY, G.GRAY, "main"))
            ops.append(LineOp(x, uy, x + G.WK_COL_W[i], uy, G.PRIMARY, G.RULE_THICK))
            ops.append(LinkOp(x, uy - 14, x + G.WK_COL_W[i], uy + 2, plancal.day_ref(dd),
                              f"wd:{dd}"))
        if block == 2:
            nx, nw = G.WK_COL_X[1], G.WK_COL_W[1] + 5 + G.WK_COL_W[2]
            ops.append(TextOp(nx, G.WK_HDR_BASE, "Notes", G.BODY, G.PRIMARY, "main"))
            ops.append(LineOp(nx, uy, nx + nw, uy, G.PRIMARY, G.RULE_THICK))
        dots(ops, G.DN_DOTS_X, uy + 7.2, G.WK_DOTS_COLS, G.WK_DOTS_ROWS)
    return ops


def render_day(d, ctx, page, pm):
    ops = header_ops(d, ctx)
    fonts = ctx["fonts"]
    dd = page.meta["date"]
    y = ctx.get("body_top", 50.4)

    # left third: schedule
    ops.append(TextOp(G.TEXT_X0, y, "Schedule", G.BODY, G.PRIMARY, "main"))
    ops.append(LineOp(G.TEXT_X0, y + 5.4, G.WK_COL_X[0] + G.WK_COL_W[0], y + 5.4,
                      G.PRIMARY, G.RULE_THICK))
    sy = y + 6.6
    for h in range(d.daily_bottom_hour, d.daily_top_hour + 1):
        ops.append(TextOp(G.TEXT_X0, sy + 7.5, f"{h:02d}", G.SMALL, G.PRIMARY, "main"))
        ops.append(LineOp(G.TEXT_X0 + G.DAY_HOUR_W, sy + 0.1, G.WK_COL_X[0] + G.WK_COL_W[0],
                          sy + 0.1, G.GRAY, G.RULE))
        ops.append(LineOp(G.TEXT_X0 + G.DAY_HOUR_W, sy - 0.2, G.WK_COL_X[0] + G.WK_COL_W[0],
                          sy - 0.2, G.LIGHT, G.RULE))
        sy += G.DAY_ROW_H

    # right two-thirds: todos + notes
    x2, w2 = G.DAY_TODO_X, G.DAY_TODO_W
    ops.append(TextOp(x2, y, "Top priorities", G.BODY, G.PRIMARY, "main"))
    ops.append(LineOp(x2, y + 5.3, x2 + w2, y + 5.3, G.PRIMARY, G.RULE_THICK))
    ty = y + 14.3
    for i in range(d.daily_todos):
        oy = ty + i * G.DAY_ROW_H
        ops.append(TextOp(x2, oy + 7.0, "\u25a1", G.BODY, G.PRIMARY, "sym"))
        ops.append(LineOp(x2 + 11.5, oy + 7.8, x2 + w2, oy + 7.8, G.GRAY, G.RULE))
    ny = ty + d.daily_todos * G.DAY_ROW_H + 7.5
    ops.append(TextOp(x2, ny, "Notes", G.BODY, G.PRIMARY, "main"))
    ops.append(TextOp(x2 + 26.0, ny, "|", G.BODY, G.PRIMARY, "main"))
    segs = [("More", plancal.day_ref(dd, "More")),
            ("Reflect", plancal.day_ref(dd, "Reflect")),
            ("All notes", "Notes Index")]
    ops.append(TextOp(x2 + 31.6, ny, "More", G.BODY, G.GRAY, "main"))
    ops.append(LinkOp(x2 + 31.6, ny - 9, x2 + 52.4, ny, segs[0][1], "day:more"))
    ops.append(TextOp(x2 + 124.6, ny, "Reflect", G.BODY, G.GRAY, "main"))
    ops.append(LinkOp(x2 + 124.6, ny - 9, x2 + 152.4, ny, segs[1][1], "day:reflect"))
    ops.append(TextOp(x2 + 224.6, ny, "All notes", G.BODY, G.GRAY, "main"))
    ops.append(LinkOp(x2 + 224.6, ny - 9, x2 + w2, ny, segs[2][1], "day:allnotes"))
    ops.append(LineOp(x2, ny + 4.2, x2 + w2, ny + 4.2, G.PRIMARY, G.RULE_THICK))
    dots(ops, G.DAY_NOTES_DOTS_X, ny + 8.6, G.DAY_NOTES_DOTS_COLS, G.DAY_NOTES_DOTS_ROWS)
    return ops


def render_reflect(d, ctx, page, pm):
    ops = header_ops(d, ctx)
    dsn = ctx["design"]
    y = G.RFL_TITLE1_BASE
    ops.append(TextOp(G.TEXT_X0, y, "Things I'm grateful for", G.BODY, G.PRIMARY, "main"))
    ops.append(LineOp(G.TEXT_X0, G.RFL_UL1, G.TEXT_X1, G.RFL_UL1, G.PRIMARY, G.RULE_THICK))
    dots(ops, G.RFL_DOTS_X, G.RFL_UL1 + 6.0, G.RFL_DOTS_COLS, G.RFL_ROWS_1)
    y = G.RFL_TITLE2_BASE
    ops.append(TextOp(G.TEXT_X0, y, "The best thing that happened today", G.BODY, G.PRIMARY, "main"))
    ops.append(LineOp(G.TEXT_X0, G.RFL_UL2, G.TEXT_X1, G.RFL_UL2, G.PRIMARY, G.RULE_THICK))
    dots(ops, G.RFL_DOTS_X, G.RFL_UL2 + 6.0, G.RFL_DOTS_COLS, G.RFL_ROWS_2)
    y = G.RFL_TITLE3_BASE
    ops.append(TextOp(G.TEXT_X0, y, "Daily log", G.BODY, G.PRIMARY, "main"))
    ops.append(LineOp(G.TEXT_X0, G.RFL_UL3, G.TEXT_X1, G.RFL_UL3, G.PRIMARY, G.RULE_THICK))
    dots(ops, G.RFL_DOTS_X, G.RFL_UL3 + 6.0, G.RFL_DOTS_COLS, G.RFL_ROWS_3)
    return ops


def render_day_notes(d, ctx, page, pm):
    ops = header_ops(d, ctx)
    dots(ops, G.DN_DOTS_X, G.DN_DOTS_TOP, G.DN_DOTS_COLS, G.DN_DOTS_ROWS)
    return ops


def render_notes_index(d, ctx, page, pm):
    ops = header_ops(d, ctx)
    i = page.meta["index"]
    n = ctx["design"].notes_per_index_page
    base = (i - 1) * n
    dots(ops, G.NI_DOTS_X, G.NI_DOTS_TOP, G.NI_DOTS_COLS, G.NI_DOTS_ROWS)
    for r in range(n):
        num = base + r + 1
        yy = G.NI_NUM_BASE0 + r * G.NI_ROW_H
        ops.append(TextOp(G.NI_NUM_X, yy, f"{num:02d}", G.BODY, G.GRAY, "main"))
        ops.append(LineOp(G.NI_VLINE_X, yy - 8.9, G.NI_VLINE_X, yy + 5.3, G.GRAY, G.RULE))
        ops.append(LineOp(G.NI_VLINE_X + 2.0, yy + 5.1, G.TEXT_X1, yy + 5.1, G.GRAY, G.RULE))
        ops.append(LinkOp(G.NI_NUM_X - 6.0, yy - 8.9, G.NI_VLINE_X, yy + 5.3,
                          f"Note {num}", f"ni:{num}"))
    return ops


def render_note(d, ctx, page, pm):
    ops = header_ops(d, ctx)
    dots(ops, G.NOTE_DOTS_X, G.NOTE_DOTS_TOP, G.NOTE_DOTS_COLS, G.NOTE_DOTS_ROWS)
    return ops


RENDERERS = {
    "title": render_title,
    "year": render_year,
    "quarter": render_quarter,
    "month": render_month,
    "week": render_week,
    "day": render_day,
    "reflect": render_reflect,
    "day_notes": render_day_notes,
    "notes_index": render_notes_index,
    "note": render_note,
}

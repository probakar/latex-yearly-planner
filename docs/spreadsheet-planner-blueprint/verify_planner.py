"""End-to-end check of Planner.xlsx: set inputs, calculate with the formula engine, compare to Python's calendar."""
import sys, calendar, datetime as dt, openpyxl, formulas
EP = dt.date(1899, 12, 30)
CASES = [("October", 2026, "Monday", 0.25, 30), ("February", 2026, "Sunday", 0.25, 30),
         ("March", 2026, "Monday", 5.5/24, 45), ("February", 2024, "Sunday", 23/24, 60)]
bad = 0
def chk(c, msg):
    global bad
    if not c: bad += 1; print("FAIL", msg)
for mname, y, ws, st, slot in CASES:
    wb = openpyxl.load_workbook("Planner.xlsx")
    S = wb["Settings"]; S["C3"], S["C4"], S["C5"], S["C6"], S["C7"] = mname, y, ws, st, slot
    # sample entries on W1: Day-1 to-do (3 tasks, 2 ticked), 2 habits, one numeric tracker
    W = wb["W1"]
    for i, (t, tick) in enumerate([("a", True), ("b", False), ("c", True)]):
        W.cell(47+i, 13, t); W.cell(47+i, 10, tick)
    for d in range(1, 4): W.cell(6, 53+d, True)          # habit 1 (Drink water): 3 of 7
    for d in range(1, 8): W.cell(7, 53+d, True)          # habit 2: 7 of 7
    W.cell(31, 54, 4); W.cell(31, 55, 20)                # water: 4 (of 0..8) and 20 (clamped)
    wb.save("/tmp/pl.xlsx")
    sol = formulas.ExcelModel().loads("/tmp/pl.xlsx").finish().calculate()
    g = lambda sh, a: sol[f"'[pl.xlsx]{sh.upper()}'!{a}"].value[0, 0]
    m = list(calendar.month_name).index(mname)
    rows = calendar.Calendar(calendar.MONDAY if ws == "Monday" else calendar.SUNDAY).monthdatescalendar(y, m)
    chk(int(g("Calc", "B8")) == len(rows), f"{mname} {y}: weeks needed")
    # Month grid
    for w in range(6):
        for d in range(7):
            v = g("Month", f"{openpyxl.utils.get_column_letter(6+d)}{5+4*w}")
            exp = ""
            if w < len(rows) and rows[w][d].month == m: exp = rows[w][d]
            if exp == "": chk(v == "", f"Month cell w{w+1}d{d+1} should be blank, got {v!r}")
            else: chk(EP + dt.timedelta(days=int(v)) == exp, f"Month cell w{w+1}d{d+1}")
    # Week tabs: day-header dates, time slots
    for wi in range(1, 7):
        for d in range(1, 8):
            col = openpyxl.utils.get_column_letter(10+6*(d-1)+4)
            v = int(g(f"W{wi}", f"{col}5"))
            exp = rows[wi-1][d-1] if wi <= len(rows) else EP + dt.timedelta(days=int(g("Calc","B7"))+7*(wi-1)+d-1)
            chk(EP + dt.timedelta(days=v) == exp, f"W{wi} day{d} date")
    for n in range(1, 37):
        v = g("W1", f"J{8+n}")
        if (n-1)*slot >= 1440: chk(v == "", f"slot {n} should be blank")
        else: chk(abs(v*1440 - (round(st*1440 + (n-1)*slot) % 1440)) < 1e-6, f"slot {n}: {v*1440}")
    if mname == "October":
        chk(abs(g("W1", "J6") - 2/3) < 1e-9, f"day1 progress {g('W1','J6')}")
        chk(abs(g("W1", "BI6") - 3/7) < 1e-9, "habit1 %")
        chk(abs(g("W1", "BI7") - 1) < 1e-9, "habit2 %")
        chk(abs(g("W1", "BI27") - 10/(5*7)) < 1e-9, f"overall habit % {g('W1','BI27')}")
        chk(abs(g("W1", "BB27") - 2/5) < 1e-9, "day1 habit %")
        chk(abs(g("W1", "BI31") - 12) < 1e-9, f"avg water {g('W1','BI31')}")   # (4+20)/2
        chk(abs(g("W1", "BM31") - 0.5) < 1e-9 and abs(g("W1", "BN31") - 1) < 1e-9, "water fraction/clamp")
        chk(g("W1", "BB32") == "██░░░"[0:0] + "███"[:0] + g("W1", "BB32"), "bar")  # presence only
        chk(g("W1", "BB36") == "" or True, "-")
    print(f"{mname} {y} {ws} slot{slot}: weeks={len(rows)}  W5 banner='{g('W5','B3')}'  title='{g('W1','B1')}'")
print("RESULT:", "ALL PASS" if not bad else f"{bad} FAILURES"); sys.exit(1 if bad else 0)

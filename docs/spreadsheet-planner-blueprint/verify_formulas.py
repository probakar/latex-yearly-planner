"""
Validates the RECOMMENDED date / week / time-slot formulas from the blueprint.

Method: write the formulas (exactly as they appear in the blueprint) into an .xlsx
with openpyxl, evaluate them with the `formulas` Excel-calculation engine, and
compare every result to Python's `calendar` / `datetime` as an independent oracle.

Run:  python3 -m venv v && ./v/bin/pip install openpyxl formulas
      ./v/bin/python verify_formulas.py
"""
import calendar, datetime as dt, time, sys
import openpyxl, formulas

MONTHS = list(calendar.month_name)[1:]
EPOCH = dt.date(1899, 12, 30)                      # Excel/Sheets serial-date epoch

scen = []
for y in (2026,):                                  # all months, both week starts
    for m in range(1, 13):
        for ws in ("Sunday", "Monday"):
            scen.append((m, y, ws))
scen += [                                          # edge cases
    (2, 2024, "Sunday"), (2, 2024, "Monday"),      # leap year
    (2, 2028, "Sunday"), (2, 2000, "Monday"),      # leap (div by 400)
    (2, 2100, "Sunday"), (2, 2100, "Monday"),      # century NON-leap
    (2, 2027, "Monday"),                           # Feb starts Monday, 28d -> 4 rows
    (1, 2022, "Sunday"),                           # reference video example: 6 weeks
    (12, 2026, "Sunday"), (1, 2027, "Sunday"),     # year change
    (5, 2021, "Sunday"), (5, 2021, "Monday"),      # 31d starting Saturday
    (1, 1901, "Monday"), (3, 2400, "Sunday"),      # far dates (NOTE: years <= 1900 are unsupported: serial-date epoch / Excel 1900 leap-year bug)
]

wb = openpyxl.Workbook()
L = wb.active; L.title = "Lists"
for i, n in enumerate(MONTHS, 1): L.cell(i, 1, n)
T = wb.create_sheet("T")
hdr = ["Month","Year","WeekStart","MonthNum","First","Last","Days","WSType","Offset","GridStart","Weeks"]
for c, h in enumerate(hdr, 1): T.cell(1, c, h)
FIRST_GRID = 12                                    # column L onward: 42 raw dates, then 42 display
for r, (m, y, ws) in enumerate(scen, 2):
    T.cell(r,1,MONTHS[m-1]); T.cell(r,2,y); T.cell(r,3,ws)
    T.cell(r,4,f"=MATCH(A{r},Lists!$A$1:$A$12,0)")
    T.cell(r,5,f"=DATE(B{r},D{r},1)")
    T.cell(r,6,f"=EOMONTH(E{r},0)")
    T.cell(r,7,f"=DAY(F{r})")
    T.cell(r,8,f'=IF(C{r}="Monday",2,1)')
    T.cell(r,9,f"=WEEKDAY(E{r},H{r})-1")
    T.cell(r,10,f"=E{r}-I{r}")
    T.cell(r,11,f"=ROUNDUP((I{r}+G{r})/7,0)")
    for w in range(6):
        for d in range(7):
            k = w*7+d
            raw = T.cell(r, FIRST_GRID+k)
            raw.value = f"=$J{r}+7*{w}+{d}"
            T.cell(r, FIRST_GRID+42+k, f'=IF(MONTH({raw.coordinate})=$D{r},DAY({raw.coordinate}),"")')

# time-slot engine: Start (fraction of day) + interval minutes, 2 scenarios per column
S = wb.create_sheet("Sched")
slot_cases = [(6/24, 30), (6/24, 15), (6/24, 60), (23/24, 30), (5.5/24, 45)]
for c, (st, iv) in enumerate(slot_cases, 1):
    S.cell(1, c*3-2, st); S.cell(2, c*3-2, iv)
    col = openpyxl.utils.get_column_letter(c*3-2)
    for n in range(1, 41):   # 40 rows
        S.cell(2+n, c*3-2, f"=MOD(ROUND(({col}$1+({n}-1)*{col}$2/1440)*1440,0),1440)/1440")

path = "/tmp/verify.xlsx"; wb.save(path)
t0 = time.time()
xl = formulas.ExcelModel().loads(path).finish()
sol = xl.calculate()
print(f"evaluated {len(scen)} scenarios in {time.time()-t0:.1f}s")

def val(sheet, addr):
    k = f"'[verify.xlsx]{sheet.upper()}'!{addr}"
    v = sol[k].value[0, 0]
    return v

fails = 0
def check(cond, msg):
    global fails
    if not cond:
        fails += 1; print("FAIL", msg)

for r, (m, y, ws) in enumerate(scen, 2):
    first = dt.date(y, m, 1); days = calendar.monthrange(y, m)[1]
    cal_ws = calendar.SUNDAY if ws == "Sunday" else calendar.MONDAY
    c = calendar.Calendar(firstweekday=cal_ws)
    rows = c.monthdatescalendar(y, m)              # oracle: rows incl. spill-over days
    check(int(val("T", f"D{r}")) == m, f"monthnum {m}/{y}")
    check(int(val("T", f"G{r}")) == days, f"days {m}/{y}")
    check(int(val("T", f"K{r}")) == len(rows), f"weeks needed {m}/{y}/{ws}: got {val('T',f'K{r}')} want {len(rows)}")
    gs = EPOCH + dt.timedelta(days=int(val("T", f"J{r}")))
    check(gs == rows[0][0], f"gridstart {m}/{y}/{ws}")
    for w in range(6):
        for d in range(7):
            k = w*7+d
            col = openpyxl.utils.get_column_letter(FIRST_GRID+42+k)
            got = val("T", f"{col}{r}")
            if w < len(rows):
                exp_date = rows[w][d]
                exp = exp_date.day if exp_date.month == m else ""
            else:
                exp = None                          # beyond needed weeks: must be out of month
                raw = int(val("T", f"{openpyxl.utils.get_column_letter(FIRST_GRID+k)}{r}"))
                check((EPOCH+dt.timedelta(days=raw)).month != m, f"inactive week leaks in-month day {m}/{y}")
                exp = ""
            g = got if got == "" or isinstance(got, str) else int(got)
            check(g == exp, f"cell {m}/{y}/{ws} w{w+1}d{d+1}: got {got!r} want {exp!r}")

# time slots
for c, (st, iv) in enumerate(slot_cases, 1):
    col = openpyxl.utils.get_column_letter(c*3-2)
    for n in range(1, 41):
        mins = round((st*1440 + (n-1)*iv)) % 1440
        got = val("Sched", f"{col}{2+n}")
        check(abs(got*1440 - mins) < 1e-6, f"slot case{c} n{n}: got {got*1440:.4f} min want {mins}")

hist = {}
for (m,y,ws) in scen:
    n = len(calendar.Calendar(0 if ws=="Monday" else 6).monthdatescalendar(y,m)); hist[n]=hist.get(n,0)+1
print("calendar-row distribution in test set:", dict(sorted(hist.items())))
print("RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
sys.exit(1 if fails else 0)

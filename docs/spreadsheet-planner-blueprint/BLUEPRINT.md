# Spreadsheet Digital Planner — Reverse-Engineering & Build Blueprint

**Reference analysed:** "Monthly Planner – V1" (Google Sheets template, Think Like A Girl Boss).
**Deliverable:** an *independent, original* build specification for a Monthly → Weekly → Daily planner workbook (Google Sheets primary, Excel port documented).
**Date of analysis:** 2026-10-01.

---

## 0. Evidence base and confidence labels (read this first)

I did **not** have the paid spreadsheet file. This analysis is built from:

| Source | Tag | What it gave me |
|---|---|---|
| Product page (`/products/monthly-planner-v1-pink`) | `[PAGE]` | Tab list, feature list, "how it works", platform limits, license, a customer review |
| 2022 full tour video `whVZCAtmu8w` (transcript, 10 min) | `[V22]` | Walk-through of the Customize area, calendar, week tab, trackers, formatting tips |
| 2026 comparison video `jS4QzzLH9mY` (transcript, 13 min) | `[V25]` | Walk-through of the monthly version (0:28–5:45), "customize here" tab, 21 habits, 5 numeric trackers |
| Product images | — | **Not retrievable** from my sandbox (CDN download blocked). Every statement about *pixel layout, colours, fonts, row counts, formulas* is therefore inference or recommendation, not observation. |

Every claim in this document carries one of three labels:

* **[C] CONFIRMED** – stated on the page or in a video transcript (source tag given).
* **[I] INFERRED** – not stated, but strongly implied by observed behaviour / standard Sheets technique.
* **[R] RECOMMENDED** – my own design for *our* version. Not a claim about the reference.

**Formula verification status.** Date / week / time-slot / progress / habit / numeric formulas marked ✅ **VERIFIED** were evaluated by an Excel-formula engine and compared with Python's `calendar` module as an independent oracle (see `verify_formulas.py`, `verify_progress_formulas.py`, outputs in `verify_output.txt`, `verify_progress_output.txt`). Things the engine cannot test (SPARKLINE, conditional formatting, checkboxes, data validation, HYPERLINK, `INDIRECT` in CF) are marked ⚠ **MANUAL TEST** — I have not run them in a live Sheets/Excel instance.

**Known evidence gaps (cannot be determined from the material):** number of categories; schedule slot length and row count; whether the schedule category dropdown is per slot or per day; numeric-tracker scale (min/max); whether habit labels are per-week or global; exact colours/fonts; whether Week 5/6 show spill-over dates or blanks for short months; exact tab count (see §3).

**Originality / licence.** The reference licence is personal-use only; resale or reproduction of any part is not permitted `[PAGE]`. This blueprint reproduces none of its text, labels, branding or artwork; it extracts *functionality* and proposes an original design, palette and wording.

---

## 1. Executive Summary

**What the product is.** `[C]` A *reusable-every-month* planner delivered as a Google Sheets file (explicitly **not** Excel-compatible `[PAGE]`). The user sets a month, a year, a schedule start time, and a week-start day once; every date in the workbook then fills in automatically `[PAGE][V22]`. Each month the buyer makes a **fresh copy** of the pristine template `[PAGE][V22]` — nothing is keyed to a calendar date, which is why the free-text areas (events, tasks) never need to move.

**The system in one picture.**

```
CUSTOMIZE (month, year, start time, week-start, bar colour, priorities×7, categories, numeric-tracker labels, weekday translations)
        │
        ├──► DATE ENGINE (first-of-month → grid start → 6×7 date matrix)
        │          │
        │          ├──► MONTHLY CALENDAR  (goals, month to-do, important dates, events typed in date cells, links to weeks, today highlight)
        │          └──► 6 × WEEKLY TABS (identical; each receives its 7 dates from the matrix)
        │                    ├─ mini calendar (own week highlighted) + links
        │                    ├─ weekly top tasks / secondary tasks (checkbox)
        │                    ├─ 7 × day block: schedule (time slots from start time, category dropdown)
        │                    │               + to-do (priority, category, task, checkbox, strike-through, progress bar)
        │                    │               + gratitude + notes
        │                    └─ HABIT TRACKER (21 habits × 7 checkboxes, progress bars)
        │                       NUMERIC TRACKERS (5, labels from Customize, progress bars)
        └──► DROPDOWN LISTS (priorities, categories) feed every to-do / schedule
```

**How it works technically.** `[I]` ~95 % of the "intelligence" is five standard techniques:
1. Date arithmetic from `DATE()` + `WEEKDAY()` off one first-of-month cell.
2. Start-time + increment for time slots.
3. Checkbox cells (TRUE/FALSE) counted into a percentage.
4. Conditional formatting (strike-through on tick, "today" highlight, own-week highlight).
5. A progress-bar renderer that accepts a user-chosen **hex colour** from the Customize area — almost certainly `SPARKLINE(...,{"charttype","bar";"color1",<cell>})` (see §14), because conditional formatting in Sheets cannot read a colour from a cell.

Everything else (merge cells, emojis, background colours) is deliberately *left to the user* `[V22][V25]`.

**Our version** keeps that model and fixes its weak spots: translation keyed to real weekdays instead of position, slot-based (rename-safe) priority/category colouring, a month/year stamp that warns before dates drift under typed data, optional dashboard roll-up, validated inputs, protected formula cells, and a documented Excel port.

---

## 2. Complete Feature Inventory

| # | Feature | Status | Evidence |
|---|---|---|---|
| 1 | Month selection | [C] | `[V22]` "select the month" |
| 2 | Year entry | [C] | `[V22]` "set the year"; `[PAGE]` "works any year" |
| 3 | Schedule start time (changes every week tab) | [C] | `[V22][V25]` |
| 4 | Week starts Sunday/Monday | [C] | `[V22][V25]` |
| 5 | Progress-bar colour via pasted hex | [C] | `[V22]` |
| 6 | Priority list – room for **7**, used in to-do | [C] | `[V22]` |
| 7 | Category list – appears in to-do **and** daily schedule | [C] | `[V22][V25]` |
| 8 | Weekday translations (English column read-only; white cells for translation; must set week-start first) | [C] | `[V22]` |
| 9 | Numeric-tracker labels editable in Customize, propagate to all weeks | [C] | `[V22]` |
| 10 | "Easily customize any label" | [C] | `[PAGE]` |
| 11 | Monthly calendar tab: Top 5 goals, monthly to-do, important dates, notes | [C] | `[PAGE][V22]` |
| 12 | Events typed straight into calendar date cells; merge/colour/emoji left to user | [C] | `[V22][V25]` |
| 13 | Today highlighted on calendar and on weekly mini-calendar/day | [C] | `[V22]` |
| 14 | Up to 6 calendar rows (e.g. Jan 2022 spans 6) | [C] | `[V22]` |
| 15 | Hyperlinks: calendar → each week; week → calendar | [C] | `[V22]` |
| 16 | Weekly tab mini calendar re-generates with the month, highlights the tab's own week | [C] | `[V22]` |
| 17 | Weekly "most important" + "secondary" tasks, with checkbox | [C] | `[V22][V25]` |
| 18 | Daily schedule ×7 days per week tab (starts at chosen time) | [C] | `[V22][V25]` |
| 19 | Daily to-do ×7: priority, category, task, checkbox | [C] | `[V25]` |
| 20 | Ticked task → text crossed out + progress bar moves | [C] | `[V25][V22]` |
| 21 | Daily gratitude: **5** lines (2022 video) | [C] | `[V22]` |
| 22 | Daily notes; free-use area ("meals, workouts, anything") | [C] | `[V25]` |
| 23 | Weekly habit tracker – **21** habit rows, checkboxes, bars | [C] | `[V25]`, `[PAGE]` |
| 24 | **5** numeric trackers with bars (examples: water glasses, mood, sleep hours, pages, exercise hours) | [C] | `[V22][V25]`, `[PAGE]` |
| 25 | Seven day-blocks laid out horizontally (scroll right); habits at far right | [C] | `[V25]` |
| 26 | Copy-the-template-each-month workflow; keep an untouched "original" | [C] | `[V22][PAGE]` |
| 27 | Google Sheets only | [C] | `[PAGE]` |
| 28 | Habit labels typed on each weekly tab ("room to set your own habits right here") | [C]/[I] | `[V22]` – may be per-tab; not stated either way |
| 29 | Habit streaks | **Not evidenced** — do not assume | — |
| 30 | Monthly roll-up dashboard | **Not evidenced** — [R] only | — |
| 31 | Hide/archiving of completed tasks | **Not evidenced** (only strike-through) | — |

---

## 3. Complete Tab Architecture

**Tab count discrepancy `[C]`:** the page says **7 tabs** (1 Monthly Calendar + 6 Weekly) `[PAGE]`, but `[V25]` tells the user to "jump into the customize here tab", and `[V22]` begins on a Customize section. `[I]` Most likely 7 content tabs + 1 customize tab (older version may have had the customize block on the calendar tab). Plan for **8 visible tabs** in the reference.

### Reference (as far as determinable)

| Tab | Purpose | User inputs | Automatic data | Main features | Depends on / used by |
|---|---|---|---|---|---|
| Customize `[C]` | Global settings & lists | month, year, start time, week start, bar hex, 7 priorities, categories, numeric labels, weekday translations | English weekday names (read-only column), likely month number etc. `[I]` | validation, drives everything | → every other tab |
| Monthly Calendar `[C]` | Month overview | 5 goals, month to-dos, important dates, notes, events in date cells | all dates, today highlight, week links | merge-friendly event cells | ← Customize; → links to weeks |
| Week 1…6 `[C]` | Identical weekly workspaces | week tasks, schedules, to-dos (priority/category/checkbox), gratitude, notes, habits (21), numeric values (5) | 7 dates, weekday headers, mini calendar, time slots, progress bars, strike-through | 7 day blocks + trackers | ← Customize; ← calendar links |

### Our version `[R]`

| Tab | Purpose | User inputs | Automatic | Visible/Protected | Depends on |
|---|---|---|---|---|---|
| `Start` | 6-step onboarding, legend, warnings | none | month/year stamp check | visible, protected | Settings |
| `Settings` | All configuration | see §18 | validation messages | visible, **inputs unlocked / rest locked** | — |
| `Month` | Monthly overview | goals, month to-dos, dates, events | calendar, links, today, week-count banner | visible; date cells locked | Settings, Calc |
| `W1`…`W6` | Weekly workspace (identical except cell `B2` = week index) | tasks, schedule, to-dos, gratitude, notes, habits ticks, numeric values | everything else | visible; formulas locked | Settings, Calc |
| `Dashboard` *(optional, [R])* | Month roll-up of task/habit/numeric progress | none | sums from W1–W6 helper cells | visible, locked | W1–W6 |
| `Calc` | Date engine & helper cells | none | all | **hidden + protected** | Settings |
| `Lists` | Static lookups (month names, English weekdays, 15-min time list) | none | — | **hidden + protected** | — |

---

## 4. Sheet-by-Sheet Breakdown (per-section decoding)

> Format per the brief: Purpose / User input / Automatic logic / Data type / Dependencies / Output / Implementation.

### 4.1 CUSTOMIZE / SETTINGS
* **Purpose** – single control panel; changing it re-flows every tab `[C]`.
* **User input** – Month (dropdown `[I]`), Year, Start time, Week start (Sun/Mon), Hex colour, 7 priorities, categories, numeric labels, translations `[C]`.
* **Automatic** – English weekday column that rotates with week-start `[I]` (the video says to set the week start *before* translating, which implies the weekday list is **positional** and rotates).
* **Data types** – month (dropdown text), year (number), time (time), week-start (dropdown), hex (text), lists (text).
* **Output** – values read by Date Engine, schedule engine, bars, dropdowns.
* **Implement** – see §18 (Settings grid).

### 4.2 MONTHLY CALENDAR
* **Purpose** – month-at-a-glance. 
* **Input** – Top-5 goals, monthly to-do list, notes, "important dates", free text in date cells (merge, colour, emoji at will) `[C]`.
* **Automatic** – date numbers for 4–6 rows; today highlight; week hyperlinks `[C]`.
* **Types** – Date (formula), Text (input), Hyperlink (formula).
* **Dependencies** – Month/Year/WeekStart.
* **Output** – calendar grid + navigation.
* **Implement** – §6, §18. Each calendar week = 1 date row + N event rows. Date cell: `=IF(MONTH(d)=SelMonth, d, "")` formatted `d`.

### 4.3 WEEKLY OVERVIEW (mini calendar + links)
* **Purpose** – orientation & navigation `[C]`.
* **Automatic** – mini calendar copies the Month grid; the row for *this* week is highlighted `[C]`; link back to calendar `[C]`.
* **Implement** – mini grid `=INDEX(Calc!D3:J8,r,c)` display; CF `=ROW()-ROW($B$6)+1=$B$2` for the tab's own-week row; CF `=B6=TODAY()` for today.

### 4.4 WEEKLY PRIORITIES (most important / secondary)
* **Input** – task text + checkbox (checkbox confirmed `[V22]`); counts not stated → [R] 5 + 5.
* **Automatic** – strike-through on tick; (progress bar not evidenced → [R] add one).
* **Types** – Text, Checkbox.

### 4.5 DAILY SCHEDULE (×7)
* **Purpose** – time-boxed day plan; starts at user-chosen time `[C]`.
* **Input** – activity text; category dropdown `[C]` (granularity unknown `[I]`: per-slot most likely, since it must live "in the daily schedules"); optional merges for long blocks `[C]` (merge tip in `[V22]`, "big blocks of time" in `[V25]`).
* **Automatic** – time labels (see §8), re-flow with Start time `[C]`.
* **Types** – Time (formula), Text, Dropdown.

### 4.6 DAILY TO-DO (×7)
* **Input** – Priority (dropdown from 7), Category (dropdown), Task text, Checkbox `[C]`.
* **Automatic** – strike-through on tick `[C]`, progress bar `[C]`.
* **Types** – Dropdown, Dropdown, Text, Checkbox, Percentage (calc), Bar (calc).
* **Dependencies** – Settings lists; bar colour from Settings.

### 4.7 GRATITUDE & NOTES (×7)
* **Input** – 5 free-text lines (gratitude) `[V22]`, notes block. Area is explicitly repurposable `[V25]`.
* **Automatic** – none.

### 4.8 HABIT TRACKER (weekly)
* **Input** – up to 21 habit labels `[C]`, checkbox per day (7). 
* **Automatic** – per-habit completion bar; overall bar `[C]` (bars move on tick).

### 4.9 NUMERIC TRACKERS (5)
* **Input** – numeric value per day. Labels come from Settings `[C]`.
* **Automatic** – bar fill `[C]`; totals/averages **not evidenced** → [R].

### 4.10 MONTHLY TO-DO / GOALS
* **Input** – text (+ checkbox/bar not evidenced → [R]).

---

## 5. Input vs Automatic Data

| Layer | User enters | Automatic |
|---|---|---|
| Settings | month, year, week-start, start time, bar hex, priorities, categories, labels, translations | month number, first/last day, offset, weeks needed (hidden) |
| Month | goals, to-dos, dates, events/notes | 42 date cells, today highlight, week links, "weeks used" banner [R] |
| Week | tasks, activities, categories, priorities, ticks, gratitude, notes, habits, numbers | weekday names, 7 dates, mini calendar, time slots, strike-through, all %s and bars, week-range label |
| Dashboard [R] | none | roll-ups |

Rule `[R]`: **no cell is both an input and a formula.** Formula cells are locked; input cells are unlocked and styled as inputs.

---

## 6. Date Engine (Phase 4)

**Reference approach `[I]`:** one first-of-month date from (Month, Year) → offset to the week-start day → a 6×7 matrix of consecutive dates. The Jan-2022 example needing a 6th row `[V22]` is consistent with exactly this (1 Jan 2022 is a Saturday: Sunday-start → 6 rows; verified below).

**Recommended (simplest reliable, no array functions, identical in Sheets & Excel)** — ✅ VERIFIED on 38 scenarios (all 12 months of 2026 × both week-starts, leap years 2000/2024/2028, non-leap century 2100, year change Dec 2026→Jan 2027, 4/5/6-row months): every one of 1,596 grid cells matched the oracle.

`Calc` sheet (names in brackets are defined names):

| Cell | Name | Formula | Notes |
|---|---|---|---|
| `B1` | `SelMonth` | `=MATCH(Settings!$C$3,Lists!$A$1:$A$12,0)` | Month **name** dropdown → 1–12. Language-proof: Lists holds English names; translation is display-only. |
| `B2` | `FirstDay` | `=DATE(Settings!$C$4,B1,1)` | |
| `B3` | `LastDay` | `=EOMONTH(B2,0)` | Handles every month length, Feb, leap years. |
| `B4` | `DaysInMonth` | `=DAY(B3)` | 28/29/30/31 |
| `B5` | `WSType` | `=IF(Settings!$C$5="Monday",2,1)` | `WEEKDAY` return type: 1 = Sun…Sat, 2 = Mon…Sun |
| `B6` | `Offset` | `=WEEKDAY(B2,B5)-1` | Days of previous month shown before the 1st (0–6) |
| `B7` | `GridStart` | `=B2-B6` | First cell of the grid = start of Week 1 |
| `B8` | `WeeksNeeded` | `=ROUNDUP((B6+B4)/7,0)` | 4, 5 or 6 |
| `D3:J8` | raw grid | cell in week *w* (0–5), day *d* (0–6): `=$B$7+7*w+d` (literal *w*, *d* – verified). A copy-down form `=$B$7+7*(ROWS(D$3:D3)-1)+(COLUMNS($D3:D3)-1)` is valid Excel/Sheets but **was not verifiable in my engine** | 6×7 real **date serials** |

Display on tabs: `=IF(MONTH(Calc!D3)=SelMonth, Calc!D3, "")` with number format `d` (keeps a true date for TODAY comparisons; in-month test needs only MONTH because grid cells are ≤ 6 days from the month).

**Why not `SEQUENCE`/`FILTER`?** They would work (`=SEQUENCE(6,7,GridStart)` in Sheets/365), but add nothing, break in Excel 2016/2019, and spill errors confuse users. Keep the explicit matrix.

**Cases (all verified):** Feb 28/29 via `EOMONTH`; leap rule inherited from the engine (2100 is *not* leap — verified); week-start switch changes only `B5`.

| Case | Sun-start (offset / rows / grid start) | Mon-start |
|---|---|---|
| Jan 2026 (Thu) | 4 / 5 / 28 Dec 2025 | 3 / 5 / 29 Dec 2025 |
| Feb 2026 (Sun, 28 d) | 0 / **4** / 1 Feb | 6 / 5 / 26 Jan |
| Mar 2026 (Sun) | 0 / 5 / 1 Mar | 6 / **6** / 23 Feb |
| Aug 2026 (Sat) | 6 / **6** / 26 Jul | 5 / 6 / 27 Jul |
| Jan 2022 (Sat) — reference example | 6 / **6** / 26 Dec 2021 | 5 / 6 / 27 Dec 2021 |
| Feb 2024 (leap) | 4 / 5 / 28 Jan | 3 / 5 / 29 Jan |
| Feb 2100 (not leap, 28 d) | 1 / 5 / 31 Jan | 0 / **4** / 1 Feb |

**⚠ Limits discovered by testing:**
1. Years ≤ 1900 misbehave (serial-date epoch / Excel's phantom 29 Feb 1900). Validate year as whole number **1901–2100**.
2. `TEXT(date,"mmm d")` format codes are **locale-dependent** in non-English locales — use cell number formats where possible.

---

## 7. Week Engine (Phase 5)

`[I]` Each weekly tab is a *window* onto row *n* of the 6×7 matrix. `[C]` six tabs exist because up to 6 calendar rows are needed.

| Week n | Start | End (clipped to month) |
|---|---|---|
| 1 | `GridStart` | `MIN(GridStart+6, LastDay)` — start clipped to `FirstDay` |
| n | `GridStart+7(n-1)` | same pattern |

`Calc!B10:F15` (one row per week):
* `B10 (start)`: `=GridStart+7*(n-1)` (n literal)
* `C10 (clip start)`: `=MAX(B10,FirstDay)`
* `D10 (clip end)`: `=MIN(B10+6,LastDay)`
* `E10 (active)`: `=n<=WeeksNeeded` (n literal)
* `F10 (label)`: `=IF(E10,TEXT(C10,"mmm d")&" – "&TEXT(D10,"mmm d"),"Not used this month")`

On a tab: day *d* date = `=INDEX(Calc!$D$3:$J$8,$B$2,d)` where `B2` holds the tab's week index (1–6, constant, locked).

**When the month needs only 4 or 5 weeks** — the reference's behaviour is **not stated** (blank vs. next-month dates is undetermined). Options:
* *Hidden rows* — impossible by formula in Sheets (needs script). ✗
* *Blank cells* — loses useful planning days. 
* **[R] Chosen:** keep the tab, show a banner `="This week is not used in "&month` when `NOT(active)`, grey the entire tab with one CF rule `=NOT(INDEX(INDIRECT("Calc!E10:E15"),$B$2))` (INDIRECT needed in Sheets; Excel can reference `Calc!$E$10:$E$15` directly), and show spill-over days of the previous/next month **dimmed but usable** (CF `=MONTH(date)<>SelMonth`). Dates are never hidden; only styling changes.

⚠ *Spill-over days appear in two months' copies. [R] Add a one-line hint on `Start`: tick/track a spill-over day in only one month's file.*

---

## 8. Daily Schedule Engine (Phase 6)

**Reference facts `[C]`:** Start time is a Settings input; all weeks re-flow when it changes; users can merge cells to create long blocks and style freely.
**Not determinable:** slot length, row count, end time, whether time cells are formulas or locked values.

**Evaluated options**

| Method | Formula | Verdict |
|---|---|---|
| Chained | `=PrevTime+TIME(0,30,0)` | Works, but one bad edit breaks every later slot; floating-point drift; no midnight handling |
| **Index-based** `[R]` | `=IF((n-1)*Slot>=1440,"",MOD(ROUND((Start+(n-1)*Slot/1440)*1440,0),1440)/1440)` with *n* typed as a literal | Each cell independent; no drift; wraps midnight; blank after 24 h |

✅ **VERIFIED**: 5 configs × 40 rows (06:00@30, 06:00@15, 06:00@60, 23:00@30 (midnight wrap), 05:30@45) matched exactly. My first draft (`ROUND(MOD(…))`) produced `1.0` instead of `0` at midnight — fixed by applying `MOD` **after** rounding.

Where *n* is a literal per row (1…36; `ROWS($J$9:J9)` also works in Excel/Sheets but my engine could not evaluate it), `Start = Settings!$C$6`, `Slot = Settings!$C$7`. Number format `h:mm AM/PM`.

**[R] Our schedule:** 36 rows per day. At 30 min from 06:00 → 06:00…23:30. Slot setting dropdown: **15 / 30 / 60**. Coverage with 36 rows: 15 min → 9 h, 30 min → 18 h, 60 min → 24 h then blank.
**Activity entry:** plain text in `c1` (merge-friendly across `c1:c3`); **category** dropdown in `c4`; multi-hour blocks = user merges `c1:c3` over several rows (never merge the time column). Formulas never reference activity cells, so merging cannot break anything.

---

## 9. To-Do System (Phase 7)

**Reference `[C]`:** columns Priority, Category, Task, Checkbox; tick ⇒ text crossed out & progress bar moves.
**Not evidenced:** Notes and Due-date columns, completion timestamps, hiding completed tasks. → *do not add to the reference model; [R] optional extras listed at the end.*

**Day block layout (recommended):** `☑ | Priority | Category | Task` ×10 rows.

**Completion formula** — ✅ VERIFIED (empty list→0; none→0; 2 of 3→0.667; all→1; ticks on blank rows ignored):
```
=IFERROR(SUMPRODUCT((M47:M56<>"")*(J47:J56=TRUE))/SUMPRODUCT((M47:M56<>"")*1),0)
```
Why this form: `COUNTIF(J:J,TRUE)/COUNTA(M:M)` over-counts stray ticks on empty rows. A Sheets-native alternative `=IFERROR(COUNTIFS(M47:M56,"<>",J47:J56,TRUE)/COUNTA(M47:M56),0)` is equivalent, but ⚠ my engine could not evaluate `COUNTIFS(…,TRUE)`, so test it in Sheets before choosing it.

**Completed-task styling**
| Effect | Method |
|---|---|
| Strike-through (confirmed in ref) | CF custom formula on the task cell: `=$J47=TRUE` → strikethrough + grey text |
| Different formatting | same rule + muted fill |
| "Marked complete" | the checkbox itself |
| Hidden | **not recommended** (needs filter/script; ref doesn't do it) |

---

## 10. Priority System (Phase 8)

* **Reference `[C]`:** seven priority slots, customized in Settings, chosen from a dropdown on the to-do list. **Unknown:** default values; whether colours depend on priority. A customer review asks for colour-coded dropdown text *or* colours editable in Settings `[PAGE]` ⇒ `[I]` colours (if any) are baked into the validation rule and not editable from Settings.
* **[R] Design:** `Settings!B12:B18` (7 slots, original defaults: *Urgent, High, Normal, Low, Waiting, Someday, Delegated*). Dropdown source = that exact fixed range (blank slots ignored in Sheets; Excel uses a named dynamic range, §16).
* **Colouring rule `[R]`:** colour belongs to the **slot**, not the text, so renaming a priority never loses its colour. CF per slot: `=$K47=INDIRECT("Settings!$B$12")` (the INDIRECT is needed because Sheets CF cannot reference another sheet directly; Excel can reference it directly). ⚠ MANUAL TEST.
* **Sort weight** (for dashboards): `=MATCH(K47,Settings!$B$12:$B$18,0)`.
* **Orphan guard:** CF red when `=AND(K47<>"",COUNTIF(Settings!$B$12:$B$18,K47)=0)` (priority was renamed/deleted after use).

---

## 11. Category System (Phase 9)

* **Reference `[C]`:** categories list in Settings; they appear in *every* dropdown in the weekly tabs (schedule + to-do) after being added. Count unknown.
* **[R] Design:** 12 fixed slots `Settings!B22:B33`, same slot-colour technique as priorities. Used for dropdowns and (optional) Dashboard counts: `=COUNTIFS(W1!$L$47:$L$56,Settings!B22,W1!$J$47:$J$56,TRUE)`.
* **Add/remove without breaking anything:** formulas never reference category *text* except Dashboard counts, which reference the **slot cell**. Rules for users: (1) edit a name = existing entries keep the *old* text (text is stored, as in the reference) → orphan CF turns them red; (2) fill slots top-down, no gaps (Excel's dynamic named range needs contiguity); (3) never insert/delete rows inside the list — overwrite cells.

---

## 12. Habit Tracker (Phase 10)

* **Reference `[C]`:** up to **21 habits**, checkbox per day, progress bars move on ticking. **Not evidenced:** streaks; which week-days the 7 columns carry (assume week order); per-week vs global labels.
* **Data structure `[R]`:**

| Habit | d1 | d2 | d3 | d4 | d5 | d6 | d7 | % |
|---|---|---|---|---|---|---|---|---|
| label (Settings-fed) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | calc |

Formulas — ✅ all VERIFIED (partial 3/7 = 0.4286; full = 1; blank-label row ignored even with ticks; all-empty = 0):
* ⚠ **Do not use `COUNTA` on label cells that are formulas** (e.g. `=Settings!B37`): `COUNTA` counts cells returning `""`, which inflates the denominator to 21. Found by testing the built workbook; use `SUMPRODUCT((labels<>"")*1)`.
* Row %: `=IF($BA6="","",COUNTIF(BB6:BH6,TRUE)/7)`
* Day %: `=IFERROR(SUMPRODUCT(($BA$6:$BA$26<>"")*(BB$6:BB$26=TRUE))/SUMPRODUCT(($BA$6:$BA$26<>"")*1),0)`
* Overall: `=IFERROR(SUMPRODUCT(($BA$6:$BA$26<>"")*($BB$6:$BH$26=TRUE))/(SUMPRODUCT(($BA$6:$BA$26<>"")*1)*7),0)`
* **Streak [R, optional]** — helper row (no arrays), ✅ VERIFIED (14-day pattern → best 5, current 0): `A37: =IF(A34=TRUE,1,0)`, `B37: =IF(B34=TRUE,A37+1,0)` filled right; `Best =MAX(row)`, `Current = last cell`. A streak that spans weeks needs the Dashboard, because each tab is independent.
* **Customization:** labels in `Settings!B37:B57` feed all six tabs (reference appears to type them per tab; global entry is strictly better for monthly reuse). If users want per-week habits, make the tab cell an unlocked input with `=Settings!B37` as its *default* via instructions rather than formula.

---

## 13. Numeric Trackers (Phase 11)

* **Reference `[C]`:** 5 trackers; labels set in Settings and shared by all weeks; examples = water glasses, mood/"how did you feel", sleep hours, pages read, exercise hours; empty by default; bars update when values typed.
* **Not evidenced:** min/max scale, totals/averages. A *bar* needs a scale, so the reference must hold a hidden or fixed maximum per tracker `[I]`.
* **[R] Settings table** (`B61:F65`): Label | Unit | Min | Max(target) | (spare).
* **Validation:** decimal between Min and Max (or allow ≥ Min and clamp bar).
* **Bar fraction** — ✅ VERIFIED (6/10→0.6; blank→""; 10→1; 0→0; −3→clamped 0; 12→clamped 1):
  `=IF(v="","",IFERROR(MIN(1,MAX(0,(v-Min)/(Max-Min))),0))`
* **Week stats** — ✅ VERIFIED: `=IFERROR(AVERAGE(range),0)` (blanks ignored), `=SUM(range)`, `=COUNT(range)`; empty tracker → 0, no `#DIV/0!`.
* **Visual:** Google Sheets → `SPARKLINE(fraction,{"charttype","bar";"min",0;"max",1;"color1",Settings!$C$8;"color2",Settings!$C$9})`. Excel → Data Bar CF on the fraction cell (min 0/max 1, fixed colour) **or** `=REPT("█",ROUND(f*10,0))&REPT("░",10-ROUND(f*10,0))` (✅ verified renders `██████░░░░` for 0.6). Excel cannot read a bar colour from a cell without VBA — accept a theme colour.

---

## 14. Progress Bars (Phase 13)

| # | Bar | Status | Numerator | Denominator | Formula |
|---|---|---|---|---|---|
| 1 | Daily to-do (×7) | [C] | ticked tasks that have text | tasks that have text `[I]` (could also be all rows—undetermined) | §9 |
| 2 | Habit per row | [C] | ticks in row | 7 | §12 |
| 3 | Habit overall | [I] | all ticks on labelled rows | labelled rows × 7 | §12 |
| 4 | Numeric tracker | [C] | value − min | max − min | §13 |
| 5 | Weekly tasks | not evidenced → [R] | ticks | tasks with text | §9 pattern |
| 6 | Monthly to-do | not evidenced → [R] | ticks | tasks with text | §9 pattern |

**Renderer `[I]` + `[R]`:** the hex-paste workflow `[V22]` (paint a cell, copy the hex, paste into Customize ⇒ *all* bars recolour) fits **one** mechanism in Google Sheets: `SPARKLINE` with `"color1"` pointing at that cell. Conditional-formatting fills cannot be driven by a cell value in Sheets, so CF-based bars could not recolour like that.

```
Sheets : =SPARKLINE(IFERROR(MIN(1,pct),0), {"charttype","bar";"min",0;"max",1;"color1",Settings!$C$8;"color2",Settings!$C$9})
Excel  : Data bar (fixed colour)  or  REPT block string
```
Updating is automatic (pure dependency chain: tick → % → bar). ⚠ MANUAL TEST: SPARKLINE accepts `#RRGGBB` text from a cell — validate that and add input validation `=REGEXMATCH(C8,"^#[0-9A-Fa-f]{6}$")` (Sheets) to avoid silently-default bars.

---

## 15. Data Flow (Phase 14)

```
USER INPUT ─► SETTINGS ─────────────────────────────────────────────┐
 (month, year, week-start, start time, slot, hex, lists, labels)    │
        │                                                           │
        ▼                                                           ▼
   CALC: SelMonth→FirstDay→Offset→GridStart→6×7 date matrix     DROPDOWN LISTS
        │ WeeksNeeded, week ranges                           (priority, category)
        ├────────────► MONTH TAB (dates, today, links)              │
        └────────────► W1..W6 (INDEX row n of matrix) ◄─────────────┘
                          │
        ┌─────────────────┼───────────────────────────┐
        ▼                 ▼                           ▼
  Schedule engine   To-do / priorities           Habits & numeric
  (Start+Slot)      (checkbox → strike, %)       (checkbox/value → %, avg)
        └─────────────────┴──────────┬────────────────┘
                                     ▼
                       PROGRESS % ─► BAR (colour from Settings)
                                     ▼
                       [R] DASHBOARD roll-up (ratio of sums)
```
Actual dependencies from the reference `[C]`: Customize → dates on all tabs; Customize → start time on schedules; Customize → priorities/categories in dropdowns; Customize → numeric labels on every week; Customize → bar colour on every bar; ticks → bars (same tab). Cross-tab flow *between* weeks or into the calendar is **not** evidenced; the calendar and weeks are linked only by dates and hyperlinks.

---

## 16. Backend / Helper Architecture (Phase 15)

| Area | Where | Visibility | Protection |
|---|---|---|---|
| Settings inputs | `Settings` | Visible | Input cells unlocked, rest locked |
| Priority / category / habit / numeric lists | `Settings` | Visible | Unlocked |
| English weekday & month lists, 15-min time list | `Lists` | Hidden | Locked |
| Date engine, week ranges, active flags | `Calc` | Hidden | Locked |
| Per-week numerators/denominators (for dashboard) | hidden cells on each `W*` (e.g. `BK40:BK45`) | Hidden columns | Locked |
| Named ranges | workbook | — | — |

Named ranges `[R]`: `SelMonth, FirstDay, LastDay, DaysInMonth, WSType, Offset, GridStart, WeeksNeeded, SlotStart, SlotMin, BarColor, TrackColor, PriorityList, CategoryList`.
* Sheets: `PriorityList = Settings!$B$12:$B$18`; `CategoryList = Settings!$B$22:$B$33`.
* Excel dynamic (contiguous list): `CategoryList =Settings!$B$22:INDEX(Settings!$B$22:$B$33,MAX(1,COUNTA(Settings!$B$22:$B$33)))`.

---

## 17. Formula Blueprint (Phase 16)

Legend: **C** = confirmed behaviour, **L** = likely, **R** = recommended; ✅ verified in engine; ⚠ manual test. GS = Google Sheets, XL = Excel.

| Feature | Place | Formula | Label | GS | XL |
|---|---|---|---|---|---|
| Month number | `Calc!B1` | `=MATCH(Settings!$C$3,Lists!$A$1:$A$12,0)` | R ✅ | ✓ | ✓ |
| First day | `Calc!B2` | `=DATE(Settings!$C$4,B1,1)` | R ✅ | ✓ | ✓ |
| Last day | `Calc!B3` | `=EOMONTH(B2,0)` | R ✅ | ✓ | ✓ |
| Days in month | `Calc!B4` | `=DAY(B3)` | R ✅ | ✓ | ✓ |
| Weekday type | `Calc!B5` | `=IF(Settings!$C$5="Monday",2,1)` | R ✅ | ✓ | ✓ |
| Offset | `Calc!B6` | `=WEEKDAY(B2,B5)-1` | R ✅ | ✓ | ✓ |
| Grid start | `Calc!B7` | `=B2-B6` | R ✅ | ✓ | ✓ |
| Weeks needed | `Calc!B8` | `=ROUNDUP((B6+B4)/7,0)` | R ✅ | ✓ | ✓ |
| Date matrix | `Calc!D3:J8` | `=$B$7+7*w+d` (literals) | R ✅ | ✓ | ✓ |
| Calendar cell | `Month!F5…` | `=IF(MONTH(Calc!D3)=SelMonth,Calc!D3,"")` | R ✅ | ✓ | ✓ |
| Week-tab date | `W*!<c0>5` | `=INDEX(Calc!$D$3:$J$8,$B$2,d)` | R | ✓ | ✓ |
| Weekday label | `W*!<c0>4` | `=IF(INDEX(Settings!$C$69:$C$75,WEEKDAY(date,1))="",INDEX(Settings!$B$69:$B$75,WEEKDAY(date,1)),INDEX(Settings!$C$69:$C$75,WEEKDAY(date,1)))` (translation keyed to *real* weekday) | R | ✓ | ✓ |
| Time slot | `W*!<c0>9…44` | `=IF((n-1)*SlotMin>=1440,"",MOD(ROUND((SlotStart+(n-1)*SlotMin/1440)*1440,0),1440)/1440)` | R ✅ | ✓ | ✓ |
| Task % | `W*!<c1>6` | §9 SUMPRODUCT | R ✅ | ✓ | ✓ |
| Habit %s, streak | habit zone | §12 | R ✅ | ✓ | ✓ |
| Numeric fraction/avg | tracker zone | §13 | R ✅ | ✓ | ✓ |
| Progress bar | next to each % | `SPARKLINE` (§14) | L (colour from cell) / R ⚠ | ✓ | ✗ (use data bar/REPT) |
| Strike-through | task cells | CF `=$J47=TRUE` | C behaviour, R formula ⚠ | ✓ | ✓ |
| Today highlight | date cells | CF `=AND(ISNUMBER(F5),F5=TODAY())` | C behaviour, R formula ⚠ | ✓ | ✓ |
| Own-week highlight | mini calendar | CF `=ROW()-ROW($B$6)+1=$B$2` | C behaviour, R formula ⚠ | ✓ | ✓ |
| Week link | `Month!E5…` | `=HYPERLINK("#gid=<W1 gid>","Week 1")` (Sheets) / `=HYPERLINK("#'W1'!A1","Week 1")` (Excel) | C behaviour, R formula ⚠ — verify the gid survives "Make a copy" | ✓ | ✓ |
| Dropdowns | task/activity cells | Data validation list = `PriorityList` / `CategoryList` | C | ✓ | ✓ |
| Checkbox | to-do/habit | Sheets: Insert ▸ Checkbox. Excel 365: Insert ▸ Checkbox; Excel ≤2019: dropdown `✔`/blank + `COUNTIF(range,"✔")` | C (Sheets) | ✓ | partial |

**Not determinable / not fabricated:** the reference's exact formulas, cell addresses and rule definitions. Everything above is **R** unless the label says otherwise.

---

## 18. Cell / Grid Blueprint (Phase 17) — **independent design**

### `Settings`
| Range | Purpose | Type |
|---|---|---|
| `C3` | Month (name) | Dropdown from `Lists!A1:A12` |
| `C4` | Year | Number, validation whole 1901–2100 |
| `C5` | Week starts | Dropdown Sunday/Monday |
| `C6` | Schedule start | Time, validation `=AND(ISNUMBER(C6),C6>=0,C6<1)` |
| `C7` | Slot minutes | Dropdown 15/30/60 |
| `C8` / `C9` | Bar colour / track colour | Hex text, regex validation |
| `B12:B18` | Priorities (7) | Text input |
| `B22:B33` | Categories (12) | Text input |
| `B37:B57` | Habit labels (21) | Text input |
| `B61:F65` | Numeric trackers: Label, Unit, Min, Max | Input |
| `B69:C75` | Weekday translation: B = English Sun…Sat (locked), C = your word | Locked / input |
| `B79:C90` | Month translation (display-only) | Locked / input |
| `B94:C110` | Section-label overrides (e.g. "Schedule", "Gratitude") | Input (supports "customize any label" `[C]`) |

### `Calc` (hidden)
`B1:B8` date engine · `D3:J8` matrix · `B10:F15` week ranges (start, clip-start, clip-end, active flag in `E`, label in `F`).

### `Month`
| Range | Purpose | Type |
|---|---|---|
| `B2` | Title `=TEXT(FirstDay,"mmmm yyyy")` | Formula |
| `B4:C8` | Top goals (☐ + text) | Input |
| `B11:D25` | Monthly to-do (☐, priority, text); `B10` progress | Input / formula |
| `B28:D32` | Important dates (date, text) | Input |
| `E5,E9,E13,E17,E21,E25` | Week links | Formula |
| `F4:L4` | Weekday headers | Formula |
| `F5:L28` | 6 × (1 date row + 3 event rows): date rows 5,9,13,17,21,25; event rows below | Date = formula, events = **input (merge allowed)** |
| `F5:L28` CF | today highlight; unused-week grey | |

### `W1`…`W6`  (identical; `B2` = week index, constant)
Columns: `A` gutter · `B:H` overview · `I` gap · day blocks of **6 columns** (`c0…c5`) starting at col 10 (`J`): Day *d* start = col `10+6(d-1)` ⇒ J, P, V, AB, AH, AN, AT · `AZ` gap · `BA:BI` trackers.

| Range (Day 1; shift +6 columns per day) | Purpose | Type |
|---|---|---|
| `J5:O5` | Weekday + date header | Formula |
| `J6:O6` | Day progress bar | Formula |
| `J9:J44` | Time slots (36) | Formula |
| `K9:M44` | Activity (merge across K:M allowed) | Input |
| `N9:N44` | Category | Dropdown |
| `J47:J56` | ☐ | Checkbox |
| `K47:K56` | Priority | Dropdown |
| `L47:L56` | Category | Dropdown |
| `M47:N56` | Task text (`M` is the tested column) | Input |
| `J59:O63` | Gratitude ×5 | Input |
| `J66:O71` | Notes | Input |
| `B4:H11` | Mini calendar (header + 6 rows) | Formula |
| `B14:H19` / `B22:H27` | Weekly priority / secondary tasks (☐ in B, text C:H) | Input |
| `B12` | Week range label | Formula |
| `BA5:BI5` | Habit header | Formula |
| `BA6:BA26` | Habit labels (21) | Formula (=Settings) |
| `BB6:BH26` | Habit ticks | Checkbox |
| `BI6:BI26` | Row % / bar | Formula |
| `BB27:BH27` | Day % | Formula |
| `BA31:BI40` | 5 numeric trackers × 2 rows: value row (`BB:BH` input) + bar row; `BI` = average/total | Input / formula |
| `BK40:BK45` | hidden numerators / denominators for Dashboard | Formula |

Conditional-formatting ranges: task text (strike), date cells (today, out-of-month dim), mini-calendar (own week, today), priority/category cells (slot colours), whole tab (unused week), schedule category cells.

---

## 19. UI / Graphic Design System (Phase 18)

**Reference `[C]/[I]`:** "Pink" is the product variant (+ B&W variant) `[PAGE]`; today highlighted in a pink-purple shade `[V22]`; planner mimics a physical-planner layout `[PAGE]`. Fonts, radius, exact hexes: **not determinable** without images.

**Original palette `[R]` — "Slate & Teal"** (deliberately unrelated to the reference's pink)

| Role | Hex |
|---|---|
| Primary | `#24566B` deep teal |
| Secondary | `#E8F1F2` mist |
| Accent (today, focus) | `#F2A541` amber |
| Progress default | `#3BA776` |
| Track | `#E3E9EC` |
| Danger / orphan | `#D1495B` |
| Background / surface | `#FFFFFF` / `#F7F9FA` |
| Border | `#D5DDE0` |
| Text / muted / dimmed date | `#1E2A30` / `#6B7A83` / `#B8C2C7` |

**Typography (Sheets/Excel safe)** — H1 Montserrat 20 bold (Excel: Segoe UI Semibold) · H2 13 bold caps, tracked · H3 11 semibold · Body 10 Lato/Roboto (Excel: Calibri) · Labels 9 muted.
**Spacing** — S = 8 px gutter/spacer · M = 16 px · L = 32 px section gap; body rows 22 px, header rows 30 px.
**Components** — cards = bordered zones with H2 banner in Primary and white text; no rounded corners (Sheets can't); inputs = white with 1px border, formulas = surface grey, locked; checkboxes = default; bars = sparkline in 10-px-tall rows; icons = Unicode (✔ ▶ ★) only.
**Hierarchy** — tab title › section banner › day header › sub-labels › entries.

---

## 20. GitHub Research (Phase 20)

Searches run via `gh search repos` over ~12 concept queries (Sheets planner, Excel planner, habit tracker spreadsheet, calendar generator, Apps Script planner, openpyxl planner, …). **Coverage is thin: many queries returned nothing and no open-source clone of the reference exists.** I read the code/READMEs of the items below; I did *not* run them.

| Repo | What it does | Architecture / technique | Learn | Do NOT copy |
|---|---|---|---|---|
| `justinyaodu/gsheet-planner` (MIT) | Self-sorting event/assignment planner | Apps Script `onEdit` sorts a range; Settings sheet holds categories; date macros (`f3`, `w1`, `d3-14`); category colours via CF | Settings-fed category list; input-macro idea; "sort key" helper column | Auto-sort on edit — its own README warns rows move while you type; any script dependency (our product should be formula-only so it survives "Make a copy") |
| `WillDev12/Google-Sheets-Planner` (no licence) | Planner with script buttons | `goClick()` writes prefixed text into the active cell | Nothing reusable | Code has `if (sheet = "Home")` (assignment, not comparison — always true) → buggy; unlicensed |
| `ShubhPS/weekly-planner` (no licence) | Next.js week-at-a-glance rebuilt from a Sheets planner | Components `DayCard`, `HabitTracker`, `WeekDial`, `Donut` | Confirms same data model (day → tasks/habits → % ring) | It's a web app; no formulas |
| `masoumeh-ashrafi/habit-tracker-google-sheets` (no licence) | Habit dashboard | Repo contains README + screenshots/video only | Dashboard-page idea | Nothing — no formulas to inspect |
| `kudrykv/latex-yearly-planner` (this checkout, MIT) | PDF planner generator in Go | `NewWeeksForMonth`: `shift := (7 + weekday - wd) % 7`; fill days until month changes; append weeks | **Independent cross-check of our offset formula**: its `shift` is the same quantity as our `Offset = WEEKDAY(first,type)-1`; its loop yields 4–6 weeks | Go/LaTeX generation approach (offline PDF; not a spreadsheet) |

**Validation note:** nothing from GitHub was adopted as-is. The date logic recommended here was independently tested (see §0) rather than taken from any repo.

---

## 21. Reference vs Our Original Version

| Feature | Reference | Ours `[R]` |
|---|---|---|
| Platform | Sheets only `[C]` | Sheets primary; documented Excel port |
| Month/year | dropdown + number | Month name dropdown (language-proof), year 1901–2100 validated, **month/year stamp warning** |
| Monthly calendar | 6 rows, typed events, links, today | Same + weeks-used banner, dimmed out-of-month, week links |
| Week tabs | 6 identical tabs | Same; unused-week banner + grey |
| Daily schedule | start-time driven; interval unknown | Start time **+ 15/30/60 slot**, 36 rows, index-based formula, midnight-safe |
| To-do | priority, category, task, ☑, strike, bar | Same + orphan-value guard, slot-colour priorities |
| Priorities | 7, Settings | 7, Settings, **colour tied to slot** |
| Categories | Settings, count unknown | 12 slots, slot colours, orphan guard |
| Habits | 21, ticks, bars; labels per tab `[I]` | 21, labels **global** in Settings, streak helper, day %, overall % |
| Numeric | 5, labels from Settings, bars | 5, labels + unit + **min/max** from Settings, avg/total/bar |
| Progress | bars colour from hex cell `[C]` | Same, hex validated, track colour option |
| Translations | positional (set week-start first) `[C]` | **keyed to real weekday**, independent of week-start |
| Reporting | none evidenced | Optional Dashboard (ratio-of-sums) |
| Protection | not stated | Formula cells locked, helper sheets hidden |

---

## 22. Final Workbook Architecture

```
WORKBOOK
│
├── Start            (visible, locked)   onboarding, legend, stamp warning
├── Settings         (visible)           inputs + lists + translations
├── Month            (visible)           goals, month to-do, important dates, calendar, week links
├── W1 … W6          (visible)           identical weekly workspace (B2 = 1…6)
│     ├─ Overview: mini calendar, week range, weekly priority/secondary tasks
│     ├─ Day blocks ×7: schedule(36) · to-do(10) · gratitude(5) · notes
│     └─ Trackers: habits(21×7) · numeric(5×7)
├── Dashboard        (optional, locked)  roll-up of W1–W6 helper cells
├── Calc             (HIDDEN, locked)    date engine · week ranges · active flags
└── Lists            (HIDDEN, locked)    month names · English weekdays · time list
```
Workflow `[C]`: keep one pristine, customised **master**; each month → *File ▸ Make a copy* → set month/year → plan.

---

## 23. Build Order

| # | Stage | Build | Why / dependency | Test before moving on |
|---|---|---|---|---|
| 1 | Architecture | Create all tabs; hide/protect later; define names | everything refers to names | tabs & names exist |
| 2 | Settings | Inputs + validation + lists | engine inputs | each validation rejects bad input (year 1850, hex "red", time 25:00) |
| 3 | Date engine | `Calc!B1:B8`, matrix `D3:J8` | foundation of all dates | §24 date cases incl. Feb 2100, Jan 2022 |
| 4 | Month calendar | Grid, today CF, links | uses matrix | 4/5/6-row months |
| 5 | Week structure | `W1`, copy ×5, set `B2`, week ranges | uses matrix + ranges | Week 5/6 inactive for Feb 2026 Sunday-start (4 rows) |
| 6 | Daily schedule | slot formula, category dropdown | needs Start/Slot | §24 time cases |
| 7 | Task system | to-do block, strike CF, % formula | needs lists | empty / partial / full |
| 8 | Habit tracker | 21×7 + % + streak helper | independent | partial/full/blank-label |
| 9 | Numeric trackers | settings table, fraction, avg, bars | needs min/max | min/max/clamp/empty |
| 10 | Progress calcs | all % cells + hidden dashboard cells | needs 7–9 | numerator/denominator checks |
| 11 | Conditional formatting | strike, today, own-week, unused week, slot colours, orphans | needs data in place | visual pass |
| 12 | Dropdowns | priority/category validation | needs lists | add 12th category; rename test |
| 13 | UI | palette, fonts, widths, freeze panes | last cosmetic layer | print/zoom view |
| 14 | Protection | lock formulas, hide Calc/Lists | after all formulas final | user can type in every input, none in formulas |
| 15 | Testing | full §24 matrix | — | all pass |

---

## 24. Testing Plan (Phase 24)

**Date engine** — expected values from independent oracle (`calendar` module); ✅ = also confirmed by the formula-engine run.

| Test | Input | Expected |
|---|---|---|
| January | Jan 2026, Sun | 31 d, offset 4, **5 rows**, grid starts 28 Dec 2025 ✅ |
| February | Feb 2026, Sun | 28 d, offset 0, **4 rows**, starts 1 Feb ✅ |
| Feb leap | Feb 2024 | **29 d**, 5 rows ✅ |
| Feb century | Feb 2100 / Feb 2000 | 28 d (not leap) / 29 d (leap) ✅ |
| March | Mar 2026, Sun / Mon | 5 rows / **6 rows** ✅ |
| April | Apr 2026, Sun | 30 d, offset 3, 5 rows ✅ |
| December → year change | Dec 2026 then Jan 2027, Sun | grid starts 29 Nov 2026 / **27 Dec 2026**; Jan 2027 = **6 rows** ✅ |
| Month change only | switch C3 | all tabs re-flow, tick data stays (stamp warning appears) ⚠ |
| 4-week month | Feb 2026 Sun | W5, W6 inactive banner ⚠ |
| 5-week month | Apr 2026 Sun | W6 inactive ⚠ |
| 6-row month | Aug 2026 Sun (or Jan 2022) | all 6 active ✅ |
| Week-start flip | any month Sun↔Mon | offset & grid change, weekday headers follow ✅ |
| Out-of-range year | 1850 / 2200 | validation rejects ⚠ |

**Schedule** ✅: 06:00@30 → first 06:00, 6th 08:30; 06:00@15 → 6th 07:15; 06:00@60 → 6th 11:00; 23:00@30 → 3rd slot = **00:00** (value 0, not 1); 05:30@45; `60-min` rows beyond 24 h → blank.

**Tasks** ✅: empty list → 0 % (no `#DIV/0!`); 3 tasks 0 ticks → 0; 3 tasks 2 ticks → 66.7 %; all → 100 %; ticks on blank rows ignored; ⚠ ticking applies strike-through.

**Habits** ✅: 3/7 → 42.9 %; 7/7 → 100 %; 0/7 → 0 %; blank-label row shows "" and is excluded from overall (test: 3 labelled habits, 10 ticks out of 3×7 = 21 cells → 47.6 %).

**Numeric** ✅: blank → "" (no bar); value 6 on 0–10 → 0.6 / `██████░░░░`; max 10 → 1; min 0 → 0; below min (−3) → 0 (clamped); above max (12) → 1 (clamped); empty tracker avg → 0.

**Identified risks:** Excel/Sheets 1900 epoch; `TEXT` locale codes; user typing over formulas (→ protect); merged cells in input zones are safe only if no formula references them; checkbox on blank rows (handled); renamed category/priority leaves orphan text (red guard); `INDIRECT` in CF is volatile (keep few rules); SPARKLINE absent in Excel; hyperlink gids after copy ⚠; spill-over dates exist in two months' files; changing month after typing misaligns events (stamp warning).

---

## 25. Recommended Improvements (all `[R]`, none claimed from the reference)

1. **Month/year stamp**: `Calc!B20 = Settings month&year` captured once; warn on `Start` if inputs exist and stamp ≠ current — directly prevents the "change month, events now sit on wrong dates" trap inherent in text-in-date-cell design.
2. Translations keyed by real weekday (removes the order-of-setup trap).
3. Slot-based colours for priorities/categories + orphan guard.
4. Global habit & numeric labels with min/max/units.
5. Validated hex input with sample swatch next to it.
6. Optional Dashboard using ratio-of-sums (never average the weekly percentages).
7. 15/30/60 slot setting; midnight-safe times.
8. Optional extra columns (due date, notes) are **not** in the reference; add only if you want to diverge: `Due` validated ≥ FirstDay-6, overdue CF `=AND(due<>"",due<TODAY(),chk=FALSE)`.
9. Excel port: dropdown ✔ markers for pre-365, Data Bars, fixed bar colour.
10. Confusions to defuse on `Start`: "make a copy each month", "spill-over days", "type events in the cell below the date", "don't type over grey cells".

---

# BUILD SPECIFICATION (developer-ready)

**Scope:** 1 workbook, 8–9 tabs: `Start, Settings, Month, W1..W6, [Dashboard], Calc(hidden), Lists(hidden)`. Target Google Sheets; Excel port per notes. **Formula-only, no scripts.**

**1 Settings (inputs)** `C3` month name (list `Lists!A1:A12`) · `C4` year (whole 1901–2100) · `C5` Sunday/Monday · `C6` time ≥0,<1 · `C7` 15/30/60 · `C8` hex bar · `C9` hex track · `B12:B18` priorities(7) · `B22:B33` categories(12) · `B37:B57` habits(21) · `B61:F65` numeric (Label/Unit/Min/Max) · `B69:C75` weekday translations (B English Sun–Sat) · `B79:C90` month translations · `B94:C110` label overrides.

**2 Calc** `B1=MATCH(Settings!C3,Lists!A1:A12,0)` · `B2=DATE(Settings!C4,B1,1)` · `B3=EOMONTH(B2,0)` · `B4=DAY(B3)` · `B5=IF(Settings!C5="Monday",2,1)` · `B6=WEEKDAY(B2,B5)-1` · `B7=B2-B6` · `B8=ROUNDUP((B6+B4)/7,0)` · `D3:J8 =$B$7+7*w+d` (w=0..5, d=0..6 as literals) · week table `B10:F15` (start, clip-start, clip-end, active, label) as §7.

**3 Month** title; goals (5), month to-do (15, ☑/priority/text), important dates (5); calendar `F5:L28` date rows `=IF(MONTH(Calc!D3)=SelMonth,Calc!D3,"")` (fmt `d`), 3 input event rows under each date row; week links in `E`; CF today = `=AND(ISNUMBER(F5),F5=TODAY())`.

**4 Week tab (×6)** `B2`=1..6. Dates `=INDEX(Calc!$D$3:$J$8,$B$2,d)`. Mini calendar `B4:H11` with own-week + today CF. Weekly priority (5) + secondary (5) with ☑ and strike CF. **7 day blocks**, 6 cols each starting J: header (weekday via real-weekday translation lookup, date), progress bar, **36 slots** `=IF((n-1)*SlotMin>=1440,"",MOD(ROUND((SlotStart+(n-1)*SlotMin/1440)*1440,0),1440)/1440)` fmt `h:mm AM/PM`, activity (merge-friendly), category dropdown; **10 to-dos** `☑|Priority|Category|Task` with strike CF `=$J47=TRUE`; % `=IFERROR(SUMPRODUCT((M47:M56<>"")*(J47:J56=TRUE))/SUMPRODUCT((M47:M56<>"")*1),0)`; 5 gratitude lines; notes block.
**Trackers** (`BA:BI`): 21 habit rows (label `=Settings!B37`, 7 ☑, row % `=IF($BA6="","",COUNTIF(BB6:BH6,TRUE)/7)`, overall % per §12, day % per §12). 5 numeric trackers: 7 inputs (validated Min–Max), fraction `=IF(v="","",IFERROR(MIN(1,MAX(0,(v-Min)/(Max-Min))),0))`, avg `=IFERROR(AVERAGE(r),0)`, total `=SUM(r)`.
**Bars:** `=SPARKLINE(IFERROR(MIN(1,pct),0),{"charttype","bar";"min",0;"max",1;"color1",Settings!$C$8;"color2",Settings!$C$9})` (Excel: data bar or REPT).

**5 CF rules (every tab)** strike on tick · today · own week · out-of-month dim · unused week grey (`INDIRECT` in Sheets) · priority & category slot colours (`=$K47=INDIRECT("Settings!$B$12")`, …) · orphan red.

**6 Dropdowns** priority → `Settings!B12:B18`; category → `Settings!B22:B33` (Excel: dynamic named range); week start, slot, month lists as above.

**7 Dashboard (optional)** per-week hidden numerators/denominators on each `W*`; roll-up = `SUM(numerators)/SUM(denominators)` wrapped in `IFERROR(…,0)`.

**8 Protection** lock all formula cells and `Calc/Lists/Start`; leave inputs, event rows, notes unlocked; hide `Calc`, `Lists`.

**9 Design** palette & type per §19; freeze first 3 rows / first column on week tabs; column widths: time 64 px, activity 3×90 px, category 90 px, spacer 12 px.

**10 Acceptance:** all §24 tests pass; `verify_formulas.py` and `verify_progress_formulas.py` → `ALL PASS`; manual checks (⚠ items: SPARKLINE hex, CF rules, hyperlinks after copy, checkbox strike, dropdown blanks) signed off in a live Google Sheet before release.

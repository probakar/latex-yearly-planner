# Planner.xlsx – kaise use karein / how to use

**Roman Urdu**
1. `Planner.xlsx` ko Google Drive mein upload karein → right-click → *Open with → Google Sheets*.
2. Ek baar script chalayen: *Extensions → Apps Script* → `setup_google_sheets.gs` ka code paste karein → *Run → setupPlanner*.
   (Isse TRUE/FALSE cells asli checkboxes ban jaate hain aur bars aap ke chune hue rang mein ho jaate hain.)
3. **Settings** tab kholein: Month, Year, Week start (Sunday/Monday), schedule ka start time, slot (15/30/60 min) chunein.
   Priorities, categories, habits aur 5 numeric trackers wahin likhein.
4. **Month** tab: goals, monthly to-do, important dates; events date ke neeche wale cells mein type karein.
5. **W1–W6**: har hafte ka schedule, to-do, gratitude, notes, habits aur numbers. Task tick karein → text par line aa jati hai aur bar barhta hai.
6. Har mahine file ki **nayi copy** banayein (File → Make a copy). Original ko khali rakhein.

Grey cells formulas hain (type na karein). White cells aap ki hain. Hidden tabs `Calc` aur `Lists` ko na chherein.

**English**
Import to Google Sheets → run `setup_google_sheets.gs` once → fill *Settings* → plan in *Month* and *W1–W6* → make a fresh copy each month.

## Deviations from BLUEPRINT.md
* Monthly *Important dates*: date in column C, text in D (B unused) – column B is too narrow for a date.
* Dashboard tab (optional in the blueprint) is **not** built.
* Time slots / date matrix use literal offsets instead of `ROWS()`/`COLUMNS()` (identical results; verifiable).
* In the `.xlsx` itself, bars are text blocks (work in Excel too) and checkboxes are TRUE/FALSE cells; the Google script upgrades both.

## Rebuild / verify
```
python3 -m venv v && ./v/bin/pip install openpyxl formulas
./v/bin/python build_planner.py Planner.xlsx
./v/bin/python verify_planner.py        # recalculates 4 month/year scenarios and compares with Python's calendar
```
Not tested in a live Google Sheet/Excel: conditional-formatting colours, INDIRECT-based slot colours, protection behaviour, hyperlinks, the `.gs` script.

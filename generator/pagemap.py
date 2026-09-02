"""PAGE_MAP — the complete page architecture and hyperlink graph of the
planner, mirroring the reference planner's structure exactly.

Page order (identical to the reference 1,283-page planner):

  1  title        (cover)
  1  year         (annual overview, target name "Calendar" + "2027")
  4  quarter      Q1..Q4
 12  month        January..December
 53  week         fwWeek 53, Week 1 .. Week 52
 365 day          Jan 1 .. Dec 31 (ordered by month-grid rows, i.e. strictly
                  chronological inside each month)
 365 reflect      one per day
 365 day_notes    one per day ("More/Notes" page)
   3  notes_index Notes Index, Notes Index 2, Notes Index 3
 114  note        Note 1 .. Note 114  (3 index pages x 38 notes each)

Targets (named destinations) used by the reference planner:
  "2027", "Q1".."Q4", month names, "fwWeek 53"/"Week 1".."Week 52",
  day refs "YYYY-MM-DDT00:00:00Z" with prefixes "" / "Reflect" / "More",
  "Calendar" (annual heading), "Notes Index".."Notes Index 3",
  "Note 1".."Note 114".
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

import plancal
from plancal import (
    MONTH_NAMES, MONTH_SHORT, day_ref, day_week_ref, month_grid_weeks,
    month_next, month_prev, quarter_of, week_next_exists, week_number,
    week_prev_exists, week_ref, year_weeks,
)

YEAR = 2027
NOTES_INDEX_PAGES = 3   # reference: notesindexpages
NOTES_PER_INDEX_PAGE = 38  # reference: notesonpage (rm2.base)
NOTES_TOTAL = NOTES_INDEX_PAGES * NOTES_PER_INDEX_PAGE  # 114


@dataclass
class Page:
    idx: int                 # 0-based position in the document
    kind: str                # title|year|quarter|month|week|day|reflect|day_notes|notes_index|note
    label: str               # human label
    target: Optional[str]    # primary named destination (None for title)
    meta: dict = field(default_factory=dict)

    def __repr__(self):
        return f"[{self.idx:4d}] {self.kind:11s} {self.label}"


class PageMap:
    def __init__(self, year: int = YEAR):
        self.year = year
        self.pages: list[Page] = []
        self.by_target: dict[str, int] = {}

        # ---- calendar datasets -------------------------------------------
        self.yweeks = year_weeks(year)                     # 53 rows x 7 days
        self.mweeks = {m: month_grid_weeks(year, m) for m in range(1, 13)}
        self.all_days = [d for m in range(1, 13) for row in self.mweeks[m] for d in row if d]

        self._build()

    # ------------------------------------------------------------------
    def _add(self, kind: str, label: str, target: Optional[str], **meta) -> Page:
        page = Page(idx=len(self.pages), kind=kind, label=label, target=target, meta=meta)
        self.pages.append(page)
        if target is not None:
            if target in self.by_target:
                raise RuntimeError(f"duplicate target {target!r}")
            self.by_target[target] = page.idx
        return page

    def _build(self):
        y = self.year

        # 1. cover ---------------------------------------------------------
        self._add("title", f"{y} Digital Planner", None)

        # 2. year ----------------------------------------------------------
        # Reference target name for the annual page is "Calendar" (the
        # Calendar tab links here); no separate "2027" destination exists.
        self._add("year", str(y), "Calendar")

        # 3. quarters --------------------------------------------------------
        for q in range(1, 5):
            self._add("quarter", f"Q{q}", f"Q{q}", quarter=q,
                      months=list(range(q * 3 - 2, q * 3 + 1)))

        # 4. months ----------------------------------------------------------
        for m in range(1, 13):
            self._add("month", MONTH_NAMES[m - 1], MONTH_NAMES[m - 1],
                      month=m, quarter=quarter_of(m))

        # 5. weeks -----------------------------------------------------------
        for days in self.yweeks:
            ref = week_ref(days, y)
            self._add("week", f"Week {week_number(days)}", ref, days=days,
                      prev_exists=week_prev_exists(days, y),
                      next_exists=week_next_exists(days, y))

        # 6./7./8. daily triplets ---------------------------------------------
        # Reference orders daily pages by month-grid rows (month by month).
        for d in self.all_days:
            self._add("day", d.isoformat(), day_ref(d), date=d)
        for d in self.all_days:
            self._add("reflect", "Reflect " + d.isoformat(), day_ref(d, "Reflect"), date=d)
        for d in self.all_days:
            self._add("day_notes", "Notes " + d.isoformat(), day_ref(d, "More"), date=d)

        # 9. notes index ------------------------------------------------------
        for i in range(1, NOTES_INDEX_PAGES + 1):
            label = "Notes Index" if i == 1 else f"Notes Index {i}"
            self._add("notes_index", label, label, index=i)

        # 10. note pages -------------------------------------------------------
        for n in range(1, NOTES_TOTAL + 1):
            page_of_note = (n - 1) // NOTES_PER_INDEX_PAGE + 1
            self._add("note", f"Note {n}", f"Note {n}", number=n, indexpage=page_of_note)

    # ------------------------------------------------------------------
    # Lookups used when wiring links.
    # ------------------------------------------------------------------
    def target_of(self, name: str) -> Optional[int]:
        return self.by_target.get(name)

    def day_page(self, d: dt.date) -> Page:
        return self.pages[self.by_target[day_ref(d)]]

    def reflect_page(self, d: dt.date) -> Page:
        return self.pages[self.by_target[day_ref(d, "Reflect")]]

    def more_page(self, d: dt.date) -> Page:
        return self.pages[self.by_target[day_ref(d, "More")]]

    def month_page(self, m: int) -> Page:
        return self.pages[self.by_target[MONTH_NAMES[m - 1]]]

    def quarter_page(self, q: int) -> Page:
        return self.pages[self.by_target[f"Q{q}"]]

    def year_page(self) -> Page:
        return self.pages[self.by_target[str(self.year)]]

    def notes_index_page(self, i: int = 1) -> Page:
        name = "Notes Index" if i == 1 else f"Notes Index {i}"
        return self.pages[self.by_target[name]]

    def note_page(self, n: int) -> Page:
        return self.pages[self.by_target[f"Note {n}"]]

    def week_page_for_day(self, d: dt.date) -> Page:
        return self.pages[self.by_target[day_week_ref(d)]]

    def counts(self) -> dict:
        out = {}
        for p in self.pages:
            out[p.kind] = out.get(p.kind, 0) + 1
        return out

    def summary(self) -> str:
        lines = [f"PageMap for {self.year}: {len(self.pages)} pages"]
        for kind, n in self.counts().items():
            lines.append(f"  {kind:12s} {n}")
        return "\n".join(lines)


if __name__ == "__main__":
    pm = PageMap()
    print(pm.summary())
    print("total targets:", len(pm.by_target))

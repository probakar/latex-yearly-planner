"""Calendar engine for the 2027 planner.

Faithfully replicates the semantics of the reference planner's Go calendar
(latex-yearly-planner app/components/cal):

* Weeks start on Monday (cfg weekstart: 1).
* "Year weeks" (the weekly section): start from the week (Mon..Sun) that
  contains Jan 1; if that Monday is after Jan 1, back up one week, so the
  first weekly page begins in the previous December. The last weekly page is
  the one whose Monday is still inside the target year.
* Week numbering shown to users: the ISO week number of the week's first day;
  if any day of the week has a different ISO week number, that number wins.
  The first week of the year page is additionally disambiguated with the
  "fw" (first week) prefix inside link targets, e.g. "fwWeek 53".
* "Month weeks" (month grids and the daily section ordering): plain calendar
  rows of each month; days outside the month are blank.
* Quarters are calendar quarters Q1..Q4.

2027 facts used for validation:
* Jan 1, 2027 is a Friday; Dec 31, 2027 is a Friday.
* ISO year 2027 has 52 weeks; Jan 1-3 belong to ISO week 2026-W53.
* The weekly section has 53 pages: fwWeek 53 (2026-12-28..2027-01-03),
  then Week 1 (Jan 4-10) .. Week 52 (2027-12-27..2028-01-02).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

WEEK_START = 0  # Monday in Python's weekday() convention (Go weekstart: 1)

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MONTH_SHORT = [m[:3] for m in MONTH_NAMES]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def quarter_of(month: int) -> int:
    return (month + 2) // 3  # ceil(month/3)


def month_grid_weeks(year: int, month: int, week_start: int = WEEK_START):
    """Calendar-grid rows for one month. Mirrors Go NewWeeksForMonth.

    Returns a list of rows; each row is a list of 7 entries (datetime or None).
    The first row is left-padded when the month does not start on week_start;
    the last row is right-padded.
    """
    first = dt.date(year, month, 1)
    shift = (first.weekday() - week_start) % 7
    weeks: list[list] = []
    row: list = [None] * shift
    day = first
    while day.month == month:
        row.append(day)
        if len(row) == 7:
            weeks.append(row)
            row = []
        day += dt.timedelta(days=1)
    if row:
        weeks.append(row + [None] * (7 - len(row)))
    return weeks


def select_start_week(year: int, week_start: int = WEEK_START) -> dt.date:
    """Monday of the week containing Jan 1, clamped so we never skip past Jan 1."""
    sow = dt.date(year, 1, 1)
    while sow.weekday() != week_start:
        sow += dt.timedelta(days=1)
    if sow.year == year and sow.day > 1:
        sow -= dt.timedelta(days=7)
    return sow


def year_weeks(year: int, week_start: int = WEEK_START):
    """The weekly-section weeks. Mirrors Go NewWeeksForYear.

    Returns list of rows of 7 datetimes. First row may start in December of
    the previous year; last row may extend into January of the next year.
    """
    weeks: list[list[dt.date]] = []
    ptr = select_start_week(year, week_start)
    while True:
        weeks.append([ptr + dt.timedelta(days=i) for i in range(7)])
        ptr += dt.timedelta(days=7)
        if ptr.year != year:
            break
    return weeks


def week_number(days) -> int:
    """Displayed week number for a 7-day row. Mirrors Go Week.weekNumber.

    None entries (blank grid cells) are skipped, exactly like the reference
    skips zero Days: the seed is the first real day's ISO week, then any later
    real day in a different ISO week wins.
    """
    wn = None
    for d in days:
        if d is None:
            continue
        cwn = d.isocalendar()[1]
        if wn is None:
            wn = cwn
        elif cwn != wn:
            return cwn
    if wn is None:
        raise ValueError("week row has no days")
    return wn


def week_ref(days, year: int) -> str:
    """Link-target name for a weekly page. Mirrors Go Week.ref()."""
    wn = week_number(days)
    right_month = next(d for d in reversed(days) if d is not None).month
    right_year = next(d for d in reversed(days) if d is not None).year
    prefix = ""
    if wn > 50 and right_month == 1 and right_year == year:
        prefix = "fw"
    return f"{prefix}Week {wn}"


def day_week_ref(day: dt.date) -> str:
    """The weekly-page target a given day links to. Mirrors Go Day.Breadcrumb."""
    iso_year, wn = day.isocalendar()[0], day.isocalendar()[1]
    prefix = ""
    if wn > 50 and day.month == 1:
        prefix = "fw"
    return f"{prefix}Week {wn}"


def day_ref(day: dt.date, prefix: str = "") -> str:
    """Named target of a daily-style page. Mirrors Go Day.ref (RFC3339, UTC)."""
    return f"{prefix}{day.isoformat()}T00:00:00Z"


@dataclass
class DayInfo:
    date: dt.date

    @property
    def quarter(self) -> int:
        return quarter_of(self.date.month)

    @property
    def iso_week(self) -> int:
        return self.date.isocalendar()[1]

    @property
    def weekday_name(self) -> str:
        return DAY_NAMES[self.date.weekday()]

    @property
    def month_name(self) -> str:
        return MONTH_NAMES[self.date.month - 1]


@dataclass
class WeekInfo:
    days: list  # 7 datetimes
    year: int = 0  # planner year this page belongs to
    number: int = 0

    def __post_init__(self):
        if self.number == 0:
            self.number = week_number(self.days)

    @property
    def ref(self) -> str:
        return week_ref(self.days, self.year)

    @property
    def label(self) -> str:
        return f"Week {self.number}"


def prev_week_days(days, n=7):
    return [d - dt.timedelta(days=n) for d in days]


def next_week_days(days, n=7):
    return [d + dt.timedelta(days=n) for d in days]


def week_prev_exists(days, year: int) -> bool:
    """Mirror of Go Week.PrevExists."""
    still_this_year = days[0].year == year
    isnt_first_day = not (days[0].month == 1 and days[0].day == 1)
    return still_this_year and isnt_first_day


def week_next_exists(days, year: int) -> bool:
    """Mirror of Go Week.NextExists."""
    still_this_year = days[6].year == year
    isnt_last_day = not (days[0].month == 12 and days[0].day == 31)
    return still_this_year and isnt_last_day


def month_prev(month: int) -> int:
    return 12 if month == 1 else month - 1


def month_next(month: int) -> int:
    return 1 if month == 12 else month + 1

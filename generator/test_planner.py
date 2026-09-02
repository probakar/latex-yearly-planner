"""Validation of the calendar engine and page map against hard 2027 facts."""

import datetime as dt
import unittest

import plancal
from pagemap import NOTES_TOTAL, PageMap


class Test2027Calendar(unittest.TestCase):
    def test_first_last_day(self):
        self.assertEqual(dt.date(2027, 1, 1).weekday(), 4)  # Friday
        self.assertEqual(dt.date(2027, 12, 31).weekday(), 4)  # Friday
        with self.assertRaises(ValueError):  # 2027 is not a leap year
            dt.date(2027, 2, 29)

    def test_month_lengths(self):
        lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        for m, n in enumerate(lengths, 1):
            days = [d for row in plancal.month_grid_weeks(2027, m) for d in row if d]
            self.assertEqual(len(days), n, f"month {m}")

    def test_month_grid_no_dupes_no_gaps(self):
        all_days = []
        for m in range(1, 13):
            for row in plancal.month_grid_weeks(2027, m):
                self.assertEqual(len(row), 7)
                for d in row:
                    if d is not None:
                        self.assertEqual(d.month, m)
                        all_days.append(d)
        all_days.sort()
        self.assertEqual(all_days[0], dt.date(2027, 1, 1))
        self.assertEqual(all_days[-1], dt.date(2027, 12, 31))
        for a, b in zip(all_days, all_days[1:]):
            self.assertEqual((b - a).days, 1)
        self.assertEqual(len(all_days), 365)

    def test_year_weeks_shape(self):
        weeks = plancal.year_weeks(2027)
        self.assertEqual(len(weeks), 53)
        for row in weeks:
            self.assertEqual(len(row), 7)
            self.assertEqual(row[0].weekday(), 0)  # Mondays
        self.assertEqual(weeks[0][0], dt.date(2026, 12, 28))
        self.assertEqual(weeks[-1][0], dt.date(2027, 12, 27))
        self.assertEqual(weeks[-1][6], dt.date(2028, 1, 2))
        # every 2027 day appears exactly once
        seen = [d for row in weeks for d in row if d.year == 2027]
        self.assertEqual(len(seen), 365)
        self.assertEqual(len(set(seen)), 365)

    def test_week_numbers_2027(self):
        weeks = plancal.year_weeks(2027)
        nums = [plancal.week_number(row) for row in weeks]
        self.assertEqual(nums, [53] + list(range(1, 53)))
        refs = [plancal.week_ref(row, 2027) for row in weeks]
        self.assertEqual(refs[0], "fwWeek 53")
        self.assertEqual(refs[1], "Week 1")
        self.assertEqual(refs[-1], "Week 52")
        self.assertEqual(len(set(refs)), 53)

    def test_day_week_refs(self):
        # Jan 1-3 2027 belong to ISO 2026-W53 -> first weekly page
        for d in (dt.date(2027, 1, 1), dt.date(2027, 1, 2), dt.date(2027, 1, 3)):
            self.assertEqual(plancal.day_week_ref(d), "fwWeek 53")
        self.assertEqual(plancal.day_week_ref(dt.date(2027, 1, 4)), "Week 1")
        self.assertEqual(plancal.day_week_ref(dt.date(2027, 12, 31)), "Week 52")

    def test_quarters(self):
        for m, q in [(1, 1), (3, 1), (4, 2), (6, 2), (7, 3), (9, 3), (10, 4), (12, 4)]:
            self.assertEqual(plancal.quarter_of(m), q)

    def test_week_prev_next_bounds(self):
        weeks = plancal.year_weeks(2027)
        self.assertFalse(plancal.week_prev_exists(weeks[0], 2027))
        self.assertTrue(plancal.week_next_exists(weeks[0], 2027))
        self.assertTrue(plancal.week_prev_exists(weeks[-1], 2027))
        self.assertFalse(plancal.week_next_exists(weeks[-1], 2027))


class TestPageMap(unittest.TestCase):
    def setUp(self):
        self.pm = PageMap(2027)

    def test_total_pages(self):
        self.assertEqual(len(self.pm.pages), 1283)

    def test_expected_counts(self):
        c = self.pm.counts()
        self.assertEqual(c["title"], 1)
        self.assertEqual(c["year"], 1)
        self.assertEqual(c["quarter"], 4)
        self.assertEqual(c["month"], 12)
        self.assertEqual(c["week"], 53)
        self.assertEqual(c["day"], 365)
        self.assertEqual(c["reflect"], 365)
        self.assertEqual(c["day_notes"], 365)
        self.assertEqual(c["notes_index"], 3)
        self.assertEqual(c["note"], NOTES_TOTAL)

    def test_section_order(self):
        kinds = [p.kind for p in self.pm.pages]
        # sections appear as contiguous blocks in the reference order
        expected_head = (["title", "year"] + ["quarter"] * 4 + ["month"] * 12
                         + ["week"] * 53 + ["day"] * 365 + ["reflect"] * 365
                         + ["day_notes"] * 365 + ["notes_index"] * 3 + ["note"] * 114)
        self.assertEqual(kinds, expected_head)

    def test_day_ordering_chronological_per_month_grid(self):
        days = [p.meta["date"] for p in self.pm.pages if p.kind == "day"]
        self.assertEqual(days[0], dt.date(2027, 1, 1))
        self.assertEqual(days[-1], dt.date(2027, 12, 31))
        self.assertEqual(len(set(days)), 365)
        for prev, nxt in zip(days, days[1:]):
            self.assertEqual((nxt - prev).days, 1)

    def test_unique_targets(self):
        # by_target construction already enforces uniqueness; sanity check count
        self.assertEqual(len(self.pm.by_target), 1282)  # all but title

    def test_key_navigation(self):
        pm = self.pm
        self.assertEqual(pm.day_page(dt.date(2027, 12, 31)).idx, 1283 - 1 - 114 - 3 - 365 * 2)
        self.assertEqual(pm.month_page(1).label, "January")
        self.assertEqual(pm.quarter_page(4).label, "Q4")
        self.assertEqual(pm.notes_index_page(2).label, "Notes Index 2")
        self.assertEqual(pm.note_page(114).label, "Note 114")
        self.assertEqual(pm.week_page_for_day(dt.date(2027, 7, 4)).label, "Week 26")  # Sunday of W26

    def test_boundary_links(self):
        pm = self.pm
        # Dec 31 -> next day does not exist; Jan 1 -> prev does not exist
        d1 = pm.day_page(dt.date(2027, 1, 1))
        d31 = pm.day_page(dt.date(2027, 12, 31))
        self.assertEqual(pm.target_of(plancal.day_ref(dt.date(2026, 12, 31))), None)
        self.assertEqual(pm.target_of(plancal.day_ref(dt.date(2028, 1, 1))), None)
        self.assertEqual(d1.idx, 71)  # 1+1+4+12+53 = 71
        self.assertEqual(d31.idx, 71 + 364)


if __name__ == "__main__":
    unittest.main(verbosity=2)

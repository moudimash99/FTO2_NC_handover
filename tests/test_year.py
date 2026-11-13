"""The year followed, in the calculations that count by month and by week.

  - the production volume of an aircraft lands in the months and the ISO weeks of the year asked for, whatever the year;
  - the deliveries of a past year are counted in the production plan when that year has no deliveries table;
  - the alarm engine of the pages (build/templates/dashboard.html) gives every day its ISO week of the year followed,
    and no week to a day outside it, for years of 52 and of 53 weeks.

The whole run and the pages in another year: tests/next_year_rehearsal.py and tests/next_year_page.js (tests/README.md).

    python3 -m unittest discover -s tests -t .
"""
import datetime as dt
import json
import os
import shutil
import subprocess
import tempfile
import unittest

import pandas as pd

from fto2 import reference

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "build", "templates", "dashboard.html")
D = dt.date


def aircraft(line, prod, msn, start, end, real_end=None):
    """One product of one aircraft as the production plan gives it: planned from start to end, delivered on real_end."""
    plan, real = [start] + [None] * 6 + [end], [None] * 7 + [real_end]
    return {"line": line, "prod": prod, "msn": msn, "plan": plan, "real": real}


class Volume(unittest.TestCase):
    def setUp(self):   # no shutdown: only weekends and public holidays are left out
        self.table = reference.config.table
        reference.config.table = lambda name, columns=None: (pd.DataFrame(columns=["debut", "fin", "poids"])
                                                             if name == "1_calendrier_production.csv" else self.table(name, columns))

    def tearDown(self):
        reference.config.table = self.table

    def test_months_and_weeks_of_the_year_asked_for(self):
        """Two working weeks of March 2031: the whole aircraft in March, half in each of the ISO weeks 10 and 11."""
        recs, asof = [aircraft("A350", "MIP A350", "900", D(2031, 3, 3), D(2031, 3, 14))], D(2031, 6, 1)
        months = reference.working_day_volume(asof, recs, year=2031)
        self.assertEqual(months, {"MIP A350": [0, 0, 1.0] + [0] * 9})
        weeks = reference.working_day_volume(asof, recs, weekly=True, year=2031)
        self.assertEqual({i + 1: v for i, v in enumerate(weeks["line"]["A350"]) if v}, {10: 0.5, 11: 0.5})
        self.assertEqual(weeks["prod"]["MIP A350"], weeks["line"]["A350"])
        self.assertEqual(reference.working_day_volume(asof, recs, year=2030), {"MIP A350": [0] * 12})

    def test_an_aircraft_across_two_years_is_shared(self):
        """Built from Monday 15 December 2031 to Friday 9 January 2032, with 25 December and 1 January off: 18 working days,
        12 of them in 2031."""
        recs, asof = [aircraft("A330", "PTVU", "2500", D(2031, 12, 15), D(2032, 1, 9))], D(2032, 2, 1)
        a = reference.working_day_volume(asof, recs, year=2031)["PTVU"]
        b = reference.working_day_volume(asof, recs, year=2032)["PTVU"]
        self.assertEqual((a[11], b[0]), (round(12 / 18, 2), round(6 / 18, 2)))
        self.assertEqual(sum(a[:11]) + sum(b[1:]), 0)

    def test_the_last_week_of_a_long_year(self):
        """2026 has 53 ISO weeks: Monday 28 to Thursday 31 December 2026 is its week 53; Friday 1 January 2027 is still in
        that week, and belongs to no week of 2027."""
        recs, asof = [aircraft("A320", "MFRL", "12000", D(2026, 12, 28), D(2026, 12, 31))], D(2027, 2, 1)
        w = reference.working_day_volume(asof, recs, weekly=True, year=2026)["line"]["A320"]
        self.assertEqual({i + 1: v for i, v in enumerate(w) if v}, {53: 1.0})
        self.assertEqual(sum(reference.working_day_volume(asof, recs, weekly=True, year=2027)["line"]["A320"]), 0)


class Deliveries(unittest.TestCase):
    def setUp(self):
        self.export = reference._production_export

    def tearDown(self):
        reference._production_export = self.export

    def test_counted_in_the_production_plan(self):
        """A year with no deliveries table: a product is delivered in the month of its Départ OTA, the real date when there
        is one."""
        recs = [aircraft("A350", "MIP A350", "901", D(2029, 11, 5), D(2030, 1, 20), real_end=D(2030, 2, 3)),
                aircraft("A350", "MIP A350", "902", D(2030, 1, 7), D(2030, 2, 25)),
                aircraft("A330", "PTVU", "2501", D(2030, 10, 1), D(2031, 1, 15)),
                aircraft("A330", "PTVU", "2502", D(2029, 9, 1), D(2029, 12, 15))]
        reference._production_export = lambda: (D(2031, 3, 1), recs)
        got = reference.deliveries(2030)
        self.assertEqual(got["delivered"], "plan")
        self.assertEqual(got["prod"], {"MIP A350": [0, 2.0] + [0] * 10})   # 901 on its real date, 902 on its planned one
        self.assertEqual(got["months"][0], "2030-01")
        self.assertIsNone(reference.deliveries(2028))   # nothing was delivered that year

    def test_the_deliveries_table_wins(self):
        """2025 has its table (config/1_livraisons_2025.csv): the plan is not asked."""
        reference._production_export = lambda: self.fail("the production plan was read")
        got = reference.deliveries(2025)
        self.assertEqual(got["delivered"], "sheet")
        self.assertEqual(len(got["months"]), 12)


@unittest.skipUnless(shutil.which("node"), "needs Node")
class AlarmWeeks(unittest.TestCase):
    """The pages' alarm engine counts in weeks of the year followed (window.FTO2_YEAR)."""

    def weeks(self, year, days):
        with open(TEMPLATE, encoding="utf-8") as f:
            page = f.read()
        a, b = "/* ===== ALARM ENGINE START ===== */", "/* ===== ALARM ENGINE END ===== */"
        engine = page[page.index(a):page.index(b)]
        code = ("var window = { FTO2_ALARM_P: {}, FTO2_YEAR: %d };\n%s\n"
                "console.log(JSON.stringify(%s.map(function (d) { return ALARM.week(d); })));\n" % (year, engine, json.dumps(days)))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "weeks.js")
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            r = subprocess.run(["node", path], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-600:])
        return json.loads(r.stdout)

    def test_every_day_of_ten_years(self):
        for year in range(2024, 2034):   # 2026 and 2032 have 53 weeks; 2024, 2028 and 2032 are leap years
            days = [D(year - 1, 12, 1) + dt.timedelta(n) for n in range(31 + 366 + 31)]
            want = [d.isocalendar()[1] - 1 if d.isocalendar()[0] == year else -1 for d in days]
            self.assertEqual(self.weeks(year, [d.isoformat() for d in days]), want, "weeks of %d" % year)

    def test_a_date_with_its_time(self):
        self.assertEqual(self.weeks(2027, ["2027-01-04T08:15:00Z", "2027-01-03", "", "not a date"]), [0, -1, -1, -1])


if __name__ == "__main__":
    unittest.main()

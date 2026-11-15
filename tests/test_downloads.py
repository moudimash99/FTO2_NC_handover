"""The files saved beside the notebook as they were downloaded (fto2/downloads.py): the production plan from the exports of
the Tableau Avances / Retards, the cable requests from the cable team's tracker.

  - the laptop's exports (06_input_data/) give exactly the tables of config/ (0_plan_msn.csv, 0_demandes_cables.csv);
  - a new export replaces the rows it lists, keeps the aircraft delivered before it, drops the rows that left the plan;
  - the day of a download is in its name, else the day the file was saved; a file that is not the expected export says so.

    python3 -m unittest discover -s tests -t .
"""
import glob
import os
import shutil
import tempfile
import time
import unittest

import pandas as pd

from fto2 import config, downloads

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "06_input_data")
EXPORTS = sorted(glob.glob(os.path.join(RAW, "Avances_Retards_*.csv")))
TRACKER = os.path.join(RAW, "cable_team_tracker_A30_NC_cables.csv")


def rows(*aircraft):
    """Plan rows: (msn, planned OTA, real OTA) of one product."""
    t = pd.DataFrame([{c: "" for c in downloads.PLAN_COLUMNS} for _ in aircraft])
    for i, (msn, planned, real) in enumerate(aircraft):
        t.loc[i, ["ligne", "produit", "msn", "prevu_depart_ota", "reel_depart_ota"]] = ["A350", "MIP A350", msn, planned, real]
    return t


class Plan(unittest.TestCase):
    def test_newest_export_wins_and_delivered_aircraft_stay(self):
        """801 was delivered before the second export, which no longer lists it: it stays. 803 was still to be delivered when
        it left the export: it has left the plan. 802 takes the row of the newest export."""
        first = rows(("801", "2026-01-10", "2026-01-12"), ("802", "2026-03-01", ""), ("803", "2026-06-01", ""))
        second = rows(("802", "2026-03-01", "2026-03-04"), ("804", "2026-07-01", ""))
        t = downloads.merge_plan([("2026-03-15", second), ("2026-01-20", first)]).set_index("msn")
        self.assertEqual(sorted(t.index), ["801", "802", "804"])
        self.assertEqual(t.loc["802", "reel_depart_ota"], "2026-03-04")
        self.assertEqual(t.loc["801", "reel_depart_ota"], "2026-01-12")

    def test_a_planned_delivery_in_the_past_counts_as_delivered(self):
        first = rows(("801", "2026-01-10", ""))
        t = downloads.merge_plan([("2026-01-05", first), ("2026-02-01", rows(("802", "2026-05-01", "")))])
        self.assertEqual(sorted(t.msn), ["801", "802"])

    def test_no_export(self):
        self.assertEqual(list(downloads.merge_plan([]).columns), downloads.PLAN_COLUMNS)

    @unittest.skipUnless(len(EXPORTS) >= 2, "needs the exports of 06_input_data")
    def test_the_laptop_exports_give_the_table(self):
        table = config.table(downloads.PLAN_TABLE)[downloads.PLAN_COLUMNS]
        layers = [(downloads.file_day(f), downloads.plan_of_export(f, EXPORTS[:i])) for i, f in enumerate(EXPORTS)]
        got = downloads.merge_plan(layers)
        self.assertEqual(got.shape, table.shape)
        self.assertTrue((got.values == table.values).all(), "the exports no longer give config/%s" % downloads.PLAN_TABLE)
        # with the table read as one more export, nothing changes
        again = downloads.merge_plan(layers + [(max(table.export_du), table)])
        self.assertEqual(sorted(map(tuple, again.values)), sorted(map(tuple, table.values)))

    def test_not_an_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "Avances_Retards_2026-11-03.csv")
            with open(path, "w", encoding="utf-8") as f:
                f.write("a,b,c\n1,2,3\n")
            with self.assertRaises(config.ConfigError) as e:
                downloads.plan_of_export(path)
            self.assertIn("is it an export of the Tableau Avances / Retards?", str(e.exception))


class Cables(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(TRACKER), "needs the tracker of 06_input_data")
    def test_the_laptop_export_gives_the_table(self):
        table = config.table(downloads.CABLE_TABLE)[downloads.CABLE_COLUMNS]
        got = downloads.cables_of_export(TRACKER)
        self.assertEqual(got.shape, table.shape)
        self.assertTrue((got.values == table.values).all(), "the tracker no longer gives config/%s" % downloads.CABLE_TABLE)

    def test_not_a_tracker(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "suivi_cables.csv")
            with open(path, "w", encoding="utf-8") as f:
                f.write("NC;Semaine\n1;S02\n")
            with self.assertRaises(config.ConfigError) as e:
                downloads.cables_of_export(path)
            self.assertIn("is it an export of the cable team's tracker?", str(e.exception))


class Files(unittest.TestCase):
    def test_the_day_of_a_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            named, plain = os.path.join(tmp, "Avances_Retards_2026-11-03.csv"), os.path.join(tmp, "Avances_Retards.csv")
            for p in (named, plain):
                open(p, "w").close()
            noon = time.mktime((2026, 9, 22, 12, 0, 0, 0, 0, -1))   # saved on 22 September 2026
            os.utime(plain, (noon, noon))
            self.assertEqual(downloads.file_day(named), "2026-11-03")
            self.assertEqual(downloads.file_day(plain), "2026-09-22")

    def test_files_of_a_setting_oldest_first(self):
        """The line exports_plan of 2_sources.csv names the files, with * for any text; without the line, no file."""
        tmp, here, kept = tempfile.mkdtemp(), os.getcwd(), dict(config._PARAMS)
        try:
            os.makedirs(os.path.join(tmp, "data"))
            for name in ("Avances_Retards_2026-11-03.csv", "Avances_Retards_2026-10-07.csv", "autre.csv"):
                open(os.path.join(tmp, "data", name), "w").close()
            os.chdir(tmp)
            config._PARAMS[downloads.SOURCES] = {"exports_plan": "data/Avances_Retards*.csv"}
            self.assertEqual([os.path.basename(f) for f in downloads.files("exports_plan")], ["Avances_Retards_2026-10-07.csv", "Avances_Retards_2026-11-03.csv"])
            self.assertEqual(downloads.files("suivi_cables"), [])
        finally:
            os.chdir(here)
            config._PARAMS.clear()
            config._PARAMS.update(kept)
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

"""The settings kept in Fusion (fto2/fusion.py): each sheet of the settings spreadsheet, read as a sync would give it, must
give back the same settings as the files; a sheet that cannot be used leaves its file."""
import os
import re
import shutil
import unittest

import pandas as pd

from fto2 import config, fusion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET = os.path.join(ROOT, "03_reports", "skywise", "fusion", "FTO2 NC Dashboard - Settings.xlsx")


class FakeDataset:
    tables = {}

    def __init__(self, name):
        self.name = name

    @classmethod
    def get(cls, name):
        return cls(name)

    def read_table(self, format="pandas"):
        if self.name not in self.tables:
            raise KeyError("AliasNotDefined: %s" % self.name)
        return self.tables[self.name].copy()


@unittest.skipUnless(os.path.exists(SHEET), "the settings spreadsheet is written by build/fusion_sheet.py")
class TestFusion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        readme = pd.read_excel(SHEET, sheet_name="Read me", header=3)
        cls.sheets = {d: pd.read_excel(SHEET, sheet_name=s) for d, s in zip(readme["Dataset"], readme["Sheet"])}

    def setUp(self):
        self.env = {k: os.environ.get(k) for k in ("FTO2_CONFIG", "FTO2_FUSION_FROM")}
        os.environ["FTO2_CONFIG"] = os.path.join(ROOT, "config")
        os.environ.pop("FTO2_FUSION_FROM", None)
        config._PARAMS.clear()

    def tearDown(self):
        work = os.environ.get("FTO2_CONFIG")
        if work and os.path.basename(work).startswith("fto2_settings_"):
            shutil.rmtree(work, ignore_errors=True)
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        config._PARAMS.clear()

    def tables(self):
        return {t: config.table(t) for t in ["1_reglages_pages.csv", "1_cout_parametres.csv", "1_calendrier_production.csv",
                                              "0_livraisons_2025.csv", "1_prix_pieces.csv", "2_parametres.csv"]}

    def test_the_sheets_give_the_same_settings(self):
        before = self.tables()
        FakeDataset.tables = dict(self.sheets)
        used = fusion.load(FakeDataset, say=lambda m: None)
        self.assertIn("fto2_set_cost", used)
        self.assertNotIn("fto2_set_gps", used)   # header only: the file is kept
        for name, t in self.tables().items():
            pd.testing.assert_frame_equal(t, before[name], obj=name)

    def test_no_dataset_keeps_the_files(self):
        FakeDataset.tables = {}
        self.assertEqual(fusion.load(FakeDataset, say=lambda m: None), {})
        self.assertEqual(config.parameter("usine"), "FTO2")

    def test_a_missing_column_keeps_the_file(self):
        FakeDataset.tables = {"fto2_set_cost": self.sheets["fto2_set_cost"].iloc[:, :1]}
        said = []
        fusion.load(FakeDataset, say=said.append)
        self.assertNotIn("fto2_set_cost", fusion.USED)
        self.assertTrue(any("fto2_set_cost not used" in m for m in said))

    def test_column_names_written_differently(self):
        t = self.sheets["fto2_set_plant"].copy()
        t.columns = [c.upper() for c in t.columns]
        t.loc[t.iloc[:, 0] == "usine", t.columns[1]] = "FTO9"
        FakeDataset.tables = {"fto2_set_plant": t}
        fusion.load(FakeDataset, say=lambda m: None)
        self.assertEqual(config.parameter("usine"), "FTO9")

    def test_a_list_pasted_from_its_header(self):
        from fto2 import manual_lists
        cols = {"N_NC_AM_AF": [12345678.0, None], "Date_SAP": [pd.Timestamp(config.year(), 3, 5), None]}
        for c in manual_lists.GPS_LIST_COLUMNS:   # as a sync may write them: signs and accented letters replaced
            cols[re.sub(r"[^0-9A-Za-z]", "_", c)] = ["x", None]
        FakeDataset.tables = {"fto2_set_gps": pd.DataFrame(cols)}
        fusion.load(FakeDataset, say=lambda m: None)
        self.assertEqual(manual_lists._src("liste_gps_lignes_avant_entete"), "0")
        self.assertIn("12345678", manual_lists._ids(manual_lists._src("liste_gps"), manual_lists._src("liste_gps_colonne_numero"),
                                                    manual_lists._src("liste_gps_colonne_date"), 0, config.year()))
        ext = manual_lists.external_table()
        self.assertEqual(ext.loc[ext.notification_number == "12345678", "GPS_Type_NC"].tolist(), ["x"])

    def test_a_list_missing_a_column_keeps_the_file(self):
        FakeDataset.tables = {"fto2_set_gps": pd.DataFrame({"N° NC / AM / AF": [1.0], "Date SAP": ["05/03/2026"]})}
        said = []
        fusion.load(FakeDataset, say=said.append)
        self.assertNotIn("fto2_set_gps", fusion.USED)
        self.assertTrue(any("fto2_set_gps not used, column(s) missing: Produit" in m for m in said))


if __name__ == "__main__":
    unittest.main()

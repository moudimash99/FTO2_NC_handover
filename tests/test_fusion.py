"""The settings kept in Fusion (fto2/fusion.py): each sheet of the settings spreadsheet, read as a sync would give it, must
give back the same settings as the files; a sheet that cannot be used leaves its file.

The lists and the production plan are pasted whole, as they are: title rows above the header, blank header cells, columns
the run does not read, empty rows. A sync names the columns after the sheet's first row (pasted() below): the run finds the
header row itself and gives the same lists, cable requests and plan as the files; a sheet whose header is not found is
said loudly and the previous table is kept."""
import csv
import datetime as dt
import io
import os
import re
import shutil
import unittest

import pandas as pd

from fto2 import config, downloads, fusion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET = os.path.join(ROOT, "03_reports", "skywise", "fusion", "FTO2 NC Dashboard - Settings.xlsx")
TRACKER = os.path.join(ROOT, "06_input_data", "cable_team_tracker_A30_NC_cables.csv")
EXPORT = os.path.join(ROOT, "06_input_data", "Avances_Retards_2026-11-03.csv")
GPS_HEADER = ["N°  NC / AM / AF", " Date SAP", "Produit", "Nombre total retouches", "Non conformité constatée", "Type NC",
              "Statut décision", "IMPUTATION \n(après analyse)", "Nombre de retouches majeures", "Nombre de retouches mineures"]


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


def pasted(rows):
    """A sheet pasted as it is, as a Fusion sync gives it: its first row as the column names (a blank cell gets a name of
    its own), the other rows as data, every cell as text."""
    n = max(len(r) for r in rows)
    rows = [list(r) + [""] * (n - len(r)) for r in rows]
    return pd.DataFrame(rows[1:], columns=[c if c.strip() else "Column %d" % (i + 1) for i, c in enumerate(rows[0])])


def csv_rows(path):
    return list(csv.reader(io.StringIO(downloads._text(path), newline="")))


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

    def load(self, **tables):
        FakeDataset.tables = tables
        said = []
        fusion.load(FakeDataset, say=said.append)
        return said

    def tables(self):
        return {t: config.table(t) for t in ["1_reglages_pages.csv", "1_cout_parametres.csv", "1_calendrier_production.csv",
                                              "0_livraisons_2025.csv", "1_prix_pieces.csv", "2_parametres.csv"]}

    def test_the_sheets_give_the_same_settings(self):
        before = self.tables()
        said = self.load(**self.sheets)
        self.assertIn("fto2_set_cost", fusion.USED)
        # only the note: nothing pasted yet, the previous table is kept, and the run says so; the template has no sheet for the
        # production plan any more (its exports are CSV files kept with the code, 18 Nov), and its absence is not said
        for name in [n for n in fusion.PASTED if n != fusion.PLAN]:
            self.assertNotIn(name, fusion.USED)
            self.assertTrue(any(m.startswith("⚠️ Fusion sheet %s NOT USED: empty" % fusion.PASTED[name]) for m in said), said)
        self.assertFalse(any("Production plan" in m for m in said), said)
        self.assertEqual(len(fusion.ALERTS), 3)
        for name, t in self.tables().items():
            pd.testing.assert_frame_equal(t, before[name], obj=name)

    def test_no_dataset_keeps_the_files(self):
        said = self.load()
        self.assertEqual(fusion.USED, {})
        self.assertEqual(fusion.ALERTS, [])
        self.assertEqual(config.parameter("usine"), "FTO2")
        self.assertIn("Fusion sheet GPS register: not given to the run", "\n".join(said))

    def test_a_missing_column_keeps_the_file(self):
        said = self.load(fto2_set_cost=self.sheets["fto2_set_cost"].iloc[:, :1])
        self.assertNotIn("fto2_set_cost", fusion.USED)
        self.assertTrue(any("fto2_set_cost not used" in m for m in said))

    def test_column_names_written_differently(self):
        t = self.sheets["fto2_set_cost"].copy()
        t.columns = [c.upper() for c in t.columns]
        t.loc[t.iloc[:, 0] == "taux_qualite", t.columns[1]] = 99
        self.load(fto2_set_cost=t)
        self.assertEqual(config.table("1_cout_parametres.csv").set_index("nom").valeur["taux_qualite"], "99")

    # ------------------------------------------------------------ the sheets pasted whole
    def gps_ids(self):
        from fto2 import manual_lists
        return manual_lists._ids(manual_lists._src("liste_gps"), manual_lists._src("liste_gps_colonne_numero"),
                                 manual_lists._src("liste_gps_colonne_date"), 0, config.year())

    def test_a_list_pasted_from_its_header(self):
        """The sheet's first row is the header: the sync's column names are the header's (signs replaced, dates typed)."""
        from fto2 import manual_lists
        cols = {"N_NC_AM_AF": [12345678.0, None], "Date_SAP": [pd.Timestamp(config.year(), 3, 5), None]}
        for c in manual_lists.GPS_LIST_COLUMNS:   # as a sync may write them: signs and accented letters replaced
            cols[re.sub(r"[^0-9A-Za-z]", "_", c)] = ["x", None]
        said = self.load(fto2_set_gps=pd.DataFrame(cols))
        self.assertIn("Fusion sheet GPS register: header on row 1, 1 rows", said)
        self.assertEqual(manual_lists._src("liste_gps_lignes_avant_entete"), "0")
        self.assertIn("12345678", self.gps_ids())
        ext = manual_lists.external_table()
        self.assertEqual(ext.loc[ext.notification_number == "12345678", "GPS_Type_NC"].tolist(), ["x"])

    def test_title_rows_blank_header_cells_and_extra_columns(self):
        """The whole Google sheet: a title and a date above the header, a column the run does not read, a header cell left
        blank, an empty row, a date written 2026-03-05."""
        from fto2 import manual_lists
        y = config.year()
        header = GPS_HEADER[:2] + ["Commentaire", ""] + GPS_HEADER[2:]
        row = lambda nc, day, kind: [nc, day, "à revoir", "42", "PTVU", "2", "Câble abîmé", kind, "Acceptée", "FTO2", "1", "1"]
        said = self.load(fto2_set_gps=pasted([
            ["GPS NC INT SERIE ELEC %d - NC REGISTRE" % y], [], ["Mise à jour le 05/03/%d" % y], header,
            row("12345678", "%d-03-05" % y, "Câblage"), [], row("12345679", "06/03/%d" % y, "Montage")]))
        self.assertIn("Fusion sheet GPS register: header on row 4, 2 rows", said)
        self.assertEqual(fusion.ALERTS, [])
        self.assertEqual({"12345678", "12345679"} & self.gps_ids(), {"12345678", "12345679"})
        ext = manual_lists.external_table().set_index("notification_number")
        self.assertEqual(ext.loc["12345679", ["GPS_Type_NC", "GPS_Imputation", "Ext_Produit"]].tolist(), ["Montage", "FTO2", "PTVU"])

    def test_the_note_row_is_passed_over(self):
        """Pasted under the template's note (A2): the note is the first row, then the sheet with its two title rows."""
        from fto2 import manual_lists
        note = self.sheets["fto2_set_test"].columns[0]
        self.assertTrue(note.startswith("Collez ici"))
        y = config.year()
        said = self.load(fto2_set_test=pasted([
            [note], ["NC TEST"], ["x"], ["N° NC", "Dates", "Produit", "VU\nuniquement PTVU", "Nb défaut", "Défaut majeur"],
            ["22334455", "15/03/%d" % y, "PTVU", "", "3", "Câble court"]]))
        self.assertIn("Fusion sheet Test list: header on row 4, 1 rows", said)
        ext = manual_lists.external_table().set_index("notification_number")
        self.assertEqual(ext.loc["22334455", ["Ext_Source", "Ext_Defaut_Constate"]].tolist(), ["Test", "Câble court"])

    @unittest.skipUnless(os.path.exists(TRACKER), "needs the tracker of 06_input_data")
    def test_the_cable_tracker_pasted_as_it_is(self):
        """The tracker with a title row and an empty row above its header gives the same requests as its export."""
        said = self.load(fto2_set_cables=pasted([["Suivi des demandes de câbles A30"], []] + csv_rows(TRACKER)))
        self.assertTrue(any(m.startswith("Fusion sheet Cable tracker: header on row 3, ") for m in said), said)
        got, want = downloads.cables(), downloads.cables_of_export(TRACKER)
        self.assertEqual(got.shape, want.shape)
        self.assertTrue((got.values == want.values).all())
        self.assertEqual(downloads.report()[1], "cable requests: from the Fusion sheet Cable tracker")

    @unittest.skipUnless(os.path.exists(TRACKER), "needs the tracker of 06_input_data")
    def test_a_header_not_found_keeps_the_previous_table(self):
        """A column renamed in the tracker: the sheet is not used, the run says which column it lacks and what it keeps, at
        the start and again at the end (ALERTS); the cable requests stay those of the table."""
        rows = [["Suivi des demandes de câbles A30"]] + csv_rows(TRACKER)
        rows[1] = ["État" if c == "Statut" else c for c in rows[1]]
        said = self.load(fto2_set_cables=pasted(rows))
        self.assertNotIn("fto2_set_cables", fusion.USED)
        self.assertEqual(len(fusion.ALERTS), 1)
        alert = fusion.ALERTS[0]
        self.assertIn(alert, said)
        for part in ("⚠️ Fusion sheet Cable tracker NOT USED", "the closest, row 2, lacks the column(s) Statut",
                     "The previous cable requests are kept: the table 0_demandes_cables.csv"):
            self.assertIn(part, alert)
        self.assertEqual(config.parameter("suivi_cables", downloads.SOURCES), "data/*cables*.csv")
        self.assertTrue((downloads.cables().values == config.table(downloads.CABLE_TABLE).values).all())
        # a sheet that holds nothing like the header
        self.load(fto2_set_cables=pasted([["Bonjour"], ["a", "b"], ["1", "2"]]))
        self.assertIn("none of its first 3 rows holds the columns NC, Date de création de la NC", fusion.ALERTS[0])

    # ------------------------------------------------------------ the production plan
    def table(self):
        return config.table(downloads.PLAN_TABLE)[downloads.PLAN_COLUMNS]

    @unittest.skipUnless(os.path.exists(EXPORT), "needs the exports of 06_input_data")
    def test_the_plan_pasted_with_its_date(self):
        """The export pasted one column to the right, under a title that gives its date: the plan is the one the exports
        saved in data/ give (the table of config/), and an MSN '#N/A' is repaired from the table."""
        table = self.table()
        said = self.load(fto2_set_plan=pasted([["", "Tableau Avances / Retards au 03/11/2026"]] + [[""] + r for r in csv_rows(EXPORT)]))
        line = [m for m in said if m.startswith("Fusion sheet Production plan")]
        self.assertEqual(len(line), 1)
        self.assertRegex(line[0], r"^Fusion sheet Production plan: header on row 7, \d+ aircraft and products, export of 03/11/2026 "
                                  r"\(the date written above its header\)$")
        got = downloads.plan()
        self.assertEqual(got.shape, table.shape)
        self.assertTrue((got.values == table.values).all())
        self.assertIn("the Fusion sheet Production plan (export of 2026-11-03)", downloads.report()[0])

    @unittest.skipUnless(os.path.exists(EXPORT), "needs the exports of 06_input_data")
    def test_the_plan_without_a_date_takes_the_day_of_the_run(self):
        rows = csv_rows(EXPORT)
        head = next(i for i, r in enumerate(rows) if r[:3] == ["S/HS", "Prog", "Produit"])
        said = self.load(fto2_set_plan=pasted(rows[head:]))   # pasted from its header row
        today = dt.date.today()
        self.assertIn("header on row 1", fusion.USED["fto2_set_plan"])
        self.assertIn("export of %s (no date in the sheet: the day of the run)" % today.strftime("%d/%m/%Y"), "\n".join(said))
        self.assertEqual(max(downloads.plan().export_du), today.isoformat())

    def test_a_plan_sheet_that_is_not_the_export(self):
        said = self.load(fto2_set_plan=pasted([["Plan"], ["S/HS", "Produit", "Prog", "MSN"], ["Serie", "MIP", "A350", "809"]]))
        self.assertNotIn("fto2_set_plan", fusion.USED)
        self.assertIn("⚠️ Fusion sheet Production plan NOT USED: its header row was not found", fusion.ALERTS[0])
        self.assertIn("The plan stays as last read: the table 0_plan_msn.csv.", fusion.ALERTS[0])
        self.assertIn(fusion.ALERTS[0], said)
        self.assertEqual(downloads.plan_exports(), [])
        # the right header, but no aircraft under it
        self.load(fto2_set_plan=pasted([["S/HS", "Prog", "Produit", "MSN", "Rank"], ["Serie", "A350", "MIP", "809", "767"]]))
        self.assertIn("no aircraft under its header row (row 1)", fusion.ALERTS[0])


if __name__ == "__main__":
    unittest.main()

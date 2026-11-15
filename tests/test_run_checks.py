"""The check at the start of the run (fto2/skywise.py, check_settings): a typing mistake in one of the tables a person
edits, or a file in data/ that is not the expected download, stops the run before anything is fetched or written, with a
message that names the table, the line and what to write.

    python3 -m unittest discover -s tests -t .
"""
import os
import shutil
import tempfile
import unittest

from fto2 import config, downloads, skywise


class Mistakes(unittest.TestCase):
    def setUp(self):
        self.folder = os.path.join(tempfile.mkdtemp(prefix="fto2_checks_"), "config")
        shutil.copytree(config.folder(), self.folder)
        self.before, self.cache, self.here = os.environ.get("FTO2_CONFIG"), dict(config._PARAMS), os.getcwd()
        os.environ["FTO2_CONFIG"] = self.folder
        os.chdir(os.path.dirname(self.folder))   # no data/ here: no download is read
        config._PARAMS.clear()
        downloads._PLAN.clear()

    def tearDown(self):
        os.chdir(self.here)
        if self.before is None:
            del os.environ["FTO2_CONFIG"]
        else:
            os.environ["FTO2_CONFIG"] = self.before
        config._PARAMS.clear()
        config._PARAMS.update(self.cache)
        downloads._PLAN.clear()
        shutil.rmtree(os.path.dirname(self.folder), ignore_errors=True)

    def change(self, table, old, new):
        path = os.path.join(self.folder, table)
        with open(path, encoding="utf-8-sig") as f:
            text = f.read()
        self.assertIn(old, text)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(old, new, 1))

    def stops_with(self, message):
        with self.assertRaises(config.ConfigError) as e:
            skywise.check_settings()
        self.assertIn(message, str(e.exception))

    def test_the_settings_as_they_are_pass(self):
        skywise.check_settings()

    def test_the_target(self):
        self.change("1_reglages_pages.csv", "objectif_baisse;0.25", "objectif_baisse;un quart")
        self.stops_with("1_reglages_pages.csv, objectif_baisse: 'un quart' is not a number")

    def test_the_opening_view(self):
        self.change("1_reglages_pages.csv", "defaut_periode;ytd", "defaut_periode;3 mois")
        self.stops_with("1_reglages_pages.csv, defaut_periode: '3 mois' is not one of ytd, m1, m3, m6, m12, all")

    def test_the_year(self):
        self.change("1_parametres.csv", "annee;2026", "annee;26")
        self.stops_with("1_parametres.csv, annee: '26' is not a year")

    def test_a_shutdown_date(self):
        self.change("1_calendrier_production.csv", "2026-05-15;2026-05-15", "15 mai;2026-05-15")
        self.stops_with("1_calendrier_production.csv line 3, debut: '15 mai' is not a date")

    def test_two_actions_with_one_id(self):
        self.change("1_actions_mft.csv", "trk-a330-2;", "trk-a330-1;")
        self.stops_with("1_actions_mft.csv line 3: the id 'trk-a330-1' is already used by an action above")

    def test_an_action_with_an_unknown_kind_of_problem(self):
        self.change("1_actions_mft.csv", ";rca;", ";racine;")
        self.stops_with("niveau 'racine' is not one of cat")

    def test_a_price_that_is_not_a_number(self):
        with open(os.path.join(self.folder, "1_prix_pieces.csv"), "w", encoding="utf-8") as f:
            f.write("materiel;designation;prix_unitaire_eur\nABC-1;relais;dix euros\n")
        self.stops_with("is not a price (line 2)")

    def test_a_file_that_is_not_the_export(self):
        os.makedirs("data")
        with open(os.path.join("data", "Avances_Retards_2026-12-01.csv"), "w", encoding="utf-8") as f:
            f.write("ceci,n'est,pas\nl'export,du,plan\n")
        self.stops_with("Avances_Retards_2026-12-01.csv: the header line 'S/HS, Prog, Produit' was not found")


if __name__ == "__main__":
    unittest.main()

"""Checks that keep the settings in one place.

  - every table of config/ is listed in config/lisez_moi.csv, and every table listed there exists;
  - every table of config/ is read by the code (a table nobody reads would mislead whoever edits it);
  - the backend code holds no business value that belongs in config/ (rates, plant codes, the year, target cut...);
  - the year followed is one line of config/1_parametres.csv, and the dates tied to it follow;
  - a settings folder made before the tables were regrouped (former names, no 1_ part) is still read.

    python3 -m unittest discover -s tests -t .
"""
import glob
import os
import re
import unittest

from fto2 import config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = [p for p in glob.glob(os.path.join(ROOT, "fto2", "**", "*.py"), recursive=True)] + \
       [os.path.join(ROOT, "build", "build_all.py"), os.path.join(ROOT, "07_scripts", "mft", "build_mft.py"),
        os.path.join(ROOT, "07_scripts", "mft", "build_mft_slate.py")]
# values that live in config/ and must not be typed again in the backend code (the parser's text rules excepted)
BUSINESS_VALUES = [r'"FTO2"', r"'FTO2'", r'"FT02"', r"'FT02'", r"\b123\.0?\b", r"\b78\.16\b",
                   r"\b107\.0?\b", r"\b76\.0\b", r"\b0\.75\b",
                   r"\b20[2-9]\d\b"]   # a year: the code takes it from config.year() / config.comparison_year()
# lines that may name a year: an example in a message, the fixed date of the files inside the installation zip
YEAR_ALLOWED = ["is not a date (write it as", "is not a year (write it with four digits", "the file name must end with its date",
                '"createdAt"']
ALLOWED = {os.path.join(ROOT, "fto2", "parser", "nc_defect_parser.py")}   # expert text-reading rules, listed in the index


def _code(path):
    """The code of a file without its comments and docstrings (they may quote values)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r'"""[\s\S]*?"""', "", text)
    return "\n".join(line.split("#")[0] for line in text.splitlines())


class Index(unittest.TestCase):
    def test_every_table_is_in_the_index(self):
        listed = set(config.table("lisez_moi.csv", ["fichier", "niveau", "ce_que_ca_change", "qui_modifie"]).fichier)
        tables = {os.path.basename(p) for p in glob.glob(os.path.join(config.folder(), "*.csv"))} - {"lisez_moi.csv"}
        self.assertEqual(sorted(tables - listed), [], "tables missing from config/lisez_moi.csv")
        self.assertEqual(sorted(t for t in listed - tables if not t.startswith("(")), [], "lisez_moi.csv lists tables that do not exist")

    def test_level_in_the_name(self):
        for p in glob.glob(os.path.join(config.folder(), "*.csv")):
            name = os.path.basename(p)
            if name != "lisez_moi.csv":
                self.assertRegex(name, r"^[0123]_", "%s: the name must start with its group 0_, 1_, 2_ or 3_" % name)

    def test_every_table_is_read(self):
        code = ""
        for p in CODE:
            with open(p, encoding="utf-8") as f:
                code += f.read()
        for p in glob.glob(os.path.join(config.folder(), "*.csv")):
            name = os.path.basename(p)
            if name != "lisez_moi.csv":
                by_year = re.sub(r"_(19|20)\d\d(?=[_.])", "_%d", name)   # a year's table is read by a name made from the year
                self.assertTrue(name in code or by_year in code, "%s is not read by the code" % name)


class NoValuesInCode(unittest.TestCase):
    def test_no_business_value_in_the_backend(self):
        found = []
        for path in CODE:
            if path in ALLOWED:
                continue
            text = _code(path)
            lines = text.splitlines()
            for pat in BUSINESS_VALUES:
                for m in re.finditer(pat, text):
                    line = text[:m.start()].count("\n") + 1
                    if any(a in lines[line - 1] for a in YEAR_ALLOWED):
                        continue
                    found.append("%s:%d %s" % (os.path.relpath(path, ROOT), line, m.group(0)))
        self.assertEqual(found, [], "values that belong in config/ (move them there):\n" + "\n".join(found))


class Year(unittest.TestCase):
    """The year followed: config/1_parametres.csv, annee."""

    def setUp(self):
        config.parameter("usine")   # reads the table once
        self.values = config._PARAMS["2_parametres.csv"]
        self.kept = dict(self.values)

    def tearDown(self):
        self.values.clear()
        self.values.update(self.kept)

    def test_dates_follow_the_year(self):
        self.values.update(annee="2027", annee_comparaison="")
        self.assertEqual((config.year(), config.comparison_year()), (2027, 2026))
        self.assertEqual((config.first_day(), config.year_end(), config.aleas_since()), ("2027-01-01", "2028-01-01", "2026-12-01"))

    def test_comparison_year_can_be_named(self):
        self.values.update(annee="2027", annee_comparaison="2025")
        self.assertEqual(config.comparison_year(), 2025)
        self.values.update(annee_comparaison="2027")
        with self.assertRaises(config.ConfigError) as e:
            config.comparison_year()
        self.assertIn("must be before the year followed", str(e.exception))

    def test_a_wrong_year_says_so(self):
        self.values.update(annee="26")
        with self.assertRaises(config.ConfigError) as e:
            config.year()
        self.assertIn("1_parametres.csv, annee: '26' is not a year", str(e.exception))   # the table that holds the line

    def test_settings_written_before_the_line_existed(self):
        del self.values["annee"]
        self.values["date_debut"] = "2026-01-01"   # the former start date gives the year
        self.assertEqual((config.year(), config.first_day()), (2026, "2026-01-01"))
        self.values["date_debut"] = "01/01/2026"   # as Excel saves it
        self.assertEqual(config.year(), 2026)

    def test_an_empty_year_is_the_current_year(self):
        import datetime as dt
        self.values.update(annee="")
        self.values.pop("date_debut", None)
        self.assertEqual(config.year(), dt.date.today().year)


class FormerNames(unittest.TestCase):
    """A settings folder as it was before the tables were put in groups (November 2026) still works: the tables that moved are
    found under their former names, and the name / value tables hold all their lines in one part."""

    def setUp(self):
        import shutil
        import tempfile
        self.folder, self.year, self.target = tempfile.mkdtemp(prefix="fto2_former_"), config.year(), config.parameter("objectif_baisse", "2_reglages_pages.csv")
        for name in os.listdir(config.folder()):
            shutil.copy(os.path.join(config.folder(), name), self.folder)
        for new, old in (("0_plan_msn.csv", "1_plan_msn.csv"), ("0_livraisons_2025.csv", "1_livraisons_2025.csv"), ("1_cout_parametres.csv", "2_cout_parametres.csv")):
            os.rename(os.path.join(self.folder, new), os.path.join(self.folder, old))
        for whole, part in config.SPLIT.items():   # the manager's lines back in the one table
            with open(os.path.join(self.folder, part), encoding="utf-8-sig") as f:
                lines = f.read().splitlines()[1:]
            with open(os.path.join(self.folder, whole), "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            os.remove(os.path.join(self.folder, part))
        self.before, self.cache = os.environ.get("FTO2_CONFIG"), dict(config._PARAMS)
        os.environ["FTO2_CONFIG"] = self.folder
        config._PARAMS.clear()

    def tearDown(self):
        import shutil
        if self.before is None:
            del os.environ["FTO2_CONFIG"]
        else:
            os.environ["FTO2_CONFIG"] = self.before
        config._PARAMS.clear()
        config._PARAMS.update(self.cache)
        shutil.rmtree(self.folder, ignore_errors=True)

    def test_moved_tables_are_found(self):
        self.assertTrue(config.path("0_plan_msn.csv").endswith("1_plan_msn.csv"))
        self.assertEqual(len(config.table("0_plan_msn.csv")), len(config.table("1_plan_msn.csv")))
        self.assertIn("taux_production", set(config.table("1_cout_parametres.csv").nom))
        self.assertTrue(os.path.exists(config.path("0_livraisons_2025.csv")))

    def test_lines_in_one_part(self):
        self.assertEqual(config.year(), self.year)
        self.assertEqual(config.parameter("objectif_baisse", "2_reglages_pages.csv"), self.target)
        self.assertEqual(config.held_by("annee"), "2_parametres.csv")

    def test_a_line_in_both_parts_says_so(self):
        with open(os.path.join(self.folder, "1_parametres.csv"), "w", encoding="utf-8") as f:
            f.write("nom;valeur;description\nannee;2026;\n")
        config._PARAMS.clear()
        with self.assertRaises(config.ConfigError) as e:
            config.year()
        self.assertIn("the line 'annee' is in both 2_parametres.csv and 1_parametres.csv", str(e.exception))


if __name__ == "__main__":
    unittest.main()


class ExcelHabits(unittest.TestCase):
    """A table saved again from Excel still reads: Windows encoding, dates as JJ/MM/AAAA, decimal commas, empty cells at the end."""

    def test_table_saved_by_excel(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "x.csv"), "wb") as f:
                f.write("nom;valeur;description\r\nété;0,25;\"un texte; avec un point-virgule\"\r\n;;\r\nfin;2;;;\r\n".encode("cp1252"))
            old, os.environ["FTO2_CONFIG"] = os.environ.get("FTO2_CONFIG"), d
            try:
                t = config.table("x.csv", ["nom", "valeur"])
            finally:
                if old is None:
                    del os.environ["FTO2_CONFIG"]
                else:
                    os.environ["FTO2_CONFIG"] = old
        self.assertEqual(list(t.nom), ["été", "fin"])
        self.assertEqual(t.description[0], "un texte; avec un point-virgule")
        self.assertEqual(config.number(t.valeur[0], "x"), 0.25)

    def test_table_saved_with_commas(self):
        """An Excel set to English separates the columns with commas and quotes the cells that hold one."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "x.csv"), "w", encoding="utf-8-sig") as f:
                f.write('nom,valeur,description\nobjectif,"0,25","un texte, avec une virgule"\nannee,2026,\n')
            old, os.environ["FTO2_CONFIG"] = os.environ.get("FTO2_CONFIG"), d
            try:
                t = config.table("x.csv", ["nom", "valeur"])
            finally:
                if old is None:
                    del os.environ["FTO2_CONFIG"]
                else:
                    os.environ["FTO2_CONFIG"] = old
        self.assertEqual(list(t.nom), ["objectif", "annee"])
        self.assertEqual((t.valeur[0], t.description[0]), ("0,25", "un texte, avec une virgule"))

    def test_dates_and_numbers(self):
        self.assertEqual(config.day("31/01/2026", "x"), "2026-01-31")
        self.assertEqual(config.day("2026-01-31", "x"), "2026-01-31")
        self.assertEqual(config.number("1 234,5", "x"), 1234.5)
        with self.assertRaises(config.ConfigError) as e:
            config.day("janvier", "2_parametres.csv, date_debut")
        self.assertIn("2_parametres.csv, date_debut: 'janvier' is not a date", str(e.exception))

"""Checks that keep the settings in one place.

  - every table of config/ is listed in config/lisez_moi.csv, and every table listed there exists;
  - every table of config/ is read by the code (a table nobody reads would mislead whoever edits it);
  - the backend code holds no business value that belongs in config/ (rates, plant codes, start date, target cut...).

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
        os.path.join(ROOT, "07_scripts", "mft", "build_mft_slate.py")] + glob.glob(os.path.join(ROOT, "scripts", "*.py"))
# values that live in config/ and must not be typed again in the backend code (the parser's text rules excepted)
BUSINESS_VALUES = [r'"FTO2"', r"'FTO2'", r'"FT02"', r"'FT02'", r'"2026-01-01"', r"'2026-01-01'", r"\b123\.0?\b", r"\b78\.16\b",
                   r"\b107\.0?\b", r"\b76\.0\b", r"\b0\.75\b"]
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
                self.assertRegex(name, r"^[123]_", "%s: the name must start with its level 1_, 2_ or 3_" % name)

    def test_every_table_is_read(self):
        code = ""
        for p in CODE:
            with open(p, encoding="utf-8") as f:
                code += f.read()
        for p in glob.glob(os.path.join(config.folder(), "*.csv")):
            name = os.path.basename(p)
            if name != "lisez_moi.csv":
                self.assertIn(name, code, "%s is not read by the code" % name)


class NoValuesInCode(unittest.TestCase):
    def test_no_business_value_in_the_backend(self):
        found = []
        for path in CODE:
            if path in ALLOWED:
                continue
            text = _code(path)
            for pat in BUSINESS_VALUES:
                for m in re.finditer(pat, text):
                    line = text[:m.start()].count("\n") + 1
                    found.append("%s:%d %s" % (os.path.relpath(path, ROOT), line, m.group(0)))
        self.assertEqual(found, [], "values that belong in config/ (move them there):\n" + "\n".join(found))


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

    def test_dates_and_numbers(self):
        self.assertEqual(config.day("31/01/2026", "x"), "2026-01-31")
        self.assertEqual(config.day("2026-01-31", "x"), "2026-01-31")
        self.assertEqual(config.number("1 234,5", "x"), 1234.5)
        with self.assertRaises(config.ConfigError) as e:
            config.day("janvier", "2_parametres.csv, date_debut")
        self.assertIn("2_parametres.csv, date_debut: 'janvier' is not a date", str(e.exception))

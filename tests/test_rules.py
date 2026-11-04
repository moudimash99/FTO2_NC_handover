"""Checks for the rule engine and the rule tables in config/.

    python3 -m unittest discover -s tests -t .
"""
import glob
import os
import unittest

import pandas as pd

from fto2 import config, rules, selection

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTO = ["Programme_auto", "Statut_decision_auto", "Origin_auto", "Type_NC_auto", "Produit_auto"]


def table(rows):
    return pd.DataFrame(rows, columns=["ordre", "resultat", "colonne", "test", "valeur"])


class Engine(unittest.TestCase):
    df = pd.DataFrame({"wf": ["REW-REC-1", "RECEPTION", "A-CRE", "", None], "x": ["a", "b", "c", "d", "e"]})

    def test_whole_word_and_contains(self):
        t = table([["1", "REC", "wf", "mot", "REC"], ["2", "REC", "wf", "contient", "-CRE"], ["9", "SERIE", "", "toujours", ""]])
        self.assertEqual(list(rules.apply(self.df, t)), ["REC", "SERIE", "REC", "SERIE", "SERIE"])

    def test_and_within_a_rule_and_first_match(self):
        t = table([["1", "A", "wf", "commence_par", "REW"], ["1", "A", "x", "egal", "b"],   # both needed: no row
                   ["2", "B", "x", "egal", "a|e"], ["9", "C", "", "toujours", ""]])
        self.assertEqual(list(rules.apply(self.df, t)), ["B", "C", "C", "C", "B"])

    def test_extract(self):
        df = pd.DataFrame({"t": ["meuble 740VU x", "rien"]})
        t = table([["1", "{extrait}", "t", "extraire", r"(\d{3,4}V[UB])"], ["9", "Other", "", "toujours", ""]])
        self.assertEqual(list(rules.apply(df, t)), ["740VU", "Other"])

    def test_plain_errors(self):
        t = table([["x", "A", "wf", "commnce_par", "REW"], ["1", "", "nope", "regex", "("]])
        problems = rules.check(t, "2_test.csv", {"wf"})
        text = "\n".join(problems)
        self.assertIn("2_test.csv line 2: 'ordre' must be a number", text)
        self.assertIn("test 'commnce_par' is not one of", text)
        self.assertIn("2_test.csv line 3: the regular expression '(' is not valid", text)
        self.assertIn("no default rule", text)


class NotebookParity(unittest.TestCase):
    """The rule tables give the same columns the Skywise notebook wrote into its exports."""

    def test_exports(self):
        files = sorted(glob.glob(os.path.join(ROOT, "06_input_data", "fto2_dashboard_data*.csv")))
        if not files:
            self.skipTest("no export in 06_input_data")
        x = pd.concat([pd.read_csv(f, low_memory=False, dtype=str) for f in files], ignore_index=True).drop_duplicates("notification_number")
        got = selection.add_columns(x.drop(columns=AUTO))
        for c in AUTO:
            diff = (got[c].fillna("") != x[c].fillna("")).sum()
            self.assertEqual(diff, 0, "%s: %d NCs differ from the notebook" % (c, diff))


class Tables(unittest.TestCase):
    def test_every_rule_table_is_valid(self):
        for path in sorted(glob.glob(os.path.join(config.folder(), "*_regle_*.csv"))):
            config.rule_table(os.path.basename(path))   # raises with a plain message when wrong

    def test_cost_settings_load(self):
        from fto2.cost import params
        self.assertGreater(params.RATE_PROD, 0)
        self.assertIn("RWK", params.RULES)


if __name__ == "__main__":
    unittest.main()

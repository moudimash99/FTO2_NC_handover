"""Checks for the value of the part (fto2/cost/parts.py, config/1_prix_pieces.csv) and the logistics time of the cost model.

    python3 -m unittest discover -s tests -t .
"""
import math
import os
import shutil
import tempfile
import unittest

import pandas as pd

from fto2 import config
from fto2.cost import model, params, parts


class PriceList(unittest.TestCase):
    """The price list, in a copy of the settings folder."""

    def with_list(self, text, encoding="utf-8"):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        if text is not None:
            with open(os.path.join(d, parts.TABLE), "w", encoding=encoding) as f:
                f.write(text)
        old = os.environ.get("FTO2_CONFIG")
        os.environ["FTO2_CONFIG"] = d
        self.addCleanup(lambda: os.environ.pop("FTO2_CONFIG") if old is None else os.environ.__setitem__("FTO2_CONFIG", old))

    def test_price_times_quantity(self):
        self.with_list("materiel;designation;prix_unitaire_eur\nNSA9117-62F;plaque;12,50\n6325018500;switch;1 234,56 €\nE0682-01;connecteur;\n")
        v = parts.part_values(["NSA9117-62F", "000000006325018500", "e0682-01", None, "INCONNU"], [2, None, 1, 1, 1])
        self.assertEqual(v[0], 25.0)                       # price x quantity
        self.assertEqual(v[1], 1234.56)                    # leading zeros ignored, quantity 1 when empty
        self.assertTrue(all(math.isnan(x) for x in v[2:]))   # no price, no material, material not in the list

    def test_an_export_as_it_is(self):
        # other column names, a comma separator, the Excel encoding, extra columns
        self.with_list("Désignation,Material,Unit price,Devise\nRelais,ABC-1,10.5,EUR\n", encoding="cp1252")
        self.assertEqual(parts.part_values(["abc-1"])[0], 10.5)

    def test_no_list(self):
        self.with_list(None)
        self.assertTrue(math.isnan(parts.part_values(["ABC-1"])[0]))

    def test_plain_errors(self):
        self.with_list("materiel;prix_unitaire_eur\nABC-1;dix\n")
        with self.assertRaises(config.ConfigError) as e:
            parts.part_values(["ABC-1"])
        self.assertIn("is not a price (line 2)", str(e.exception))
        self.with_list("code;tarif\nABC-1;10\n")
        with self.assertRaises(config.ConfigError) as e:
            parts.part_values(["ABC-1"])
        self.assertIn("it needs a column for the material number", str(e.exception))


class CostModel(unittest.TestCase):
    """The part value and the logistics minutes in the cost of an NC."""

    def run_model(self, **changes):
        nc = pd.DataFrame({
            "notification_number": ["1", "2", "3", "4"], "statut": ["closed"] * 4, "liability": ["[FTO2]"] * 4,
            "date_creation": ["2026-03-02"] * 4,
            "decision_status": ["REJ", "RWK", "RWK", "REJ"],
            "linked_document": ["[RS_0000123]", "[RS_0000124]", "[RS_0000125]", ""], "work_order": ["9", "9", "9", "9"],
            "order_state": ["used", "used", "used", ""], "order_minutes_setup": [20.0, 20.0, 20.0, 0.0], "order_minutes_work": [60.0, 60.0, 60.0, 0.0],
            "material": ["ABC-1", "", "ABC-1", "ABC-1"], "part_value": [100.0, float("nan"), 100.0, 50.0]})
        defects = pd.DataFrame({"notification_number": ["1", "2", "3"], "seq": [1, 1, 1], "sous_groupe": ["Inversion"] * 3})
        for k, v in changes.items():
            self.addCleanup(setattr, params, k, getattr(params, k))
            setattr(params, k, v)
        out, _ = model.compute_cnq(nc, defects)
        return out.set_index("notification_number")

    def test_logistics_with_an_order_and_a_material(self):
        o = self.run_model(MIN_LOGISTICS=15, LOGISTICS_ONLY_WITH_MATERIAL=True, USE_ORDER_TIME=True)
        self.assertEqual(o.cnq_rule["1"], "REJ_RW")
        self.assertEqual(list(o.cnq_min_logistics), [15.0, 0.0, 15.0, 0.0])   # 2: no material; 4: no rework order
        self.assertEqual(o.cnq_min_setup["1"], 35.0)                          # the order's 20 minutes + 15
        self.assertEqual(o.cnq_min_setup["2"], 20.0)
        self.assertAlmostEqual(o.cnq_cost_setup["1"] - o.cnq_cost_setup["2"], 15 / 60 * params.STEP_RATES["setup"])

    def test_logistics_for_every_order(self):
        o = self.run_model(MIN_LOGISTICS=15, LOGISTICS_ONLY_WITH_MATERIAL=False, USE_ORDER_TIME=True)
        self.assertEqual(list(o.cnq_min_logistics), [15.0, 15.0, 15.0, 0.0])

    def test_part_counts_only_for_the_decisions_that_charge_it(self):
        o = self.run_model(MIN_LOGISTICS=0, USE_ORDER_TIME=True)
        self.assertEqual(o.cnq_cost_part["1"], 100.0)   # rejection with a rework order: the part counts
        self.assertEqual(o.cnq_cost_part["3"], 0.0)     # rework: no part charged, even with a price
        self.assertEqual(o.cnq_cost_part["4"], 50.0)    # rejection
        steps = o.loc["1", ["cnq_cost_admin", "cnq_cost_work", "cnq_cost_engineering", "cnq_cost_material"]].sum()
        self.assertAlmostEqual(o.cnq_cost_total["1"], steps + 100.0)


if __name__ == "__main__":
    unittest.main()

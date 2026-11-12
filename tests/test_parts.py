"""Checks for the part value of rejections, scraps and exchanges (fto2/cost/parts.py, config/1_prix_pieces.csv).

    python3 -m unittest discover -s tests -t .
"""
import math
import os
import tempfile
import unittest

from fto2.cost import parts

TABLE = """reference;prix_unitaire_eur;nc;quantite;note
ABC12345;10;;;a part found in the text
XYZ99999;;216000001;2;tied by hand, price from the reference row
XYZ99999;5,5;;;
AB12;3;;;too short to be searched
"""


class PartValues(unittest.TestCase):
    def run_with(self, table):
        with tempfile.TemporaryDirectory() as d:
            if table is not None:
                with open(os.path.join(d, parts.TABLE), "w", encoding="utf-8") as f:
                    f.write(table)
            old = os.environ.get("FTO2_CONFIG")
            os.environ["FTO2_CONFIG"] = d
            try:
                return parts.part_values(["216000001", "0216000002", "216000003", "216000004"],
                                         ["relais ABC12345 HS", "", "AB12 cassé", "rien"],
                                         ["", "remplacer abc 12345", "", ""])
            finally:
                if old is None:
                    del os.environ["FTO2_CONFIG"]
                else:
                    os.environ["FTO2_CONFIG"] = old

    def test_prices(self):
        v = self.run_with(TABLE)
        self.assertEqual(v[0], 11.0)   # tied by hand: 2 x 5.5, the text search is not used for it
        self.assertEqual(v[1], 10.0)   # found in the text, spaces and case ignored, leading zero of the NC ignored
        self.assertTrue(math.isnan(v[2]))   # a reference too short is not searched
        self.assertTrue(math.isnan(v[3]))

    def test_no_table(self):
        self.assertTrue(all(math.isnan(x) for x in self.run_with(None)))

    def test_bad_price(self):
        with self.assertRaises(Exception) as e:
            self.run_with("reference;prix_unitaire_eur;nc;quantite;note\nABC12345;dix;;;\n")
        self.assertIn("not a number", str(e.exception))


if __name__ == "__main__":
    unittest.main()

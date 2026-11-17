"""Checks that the pages' code carries no data, and that the Skywise pages paste into Slate as they are.

The data and the reference data reach the pages from the backend: in Skywise through the queries (q_fto2_nc, q_fto2_def,
q_fto2_dis, q_fto2_ref), on the laptop through a JSON block written beside the code. Two keys of the Skywise pages' state are
optional (the Fusion sheet's settings, the MFT actions kept for everyone): tests/slate/check_state_keys.js checks them.

    python3 -m unittest discover -s tests -t .
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKYWISE_JS = ["03_reports/skywise/level3_datasets/fto2_level23.js", "03_reports/skywise/mft/fto2_mft.js",
              "03_reports/skywise/elizabeth/fto2_elizabeth.js"] + \
             ["03_reports/skywise/level3_datasets/fonctions/f_fto2_%s.js" % f for f in ("objectifs", "alarmes", "cout")]   # the Slate functions
LONGEST_LITERAL = 2000   # characters: a longer array or object written in the code would be data


def _literals(text):
    """Lengths of the array / object literals that start right after '=' or ':' (a rough but sufficient scan)."""
    out = []
    for m in re.finditer(r"[=:(,]\s*([\[{])", text):
        start, depth, i = m.start(1), 0, m.start(1)
        while i < len(text):
            c = text[i]
            if c in "[{":
                depth += 1
            elif c in "]}":
                depth -= 1
                if depth == 0:
                    break
            elif c in "'\"":   # skip strings
                q, i = c, i + 1
                while i < len(text) and text[i] != q:
                    i += 2 if text[i] == "\\" else 1
            i += 1
        out.append((i - start, text[start:start + 60]))
    return out


class NoDataInTheCode(unittest.TestCase):
    def test_skywise_js(self):
        for rel in SKYWISE_JS:
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                self.skipTest("build the pages first (python3 -I build/build_all.py ...)")
            with open(path, encoding="utf-8") as f:
                text = f.read()
            big = [(n, head) for n, head in _literals(text) if n > LONGEST_LITERAL and re.match(r'[\[{]\s*("|-?\d|\[|\{\s*")', head)]   # JSON-shaped: numbers, quoted keys, nested arrays
            self.assertEqual(big, [], "%s: data written in the code (move it to the backend tables): %s" % (rel, big[:3]))

    def test_states_read_the_reference_query(self):
        for rel in ["03_reports/skywise/level3_datasets/state.json", "03_reports/skywise/mft/state.json",
                    "03_reports/skywise/elizabeth/state.json"]:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                self.assertIn("{{q_fto2_ref}}", f.read(), rel)

    def test_no_double_brace_in_the_pages(self):
        """Slate reads two opening braces as a binding: the pages' JS has none (the Slate functions have only their own,
        checked by test_slate_functions)."""
        for rel in SKYWISE_JS[:3]:
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                self.skipTest("build the pages first (python3 -I build/build_all.py ...)")
            with open(path, encoding="utf-8") as f:
                self.assertNotIn("{{", f.read(), rel)

    def test_optional_keys(self):
        """The two optional keys (reglages: the Fusion sheet's settings; store: the MFT actions kept for everyone) are added by
        hand in Slate (03_reports/skywise/README.md, steps 3 and 4): the states written do not hold them, so a page set up before
        works as it did. Their queries are written beside the pages."""
        for rel in ["03_reports/skywise/level3_datasets/state.json", "03_reports/skywise/mft/state.json",
                    "03_reports/skywise/level3_datasets/fonctions/state_2_fonctions.json",
                    "03_reports/skywise/level3_datasets/fonctions/state_3_fonctions.json"]:
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                self.skipTest("build the pages first (python3 -I build/build_all.py ...)")
            with open(path, encoding="utf-8") as f:
                text = f.read()
            self.assertNotIn("q_fto2_set_targets", text, rel)
            self.assertNotIn("q_fto2_mft_store", text, rel)
        for rel, table in [("03_reports/skywise/level3_datasets/q_fto2_set_targets.sql", "fto2_set_targets"),
                           ("03_reports/skywise/mft/q_fto2_mft_store.sql", "fto2_mft_store")]:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                self.assertIn('"foundry_sync"."%s"' % table, f.read(), rel)


if __name__ == "__main__":
    unittest.main()

"""The NC writer and the dashboard agree: a text written by the tool is read back line by line, with its sub-codes.

    python3 -m unittest tests.test_nc_writer_text

The text is made by the tool's own code (08_tools/nc_writer_slate/nc_writer.js, run with node), then read by the parser
as the tool writes it, and as it comes back from SAP: "###" written "# # #", each paragraph starting with "* ", a space
before the colons, long lines wrapped.
"""
import json
import os
import re
import shutil
import subprocess
import textwrap
import unittest

from fto2.parser import nc_defect_parser as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRITER = os.path.join(ROOT, "08_tools", "nc_writer_slate", "nc_writer.js")

DEFECTS = [
    {"sub": "Q05-001", "qty": 1, "loc": "245LF-A", "objLabel": "Élément électrique", "detail": "",
     "comment": "245LF-A non torquée, à reprendre avant le passage au contrôle final de la baie"},
    {"sub": "Q03-006", "qty": 12, "loc": "3RN1A", "objLabel": "Collier", "detail": "Cheminement", "comment": ""},
    {"sub": "T04", "qty": 1, "loc": "3RN1B", "objLabel": "Inversion de connexion", "detail": "", "comment": ""},
    {"sub": "T07-CDVE", "qty": 2, "loc": "", "objLabel": "Mesure de résistance sur métallisation non conforme",
     "detail": "", "comment": ""},
]
NODE = """
const W = require(process.argv[1]);
const d = JSON.parse(process.argv[2]);
process.stdout.write(W.buildSapText({msn: "2171", produit: "PTVU", detection: "Contrôle Final"},
  "Lors du contrôle final", "nous constatons 4 défauts.", d, "Merci de remettre en conformité", "le 245VU"));
"""


def as_in_sap(text):
    """The tool's text as the NC's long text shows it once in SAP."""
    out = []
    for line in text.replace("###", "# # #").split("\n"):
        line = re.sub(r"\s*([:,])", r" \1", line)
        if line.strip():
            parts = textwrap.wrap(line, 72)
            out += ["* " + parts[0]] + parts[1:]
    return "Task Description :\n" + "\n".join(out) + "\n" + "-- " * 20 + "\n24.09.2026 15:31:24 CET ( X )"


@unittest.skipUnless(shutil.which("node"), "node is needed to run the NC writer's code")
class WriterText(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = subprocess.run(["node", "-e", NODE, WRITER, json.dumps(DEFECTS)], capture_output=True, text=True,
                                  check=True).stdout

    def check(self, text):
        r = P.parse_nc(text)
        d = r["defects"]
        self.assertEqual([x["seq"] for x in d], [1, 2, 3, 4])
        self.assertEqual([x["sub_code"] for x in d], ["Q05-001", "Q03-006", None, "T07-CDVE"])
        self.assertEqual([x["code"] for x in d], ["Q05", "Q03", "T04", "T07"])
        self.assertEqual([x["qty"] for x in d], [1, 12, 1, 2])
        self.assertEqual([x["fin"] for x in d], ["245LF", "3RN1A", "3RN1B", None])
        self.assertEqual([x["souscat_source"] for x in d][:2], ["SOUS-CODE", "SOUS-CODE"])
        self.assertEqual(d[3]["souscat_source"], "SOUS-CODE")
        self.assertTrue(d[3]["cdve"])
        self.assertIn("contrôle final de la baie", d[0]["text"])      # the comment, wrapped in SAP, is kept whole
        for x in d:
            self.assertNotIn("Merci", x["text"])                      # the closing sentence is not a defect
            self.assertNotIn("TOTAL", x["text"])
        self.assertEqual(r["nb_defauts"], 16)
        self.assertIn("TEMPLATE_V1", r["flags"])
        self.assertFalse([f for f in r["flags"] if f.startswith("TOTAL_MISMATCH")])

    def test_as_the_tool_writes_it(self):
        self.assertIn("### DEFAUTS v1", self.text)
        self.check(self.text)

    def test_as_it_comes_back_from_sap(self):
        self.check(as_in_sap(self.text))

    def test_header_lost_in_sap(self):
        self.check(as_in_sap(self.text).replace("# # # DEFAUTS", "DEFAUTS"))


if __name__ == "__main__":
    unittest.main()

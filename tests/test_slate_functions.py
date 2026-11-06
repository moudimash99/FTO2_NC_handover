"""Checks for the dashboard's Slate functions (03_reports/skywise/level3_datasets/fonctions/, written by build/build_all.py).

  - each function file holds only its own bindings and runs as Slate runs it (tests/slate/run_function.js), on the laptop data;
  - it answers null while a query is missing, and an error as {error} instead of failing;
  - f_fto2_objectifs and f_fto2_alarmes answer each request the page sends, by its key;
  - f_fto2_cout gives, for every NC, the same figures as the notebook's table fto2_dash_cout: the two Skywise set-ups agree;
  - the shared calculations (build/templates/model.js) touch no page element.

The whole page in each set-up is checked by the snapshot (tests/slate/make_pages.py, then tests/snapshot/).

    python3 -m unittest discover -s tests -t .
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FN = os.path.join(ROOT, "03_reports", "skywise", "level3_datasets", "fonctions")
RUN = os.path.join(ROOT, "tests", "slate", "run_function.js")
BINDINGS = {"f_fto2_objectifs.js": {"q_fto2_nc", "q_fto2_def", "q_fto2_ref", "v_fto2_filtres"},
            "f_fto2_alarmes.js": {"q_fto2_nc", "q_fto2_def", "q_fto2_ref", "v_fto2_filtres"},
            "f_fto2_cout.js": {"q_fto2_nc", "q_fto2_def", "q_fto2_ref"}}


def _ready():
    return shutil.which("node") and all(os.path.exists(os.path.join(FN, f)) for f in BINDINGS) and \
        os.path.exists(os.path.join(ROOT, "05_outputs", "fto2_dash_cout.csv"))


def _queries():
    sys.path.insert(0, os.path.join(ROOT, "tests", "slate"))
    import make_pages
    return make_pages.queries()


def _run(name, values):
    with tempfile.TemporaryDirectory() as tmp:
        vin, vout = os.path.join(tmp, "values.json"), os.path.join(tmp, "answer.json")
        with open(vin, "w", encoding="utf-8") as f:
            json.dump(values, f, ensure_ascii=False)
        r = subprocess.run(["node", RUN, os.path.join(FN, name), vin, vout], capture_output=True, text=True)
        if r.returncode:
            raise AssertionError("%s did not run: %s" % (name, r.stderr[-800:]))
        with open(vout, encoding="utf-8") as f:
            return json.load(f)["answer"]


def _request(n, k, **gf):
    base = {"from": "2026-01-01", "to": "2026-10-26", "src": "all", "org": "", "fto2": True, "liab": "f", "cost": "fto2",
            "phase": "SERIE", "line": "", "pick": None}
    base.update(gf)
    return {"n": n, "k": k, "f": {"gf": base, "minor": True, "lang": "fr", "pr": ["real", "wd"]}}


class Texts(unittest.TestCase):
    def test_only_their_own_bindings(self):
        for name, allowed in BINDINGS.items():
            path = os.path.join(FN, name)
            if not os.path.exists(path):
                self.skipTest("build first: python3 -I build/build_all.py")
            with open(path, encoding="utf-8") as f:
                found = set(re.findall(r"\{\{\s*([\w.]+)\s*\}\}", f.read()))
            self.assertEqual(found, allowed, name)

    def test_model_draws_nothing(self):
        with open(os.path.join(ROOT, "build", "templates", "model.js"), encoding="utf-8") as f:
            text = f.read()
        for word in ("document", "innerHTML", "getComputedStyle", "localStorage", "addEventListener"):
            self.assertNotIn(word, text, "build/templates/model.js must compute only: it holds " + word)


@unittest.skipUnless(_ready(), "needs node and the build's outputs (python3 -I build/build_all.py)")
class Answers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.Q = _queries()

    def values(self, **extra):
        v = {k: self.Q[k] for k in ("q_fto2_nc", "q_fto2_def", "q_fto2_ref")}
        v.update(extra)
        return v

    def test_null_while_a_query_runs(self):
        for name in BINDINGS:
            v = self.values()
            v["q_fto2_def"] = None
            self.assertIsNone(_run(name, v), name)

    def test_objectifs_answers_each_request(self):
        req = [_request("objectifs", "a"), _request("objectifs", "b", line="A350"), _request("objectifs", "c", phase="REC", cost="all"),
               _request("alarmes", "x")]
        a = _run("f_fto2_objectifs.js", self.values(v_fto2_filtres={"demandes": req}))
        self.assertNotIn("error", a)
        self.assertEqual(sorted(a["results"]), ["a", "b", "c"])   # the alarms' request is not this function's
        for k, o in a["results"].items():
            self.assertTrue(o["nc"]["S2"]["act"], k)
            self.assertIn("lines", o)
        self.assertLess(a["results"]["b"]["nc"]["S2"]["tot"], a["results"]["a"]["nc"]["S2"]["tot"])   # A350 only: fewer NCs

    def test_alarmes_answers_each_request(self):
        req = [_request("alarmes", "a"), _request("alarmes", "b", phase="REC"), _request("objectifs", "x")]
        a = _run("f_fto2_alarmes.js", self.values(v_fto2_filtres=json.dumps({"demandes": req})))   # the variable may come as text
        self.assertNotIn("error", a)
        self.assertEqual(sorted(a["results"]), ["a", "b"])
        for k, o in a["results"].items():
            self.assertIsInstance(o["res"], list, k)
            self.assertLessEqual(o["first"], o["last"] + 1, k)

    def test_no_request_no_result(self):
        a = _run("f_fto2_objectifs.js", self.values(v_fto2_filtres={}))
        self.assertEqual(a, {"results": {}})

    def test_cost_explanation_same_as_the_notebook(self):
        a = _run("f_fto2_cout.js", self.values())
        self.assertNotIn("error", a)
        js = a["results"]["all"]
        t = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_cout.csv"), dtype={"nc": str, "defect_class": str, "defect_class_en": str},
                        keep_default_na=False, na_values=[""])
        nc = pd.read_csv(os.path.join(ROOT, "05_outputs", "fto2_dash_nc.csv"), dtype={"nc": str}, keep_default_na=False)
        liable = dict(zip(nc.nc, pd.to_numeric(nc.on_aec, errors="coerce").fillna(0).astype(int)))
        close = lambda x, y: math.isclose(float(x), float(y), rel_tol=1e-9, abs_tol=1e-9)
        text = lambda v: "" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)
        self.assertEqual(set(js), set(t.nc), "the same NCs")
        bad = []
        for r in t.itertuples():
            o = js[r.nc]
            if r.seq == 0:
                steps = [r.eur_alert, r.eur_writing, r.eur_support, r.eur_setup, r.eur_hands_on, r.eur_recheck]
                ok = all(close(x, y) for x, y in zip(o["eur"], steps)) and close(o["factor"], r.work_factor) and \
                    close(o["adjAll"], r.adjust) and close(o["adj"], r.adjust if liable.get(r.nc) == 1 else 0)
            else:
                line = [x for x in o["lines"] if x[0] == r.seq]
                c = text(r.defect_class)
                ok = len(line) == 1 and close(line[0][1], r.minutes) and close(line[0][2], r.material) and \
                    line[0][3] == (c or "—") and line[0][4] == (text(r.defect_class_en) or c or "—")
            if not ok:
                bad.append("%s line %s" % (r.nc, r.seq))
        self.assertEqual(bad[:10], [], "%d rows differ between f_fto2_cout and fto2_dash_cout" % len(bad))
        self.assertEqual(sum(len(o["lines"]) for o in js.values()), int((t.seq > 0).sum()), "the same defect lines")


if __name__ == "__main__":
    unittest.main()

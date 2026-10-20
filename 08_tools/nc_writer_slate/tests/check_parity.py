# -*- coding: utf-8 -*-
"""
Check that nc_writer.js says exactly what the Streamlit app says:
same codes, products, detections and FIN lists, same defect lines, same SAP text.

    python tests/check_parity.py          (needs node on the PATH)

The Python side is read from reference/app_streamlit.py without running it (no Streamlit needed).
"""
import ast, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = open(os.path.join(ROOT, "reference", "app_streamlit.py"), encoding="utf-8").read()
tree = ast.parse(src)

py, ns = {}, {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name in ("NATURES", "PRODUITS", "DETECTIONS", "FIN_MAPPING", "FIN_GLOBAL_SUGGEST"):
            py[name] = ast.literal_eval(node.value)
    if isinstance(node, ast.FunctionDef) and node.name == "gen_line":
        exec(compile(ast.Module(body=[node], type_ignores=[]), "gen_line", "exec"), ns)
gen_line = ns["gen_line"]


def py_sap_text(h, ctx_combo, ctx_text, lines, act_combo, act_text, total):
    # the review screen of app_streamlit.py, line for line
    sap_text = f"### DEFAUTS v1 | PRODUIT: {h['produit']} | DETECTION: {h['detection'].upper()}\n\n"
    full_context = f"{ctx_combo} {ctx_text}".strip()
    if full_context:
        sap_text += f"{full_context}\n\n"
    for line in lines:
        sap_text += f"{line}\n"
    full_action = f"{act_combo} {act_text}".strip()
    if full_action:
        sap_text += f"\n{full_action}\n"
    return sap_text + f"\n### TOTAL: {total}"


LINE_CASES = [
    [1, "T04", 1, "3RN3B", "Inversion de connexion", "", ""],
    [2, "Q01-003", 3, "300VG131", "Contact", "bornes 4 et 7", "vu au contrôle"],
    [3, "Q11-014", 2, "", "Câble rayé, endommagé", "", "gaine percée"],
    [12, "Q06-001", 1, "Autre zone 1M", "Harnais", "sur-longueur", ""],
]
DEFECTS = [
    {"code": "T04", "sub": "T04", "qty": 1, "loc": "3RN3B", "objLabel": "Inversion de connexion", "detail": "J <-> H", "comment": ""},
    {"code": "Q01", "sub": "Q01-003", "qty": 4, "loc": "300VG131", "objLabel": "Contact", "detail": "", "comment": "CDVE"},
    {"code": "Q03", "sub": "Q03-001", "qty": 1, "loc": "", "objLabel": "Obturateur", "detail": "", "comment": ""},
]
SAP_CASES = [
    [{"produit": "MIP A350", "detection": "Contrôle Final"}, "Lors du contrôle final", "sur le MSN", DEFECTS, "Merci de remettre en conformité", ""],
    [{"produit": "740VU", "detection": "Test"}, "", "", DEFECTS[:1], "", ""],
    [{"produit": "Banc X", "detection": "Audit"}, "", "texte libre", DEFECTS[1:], "", "avant livraison"],
]

js = r"""
const m = require(process.argv[1]);
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
console.log(JSON.stringify({
  data: { NATURES: m.NATURES, PRODUITS: m.PRODUITS, DETECTIONS: m.DETECTIONS, FIN_MAPPING: m.FIN_MAPPING, FIN_GLOBAL_SUGGEST: m.FIN_GLOBAL_SUGGEST },
  lines: input.lines.map(c => m.genLine.apply(null, c)),
  sap: input.sap.map(c => m.buildSapText.apply(null, c)),
}));
"""
out = subprocess.run(["node", "-e", js, os.path.join(ROOT, "nc_writer.js")],
                     input=json.dumps({"lines": LINE_CASES, "sap": SAP_CASES}), capture_output=True, text=True, encoding="utf-8")
if out.returncode:
    sys.exit(out.stderr)
res = json.loads(out.stdout)

fails = 0
def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else "\n     " + detail))
    fails += 0 if ok else 1

for k in py:
    check("data " + k, res["data"][k] == py[k], "JS and Python differ")
print("     %d natures, %d codes, %d with a CDVE variant" % (len(py["NATURES"]), sum(len(n["objects"]) for n in py["NATURES"]),
                                                        sum(1 for n in py["NATURES"] for o in n["objects"] if o["cdve"])))
for c, got in zip(LINE_CASES, res["lines"]):
    want = gen_line(*c)
    check("line " + want, got == want, "JS: " + got)
for c, got in zip(SAP_CASES, res["sap"]):
    h, cc, ct, defs, ac, at = c
    lines = [gen_line(i + 1, d["sub"], d["qty"], d["loc"], d["objLabel"], d["detail"], d["comment"]) for i, d in enumerate(defs)]
    want = py_sap_text(h, cc, ct, lines, ac, at, sum(d["qty"] for d in defs))
    check("SAP text, %s / %s" % (h["produit"], h["detection"]), got == want, "JS:\n" + got + "\n     Python:\n" + want)

for name in ("nc_writer.html", "nc_writer.css", "nc_writer.js"):
    check("no Handlebars braces in " + name, "{{" not in open(os.path.join(ROOT, name), encoding="utf-8").read(),
          "Slate would read them as a template")

print("\n%d check(s) failed" % fails if fails else "\nall checks passed")
sys.exit(1 if fails else 0)

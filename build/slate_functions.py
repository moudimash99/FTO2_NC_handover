"""The dashboard's Slate functions, in 03_reports/skywise/level3_datasets/fonctions/ (written by build/build_all.py).

Three calculations of the dashboard can run in Slate instead of in the page: the targets and forecast (f_fto2_objectifs), the
bell's alarms (f_fto2_alarmes) and the cost explanation (f_fto2_cout). Each function is the page's own code, copied at each
build: the table adapter, the alarm engine (alarms only) and build/templates/model.js, with a short entry that reads the queries
and the variable v_fto2_filtres. Two ways to set them up, to try in Skywise:

    3 functions                        f_fto2_objectifs, f_fto2_alarmes, f_fto2_cout        state_3_fonctions.json
    2 functions + the notebook's table f_fto2_objectifs, f_fto2_alarmes; query q_fto2_cout  state_2_fonctions.json

tests/test_slate_functions.py runs the files as Slate would (bindings replaced by values) and checks their answers against the
page's own figures.
"""
import json
import os
import re

import page_template

ADAPTER = ("/* ===== ADAPTER START ===== */", "/* ===== ADAPTER END ===== */")
ENGINE = ("/* ===== ALARM ENGINE START ===== */", "/* ===== ALARM ENGINE END ===== */")
BINDINGS = {"{{q_fto2_nc}}", "{{q_fto2_def}}", "{{q_fto2_ref}}", "{{v_fto2_filtres}}"}

WHAT = {
    "objectifs": "the targets and the forecast (cumulative NCs and cost, target line by line, forecast to December) for the "
                 "filters the page asks for",
    "alarmes": "the bell's alarms for the filters the page asks for",
    "cout": "the cost explanation of every NC (\"Expliquer le calcul\" on the cost tab): euros of each step, work factor, "
            "adjustment, and each defect line's minutes and material",
}

FUNCTION = """// FTO2 dashboard, Slate function f_fto2_@@NAME@@: @@WHAT@@.
// Paste this whole file into a Slate function named f_fto2_@@NAME@@ (see README.md beside it). It is the dashboard's own code,
// copied by build/build_all.py from build/templates/model.js (the calculations), the table adapter@@ENGINE_NOTE@@; do not edit
// it here: change the template and build again.
var nc = {{q_fto2_nc}}, def = {{q_fto2_def}}, ref = {{q_fto2_ref}}@@FILTRES@@;
if (!nc || !def || !ref) return null;   // a query still running
try {
  return (function () {
@@REF_READER@@
@@ADAPTER@@
    var R = fto2RefBlocks(ref); if (!R || !R.dashboard) return null;
    // what the page sets before its calculations
    var window = { FTO2_PAGE: 'main' };
    var D = fto2FromTables(nc, def, R.dashboard, null);
    var SET = D.settings, EQMIN = SET.msn_minimum;
    window.FTO2_ALARM_P = SET.alarmes; window.FTO2_PLACEHOLDER = SET.placeholder;
    window.FTO2_YEAR = +(SET.annee || String(D.meta.from).slice(0, 4));   // the year followed: the alarm engine's weeks
    var PAGE = 'main', G = { lang: 'fr', minor: true };
    var DM = null, GN = [], GD = [], GALLOC = [];   // the made-up data of the review pages: never in Skywise
    function gCost() { return 0; }
@@ENGINE@@
@@MODEL@@
@@ENTRY@@
  })();
} catch (e) {
  return { error: String((e && e.message) || e) };
}
"""

ENTRY = {
    "objectifs": "    if (typeof filtres === 'string') filtres = filtres ? JSON.parse(filtres) : {};\n"
                 "    return repondre('objectifs', (filtres || {}).demandes);",
    "alarmes": "    if (typeof filtres === 'string') filtres = filtres ? JSON.parse(filtres) : {};\n"
               "    return repondre('alarmes', (filtres || {}).demandes);",
    "cout": "    return { results: { all: cout() } };   // every NC at once: the page reads it whatever its filters",
}

EVENT = """// Slate event of the dashboard's code sandbox (named w_fto2_dashboard): trigger "w_fto2_dashboard.fto2Filtres", action
// "set variable v_fto2_filtres" to the value below. The page fires it when it needs results from f_fto2_objectifs or f_fto2_alarmes.
return {{w_fto2_dashboard.state.filtres}};
"""

COUT_SQL = ('-- FTO2 dashboard: the cost explanation of each NC, worked out by the Skywise notebook (dataset fto2_dash_cout:\n'
            '-- seq 0 the NC, seq 1... its defect lines). Slate query q_fto2_cout, for the set-up with two functions.\n'
            'SELECT\n    %s\nFROM "foundry_sync"."fto2_dash_cout"\nORDER BY nc, seq\n')


def _between(text, marks):
    a, b = text.index(marks[0]), text.index(marks[1]) + len(marks[1])
    return text[a:b]


def _indent(text, pad="    "):
    return "\n".join((pad + line) if line.strip() else "" for line in text.split("\n"))


def texts(ref_reader):
    """{file name: text} of the three functions. ref_reader: the JS that joins the rows of q_fto2_ref (skywise_pack)."""
    page = page_template.read()
    adapter = _between(page, ADAPTER)
    adapter = "\n".join(l for l in adapter.split("\n") if not l.startswith("if (window.DASH && window.DASH.tables)"))
    engine = _between(page, ENGINE)
    model = page_template.model()
    out = {}
    for name in ("objectifs", "alarmes", "cout"):
        t = (FUNCTION.replace("@@NAME@@", name).replace("@@WHAT@@", WHAT[name])
             .replace("@@ENGINE_NOTE@@", " and the alarm engine" if name == "alarmes" else "")
             .replace("@@FILTRES@@", "" if name == "cout" else ", filtres = {{v_fto2_filtres}}")
             .replace("@@REF_READER@@", _indent(ref_reader.rstrip("\n")))
             .replace("@@ADAPTER@@", _indent(adapter))
             .replace("@@ENGINE@@", "  " + engine if name == "alarmes" else "")
             .replace("@@MODEL@@", "  " + model.rstrip("\n").replace("\n", "\n  "))
             .replace("@@ENTRY@@", ENTRY[name]))
        found = set(re.findall(r"\{\{[^}]*\}\}", t))
        if found - BINDINGS or t.count("{{") != len(re.findall(r"\{\{[^}]*\}\}", t)):
            raise SystemExit("f_fto2_%s: a double brace that is not one of its bindings: Slate would read it as one (%s)"
                             % (name, sorted(found - BINDINGS)))
        out["f_fto2_%s.js" % name] = t
    return out


def write(out, ref_reader, nc_state, cout_columns, say=print):
    """Write the functions, the event, the two states, the query of the notebook's table and the README into out.
    nc_state: the sandbox state of levels 2 and 3 (queries), which both states extend."""
    os.makedirs(out, exist_ok=True)
    files = texts(ref_reader)
    for name, t in files.items():
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(t)
    with open(os.path.join(out, "event_fto2Filtres.js"), "w", encoding="utf-8") as f:
        f.write(EVENT)
    three = dict(nc_state, fonctions="objectifs alarmes cout", objectifs="{{f_fto2_objectifs}}", alarmes="{{f_fto2_alarmes}}",
                 cout="{{f_fto2_cout}}", filtres={})
    two = dict(nc_state, fonctions="objectifs alarmes", objectifs="{{f_fto2_objectifs}}", alarmes="{{f_fto2_alarmes}}",
               cout_table="{{q_fto2_cout}}", filtres={})
    for name, st in (("state_3_fonctions.json", three), ("state_2_fonctions.json", two)):
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            json.dump(st, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out, "q_fto2_cout.sql"), "w", encoding="utf-8") as f:
        f.write(COUT_SQL % ",\n    ".join(cout_columns))
    sizes = {k: len(v.encode()) // 1024 for k, v in files.items()}
    say("slate functions:", sizes, "KB")
    return sizes

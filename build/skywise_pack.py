# -*- coding: utf-8 -*-
"""
The dashboard for Skywise (Slate), in four levels, written to 03_reports/skywise/ by build/build_all.py.

    level1_dummy_in_js       CSS, HTML, JS for a Slate code sandbox; fictitious data written in the JS. Visual check only.
    level2_dummy_queries     same CSS and HTML; the JS reads three Slate queries (q_fto2_nc, q_fto2_def, and q_fto2_dis for the
                             disruption block, optional) through the sandbox's state. The queries make fictitious data
                             themselves (no dataset): checks the query -> page path.
    level3_datasets          same JS as level 2; the queries read the datasets fto2_dash_nc, fto2_dash_defects and
                             fto2_dash_disruptions, written by the Skywise notebook with notebook_kit/ (the laptop build's Python).
    level4_import            a Slate app (JSON) with the sandbox and the three queries already set up, for levels 2 and 3.

The fictitious data of levels 1 and 2 is the same: the level-2 queries (build/dummy_tables.py) run once on a local Postgres
give the tables written into the level-1 JS (build/dummy/*.csv).
"""
import json
import os
import re
import shutil
import uuid

import pandas as pd

ADAPTER_RUN = "if (window.DASH && window.DASH.tables) window.DASH = fto2FromTables(window.DASH.tables.nc, window.DASH.tables.def, window.DASH.ref, window.DASH.tables.dis);\n"
EXTRA_CSS = (".fto2 .fto2-err { background: #fdecea; color: #8a1c12; border: 1px solid #f1b0a8; border-radius: 8px; padding: 10px 14px; font-size: 13px; margin: 12px 20px; }\n"
             ".fto2 .fto2-wait { background: #eef4f1; color: #1d6b52; border: 1px solid #b9d5ca; border-radius: 8px; padding: 10px 14px; font-size: 13px; margin: 12px 20px; }\n"
             ".fto2 .fto2-wait.warn { background: #fff5e6; color: #7a4a00; border-color: #f0c98a; }\n")
STATE = {"nc": "{{q_fto2_nc}}", "def": "{{q_fto2_def}}", "dis": "{{q_fto2_dis}}"}

JS_HEAD = """/* @@STAMP@@ */
window.FTO2_EMBED = true;
window.FTO2_PAGE = 'main';
window.FTO2_REF = @@REF@@;
"""
JS_SHOW_ERROR = """  function showError(msg) {
    var e = document.getElementById('fto2-err');
    if (e) { e.hidden = false; e.textContent = 'Le tableau de bord n\\'a pas pu s\\'afficher / The dashboard could not load: ' + msg; }
    var w = document.getElementById('fto2-wait'); if (w) w.hidden = true;
    if (window.console) console.error('[FTO2 dashboard]', msg);
  }
  window.addEventListener('error', function (ev) { showError((ev && ev.message) || 'unknown error'); });
"""
# level 1: the tables are in the JS
JS_L1 = JS_HEAD + """window.FTO2_TABLES = @@TABLES@@;
@@ADAPTER@@
(function () {
""" + JS_SHOW_ERROR + """  function main() {
@@MAIN@@
  }
  function start() {
    if (!document.getElementById('tabs')) { showError('HTML part missing: paste the HTML part into the HTML box.'); return; }
    try { window.DASH = fto2FromTables(window.FTO2_TABLES.nc, window.FTO2_TABLES.def, window.FTO2_REF, window.FTO2_TABLES.dis); main(); }
    catch (err) { showError((err && err.message) || String(err)); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
"""
# levels 2 and 3: the tables come from Slate queries, through the code sandbox's state {"nc": "{{q_fto2_nc}}", "def": "{{q_fto2_def}}",
# "dis": "{{q_fto2_dis}}"}. The third (disruption block) is optional: without it the page starts after a few seconds, without the block.
JS_L23 = JS_HEAD + """@@ADAPTER@@
(function () {
  var MSG = {
    wait: 'Chargement des données Slate… / Loading the Slate data…',
    empty: 'La requête q_fto2_nc n’a renvoyé aucune ligne : vérifiez la requête et son jeu de données. / The q_fto2_nc query returned no row: check the query and its dataset.',
    noapi: 'État Slate introuvable : ce JavaScript doit tourner dans un code sandbox Slate dont l’état contient les deux requêtes (voir state.json). / No Slate state: this JavaScript must run in a Slate code sandbox whose state holds the two queries (see state.json).',
    cut: 'Attention : exactement {n} lignes reçues pour {q} ; Slate a peut-être coupé la requête (limite de lignes). / Exactly {n} rows received for {q}: Slate may have cut the query (row limit).',
    slow: 'Toujours en attente de {q} : vérifiez que la requête existe, porte ce nom et s’exécute sans erreur. / Still waiting for {q}: check that the query exists, has this name and runs without error.'
  };
""" + JS_SHOW_ERROR + """  function status(msg, warn) {
    var e = document.getElementById('fto2-wait');
    if (!e) return;
    e.hidden = !msg; e.textContent = msg || ''; e.className = 'fto2-wait' + (warn ? ' warn' : '');
  }
  function main() {
@@MAIN@@
  }
  var got = {}, started = false, ready = false, disTimer = null;
  function parse(v) {   // a query result arrives as an object of columns; accept JSON text too
    if (typeof v !== 'string') return v;
    var s = v.trim(); if (!s) return null;
    try { return JSON.parse(s); } catch (e) { return null; }
  }
  function count(t) {
    if (!t) return 0;
    if (Array.isArray(t)) return t.length;
    var k = Object.keys(t);
    for (var i = 0; i < k.length; i++) if (t[k[i]] && t[k[i]].length) return t[k[i]].length;
    return 0;
  }
  function loaded(t) { return !!t && (Array.isArray(t) || Object.keys(t).length > 0); }   // a result with its columns, even with no row
  function tables() {
    var nc = parse(got.nc), def = parse(got.def), dis = parse(got.dis), tb = parse(got.tables);
    if (tb) { nc = nc || tb.nc; def = def || tb.def; dis = dis || tb.dis; }
    return [nc, def, typeof dis === 'object' ? dis : null];
  }
  function tryStart() {
    if (started || !ready) return;
    var t = tables(), nc = t[0], def = t[1], dis = t[2], n1 = count(nc), n2 = count(def);
    if (loaded(nc) && !n1) { status(MSG.empty, true); return; }
    if (!n1 || !loaded(def)) { status(MSG.wait); return; }   // both queries are needed: they can arrive one after the other
    if (!loaded(dis) && !disTimer) { disTimer = setTimeout(function () { disTimer = 'over'; tryStart(); }, 4000); return; }   // the block's query: optional
    if (!loaded(dis) && disTimer !== 'over') return;
    started = true;
    try {
      window.DASH = fto2FromTables(nc, def, window.FTO2_REF, loaded(dis) ? dis : null);
      if (!window.DASH.ncs.length) {   // rows arrived but none could be read: say what came, to fix the query or the state
        var c = Array.isArray(nc) ? Object.keys(nc[0] || {}) : Object.keys(nc);
        showError('aucune NC lisible dans q_fto2_nc (colonnes reçues : ' + c.join(', ') + ') / no readable NC in q_fto2_nc (columns received: ' + c.join(', ') + ')');
        return;
      }
      status('');
      main();
      var lim = [1000, 2000, 5000, 10000, 20000, 50000, 100000], warn = [];
      if (lim.indexOf(n1) >= 0) warn.push(MSG.cut.replace('{n}', n1).replace('{q}', 'q_fto2_nc'));
      if (lim.indexOf(n2) >= 0) warn.push(MSG.cut.replace('{n}', n2).replace('{q}', 'q_fto2_def'));
      if (warn.length) status(warn.join(' '), true);
      if (window.console) console.info('[FTO2 dashboard] rows received: NC ' + n1 + ', defect lines ' + n2 + ', aléas ' + (loaded(dis) ? count(dis) : 'none (no q_fto2_dis)'));
    } catch (err) { showError((err && err.message) || String(err)); }
  }
  var api = window.SlateFunctions;
  if (api && typeof api.watch === 'function') ['nc', 'def', 'dis', 'tables'].forEach(function (k) { api.watch(k, function (v) { got[k] = v; tryStart(); }); });
  function boot() {
    ready = true;
    if (!document.getElementById('tabs')) { showError('HTML part missing: paste the HTML part into the HTML box.'); return; }
    if (!(api && typeof api.watch === 'function')) { showError(MSG.noapi); return; }
    status(MSG.wait);
    tryStart();
    setTimeout(function () {
      if (started) return;
      var t = tables(), miss = [];
      if (!count(t[0])) miss.push('q_fto2_nc');
      if (!loaded(t[1])) miss.push('q_fto2_def');
      if (miss.length) status(MSG.slow.replace(/\\{q\\}/g, miss.join(', ')), true);
    }, 20000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
"""
ONE_FILE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@</title>
<!--
  @@STAMP@@
  One file, three parts. It opens as a page as it is. For a Slate code sandbox, copy each part into its box:
    CSS box        = everything between the lines  CSS START  and  CSS END
    HTML box       = everything between the lines  HTML START  and  HTML END
    JavaScript box = everything between the lines  JS START  and  JS END
-->
<style>
/* ===== CSS START ===== */
@@CSS@@/* ===== CSS END ===== */
</style>
</head>
<body style="margin:0">
@@BEFORE@@<!-- ===== HTML START ===== -->
@@HTML@@<!-- ===== HTML END ===== -->
<script>
/* ===== JS START ===== */
@@JS@@/* ===== JS END ===== */
</script>
</body>
</html>
"""
# local preview of levels 2-3 only: a stand-in for Slate's API that hands the two tables over after a moment, as Slate does
FAKE_SLATE = """<script>
/* LOCAL PREVIEW ONLY - not for Slate. Stands in for Slate's SlateFunctions: the state starts empty, then the two query
   results arrive (one array per column, as Slate returns them). In Slate, this block does not exist. */
window.SlateFunctions = (function () {
  var cbs = {}, state = { nc: null, def: null, dis: null };
  return {
    watch: function (k, cb) { (cbs[k] = cbs[k] || []).push(cb); cb(state[k], undefined); },
    _set: function (k, v) { var old = state[k]; state[k] = v; (cbs[k] || []).forEach(function (cb) { cb(v, old); }); }
  };
})();
setTimeout(function () { SlateFunctions._set('nc', @@NC@@); SlateFunctions._set('def', @@DEF@@); SlateFunctions._set('dis', @@DIS@@); }, 800);
</script>
"""


def _sub(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace("@@%s@@" % k.upper(), v)
    return tpl


def _blob(o):
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def _colmajor(df):
    out = {}
    for c in df.columns:
        vals = []
        for v in df[c].tolist():
            if v is None or (isinstance(v, float) and v != v):
                vals.append(None)
            else:
                vals.append(v)
        out[c] = vals
    return out


def _typed(df, columns):
    """CSV text -> the types the datasets (and Slate) give: int, num, text."""
    df = df.copy()
    for name, typ, _ in columns:
        if typ == "int":
            df[name] = pd.to_numeric(df[name], errors="coerce").fillna(0).astype(int)
        elif typ == "num":
            df[name] = pd.to_numeric(df[name], errors="coerce")
        else:
            df[name] = df[name].fillna("").astype(str)
    return df


def parts(root, scope_css):
    """CSS (scoped to .fto2, the fonts import first), HTML, the page's main JavaScript and the table adapter, from the template."""
    t = open(os.path.join(root, "build", "templates", "dashboard.html"), encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", t.split("<style>", 1)[1].split("</style>", 1)[0], flags=re.S)
    fonts = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/[^"]+)">', t)
    html = t[t.index('<div class="wrap">'):t.index('<script type="application/json" id="fto2-data">')].strip()   # the page, without its data
    main = t[t.index("<script>\n(function ()") + len("<script>\n"):t.rindex("</script>")].strip()
    a, b = t.index("/* ===== ADAPTER START ===== */"), t.index("/* ===== ADAPTER END ===== */") + len("/* ===== ADAPTER END ===== */")
    adapter = t[a:b].replace(ADAPTER_RUN, "")
    assert ADAPTER_RUN not in adapter and "function fto2FromTables" in adapter
    css_out = (('/* Fonts: if Slate blocks this address, the page falls back to Georgia and the system sans-serif. */\n@import url("%s");\n' % fonts.group(1))
               if fonts else "") + scope_css(css) + EXTRA_CSS
    html_out = ('<div class="fto2">\n<div id="fto2-err" class="fto2-err" hidden></div>\n<div id="fto2-wait" class="fto2-wait" hidden></div>\n%s\n</div>\n' % html)
    return css_out, html_out, main, adapter


def write_level(out, prefix, stamp, title, css, html, js, before=""):
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, prefix + ".css"), "w", encoding="utf-8").write("/* %s */\n%s" % (stamp, css))
    open(os.path.join(out, prefix + ".html"), "w", encoding="utf-8").write("<!-- %s -->\n%s" % (stamp, html))
    open(os.path.join(out, prefix + ".js"), "w", encoding="utf-8").write(js)
    one = _sub(ONE_FILE, title=title, stamp=stamp, css=css, html=html, js=js.replace("</script", "<\\/script"), before=before)
    return one


def slate_app(name, css, html, js, queries, height=1400, width=1316):
    """A Slate app document (the format of a Slate JSON export): one code sandbox filling the page, its state wired to the
    queries, and the queries on the Postgres source the existing FTO2 app uses (postgate-airbus-2)."""
    gid = str(uuid.uuid5(uuid.NAMESPACE_URL, "fto2-nc-dashboard/" + name))
    px = lambda v: {"rawValue": "%dpx" % v, "suffix": "px", "value": v}
    box = {"actions": [], "css": css, "cssLibraries": [], "events": [], "html": html, "js": js, "libraries": [], "sl": {"cssClasses": ""}}
    widget = {"id": "w_fto2_dashboard", "layout": {"height": height, "width": width, "x": 0, "y": 0}, "locked": False,
              "model": dict(box, state={"nc": None, "def": None, "dis": None}), "movable": True, "resizable": True,
              "styles": {"css": "", "less": "", "slateCss": {"height": px(height), "left": px(0), "top": px(0), "width": px(width)}},
              "template": dict(box, state=dict(STATE)), "type": "sl-code-sandbox", "upgradeVersion": 1}
    q = {k: {"datasourceRid": "ri.slate.staging.datasource.postgate-airbus-2", "datasourceVersion": "V1", "condition": {"type": "AlwaysEnabledCondition"},
             "dataSourceId": "postgate-airbus-2", "manual": False, "refreshInterval": 0, "template": sql} for k, sql in queries}
    empty = {"partials": {}, "queries": {}, "model": {"canvas": {"children": []}, "foundryFunctionInfos": [], "objectContexts": [], "objectSets": [],
                                                      "functionInfos": [], "variables": {}, "events": {}, "folderGroups": {}}}
    doc = {"upgradeVersion": 35, "queries": q, "partials": {}, "globalPageId": gid, "routes": {}, "showShellSidebarInViewMode": True,
           "projectScopeEnabled": False, "pages": {gid: empty}, "isTitaniumModeEnabled": False, "showActionsMenuInViewMode": True,
           "model": {"canvas": {"children": [widget], "width": width}, "customStylesheets": [], "datasetInfos": [], "events": {}, "folderGroups": {},
                     "foundryFunctionInfos": [], "functionInfos": [], "functionLibraries": [], "objectContexts": [], "objectSets": [],
                     "styles": {"css": "", "darkThemeEnabled": False, "less": "", "slateCss": {}}, "toolbar": {"children": [], "height": 0}, "variables": {}},
           "showAppHeaderInViewMode": False, "foundryDatasets": []}
    return {"document": doc, "name": name, "lastModifiedDate": "2026-10-20T00:00:00.000Z", "lastModifiedBy": "", "permalink": ""}


def level3_sql(table, columns, comment, order):
    sel = ",\n    ".join("CAST(%s AS VARCHAR) AS %s" % (c, c) if t == "date" else c for c, t, _ in columns)
    return "-- %s\nSELECT\n    %s\nFROM \"foundry_sync\".\"%s\"\nORDER BY %s\n" % (comment, sel, table, order)


def notebook_kit(root, out):
    """What the Skywise notebook needs, copied from the repository so the two never differ:
    notebook_kit/fto2/ (the backend code) and notebook_kit/fto2_ai_labels.csv (the labels, uploaded once as a dataset);
    config/ (the settings, a copy of the repository's config/, to put in the workspace as data/config the first time)."""
    k = os.path.join(out, "notebook_kit")
    if os.path.isdir(k):
        shutil.rmtree(k)
    shutil.copytree(os.path.join(root, "fto2"), os.path.join(k, "fto2"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copyfile(os.path.join(root, "04_reference", "llm_labels_longtext.csv"), os.path.join(k, "fto2_ai_labels.csv"))
    c = os.path.join(out, "config")
    if os.path.isdir(c):
        shutil.rmtree(c)
    shutil.copytree(os.path.join(root, "config"), c)
    return k


# ---------------------------------------------------------------- the pipeline notebook (level 3)
# The notebook only connects Skywise to the backend: every step is in fto2/skywise.py, every setting in data/config/.
NOTEBOOK = """# FTO2 NC pipeline and dashboard tables (Skywise Code Workspace).
#
# What it does: reads the NCs, applies the rules of data/config/, and writes the dashboard's three tables
# fto2_dash_nc, fto2_dash_defects, fto2_dash_disruptions (the steps are in notebook_kit/fto2/skywise.py).
#
# Before the first run:
#   - upload the folder notebook_kit next to this notebook (the code; upload it again after each update);
#   - upload the folder config into data/, so that it becomes data/config (the settings). Then change the settings there;
#     do not upload the folder again, it would overwrite the changes;
#   - data/ keeps the station mapping, the GPS register and the Test list (their names are in data/config/2_sources.csv);
#   - Data panel: read non_conformity, fto2_ai_labels, work_order_operation, mes_disruptions;
#     write fto2_dash_nc, fto2_dash_defects, fto2_dash_disruptions, and while 'garder_anciennes_sorties' is oui
#     (data/config/2_parametres.csv) also fto2_dashboard_data, fto2_dashboard_data_missing_ids, fto2_parsed_defects,
#     fto2_parsed_defects_missing_ids.
#
# Run it as a script (python fto2_pipeline_notebook.py) or as the notebook fto2_pipeline_notebook.ipynb.

# %%
import sys
sys.path.insert(0, "notebook_kit")
from foundry.transforms import Dataset, Column
from fto2 import skywise

# %%
nc_t, def_t, dis_t = skywise.run(Dataset, Column)
"""


def pipeline_notebook(root, out):
    """Write fto2_pipeline_notebook.py and .ipynb into out. Returns the .py path."""
    compile(NOTEBOOK, "fto2_pipeline_notebook.py", "exec")   # it must at least parse
    py = os.path.join(out, "fto2_pipeline_notebook.py")
    open(py, "w", encoding="utf-8").write(NOTEBOOK)
    cells = [c.strip("\n") for c in NOTEBOOK.split("\n# %%\n")]
    nbj = {"cells": [{"cell_type": "code", "execution_count": None, "id": "fto2-%02d" % i, "metadata": {}, "outputs": [],
                      "source": [l + "\n" for l in c.split("\n")[:-1]] + [c.split("\n")[-1]]} for i, c in enumerate(cells)],
           "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                        "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    json.dump(nbj, open(os.path.join(out, "fto2_pipeline_notebook.ipynb"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return py


def build(ref, root, scope_css, say):
    """Write the four levels; returns counts for the build report."""
    sky = os.path.join(root, "03_reports", "skywise")
    css, html, main, adapter = parts(root, scope_css)
    sys_path = os.path.join(root, "build")
    import sys
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)
    from fto2_core import NC_COLUMNS, DEF_COLUMNS, DIS_COLUMNS
    report = {}
    ref_blob = _blob(ref)

    # level 1: fictitious tables in the JS
    dn, dd, ds = (os.path.join(root, "build", "dummy", f) for f in ("fto2_dash_nc_dummy.csv", "fto2_dash_defects_dummy.csv", "fto2_dash_disruptions_dummy.csv"))
    if os.path.exists(dn) and os.path.exists(dd) and os.path.exists(ds):
        nc = _typed(pd.read_csv(dn, dtype=str, keep_default_na=False), NC_COLUMNS)
        df = _typed(pd.read_csv(dd, dtype=str, keep_default_na=False), DEF_COLUMNS)
        dis = _typed(pd.read_csv(ds, dtype=str, keep_default_na=False), DIS_COLUMNS)
        tables = {"nc": _colmajor(nc), "def": _colmajor(df), "dis": _colmajor(dis)}
        stamp = "FTO2 NC dashboard, Skywise level 1 (visual check): FICTITIOUS data written in the JS (%d NCs, %d defect lines, %d aléas). Generated by build/build_all.py; do not edit by hand." % (len(nc), len(df), len(dis))
        js = _sub(JS_L1, stamp=stamp, ref=ref_blob, tables=_blob(tables), adapter=adapter, main=main)
        one = write_level(os.path.join(sky, "level1_dummy_in_js"), "fto2_level1", stamp, "FTO2 NC Dashboard - level 1", css, html, js)
        open(os.path.join(sky, "level1_dummy_in_js", "FTO2_Level1_Slate.html"), "w", encoding="utf-8").write(one)
        report["level1"] = {"ncs": len(nc), "defects": len(df), "aleas": len(dis), "js_kb": len(js.encode()) // 1024}
        # level 2 local preview: the same tables handed over as Slate would
        pre = FAKE_SLATE.replace("@@NC@@", _blob(tables["nc"])).replace("@@DEF@@", _blob(tables["def"])).replace("@@DIS@@", _blob(tables["dis"]))
    else:
        say("skywise: no build/dummy/*.csv (run build/dummy_tables.py): level 1 skipped")
        pre = None

    # levels 2 and 3: the same JS, data from the sandbox's state
    stamp23 = "FTO2 NC dashboard, Skywise levels 2 and 3: data from the Slate queries q_fto2_nc, q_fto2_def and q_fto2_dis (optional) through the code sandbox's state. Generated by build/build_all.py; do not edit by hand."
    js23 = _sub(JS_L23, stamp=stamp23, ref=ref_blob, adapter=adapter, main=main)
    l2, l3 = os.path.join(sky, "level2_dummy_queries"), os.path.join(sky, "level3_datasets")
    for out in (l2, l3):
        one = write_level(out, "fto2_level23", stamp23, "FTO2 NC Dashboard - levels 2 and 3", css, html, js23)
        open(os.path.join(out, "FTO2_Level23_Slate.html"), "w", encoding="utf-8").write(one)
        json.dump(STATE, open(os.path.join(out, "state.json"), "w"), indent=2)
        if out == l2 and pre:
            open(os.path.join(out, "preview_local_only.html"), "w", encoding="utf-8").write(
                one.replace("<!-- ===== HTML START ===== -->", pre + "<!-- ===== HTML START ===== -->", 1))
    report["level23_js_kb"] = len(js23.encode()) // 1024
    sql3 = (("q_fto2_nc", level3_sql("fto2_dash_nc", NC_COLUMNS, "FTO2 NC dashboard, level 3: one row per NC (dataset fto2_dash_nc, written by the Skywise notebook). Slate query q_fto2_nc.", "created, nc")),
            ("q_fto2_def", level3_sql("fto2_dash_defects", DEF_COLUMNS, "FTO2 NC dashboard, level 3: one row per defect line (dataset fto2_dash_defects). Slate query q_fto2_def.", "nc, seq")),
            ("q_fto2_dis", level3_sql("fto2_dash_disruptions", DIS_COLUMNS, "FTO2 NC dashboard, level 3: one row per quality aléa with no NC, the disruption block (dataset fto2_dash_disruptions). Slate query q_fto2_dis.", "opened, id")))
    for name, sql in sql3:
        open(os.path.join(l3, name + ".sql"), "w", encoding="utf-8").write(sql)
    notebook_kit(root, l3)
    for f in ("notebook_cell.py",):   # replaced by the one-step pipeline notebook
        if os.path.exists(os.path.join(l3, "notebook_kit", f)):
            os.remove(os.path.join(l3, "notebook_kit", f))
    report["pipeline_notebook"] = bool(pipeline_notebook(root, l3))
    json.dump({"nc": [{"name": c, "type": t, "meaning": m} for c, t, m in NC_COLUMNS], "defects": [{"name": c, "type": t, "meaning": m} for c, t, m in DEF_COLUMNS],
               "disruptions": [{"name": c, "type": t, "meaning": m} for c, t, m in DIS_COLUMNS]},
              open(os.path.join(l3, "columns.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    # level 4: importable Slate apps
    l4 = os.path.join(sky, "level4_import")
    os.makedirs(l4, exist_ok=True)
    q2 = [os.path.join(l2, "q_fto2_%s_dummy.sql" % k) for k in ("nc", "def", "dis")]
    if all(os.path.exists(f) for f in q2):
        sql2 = [("q_fto2_" + k, open(f, encoding="utf-8").read()) for k, f in zip(("nc", "def", "dis"), q2)]
        app2 = slate_app("FTO2 NC Dashboard (level 2, fictitious data)", css, html, js23, sql2)
        json.dump(app2, open(os.path.join(l4, "FTO2_NC_Dashboard_level2.slate.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    app3 = slate_app("FTO2 NC Dashboard", css, html, js23, sql3)
    json.dump(app3, open(os.path.join(l4, "FTO2_NC_Dashboard_level3.slate.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    report["level4"] = sorted(f for f in os.listdir(l4) if f.endswith(".json"))
    say("skywise levels:", report)
    return report

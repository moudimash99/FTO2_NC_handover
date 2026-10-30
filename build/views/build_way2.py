"""Way 2 of the views for Slate: pre-computed by a Slate function, separation of concerns. Called by build/views_pack.py.

    data (Slate queries q_fto2_nc, q_fto2_def)  ->  logic (Slate function f_fto2_views: fto2_views_model.js)  ->  display (code sandbox: fto2_views_render.js)

fto2_views_model.js is assembled here from the dashboard template, so the model and the dashboard share one set of rules:
the table adapter and the alarm engine (between their markers), and the dashboard's functions and constants named in PULL_FN
and PULL_VAR, copied unchanged; model_core.js adds the computing part of each chart (in the dashboard it is mixed with the
drawing). A function missing from the template stops the build with its name.
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TEMPLATE = os.path.join(ROOT, "build", "templates", "dashboard.html")

# the dashboard's own functions the model calls (selection, production plan, forecast, targets, 2025, alarms, labels)
PULL_FN = ["S", "L", "tidy", "whereName", "lineOrder", "dCat", "dRca", "dSub", "dMinor", "dCable", "dAlloc", "keepMinor", "dCode", "dFin", "codeDesc", "codeName",
           "plusDays", "minusMonths", "presetRange", "gNc", "ours", "gScope", "ids", "select", "isoDay",
           "ncType", "prodName", "cbLab", "catKey",
           "pSrc", "sumA", "pData", "pAgg", "pOk", "pAct", "P_", "pMonthly", "connOk",
           "v2Months", "v2Plan", "v2Fc", "v2InPlan", "v2OutK", "v2Series", "y25Sel", "y25Cum", "y25Lines", "y25Rca", "y25Rate", "v2Tgt",
           "alNc", "alCompute", "alName", "alText", "alWk"]
PULL_VAR = ["EN", "WHERE_FR", "WHERE_EN", "CB_EN", "TYPE_ALIAS", "CAT_ORDER", "ASIDE", "MAIN_CATS", "CONN_LINES", "V2W", "PRESETS", "AL"]
# the page's words the alarm texts use (French and English, as in the dashboard)
STR_KEYS = ["alAll", "alSt", "alCab", "alUp", "alCross", "alCreep", "alPlane", "alWk", "alDont", "alAlso", "alAct", "prodUnknown", "noLine"]


def _skip_str(s, k):
    q = s[k]; k += 1
    while s[k] != q:
        if s[k] == "\\":
            k += 1
        k += 1
    return k


def _block_end(s, j, kinds="{[("):
    """Index of the brace or bracket closing the one at j (strings, regular expressions and line comments skipped). A function
    body counts only its braces."""
    d, k, close = 0, j, {"{": "}", "[": "]", "(": ")"}
    shut = "".join(close[x] for x in kinds)
    while True:
        c = s[k]
        if c in kinds:
            d += 1
        elif c in shut:
            d -= 1
            if d == 0:
                return k
        elif c in "'\"":
            k = _skip_str(s, k)
        elif c == "/" and s[k + 1] == "/":
            k = s.index("\n", k) - 1
        elif c == "/" and s[:k].rstrip()[-1:] in "(,=:[!&|?{};":
            k = _skip_regex(s, k)
        k += 1


def _skip_regex(s, k):
    """Index of the slash closing the regular expression opened at k (esc's /[&<>"]/g holds a quote that is not a string)."""
    k += 1
    cls = False
    while cls or s[k] != "/":
        if s[k] == "\\":
            k += 1
        elif s[k] == "[":
            cls = True
        elif s[k] == "]":
            cls = False
        k += 1
    return k


def pull_fn(s, name, at=0):
    m = None
    for x in re.compile(r"function " + re.escape(name) + r"\s*\(").finditer(s, at):   # on a top-level line of the page's main function (2 spaces)
        line = s[s.rindex("\n", 0, x.start()) + 1:x.start()]
        if line.startswith("  ") and not line.startswith("   ") and (line == "  " or line.rstrip().endswith("}")):
            m = x
            break
    if not m:
        raise SystemExit("way 2: the dashboard has no function %s any more (build/views/build_way2.py, PULL_FN)" % name)
    return s[m.start():_block_end(s, s.index("{", m.end()), "{") + 1]


def pull_var(s, name, at=0):
    if name == "AL":
        at = s.index("/* ===== ALARM ENGINE END ===== */")   # the adapter has its own AL (aliases), earlier in the file
    m = re.compile(r"\n  var " + re.escape(name) + r" = ").search(s, at)
    if not m:
        raise SystemExit("way 2: the dashboard has no var %s any more (build/views/build_way2.py, PULL_VAR)" % name)
    k = m.end()
    while s[k] != ";":   # to the end of the statement, past any object, array or call
        if s[k] in "{[(":
            k = _block_end(s, k)
        elif s[k] in "'\"":
            k = _skip_str(s, k)
        k += 1
    return s[m.start() + 1:k + 1]


def between(s, a, b):
    i, j = s.index(a), s.index(b)
    return s[i:j + len(b)]


def strings(s):
    out = {}
    for lang, at in (("fr", s.index("    fr: {")), ("en", s.index("    en: {"))):
        o = {}
        for k in STR_KEYS:
            m = re.compile(r"\b" + k + r": '((?:[^'\\]|\\.)*)'").search(s, at)
            if not m:
                raise SystemExit("way 2: no string %s in the dashboard" % k)
            o[k] = m.group(1).replace("\\'", "'")
        out[lang] = o
    return out


def model_js(stamp):
    s = open(TEMPLATE, encoding="utf-8").read()
    adapter = between(s, "/* ===== ADAPTER START ===== */", "/* ===== ADAPTER END ===== */")
    adapter = "\n".join(l for l in adapter.split("\n") if not l.startswith("if (window.DASH && window.DASH.tables)"))
    alarm = between(s, "/* ===== ALARM ENGINE START ===== */", "/* ===== ALARM ENGINE END ===== */")
    cats = between(s, "  var RCA_CAT = {}, CODE_CAT = {};", "p[1][k] = Object.keys(o).sort(function (u, v) { return o[v] - o[u]; })[0]; }); }); })();")
    core = open(os.path.join(HERE, "model_core.js"), encoding="utf-8").read()
    parts = [
        "/* %s */" % stamp,
        "var FTO2Views = (function () {",
        adapter,
        "  // the views' model for one set of filters: tables as Slate gives them (one array per column) or as rows; ref: the dashboard's",
        "  // fixed references (production plan, 2025, codes...); filters: {line, preset, from, to, phase, fto2, minor, src, org, lang}",
        "  function model(tables, ref, filters) {",
        "    var F = filters || {}, T0 = tables || {};",
        "    var D = fto2FromTables(T0.nc, T0.def, ref, T0.dis || null), EMBED = true, PAGE = 'vues';",
        "    if (!D.ncs.length) {   // rows arrived but none could be read: say what came, to fix the query",
        "      var cols = Array.isArray(T0.nc) ? Object.keys(T0.nc[0] || {}) : Object.keys(T0.nc || {});",
        "      throw new Error('aucune NC lisible dans q_fto2_nc (colonnes reçues : ' + cols.join(', ') + ') / no readable NC in q_fto2_nc (columns received: ' + cols.join(', ') + ')');",
        "    }",
        "    var G = { lang: F.lang === 'en' ? 'en' : 'fr', minor: F.minor !== false, tab: 'syn' };",
        "    var GF = { pick: null, src: F.src || 'all', org: F.org || '', fto2: F.fto2 !== false, phase: F.phase == null ? 'SERIE' : F.phase, line: F.line || '',",
        "      preset: F.preset || 'ytd', from: F.from || '', to: F.to || '' };",
        "    if (GF.preset === 'custom' && !(GF.from && GF.to)) GF.preset = 'ytd';",
        "    var STR = %s;" % json.dumps(strings(s), ensure_ascii=False),
        "    var NC = {}; D.ncs.forEach(function (n) { NC[n[0]] = n; });",
        "    var REP = D.ncs, DMAX = D.meta.to, DMIN = REP.reduce(function (m, n) { return n[1] < m ? n[1] : m; }, DMAX);",
        "    var SEL_NC = [], SER_NC = [], CLI_NC = [], SEL = {}, SER = {}, CLI = {}, PD = null, PA = null, PCOL = {}, DM = null, GN = [], GD = [], G320 = false, V2CUT = 0.75;",
        "    var PR = { src: D.eqmsn ? 'real' : 'dummy', ver: D.eqmsn && D.eqmsn.wd ? 'wd' : 'std' };",
    ]
    parts += ["  " + pull_var(s, v) for v in PULL_VAR]
    parts += ["    var LINES = lineOrder(REP.map(function (n) { return n[3]; }));", cats]
    parts += [pull_fn(s, f) for f in PULL_FN]
    parts += [alarm, core, "  }", "  return { model: model };", "})();",
              "if (typeof module !== 'undefined' && module.exports) module.exports = FTO2Views;", ""]
    return "\n".join(parts)


# the display's helpers, the dashboard's own (formatting, SVG pieces, colours, names), taken after the adapter: the adapter has
# its own num() and day() for reading the tables
RENDER_FN = ["esc", "loc", "num", "eur", "eurK", "pct", "pct0", "day", "shortDay", "monthName", "f1", "f2", "kE", "kEur", "ord", "r1", "tx", "tip", "svg", "sw",
             "swl", "trunc", "spread", "pNice", "pGridY", "hexRgb", "tint", "catFill", "lineCol", "miniTable", "L", "S", "gx", "gT", "catLabel", "catKey",
             "v2Mo", "v2Head", "prodName", "typeName", "ruleName", "stName", "ncShareFmt"]
# the dashboard's words: its tables of strings, the additions made to them further down the page, and the views page's own
RENDER_VAR = ["MONTHS_FR", "MONTHS_EN", "CATC", "PROG_COL", "EN", "CAT_ORDER", "ASIDE", "MAIN_CATS", "RULE_FR", "STR", "GX", "GSTR"]
RENDER_ADD = [r"\n  Object\.assign\(GX\.(fr|en), \{", r"\n  Object\.assign\(GSTR, \{", r"\n    Object\.assign\(STR\.(fr|en), \{ tabSyn"]


# local preview only: stands in for Slate (state, variable v_fto2_filters, event fto2Filters, function f_fto2_views run on the
# real tables), with Slate's order of things: the model comes back a moment after the filters leave
FAKE_SLATE = """<script>
/* LOCAL PREVIEW ONLY - not for Slate. Stands in for Slate: the sandbox state, the variable v_fto2_filters, the event
   w_fto2_views.fto2Filters and the function f_fto2_views (here fto2_views_model.js on the real tables). */
window.SlateFunctions = (function () {
  var cbs = {}, state = { model: null }, v_fto2_filters = {}, TABLES = { nc: @@NC@@, def: @@DEF@@ }, REF = @@REF@@;
  function set(k, v) { var old = state[k]; state[k] = v; (cbs[k] || []).forEach(function (cb) { cb(v, old); }); }
  function f_fto2_views() {   // the Slate function: re-run when the variable changes
    var t0 = Date.now(), m;
    try { m = FTO2Views.model(TABLES, REF, v_fto2_filters); } catch (e) { m = { error: String(e && e.message || e) }; }
    window.FTO2_LAST_MS = Date.now() - t0; set('model', m);
  }
  setTimeout(f_fto2_views, 600);   // the queries arrive
  return {
    watch: function (k, cb) { (cbs[k] = cbs[k] || []).push(cb); cb(state[k], undefined); },
    getState: function () { return state; },
    setState: function (o) { Object.keys(o).forEach(function (k) { if (o[k] !== state[k]) set(k, o[k]); }); },
    triggerEvent: function (name) {   // the Slate event: set v_fto2_filters from the state, which re-runs the function
      if (name !== 'fto2Filters') return;
      v_fto2_filters = JSON.parse(JSON.stringify(state.filters || {})); setTimeout(f_fto2_views, 30);
    }
  };
})();
</script>
"""


def pull_adds(s, at):
    """The statements that add to the string tables (Object.assign(GX.fr, {...}); ...), in the page's order."""
    out = []
    for pat in RENDER_ADD:
        found = list(re.compile(pat).finditer(s, at))
        if not found:
            raise SystemExit("way 2: the dashboard has no %s any more (build/views/build_way2.py, RENDER_ADD)" % pat)
        for m in found:
            k = _block_end(s, s.index("(", m.start()))
            out.append((m.start(), "  " + s[m.start() + 1:k + 1].strip() + ";"))
    return [t for _, t in sorted(out)]


def render_js(stamp):
    s = open(TEMPLATE, encoding="utf-8").read()
    at = s.index("/* ===== ADAPTER END ===== */")
    core = open(os.path.join(HERE, "render_core.js"), encoding="utf-8").read()
    parts = ["/* %s */" % stamp, "var FTO2ViewsRender = (function () {"]
    parts += ["  " + pull_var(s, v, at) for v in RENDER_VAR]
    parts += pull_adds(s, at)
    parts += [pull_fn(s, f, at) for f in RENDER_FN]
    parts += [core.rstrip("\n"), "})();", ""]
    return "\n".join(parts)


def _no_binding(name, text):
    """Slate reads a double brace as a binding: only the function's own bindings may hold one."""
    if "{{" in text:
        k = text.index("{{")
        raise SystemExit("way 2: %s holds a double brace, which Slate would read as a binding: ...%s..." % (name, text[max(0, k - 60):k + 60]))


def build(data, out_root, say=print):
    sys.path.insert(0, os.path.dirname(HERE))
    import build_all            # noqa: E402   _scope_css: the dashboard's styles scoped to .fto2
    import skywise_pack as SP   # noqa: E402   the Slate pieces of the dashboard (CSS, one-file layout)
    out = os.path.join(out_root, "way2_precomputed")
    os.makedirs(out, exist_ok=True)
    stamp = ("FTO2 Synthèse et détail, way 2: the views' model (pure JavaScript: no page, no drawing). Runs as the Slate function "
             "f_fto2_views, in Node or in a page. Assembled by build/views/build_way2.py from the dashboard template; do not edit by hand.")
    model = model_js(stamp)
    open(os.path.join(out, "fto2_views_model.js"), "w", encoding="utf-8").write(model)

    # logic: the Slate function (the references, the model, the call)
    fstamp = ("FTO2 Synthèse et détail, way 2: the Slate function f_fto2_views (logic). Generated by build/views/build_way2.py; "
              "do not edit by hand.")
    body = model.replace("if (typeof module !== 'undefined' && module.exports) module.exports = FTO2Views;\n", "")
    ref = SP._blob(data["ref"])
    _no_binding("the model", body)
    _no_binding("the references", ref)
    fn = open(os.path.join(HERE, "slate_function.js"), encoding="utf-8").read()
    fn = fn.replace("@@STAMP@@", fstamp).replace("@@REF@@", ref).replace("@@MODEL@@", body)
    open(os.path.join(out, "f_fto2_views.js"), "w", encoding="utf-8").write(fn)

    # display: the code sandbox (the dashboard's CSS, a root for the page, the drawing and the Slate glue)
    sstamp = ("FTO2 Synthèse et détail, way 2: the code sandbox w_fto2_views (display only: it draws the model of f_fto2_views and "
              "sends the filters back). Generated by build/views/build_way2.py; do not edit by hand.")
    css, _html, _main, _adapter = SP.parts(ROOT, build_all._scope_css)
    html = ('<div class="fto2">\n<div id="fto2-err" class="fto2-err" hidden></div>\n<div id="fto2-wait" class="fto2-wait" hidden></div>\n'
            '<div id="fto2-root"></div>\n</div>\n')
    js = render_js(sstamp) + open(os.path.join(HERE, "sandbox_boot.js"), encoding="utf-8").read()
    _no_binding("the sandbox JavaScript", js)
    one = SP.write_level(out, "fto2_views_sandbox", sstamp, "FTO2 Synthèse et détail - way 2 (sandbox)", css, html, js)
    open(os.path.join(out, "FTO2_Views_way2_Slate.html"), "w", encoding="utf-8").write(one)
    json.dump({"model": "{{f_fto2_views}}"}, open(os.path.join(out, "state.json"), "w"), indent=2)
    open(os.path.join(out, "event_fto2Filters.js"), "w", encoding="utf-8").write(
        "// Slate event: trigger w_fto2_views.fto2Filters, action: set variable v_fto2_filters to the value returned below\n"
        "return {{w_fto2_views.state.filters}};\n")
    for q in ("q_fto2_nc", "q_fto2_def"):   # the dashboard's level-3 queries, unchanged
        shutil.copyfile(os.path.join(ROOT, "03_reports", "skywise", "level3_datasets", q + ".sql"), os.path.join(out, q + ".sql"))
    shutil.copyfile(os.path.join(HERE, "precompute_node.js"), os.path.join(out, "precompute_node.js"))

    # local preview: the model runs in the page, standing in for the Slate function (never paste this file into Slate)
    t = data["tables"]
    pre = (FAKE_SLATE.replace("@@NC@@", SP._blob(t["nc"])).replace("@@DEF@@", SP._blob(t["def"])).replace("@@REF@@", ref) +
           "<script>\n" + body.replace("</script", "<\\/script") + "</script>\n")
    open(os.path.join(out, "preview_local_only.html"), "w", encoding="utf-8").write(
        one.replace("<!-- ===== HTML START ===== -->", pre + "<!-- ===== HTML START ===== -->", 1))
    say("views way 2:", {f: os.path.getsize(os.path.join(out, f)) // 1024 for f in sorted(os.listdir(out))}, "KB")
    return out


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(HERE))
    import views_pack
    build(views_pack.dash_data(), views_pack.OUT)

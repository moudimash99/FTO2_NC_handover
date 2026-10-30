/* FTO2 Synthèse et détail, way 2: the views' model (pure JavaScript: no page, no drawing). Runs as the Slate function f_fto2_views, in Node or in a page. Assembled by build/views/build_way2.py from the dashboard template; do not edit by hand. */
var FTO2Views = (function () {
/* ===== ADAPTER START ===== */
// The page's data from its two tables, one row per NC and one row per defect line (columns: build/fto2_core.py, NC_COLUMNS and
// DEF_COLUMNS), plus the fixed references (code sheet, MFT actions, cost parameters, production plan, root-cause tree).
// A table comes as a Slate query result (one array per column) or as rows (an array of objects).
function fto2FromTables(ncIn, defIn, ref, disIn) {
  ref = ref || {};
  function rows(t) {
    if (!t) return [];
    if (Array.isArray(t)) return t;
    var cols = Object.keys(t), n = 0, out = [];
    cols.forEach(function (c) { if (t[c] && t[c].length > n) n = t[c].length; });
    for (var i = 0; i < n; i++) { var o = {}; cols.forEach(function (c) { o[c] = t[c] ? t[c][i] : null; }); out.push(o); }
    return out;
  }
  function str(v) { return v == null ? '' : String(v); }
  function num(v) { var x = typeof v === 'number' ? v : parseFloat(v); return isFinite(x) ? x : 0; }
  function numOrNull(v) { if (v == null || v === '') return null; var x = typeof v === 'number' ? v : parseFloat(v); return isFinite(x) ? x : null; }
  function int(v) { return Math.round(num(v)); }
  function day(v) { if (v == null || v === '') return ''; if (typeof v === 'number') return new Date(v).toISOString().slice(0, 10); return String(v).slice(0, 10); }
  function r2(x) { return Math.round(x * 100) / 100; }
  function isoWeek(iso) {   // '2026-W02', as Python's isocalendar()
    var d = new Date(iso + 'T00:00:00Z'), dow = (d.getUTCDay() + 6) % 7;
    d.setUTCDate(d.getUTCDate() - dow + 3);   // the Thursday of the week decides the year
    var y = d.getUTCFullYear(), j4 = new Date(Date.UTC(y, 0, 4)), t1 = Date.UTC(y, 0, 4 - (j4.getUTCDay() + 6) % 7 + 3);
    var w = 1 + Math.round((d.getTime() - t1) / 6048e5);
    return y + '-W' + (w < 10 ? '0' : '') + w;
  }
  function clean(t) { return t.trim().split(/\s+/).join(' ').replace(/^[ *:\-]+|[ *:\-]+$/g, ''); }
  var ncs = [], byNc = {}, notLiable = [];
  rows(ncIn).forEach(function (r) {
    var id = str(r.nc).trim().replace(/\.0$/, ''), created = day(r.created);
    if (!id || !created) return;
    var k = int(r.on_aec) === 1 ? 1 : 0;   // FTO2's cost only where FTO2 is liable; the NC still counts
    if (!k) notLiable.push(num(r.cost_total));
    var a = [id, created, isoWeek(created), str(r.line), '', int(r.on_aec), str(r.rule), str(r.decision_label), str(r.where_found),
      k * num(r.cost_airbus), k * num(r.cost_global), 0, k * num(r.cost_total), k * num(r.cost_admin), 0, k * num(r.cost_work), 0, k * num(r.cost_material), k * num(r.cost_engineering),
      0, int(r.cable), int(r.defect_lines), str(r.title), str(r.scope), str(r.phase),
      str(r.msn).replace(/\.0$/, ''), str(r.product) || 'Other', str(r.station), r.hour == null || r.hour === '' ? -1 : int(r.hour), numOrNull(r.lead_days), int(r.is_open),
      numOrNull(r.age_days), day(r.closed), str(r.type_nc), str(r.liability), str(r.sap_defect), str(r.sap_cause_group), str(r.sap_cause), str(r.status), str(r.source) || 'sky',
      [num(r.min_alert), num(r.min_writing), num(r.min_support), num(r.min_setup), num(r.min_hands_on), num(r.min_recheck), num(r.hours_engineering), int(r.final_inspection),
        str(r.work_source), str(r.order_state), str(r.rework_orders), str(r.alert_source), str(r.aleas)], str(r.origin) || 'normal', str(r.plant), k ? 0 : num(r.cost_total)];
    ncs.push(a); byNc[id] = { a: a, plant: str(r.plant), lt: str(r.long_text) };
  });
  // products the production plan does not name, put back on their plan product (04_reference/produits_alias.csv, the same rules as
  // the 2025 figures in build_all.alias_product): [line, product regex, station regex, plan product], first match wins
  var AL = (ref.eqmsn && ref.eqmsn.alias) || [], inPlan = (ref.eqmsn && ref.eqmsn.map) || {};
  if (AL.length) ncs.forEach(function (a) {
    var p = a[26] || 'Other'; if (inPlan[p.toUpperCase()]) return;
    for (var i = 0; i < AL.length; i++) { var x = AL[i];
      if (x[0] === a[3] && new RegExp(x[1]).test(p) && (!x[2] || new RegExp(x[2], 'i').test(a[27]))) { a[26] = x[3]; return; } }
  });
  // FIN: a panel or harness code (…VU, …VB) is the product, not an equipment FIN (Mohammad, 29 Oct), and a length (250CM) is no FIN;
  // take the next FIN written in the defect text, else none
  var FIN_RE = /\b(\d{1,4}[A-Z]{2,4}\d{0,4}[A-Z]{0,2})\b/g, FIN_NOT = /V[UB]$|^\d+(CM|MM|M|KG|MN|MIN|H|OHM|MOHM|KOHM|NM|DAN|ER|EME|ND|RD|TH|ST|EA|PCS)$/;
  function finOf(fin, text) {
    if (!fin || !FIN_NOT.test(fin)) return fin;   // also a length or a unit the parser took for a FIN (250CM, 100MOHM)
    var t = text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase(), m; FIN_RE.lastIndex = 0;
    while ((m = FIN_RE.exec(t))) if (!FIN_NOT.test(m[1])) return m[1];
    return '';
  }
  var defects = [], client = {}, lt = {}, qty = {}, pool = [];
  rows(defIn).forEach(function (r) {
    var id = str(r.nc).trim().replace(/\.0$/, ''), n = byNc[id];
    if (!n) return;   // an NC without a creation date is in no selection
    var a = n.a, seq = int(r.seq), k = id + '|' + seq, text = str(r.text);
    defects.push([id, seq, a[1], a[2], a[3], a[4], '', '', '', 0, 0, str(r.cat), str(r.rca), str(r.sub), int(r.minor), int(r.cable), 0, num(r.cost_alloc),
      text, '', a[23], a[24], str(r.subcode), finOf(str(r.fin), text)]);
    if (r.qty != null && r.qty !== '' && int(r.qty) !== 1) qty[k] = int(r.qty);
    if (a[23] === 'client') { client[k] = [str(r.cr_nature), str(r.cr_detection), str(r.cr_symptom), '', n.plant, a[34]]; lt[id] = n.lt; }
    if (a[23] && str(r.label_src) === 'ai' && str(r.ai_conf) === 'high' && text.length >= 30 && text.length <= 170) pool.push([a[1], id, str(r.rca), text]);
  });
  // root-cause page: three recent, clearly labelled examples per root cause
  pool.sort(function (x, y) { return x[0] < y[0] ? 1 : x[0] > y[0] ? -1 : 0; });
  var ex = {};
  pool.forEach(function (p) { var e = ex[p[2]] || (ex[p[2]] = []); if (e.length < 3 && !e.some(function (q) { return q[0] === p[1]; })) e.push([p[1], clean(p[3])]); });
  var rca = (ref.rca || []).map(function (o) { var c = {}; for (var key in o) c[key] = o[key]; c.ex = ex[o.rca] || []; return c; });
  // production plan: each product's line is the line of most of its NCs
  var eq = null;
  if (ref.eqmsn) {
    eq = {}; for (var key in ref.eqmsn) eq[key] = ref.eqmsn[key];
    var cnt = {};
    ncs.forEach(function (a) { var p = (eq.map || {})[a[26].toUpperCase()]; if (p && a[3]) { var c = cnt[p] || (cnt[p] = {}); c[a[3]] = (c[a[3]] || 0) + 1; } });
    eq.line = {};
    Object.keys(eq.std || {}).forEach(function (p) { var best = '', bv = 0, c = cnt[p] || {}; Object.keys(c).forEach(function (l) { if (c[l] > bv) { bv = c[l]; best = l; } }); eq.line[p] = best; });
  }
  var to = '', aec = ncs.filter(function (a) { return a[5] === 1; }), sum = function (xs) { return r2(xs.reduce(function (s, a) { return s + a[12]; }, 0)); };
  ncs.forEach(function (a) { if (a[1] > to) to = a[1]; });
  var nlSum = r2(notLiable.reduce(function (s, v) { return s + v; }, 0));
  var cnqp = {}; for (var k2 in (ref.cnqp || {})) cnqp[k2] = ref.cnqp[k2]; cnqp.qty = qty;
  // the disruption block (optional third table): quality aléas that led to no NC [id, opened, line, station, work order, minutes, in block, reason, status, comment]
  var dis = disIn ? rows(disIn).map(function (r) { return [str(r.id), day(r.opened), str(r.line), str(r.station), str(r.work_order), num(r.minutes), int(r.in_block), str(r.reason), str(r.status), str(r.comment)]; })
    .filter(function (a) { return a[0] && a[1]; }) : null;
  return { defects: defects, ncs: ncs, rca: rca, client: client, lt: lt, codes: ref.codes || {}, actions: ref.actions || [], cnqp: cnqp, eqmsn: eq, y25: ref.y25 || null, dis: dis, cables: ref.cables || null,
    meta: { from: ref.from || '2026-01-01', to: to, aside: { other: [notLiable.length, nlSum] },
      noLine: ncs.filter(function (a) { var p = String(a[42] || '').trim().toUpperCase(); return (p === 'FTO2' || p === 'FT02') && a[21] === 0; }).length, modelTotal: sum(aec) } };
}
/* ===== ADAPTER END ===== */
  // the views' model for one set of filters: tables as Slate gives them (one array per column) or as rows; ref: the dashboard's
  // fixed references (production plan, 2025, codes...); filters: {line, preset, from, to, phase, fto2, minor, src, org, lang}
  function model(tables, ref, filters) {
    var F = filters || {}, T0 = tables || {};
    var D = fto2FromTables(T0.nc, T0.def, ref, T0.dis || null), EMBED = true, PAGE = 'vues';
    if (!D.ncs.length) {   // rows arrived but none could be read: say what came, to fix the query
      var cols = Array.isArray(T0.nc) ? Object.keys(T0.nc[0] || {}) : Object.keys(T0.nc || {});
      throw new Error('aucune NC lisible dans q_fto2_nc (colonnes reçues : ' + cols.join(', ') + ') / no readable NC in q_fto2_nc (columns received: ' + cols.join(', ') + ')');
    }
    var G = { lang: F.lang === 'en' ? 'en' : 'fr', minor: F.minor !== false, tab: 'syn' };
    var GF = { pick: null, src: F.src || 'all', org: F.org || '', fto2: F.fto2 !== false, phase: F.phase == null ? 'SERIE' : F.phase, line: F.line || '',
      preset: F.preset || 'ytd', from: F.from || '', to: F.to || '' };
    if (GF.preset === 'custom' && !(GF.from && GF.to)) GF.preset = 'ytd';
    var STR = {"fr": {"alAll": "Toutes les causes", "alSt": "poste {v}", "alCab": "Câbles · {v}", "alUp": "{w} en hausse depuis {s}", "alCross": "{w} en hausse sur plusieurs lignes depuis {s}", "alCreep": "{w} en hausse lente depuis {s}", "alPlane": "MSN {m} : {n} NC, un {p} en a {d} d’habitude", "alWk": "S{n}", "alDont": "dont {l}", "alAlso": "aussi : {l}", "alAct": "action en cours : {t}", "prodUnknown": "Non identifié", "noLine": "NC A400M (sans texte)"}, "en": {"alAll": "All causes", "alSt": "station {v}", "alCab": "Cables · {v}", "alUp": "{w} rising since {s}", "alCross": "{w} rising on several lines since {s}", "alCreep": "{w} creeping up since {s}", "alPlane": "MSN {m}: {n} NCs, a {p} usually has {d}", "alWk": "W{n}", "alDont": "including {l}", "alAlso": "also: {l}", "alAct": "action in progress: {t}", "prodUnknown": "Not identified", "noLine": "A400M NCs (no text)"}};
    var NC = {}; D.ncs.forEach(function (n) { NC[n[0]] = n; });
    var REP = D.ncs, DMAX = D.meta.to, DMIN = REP.reduce(function (m, n) { return n[1] < m ? n[1] : m; }, DMAX);
    var SEL_NC = [], SER_NC = [], CLI_NC = [], SEL = {}, SER = {}, CLI = {}, PD = null, PA = null, PCOL = {}, DM = null, GN = [], GD = [], G320 = false, V2CUT = 0.75;
    var PR = { src: D.eqmsn ? 'real' : 'dummy', ver: D.eqmsn && D.eqmsn.wd ? 'wd' : 'std' };
    var EN = {
    'MEO Facteur humain': 'Workmanship (human factor)', 'Erreur Branchement': 'Connection error', 'Élément Manquant': 'Missing item',
    'Élément Endommagé': 'Damaged item', 'Déverrouillage': 'Unlocked contact', 'Grounding/Bonding': 'Grounding/Bonding',
    'Kitting Factory': 'Kitting Factory', 'FOD': 'FOD', 'Autre': 'Other', 'Non classé': 'Not classified',
    'Inversion': 'Swapped wires', 'Mauvaise Borne': 'Wrong terminal', 'Non Connecté': 'Not connected',
    'Frettage Incorrect': 'Incorrect lacing', 'Serrage Incorrect': 'Incorrect tightening', 'Mauvais Cheminement': 'Incorrect routing',
    'MEO Gainage': 'Sleeving workmanship', 'Finition Inachevée': 'Incomplete finishing',
    'Défaut de Sertissage sur câble standard': 'Crimping defect, standard cable', 'Défaut de Sertissage sur câble spécifique': 'Crimping defect, special cable',
    'Erreur Fixation ou Protection': 'Wrong fastener or protection', 'Erreur Composant Électrique': 'Wrong electrical component',
    'Fixation ou Protection Manquante': 'Missing fastener or protection', 'Obturateur Manquant': 'Missing blanking plug',
    'Câble ou Élément Manquant': 'Missing cable or item', 'Identification Manquante': 'Missing identification',
    'Câble Endommagé': 'Damaged cable', 'Composant Endommagé': 'Damaged component', 'Protection Endommagée': 'Damaged protection',
    'Structure Endommagée': 'Damaged structure', 'Défaut de Métallisation': 'Bonding defect', "Défaut d'Impression": 'Printing defect',
    'Erreur Dossier': 'Documentation error'
  };
    var WHERE_FR = { 'Final inspection': 'Contrôle final', 'In-process (internal)': 'Interne', 'Cables': 'Câbles', 'Supplier': 'Fournisseur',
    'Customer return': 'Retour client', 'Design query request': 'Demande de DQN', 'Damage': 'Dommages', 'Breakage': 'Casse', 'Not recorded': 'Non renseigné',
    'TEST': 'Test', 'NC Retour client': 'Retour client', 'NC Interne': 'Interne', 'QUALITE': 'Qualité', 'NC Fournisseur': 'Fournisseur' };
    var WHERE_EN = { 'TEST': 'Test', 'In-process (internal)': 'Internal', 'NC Retour client': 'Customer return', 'NC Interne': 'Internal', 'QUALITE': 'Quality', 'NC Fournisseur': 'Supplier' };
    var CB_EN = { 'Câble court': 'Short cable', 'Câble abimé': 'Damaged cable', 'Câble manquant': 'Missing cable', 'Câble coupé': 'Cut cable',
    'Câble non conforme': 'Non-conforming cable', 'Rail abimé': 'Damaged rail', 'Production ligne': 'Production line', 'Impression – machine': 'Printing – machine',
    'Impression – opérateur': 'Printing – operator', 'Définition (BE / ME)': 'Definition (design office / ME)', 'Autre / non renseigné': 'Other / blank',
    'Inconnu – à analyser': 'Unknown – to analyse', 'Coupé en production (geste à préciser)': 'Cut in production (how not stated)', 'Mauvais cheminement': 'Wrong routing',
    'Mauvaise mise en œuvre (sertissage, buscan…)': 'Poor installation (crimping, buscan…)', 'Oubli dans le lot': 'Left out of the batch', 'Mauvaise jauge / type': 'Wrong gauge / type',
    'Longueur machine (réglage / isolant)': 'Machine length (setting / insulation)', 'Marquage laser absent ou illisible': 'Laser marking missing or unreadable',
    'Longueur trop courte à la def': 'Too short in the drawing', 'Mauvais numéro': 'Wrong number', 'Pincé / écrasé': 'Pinched / crushed',
    'Défaut isolant (bobine)': 'Insulation defect (reel)', 'Entaillé / isolant abîmé': 'Nicked / insulation damaged', 'Coupe à la main': 'Cut by hand' };
    var TYPE_ALIAS = { 'NC Interne': 'INTERNE', 'NC Retour client': 'RETOUR CLIENT', 'CLIENT': 'RETOUR CLIENT' };
    var CAT_ORDER = ['MEO Facteur humain', 'Erreur Branchement', 'Élément Manquant', 'Élément Endommagé', 'Déverrouillage', 'Grounding/Bonding', 'Kitting Factory', 'FOD', 'Autre', 'Non classé'];
    var ASIDE = { 'Non classé': 1, '__none': 1 };
    var MAIN_CATS = CAT_ORDER.filter(function (c) { return !ASIDE[c]; }).concat(['aside']);
    var CONN_LINES = { A330: 1, A350: 1 };
    var V2W = { 7: 0.6, 8: 0.6 };
    var PRESETS = ['ytd', 'm1', 'm3', 'm6', 'm12', 'all', 'custom'];
    var AL = { db: null, uid: null, marks: {}, sigK: '', res: null, first: 0, last: -1, open: false, more: false };
    var LINES = lineOrder(REP.map(function (n) { return n[3]; }));
  var RCA_CAT = {}, CODE_CAT = {};
  (function () { var a = {}, b = {}; D.defects.forEach(function (r) { var c = catKey(dCat(r)), x = dRca(r), y = dCode(r);
      if (x) (a[x] || (a[x] = {}))[c] = (a[x][c] || 0) + 1; if (y) (b[y] || (b[y] = {}))[c] = (b[y][c] || 0) + 1; });
    [[a, RCA_CAT], [b, CODE_CAT]].forEach(function (p) { Object.keys(p[0]).forEach(function (k) { var o = p[0][k]; p[1][k] = Object.keys(o).sort(function (u, v) { return o[v] - o[u]; })[0]; }); }); })();
function S(k, v) { var s = STR[G.lang][k]; if (s == null) return k; Object.keys(v || {}).forEach(function (x) { s = s.split('{' + x + '}').join(v[x]); }); return s; }
function L(n) { return G.lang === 'en' && EN[n] ? EN[n] : n; }
function tidy(s) { return String(s || '').replace(/\s*\*\s*/g, ' ').replace(/\s+([,.;:)])/g, '$1').replace(/\(\s+/g, '(').replace(/\s+/g, ' ').replace(/^[\s:–-]+/, '').trim(); }
function whereName(w) { return G.lang === 'fr' ? (WHERE_FR[w] || w) : (WHERE_EN[w] || w); }
function lineOrder(vals) { return ['A350', 'A330', 'A320', 'A400M', 'Autre'].filter(function (c) { return vals.indexOf(c) >= 0; }); }
function dCat(r) { return r[11]; }
function dRca(r) { return r[12]; }
function dSub(r) { return r[13]; }
function dMinor(r) { return r[14]; }
function dCable(r) { return r[15]; }
function dAlloc(r) { return r[17]; }
function keepMinor(r) { return G.minor || !dMinor(r); }
function dCode(r) { return r[22] || ''; }
function dFin(r) { return r[23] || ''; }
function codeDesc(c) { var x = D.codes[c]; return x ? x[G.lang === 'fr' ? 1 : 0] : ''; }
function codeName(c) { var x = codeDesc(c); return x ? c + ' · ' + x : c; }
function plusDays(iso, k) { var d = new Date(iso + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + k); return isoDay(d); }
function minusMonths(iso, k) { var d = new Date(iso + 'T12:00:00Z'), dd = d.getUTCDate(); d.setUTCDate(1); d.setUTCMonth(d.getUTCMonth() - k); d.setUTCDate(Math.min(dd, new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0)).getUTCDate())); return isoDay(d); }
function presetRange(p) {
    var k = { m1: 1, m3: 3, m6: 6, m12: 12 }[p];
    if (p === 'ytd') return [DMAX.slice(0, 4) + '-01-01', DMAX];
    if (k) return [plusDays(minusMonths(DMAX, k), 1), DMAX];
    return [DMIN, DMAX];
  }
function gNc(n, anyLine) {
    if (!n) return false;
    if (GF.src !== 'all' && (GF.src === 'man' ? n[39] === 'sky' : n[39] !== GF.src)) return false;
    if (GF.org && (n[41] || 'normal') !== GF.org) return false;   // [41] the pipeline output the NC comes from: normal or missing_ids
    if (GF.pick && !pickNc(n)) return false;
    if (GF.phase && n[24] !== GF.phase) return false;
    if (GF.line && !anyLine && n[3] !== GF.line) return false;
    return n[1] >= GF.from && n[1] <= GF.to;
  }
function ours(n) { var p = String(n[42] || '').trim().toUpperCase(); return p === 'FTO2' || p === 'FT02'; }
function gScope(n) { return !GF.fto2 || ours(n); }
function ids(a) { var o = {}; a.forEach(function (n) { o[n[0]] = 1; }); return o; }
function select() {
    if (GF.preset !== 'custom') { var r = presetRange(GF.preset); GF.from = r[0]; GF.to = r[1]; }
    SEL_NC = REP.filter(function (n) { return gNc(n) && gScope(n); });
    SER_NC = SEL_NC.filter(function (n) { return ours(n) && n[23] !== 'client'; });   // FTO2's, without the customer returns (shown apart, never counted twice)
    CLI_NC = REP.filter(function (n) { return n[23] === 'client' && gNc(n); });
    SEL = ids(SEL_NC); SER = ids(SER_NC); CLI = ids(CLI_NC);
  }
function isoDay(dt) { return dt.toISOString().slice(0, 10); }
function ncType(n) { var t = String(n[33] || '').trim(); return TYPE_ALIAS[t] || t; }
function prodName(p) { return p === 'Other' ? S('prodUnknown') : p; }
function cbLab(v) { return G.lang === 'en' && CB_EN[v] ? CB_EN[v] : v; }
function catKey(c) { return ASIDE[c] ? 'aside' : c; }
function pSrc() { return PR.src === 'real' && D.eqmsn ? D.eqmsn : DM && DM.eqmsn ? DM.eqmsn : null; }
function sumA(a) { return a.reduce(function (s, v) { return s + v; }, 0); }
function pData() {
    var E = pSrc(), real = E === D.eqmsn, P = { real: real, E: E, months: E.months, fc: E.months.indexOf(E.forecastFrom), prod: E[PR.ver] || E.std, line: E.line, ncs: [], defs: [], cli: [], miss: {}, total: 0, idx: {} };
    if (P.fc < 0) P.fc = P.months.length;
    P.part = P.months.map(function () { return 1; });
    var L = real ? P.months.indexOf(D.meta.to.slice(0, 7)) : -1;
    if (L >= P.fc) { var dm = new Date(Date.UTC(+D.meta.to.slice(0, 4), +D.meta.to.slice(5, 7), 0)).getUTCDate(); P.part[L] = Math.min(1, +D.meta.to.slice(8, 10) / dm); P.fc = L + 1; P.cur = L; }
    P.all = Object.keys(P.prod).sort(function (a, b) { return sumA(P.prod[b]) - sumA(P.prod[a]); });
    var cnt = {}; (real ? REP.map(function (n) { return E.map[String(n[26] || '').toUpperCase()]; }) : GN.map(function (n) { return n[5]; })).forEach(function (p) { if (p) cnt[p] = (cnt[p] || 0) + 1; });
    PCOL = {}; P.all.slice().sort(function (a, b) { return (cnt[b] || 0) - (cnt[a] || 0) || sumA(P.prod[b]) - sumA(P.prod[a]); }).forEach(function (p, i) { PCOL[p] = i < 6 ? 'var(--c' + (i + 1) + ')' : 'var(--dim)'; });
    P.prods = P.all.filter(function (p) { return !real || !GF.line || P.line[p] === GF.line; });
    P.mask = P.months.map(function (m, i) { return i < P.fc && (!real || (m + '-31' >= GF.from && m + '-01' <= GF.to)); });
    function month(d) { var i = P.months.indexOf(d.slice(0, 7)); return i >= 0 && P.mask[i] ? i : -1; }
    if (real) {
      SEL_NC.forEach(function (n) {
        P.total++; var p = E.map[String(n[26] || '').toUpperCase()], m = month(n[1]);
        if (!p || P.prods.indexOf(p) < 0) { var lb = n[26] || '—'; P.miss[lb] = (P.miss[lb] || 0) + 1; return; }
        if (m < 0) return; P.idx[n[0]] = P.ncs.length; P.ncs.push({ id: n[0], m: m, p: p, cost: n[12], days: n[29], late: n[8] === 'Final inspection' || n[8] === 'TEST' });
      });
      D.defects.forEach(function (r) { var i = P.idx[r[0]]; if (i != null && keepMinor(r)) P.defs.push({ n: i, cat: dCat(r), rca: dRca(r), cost: dAlloc(r), cable: !!dCable(r) }); });
      CLI_NC.forEach(function (n) { var p = E.map[String(n[26] || '').toUpperCase()], m = month(n[1]); if (p && P.prods.indexOf(p) >= 0 && m >= 0) P.cli.push({ p: p, m: m }); });
    } else {
      GN.forEach(function (n, i) { P.total++; var m = month(n[1]); if (m < 0) return; P.idx[i] = P.ncs.length; P.ncs.push({ id: n[0], m: m, p: n[5], cost: gCost(n), days: n[8], late: n[9] === 'cf' || n[9] === 'test' }); if (n[9] === 'client') P.cli.push({ p: n[5], m: m }); });
      GD.forEach(function (d, j) { var i = P.idx[d[0]]; if (i != null) P.defs.push({ n: i, cat: d[1], rca: d[2], cost: GALLOC[j], cable: !!CABLE_RCA[d[2]] }); });
    }
    return P;
  }
function pAgg(P) {
    var z = function () { return P.months.map(function () { return 0; }); }, a = {};
    P.prods.forEach(function (p) { a[p] = { p: p, line: P.line[p] || '', eqm: P.prod[p].map(function (v, i) { return P.mask[i] ? v * P.part[i] : 0; }), nc: z(), def: z(), cost: z(), cab: z(), cli: z(), late: z(), connm: z(), conn: {}, cats: {}, catm: {}, rcas: {}, days: [] }; });
    P.ncs.forEach(function (x) { var o = a[x.p]; o.nc[x.m]++; o.cost[x.m] += x.cost; if (x.late) o.late[x.m]++; if (x.days != null) o.days.push(x.days); });
    P.defs.forEach(function (d) { var x = P.ncs[d.n], o = a[x.p]; o.def[x.m]++; if (d.cable) o.cab[x.m]++; if (d.cat === 'Erreur Branchement') { o.conn[d.rca] = (o.conn[d.rca] || 0) + 1; o.connm[x.m]++; } var c = catKey(d.cat); o.cats[c] = (o.cats[c] || 0) + 1; (o.catm[c] || (o.catm[c] = z()))[x.m]++; o.rcas[d.rca] = (o.rcas[d.rca] || 0) + 1; });
    P.cli.forEach(function (x) { a[x.p].cli[x.m]++; });
    P.prods.forEach(function (p) { var o = a[p]; o.EQ = sumA(o.eqm); o.NC = sumA(o.nc); o.DEF = sumA(o.def); o.COST = sumA(o.cost); o.CAB = sumA(o.cab); o.CLI = sumA(o.cli); o.LATE = sumA(o.late); o.r = o.EQ ? o.NC / o.EQ : null;
      o.FC = sumA(P.prod[p].slice(P.fc)) + (P.cur != null ? P.prod[p][P.cur] * (1 - P.part[P.cur]) : 0); });   // to come: the rest of the running month, then the months after
    return a;
  }
function pOk() { return P_().filter(function (o) { return o.EQ >= 0.5; }); }
function pAct() { return PD.months.map(function (m, i) { return i; }).filter(function (i) { return PD.mask[i]; }); }
function P_() { return PD.prods.map(function (p) { return PA[p]; }); }
function pMonthly(f, keep) { var os = P_().filter(keep || function () { return true; }); return pAct().map(function (i) { var e = sumA(os.map(function (o) { return o.eqm[i]; })); return { i: i, e: e, v: sumA(os.map(function (o) { return f(o, i); })) }; }).filter(function (x) { return x.e >= 0.5; }); }
function connOk(o) { return !!CONN_LINES[o.line]; }
function v2Months() {
    var a = [], d = new Date(GF.from.slice(0, 7) + '-01T00:00:00Z'), end = (GF.to < D.meta.to ? GF.to : D.meta.to).slice(0, 7), fc = [];
    while (d.toISOString().slice(0, 7) <= end) { a.push(d.toISOString().slice(0, 7)); d.setUTCMonth(d.getUTCMonth() + 1); }
    if (GF.to >= D.meta.to) { var y = end.slice(0, 4); d = new Date(end + '-01T00:00:00Z'); d.setUTCMonth(d.getUTCMonth() + 1); while (d.toISOString().slice(0, 4) === y) { fc.push(d.toISOString().slice(0, 7)); d.setUTCMonth(d.getUTCMonth() + 1); } }
    return { act: a, fc: fc };
  }
function v2Plan(m) { if (!PD) return null; var i = PD.months.indexOf(m); return i < 0 ? null : sumA(PD.prods.map(function (p) { return PD.prod[p][i] || 0; })); }
function v2Fc(f, M) {
    var E = pSrc(); if (!PD || !PA || !E || E !== D.eqmsn) return null;
    var byP = {}, out = 0, w = function (m) { return V2W[+m.slice(5, 7)] || 1; }, K = v2OutK(M), C = K.cur;
    SEL_NC.forEach(function (n) { var v = f(n), p = v2InPlan(n); if (p) byP[p] = (byP[p] || 0) + v; else out += v; });
    var pace = K.a ? out / K.a : 0, res = {}, per = function (i, sh) { return sumA(Object.keys(byP).map(function (p) { return i < 0 ? 0 : byP[p] / PA[p].EQ * (PD.prod[p][i] || 0) * sh; })); };
    M.fc.forEach(function (m) { res[m] = per(PD.months.indexOf(m), 1) + pace * w(m); });
    if (C) res[M.fc[0]] += per(C.i, 1 - C.part) + pace * w(C.m) * (1 - C.part);   // the rest of the running month, with the first month to come
    return { m: res, out: out, outFc: pace * K.f };
  }
function v2InPlan(n) { var E = pSrc(), p = E && E.map && E.map[String(n[26] || '').toUpperCase()]; return p && PA && PA[p] && PA[p].EQ >= 0.5 && PD.idx[n[0]] != null ? p : null; }
function v2OutK(M) {
    var w = function (m) { return V2W[+m.slice(5, 7)] || 1; }, C = PD && PD.cur != null && M.fc.length && M.act[M.act.length - 1] === PD.months[PD.cur] ? { m: PD.months[PD.cur], i: PD.cur, part: PD.part[PD.cur] } : null;
    var a = sumA(M.act.map(w)) - (C ? w(C.m) * (1 - C.part) : 0), f = sumA(M.fc.map(w)) + (C ? w(C.m) * (1 - C.part) : 0);
    return { a: a, f: f, k: a ? f / a : 0, cur: C };
  }
function v2Series(f) {
    var M = v2Months(), by = {}; SEL_NC.forEach(function (n) { var m = n[1].slice(0, 7); by[m] = (by[m] || 0) + f(n); });
    var act = M.act.map(function (m) { return { m: m, v: by[m] || 0 }; }), pa = 0, va = 0;
    act.forEach(function (x) { var p = v2Plan(x.m); if (p) { pa += p; va += x.v; } });
    var l3 = act.slice(-3), m3 = l3.length ? sumA(l3.map(function (x) { return x.v; })) / l3.length : 0;
    var F = v2Fc(f, M), fc = M.fc.map(function (m) { var p = v2Plan(m); return { m: m, v: F ? F.m[m] : pa && p != null ? va / pa * p : m3, f: true }; });
    return { act: act, fc: fc, tot: sumA(act.map(function (x) { return x.v; })), ftot: sumA(fc.map(function (x) { return x.v; })) };
  }
function y25Sel() {
    var Y = D.y25; if (!Y || !Y.rows || GF.src !== 'all' || GF.org === 'missing_ids') return null;
    var c = {}, P = GF.pick; Y.cols.forEach(function (k, i) { c[k] = i; });
    if (P && ['month', 'prod', 'pprod'].indexOf(P.k) < 0) return null;   // a pick the 2025 extract cannot follow: no 2025 comparison
    var pOk = !P ? null : P.k === 'month' ? function (r) { return String(r[c.month]).slice(5, 7) === P.v.slice(5, 7); } : P.k === 'prod' ? function (r) { return (r[c.product] || 'Other') === P.v; } :
      function (r) { return !!(D.eqmsn && D.eqmsn.map && D.eqmsn.map[String(r[c.product] || '').toUpperCase()] === P.v); };
    return Y.rows.filter(function (r) { return (r[c.scope] === 'serie' || !GF.fto2) && (!GF.phase || r[c.phase] === GF.phase) && (!GF.line || r[c.line] === GF.line) && (!pOk || pOk(r)); })
      .map(function (r) { return { m: r[c.month], line: r[c.line], p: r[c.product], nc: r[c.nc], def: G.minor ? r[c.def] : r[c.defMajor], cost: r[c.cost] }; });
  }
function y25Cum(Y, f, months) { var by = {}, c = 0; Y.forEach(function (x) { var k = x.m.slice(5, 7); by[k] = (by[k] || 0) + f(x); }); return [0].concat(months.map(function (m) { c += by[m.slice(5, 7)] || 0; return c; })); }
function y25Lines() {
    var Y = y25Sel(), L = D.y25 && D.y25.prod, E = pSrc(); if (!Y || !L || !PD || E !== D.eqmsn) return null;
    var out = {}, has = function (p) { return L[p] && sumA(L[p]) > 0 && PD.prods.indexOf(p) >= 0; };
    PD.prods.forEach(function (p) { if (!has(p)) return; var l = PD.line[p] || '—', a = out[l] || (out[l] = { nc: 0, eq: 0 }); a.eq += sumA(L[p]); });
    Y.forEach(function (x) { var p = E.map[String(x.p || '').toUpperCase()]; if (p && has(p) && out[PD.line[p] || '—']) out[PD.line[p] || '—'].nc += x.nc; });
    return out;
  }
function y25Rca() {
    var Y = D.y25; if (!Y || !Y.rca || GF.src !== 'all' || GF.org === 'missing_ids') return null;
    var c = {}, P = GF.pick; Y.rcaCols.forEach(function (k, i) { c[k] = i; });
    if (P && ['month', 'prod', 'pprod', 'cat', 'rca'].indexOf(P.k) < 0) return null;
    var ok = !P ? null : P.k === 'month' ? function (r) { return String(r[c.month]).slice(5, 7) === P.v.slice(5, 7); } : P.k === 'prod' ? function (r) { return (r[c.product] || 'Other') === P.v; } :
      P.k === 'cat' ? function (r) { return r[c.cat] === P.v; } : P.k === 'rca' ? function (r) { return r[c.rca] === P.v; } :
      function (r) { return !!(D.eqmsn && D.eqmsn.map && D.eqmsn.map[String(r[c.product] || '').toUpperCase()] === P.v); };
    return Y.rca.filter(function (r) { return (r[c.scope] === 'serie' || !GF.fto2) && (!GF.phase || r[c.phase] === GF.phase) && (!GF.line || r[c.line] === GF.line) && (!ok || ok(r)); })
      .map(function (r) { return { m: r[c.month], p: r[c.product], cat: r[c.cat], rca: r[c.rca], d: G.minor ? r[c.def] : r[c.defMajor] }; });
  }
function y25Rate(rows, f, keep) {   // keep(p): only these products of the plan (connection errors: A330 and A350)
    var L = D.y25 && D.y25.prod, E = pSrc(); if (!rows || !L || !PD || E !== D.eqmsn) return null;
    var has = function (p) { return L[p] && sumA(L[p]) > 0 && PD.prods.indexOf(p) >= 0 && (!keep || keep(p)); }, del = 0, v = 0;
    PD.prods.forEach(function (p) { if (has(p)) del += sumA(L[p]); });
    rows.forEach(function (x) { var p = E.map[String(x.p || '').toUpperCase()]; if (p && has(p)) v += f(x); });
    return del > 0 ? { v: v, del: del, r: v / del } : null;
  }
function v2Tgt(f25, f26) {
    var Y = y25Sel(), L = D.y25 && D.y25.prod, E = pSrc(); if (!Y || !L || !PD || !PA || E !== D.eqmsn) return null;
    var has = function (p) { return L[p] && sumA(L[p]) > 0; }, by = {}, out = 0, z = function () { return PD.months.map(function () { return 0; }); };
    // a product with no 2025 delivery (MDCD) does not take its line's 2025 rate: its target is its own 2026 pace × its planned
    // volume, with no cut (Mohammad, 29 Oct); its 2025 NCs show in the 2025 bar only
    PD.prods.forEach(function (p) { var l = PD.line[p] || '—', a = by[l] || (by[l] = { l: l, v25: 0, n25o: 0, del: 0, vol: z(), own: z(), v26: 0, eq26: 0 });
      if (has(p)) { a.del += sumA(L[p]); PD.prod[p].forEach(function (v, i) { a.vol[i] += v || 0; }); a.v26 += f26(PA[p]); a.eq26 += PA[p].EQ; }
      else { var r = PA[p] && PA[p].EQ > 0 ? f26(PA[p]) / PA[p].EQ : 0; PD.prod[p].forEach(function (v, i) { a.own[i] += r * (v || 0); }); } });
    Y.forEach(function (x) { var p = E.map[String(x.p || '').toUpperCase()], a = p && has(p) && by[PD.line[p] || '—'];
      if (a) { a.v25 += f25(x); return; }
      if (p && by[PD.line[p] || '—']) { by[PD.line[p] || '—'].n25o += f25(x); return; }   // in the plan, not delivered in 2025
      out += f25(x);   // out of the plan: kept with its plane type (x25), for the bars by plane type
      var l = x.line || '—', b = by[l] || (by[l] = { l: l, v25: 0, del: 0, vol: z(), v26: 0, eq26: 0, noPlan: true }); b.x25 = (b.x25 || 0) + f25(x); });
    var lines = lineOrder(Object.keys(by)).map(function (l) { var a = by[l]; a.r25 = a.del > 0 && a.v25 > 0 ? a.v25 / a.del : null; a.x25 = a.x25 || 0; a.xT = a.x25 * V2CUT;
      a.rt = (a.r25 != null ? a.r25 : a.eq26 ? a.v26 / a.eq26 : 0) * V2CUT; a.ph = a.r25 == null && !a.noPlan && sumA(a.vol) > 0; a.own = a.own || z(); a.n25o = a.n25o || 0; a.year = a.rt * sumA(a.vol) + sumA(a.own); return a; });   // no 2025 for a line: its 2026 rate - 25 %
    var wsum = 0; for (var mm = 1; mm <= 12; mm++) wsum += V2W[mm] || 1;
    return { lines: lines, out25: out, outT: out * V2CUT,
      tm: function (m) { var i = PD.months.indexOf(m); return sumA(lines.map(function (a) { return i < 0 ? 0 : a.rt * a.vol[i] + a.own[i]; })) + out * V2CUT * (V2W[+m.slice(5, 7)] || 1) / wsum; },
      year: sumA(lines.map(function (a) { return a.year; })) + out * V2CUT };
  }
function alNc(n) { return ours(n) && n[23] !== 'client' && (!GF.phase || n[24] === GF.phase) && (GF.src === 'all' || (GF.src === 'man' ? n[39] !== 'sky' : n[39] === GF.src)) && (!GF.org || (n[41] || 'normal') === GF.org); }
function alCompute(at) {   // at: a week index instead of the period's end (checks)
    var E = D.eqmsn && D.eqmsn.wdw; if (!E) return null;
    var last = at != null ? at : ALARM.lastDone(GF.to < D.meta.to ? GF.to : D.meta.to), k = [GF.phase, GF.src, GF.org, last, G.lang].join('|');
    if (k === AL.sigK) return AL.res;
    var items = {}, planes = {}, cnt = { rca: {}, code: {} }, z = function () { var a = []; for (var i = 0; i < 53; i++) a.push(0); return a; }, w0 = 53, PM = D.eqmsn.msn || {};
    function it(line, lv, v, e, hist) { var key = line + '|' + lv + '|' + v; return items[key] || (items[key] = { key: key, line: line, lv: lv, v: v, w: z(), e: e, n: [], d: [], hist: !!hist }); }
    function add(o, i, id, dk) { o.w[i]++; (o.n[i] || (o.n[i] = [])).push(id); if (dk) (o.d[i] || (o.d[i] = [])).push(dk); if (i < w0) w0 = i; }
    function tally(m, k2, v) { var q = m[k2] || (m[k2] = {}); q[v] = (q[v] || 0) + 1; }
    D.defects.forEach(function (r) {
      var n = NC[r[0]]; if (!n || !alNc(n)) return;
      var l = n[3], e = E.line[l], i = ALARM.week(n[1]), dk = r[0] + '|' + r[1]; if (!e || i < 0) return;
      var c = dCat(r), ca = dRca(r), co = dCode(r);
      add(it(l, 'all', '', e), i, n[0], dk);
      if (c) add(it(l, 'cat', c, e), i, n[0], dk);
      if (ca) { add(it(l, 'rca', ca, e), i, n[0], dk); tally(cnt.rca, l + '|' + ca, c); }
      if (co) { add(it(l, 'code', co, e), i, n[0], dk); tally(cnt.code, l + '|' + co, ca); }
      if (n[27]) add(it(l, 'station', n[27], e, true), i, n[0], dk);
      if (n[8]) add(it(l, 'where', n[8], e, true), i, n[0], dk);
    });
    D.ncs.forEach(function (n) {   // products: NCs per MSN of the product; aircraft: NCs per aircraft and product
      if (!alNc(n) || !E.prod || !D.eqmsn.map) return;
      var p = D.eqmsn.map[String(n[26] || '').toUpperCase()], i = ALARM.week(n[1]); if (!p || i < 0) return;
      if (E.prod[p]) add(it(n[3], 'prod', p, E.prod[p]), i, n[0]);
      var m = String(n[25] || ''), pm = PM[n[3] + '|' + m.replace(/^0+/, '')]; if (!m || !pm) return;
      var pk2 = n[3] + '|' + m + '|' + p, o = planes[pk2], end = ALARM.week(pm[1]);
      if (!o) o = planes[pk2] = { key: pk2, line: n[3], msn: m, prod: p, w: z(), n: [], end: end < 0 ? 99 : end };
      o.w[i]++; (o.n[i] || (o.n[i] = [])).push(n[0]);
    });
    (D.cables || []).forEach(function (a) {   // cable requests per MSN of the line
      var l = a[4] === 'A321' ? 'A320' : a[4], e = E.line[l], i = ALARM.week(a[2]); if (!e || i < 0) return;
      add(it(l, 'cimp', a[7], e), i, a[3]); add(it(l, 'cmot', a[6], e), i, a[3]);
    });
    // the actions in progress (MFT trackers): the NCs of their problem, to say that one already covers an alarm
    var AF = { cat: dCat, rca: dRca, sub: dSub, code: dCode }, acts = (D.actions || []).filter(function (a) { return a[6] && !/CLOS|TERMIN|ABANDON/i.test(a[7] || ''); }).map(function (a) {
      var vals = {}, o = { line: a[0], title: a[G.lang === 'fr' ? 1 : 2], start: ALARM.week(a[6] + '-01'), defs: {} };
      (a[4] || []).forEach(function (v) { vals[v] = 1; });
      D.defects.forEach(function (r) { var n = NC[r[0]]; if (!n || n[3] !== a[0] || !alNc(n)) return; var v = a[3] === 'where' ? n[8] : AF[a[3]] ? AF[a[3]](r) : null; if (v != null && vals[v]) o.defs[r[0] + '|' + r[1]] = 1; });
      return o;
    });
    var dom = function (m) { m = m || {}; return Object.keys(m).sort(function (a, b) { return m[b] - m[a]; })[0] || ''; };
    var first = w0 + ALARM.P.recent + ALARM.P.base - 1;
    AL.first = first; AL.last = last; AL.sigK = k;
    AL.res = last < first ? [] : ALARM.run(Object.keys(items).map(function (x) { return items[x]; }), first, last, function (a) {
      return a.lv === 'cat' ? a.line + '|all|' : a.lv === 'rca' ? a.line + '|cat|' + dom(cnt.rca[a.line + '|' + a.v]) : a.lv === 'code' ? a.line + '|rca|' + dom(cnt.code[a.line + '|' + a.v]) : ''; },
      Object.keys(planes).map(function (x) { return planes[x]; }), acts);
    return AL.res;
  }
function alName(a) {
    var v = a.v, cd = a.lv === 'code' ? codeDesc(v).split(' (')[0] : '';
    var s = a.lv === 'all' ? S('alAll') : a.lv === 'cat' || a.lv === 'rca' ? L(v) : a.lv === 'code' ? v + (cd ? ' · ' + cd : '') : a.lv === 'where' ? whereName(v) :
      a.lv === 'station' ? S('alSt', { v: v }) : a.lv === 'prod' ? prodName(v) : a.lv === 'cimp' || a.lv === 'cmot' ? S('alCab', { v: cbLab(v) }) : v;
    return s + (a.child ? ' (' + (a.lv === 'cat' ? L(a.child) : a.child) + ')' : '');
  }
function alText(g) {
    var a = g.head, s = alWk(g.since);
    if (g.kind === 'plane') return S('alPlane', { m: a.v, n: a.n, p: a.prod, d: a.med });
    return S(g.kind === 'cross' ? 'alCross' : g.kind === 'creep' ? 'alCreep' : 'alUp', { w: alName(a), s: s });
  }
function alWk(i) { return S('alWk', { n: i + 1 }); }
/* ===== ALARM ENGINE START ===== */
  // Alarms (Mohammad, 30 Oct): the bell lists what to look at, few lines, nothing raised by a single bad week. One rule for the
  // dashboard and the MFT page (build_mft.py copies this block into the MFT page). Four ways something goes wrong, each tested on
  // 2026 against a year where nothing changes:
  //  - rise ("en hausse"): an item of a line (all its defects, a category, a cause, a sub-code, a station, where they are found, a
  //    product, a cable imputation or reason), last 4 finished weeks against the 12 before, per MSN built (working days), binomial
  //    test read in σ. Minor 2.5 σ and still 1.5 σ with the biggest week set aside; major 3 σ, still 2 σ without it and 10 more
  //    defects than usual over the 4 weeks, also without it. Open until 4 weeks under 1 σ, off the list once back under 1 σ;
  //  - several lines ("sur A350 + A330"): a category or cause rising on two lines or more at once, each below the bar on its own
  //    and none carrying 70 % of the rise (a cause they share: a machine, a supplier, a training). 2026: printing defects in
  //    week 39; chance: about 0.2 in 23 weeks;
  //  - slow creep ("en hausse lente"): three blocks of 8 weeks, each 10 % above the one before, the last 3 σ above the first and
  //    still 2 σ without its biggest week, with no rise alarm on it in those last 8 weeks (the weekly view hides it). 2026: A330
  //    Structure Endommagée; chance: about 0.3 in 23 weeks;
  //  - an aircraft far above its siblings: its NCs above both 2.5 times the median and the 90th percentile + 3 of the finished
  //    aircraft of its product, while it still gets NCs. 2026: MSN 851 (14 NCs, a MIP usually ends with 5).
  // Tried and left out: a FIN coming back on several aircraft (as frequent in 2026 as in shuffled data: chance), a new sub-code on
  // 2 aircraft (mostly one-week bursts). Then one line per problem: a sub-code with the same weeks as its cause shows with it
  // ("Inversion (T04)"), a parent gives way to the child carrying 60 % of its rise, stations / places / products / cables join the
  // problem sharing more than half of their NCs; a problem an action covers says so. Weeks: 0 = ISO week 1 of 2026.
  var ALARM = (function () {
    var P = { recent: 4, base: 12, zMin: 2.5, gMin: 1.5, zMaj: 3, gMaj: 2, exMaj: 10, quiet: 4, minX: 3, hist: 3, share: 0.5,
      crossCarry: 0.7, block: 8, step: 1.1, creepZ: 3, creepG: 2, planeK: 2.5, planePlus: 3, planeMin: 6, show: 5 };
    var LF = [0];
    function lf(n) { for (var i = LF.length; i <= n; i++) LF[i] = LF[i - 1] + Math.log(i); return LF[n]; }
    function tail(x, n, p) {   // P(K >= x) for K binomial (n, p)
      if (x <= 0 || p >= 1) return 1;
      if (p <= 0 || x > n) return 0;
      var lp = Math.log(p), lq = Math.log(1 - p), t = [], m = -Infinity, s = 0, k, v;
      for (k = x; k <= n; k++) { v = lf(n) - lf(k) - lf(n - k) + k * lp + (n - k) * lq; t.push(v); if (v > m) m = v; }
      for (k = 0; k < t.length; k++) s += Math.exp(t[k] - m);
      return Math.min(1, Math.exp(m) * s);
    }
    function invN(p) {   // inverse of the standard normal distribution (Acklam)
      var a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269, -30.66479806614716, 2.506628277459239],
        b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572],
        c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783],
        d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416], q, r;
      if (p < 0.02425) { q = Math.sqrt(-2 * Math.log(p)); return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
      if (p > 1 - 0.02425) { q = Math.sqrt(-2 * Math.log(1 - p)); return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
      q = p - 0.5; r = q * q; return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
    }
    function sig(x, er, b, eb) {   // how many σ x events over the exposure er stand above b events over eb (0 under 3 events)
      if (x < P.minX || er <= 0 || eb <= 0) return 0;
      return invN(1 - Math.min(Math.max(tail(x, x + b, er / (er + eb)), 1e-12), 1 - 1e-12));
    }
    function week(iso) {   // '2026-05-14' -> its ISO week, 0 for week 1 of 2026; -1 outside 2026
      var d = new Date(String(iso).slice(0, 10) + 'T00:00:00Z'), dow = (d.getUTCDay() + 6) % 7;
      if (isNaN(d)) return -1;
      d.setUTCDate(d.getUTCDate() - dow + 3);   // the Thursday of the week decides the year
      if (d.getUTCFullYear() !== 2026) return -1;
      return Math.floor((d - Date.UTC(2026, 0, 1)) / 6048e5);   // 1 January 2026 is a Thursday
    }
    function lastDone(iso) {   // the last finished week up to that day: its own week if it is a Sunday, else the week before
      var d = new Date(String(iso).slice(0, 10) + 'T00:00:00Z');
      if (d.getUTCDay() !== 0) d.setUTCDate(d.getUTCDate() - (d.getUTCDay() + 6) % 7 - 1);
      return week(d.toISOString());
    }
    function sum(it, a, b) {   // counts and MSN over weeks a..b, with the biggest week of them
      var o = { x: 0, e: 0, big: 0, bigE: 0 };
      for (var j = Math.max(0, a); j <= b; j++) { var v = it.w[j] || 0; o.x += v; o.e += it.e ? it.e[j] || 0 : 0; if (v > o.big) { o.big = v; o.bigE = it.e ? it.e[j] || 0 : 0; } }
      return o;
    }
    function ids(it, a, b) { var o = {}; for (var j = Math.max(0, a); j <= b; j++) (it.n[j] || []).forEach(function (id) { o[id] = 1; }); return o; }
    // the rise test of one item at week i: {z, zg (without the biggest week), ex (extra over the 4 weeks, without it), lvl}
    function test(it, i) {
      var R = P.recent, B = P.base, r = sum(it, i - R + 1, i), b = sum(it, i - R - B + 1, i - R);
      var zf = sig(r.x, r.e, b.x, b.e), eg = r.e - r.bigE, zg = sig(r.x - r.big, eg, b.x, b.e);
      var ex = b.e > 0 && eg > 0 ? (r.x - r.big - b.x * eg / b.e) * r.e / eg : 0;
      var lvl = it.hist && !(it.f <= i - R - B + 1 && b.x >= P.hist) ? 0 : zf >= P.zMaj && zg >= P.gMaj && ex >= P.exMaj ? 2 : zf >= P.zMin && zg >= P.gMin ? 1 : 0;
      return { z: zf, zg: zg, ex: ex, lvl: lvl, usual: b.e > 0 ? b.x / b.e * r.e / R : 0 };
    }
    // one item week by week, from `first` to `last`: the alarm open at `last` (null if none) and the last week one was open
    function scan(it, first, last) {
      var o = null, seen = -1, ow = [];
      if (it.hist && it.f == null) { it.f = 0; while (it.f < it.w.length && !it.w[it.f]) it.f++; }   // its first week
      for (var i = Math.max(first, P.recent + P.base - 1); i <= last; i++) {
        var t = test(it, i);
        if (o) {
          o.quiet = t.z < 1 ? o.quiet + 1 : 0;
          if (o.quiet >= P.quiet) { o = null; continue; }
          if (t.lvl > o.lvl) o.lvl = t.lvl;
        } else if (t.lvl) o = { lvl: t.lvl, since: i, quiet: 0 };
        if (o) { seen = i; ow[i] = 1; if (i === last) { o.z = t.z; o.zg = t.zg; o.ex = t.ex; o.usual = t.usual; } }
      }
      return { o: o, seen: seen, ow: ow };
    }
    function creepAt(it, i) {   // three 8-week blocks up to week i, each 10 % above the one before, the last well above the first
      var K = P.block, s3 = i - K + 1, s2 = s3 - K, s1 = s2 - K; if (s1 < 0) return null;
      var b1 = sum(it, s1, s2 - 1), b2 = sum(it, s2, s3 - 1), b3 = sum(it, s3, i);
      if (!(b1.e > 0 && b2.e > 0 && b3.e > 0)) return null;
      var r1 = b1.x / b1.e, r2 = b2.x / b2.e, r3 = b3.x / b3.e;
      if (!(r2 > r1 * P.step && r3 > r2 * P.step)) return null;
      var z = sig(b3.x, b3.e, b1.x, b1.e), g = sig(b3.x - b3.big, b3.e - b3.bigE, b1.x, b1.e);
      return z >= P.creepZ && g >= P.creepG ? { since: s2, ref: b1 } : null;
    }
    // the creep week by week: it opens when nothing in its family had an alarm in those 8 weeks (famOpen) and stays while the last
    // 8 weeks are still 1 σ above the block it started from
    function creep(it, first, last, famOpen) {
      var K = P.block, c = null;
      for (var i = Math.max(first, 3 * K - 1); i <= last; i++) {
        var b3 = sum(it, i - K + 1, i);
        if (c) { c.z = sig(b3.x, b3.e, c.ref.x, c.ref.e); if (c.z < 1) c = null; }
        else { var n = creepAt(it, i); if (n && !famOpen(i - K + 1, i)) c = { lvl: 1, since: n.since, ref: n.ref, z: sig(b3.x, b3.e, n.ref.x, n.ref.e) }; }
        if (c && i === last) c.ex = b3.x - c.ref.x / c.ref.e * b3.e;
      }
      return c;
    }
    var RANK = { all: 0, cat: 0, rca: 0, code: 0, where: 1, station: 2, prod: 3, cimp: 4, cmot: 4 };
    function fam(a) { return RANK[a.lv] === 0; }
    // what is wrong at week `last`, one line per problem, the most important first.
    //  items: [{key, line, lv, v, w: [count per week], e: [MSN per week], n: [[NC ids] per week], hist}]; parentOf(item) -> the key of
    //  its parent ('' for none): line|all| <- line|cat|c <- line|rca|r <- line|code|s;
    //  planes: [{key, line, msn, prod, w: [NCs per week], end: week its build ended (99 if not yet), n}];
    //  acts: [{line, title, start: week, defs: {defect key: 1}}], the actions in progress, their problem's defect lines (items carry
    //  theirs per week in d), to say that one covers a problem
    function run(items, first, last, parentOf, planes, acts) {
      var al = [], by = {}, gone = {}, open = {}, sc = {}, kidsOf = {};
      items.forEach(function (it) { sc[it.key] = scan(it, first, last); var p = parentOf(it); if (p) (kidsOf[p] || (kidsOf[p] = [])).push(it.key); });
      var famOpen = function (key) {   // weeks a..b: was an alarm open on the item, its parents or its children?
        var keys = [key], up = function (k) { var it2 = by0[k], p = it2 ? parentOf(it2) : ''; if (p && sc[p]) { keys.push(p); up(p); } },
          down = function (k) { (kidsOf[k] || []).forEach(function (c) { keys.push(c); down(c); }); };
        up(key); down(key);
        return function (a, b) { return keys.some(function (k) { for (var j = a; j <= b; j++) if (sc[k].ow[j]) return true; return false; }); };
      }, by0 = {};
      items.forEach(function (it) { by0[it.key] = it; });
      items.forEach(function (it) {
        var s = sc[it.key], o = s.o;
        if (o) open[it.key] = 1;
        if (o && o.z >= 1) al.push(Object.assign(o, { kind: 'rise', key: it.key, line: it.line, lv: it.lv, v: it.v, it: it, ncs: ids(it, last - P.recent + 1, last) }));
        else if (!o && (it.lv === 'all' || it.lv === 'cat' || it.lv === 'rca')) {
          var c = creep(it, first, last, famOpen(it.key));
          if (c) al.push(Object.assign(c, { kind: 'creep', key: 'C|' + it.key, line: it.line, lv: it.lv, v: it.v, it: it, ncs: ids(it, last - P.block + 1, last) }));
        }
      });
      // several lines: a category or a cause rising on two lines or more at once, none alarming alone
      var grp = {};
      items.forEach(function (it) { if (it.lv === 'cat' || it.lv === 'rca') (grp[it.lv + '|' + it.v] || (grp[it.lv + '|' + it.v] = [])).push(it); });
      Object.keys(grp).forEach(function (k) {
        var its = grp[k]; if (its.length < 2 || its.some(function (it) { return open[it.key]; })) return;
        var pool = { w: [], e: [], n: [] };
        pool.d = [];
        for (var j = 0; j <= last; j++) { pool.w[j] = 0; pool.e[j] = 0; its.forEach(function (it) { pool.w[j] += it.w[j] || 0; pool.e[j] += it.e[j] || 0; if (it.n[j]) pool.n[j] = (pool.n[j] || []).concat(it.n[j]); if (it.d && it.d[j]) pool.d[j] = (pool.d[j] || []).concat(it.d[j]); }); }
        var s = scan(pool, first, last).o; if (!s || s.z < 1) return;
        var up = [], ex = [];
        its.forEach(function (it) { var t = test(it, last); if (t.z >= 1) up.push(it.line); ex.push(Math.max(0, sum(it, last - P.recent + 1, last).x - (t.usual * P.recent))); });
        var tot = ex.reduce(function (a, b) { return a + b; }, 0);
        if (up.length < 2 || Math.max.apply(null, ex) >= P.crossCarry * tot) return;
        al.push(Object.assign(s, { kind: 'cross', key: 'X|' + k, line: up.join(' + '), lines: up, lv: its[0].lv, v: its[0].v, it: pool, ncs: ids(pool, last - P.recent + 1, last) }));
      });
      // one line per problem: the family of a line (and the several-lines alarms among themselves)
      al.forEach(function (a) { by[a.key] = a; });
      var par = function (a) {   // the key of an alarm's parent alarm, of the same kind
        if (a.kind === 'cross') { var q = parentOf({ line: a.lines[0], lv: a.lv, v: a.v }); return q ? 'X|' + q.split('|').slice(1).join('|') : ''; }
        var p = parentOf(a); return a.kind === 'creep' ? (p ? 'C|' + p : '') : p;
      };
      al.forEach(function (a) { var p = by[par(a)]; if (p && sum(p.it, last - P.recent + 1, last).x === sum(a.it, last - P.recent + 1, last).x && p.kind === a.kind) { p.child = a.v; gone[a.key] = 1; } });
      ['all', 'cat', 'rca'].forEach(function (lv) {
        al.forEach(function (a) {
          if (a.lv !== lv || gone[a.key]) return;
          var kids = al.filter(function (b) { return !gone[b.key] && b.kind === a.kind && par(b) === a.key; });
          if (!kids.length) return;
          if (Math.max.apply(null, kids.map(function (b) { return b.ex; })) >= 0.6 * a.ex) gone[a.key] = 1;   // one child carries the rise
          else { a.kids = kids.map(function (b) { return b.v; }); kids.forEach(function (b) { gone[b.key] = 1; if (b.lvl > a.lvl) a.lvl = b.lvl; if (b.since < a.since) a.since = b.since; }); }
        });
      });
      // the other items join the family problem of their line that shares most of their NCs (more than half of the smaller)
      var out = [];
      al.filter(function (a) { return !gone[a.key]; }).sort(function (a, b) { return (fam(b) ? 1 : 0) - (fam(a) ? 1 : 0) || RANK[a.lv] - RANK[b.lv] || b.lvl - a.lvl || b.ex - a.ex; }).forEach(function (a) {
        var idl = Object.keys(a.ncs), best = null, bs = 0;
        if (!fam(a) && a.kind === 'rise') out.forEach(function (g) {
          if (g.line !== a.line) return;
          var n = 0, m = Object.keys(g.head.ncs).length; idl.forEach(function (id) { if (g.head.ncs[id]) n++; });
          var sh = n / Math.max(1, Math.min(idl.length, m)); if (sh > P.share && sh > bs) { best = g; bs = sh; }
        });
        if (best) { best.also.push(a); if (a.lvl > best.lvl) best.lvl = a.lvl; if (a.since < best.since) best.since = a.since; }
        else out.push({ key: a.key, kind: a.kind, line: a.line, head: a, also: [], lvl: a.lvl, since: a.since, ex: a.ex });
      });
      // aircraft far above the finished aircraft of their product, while they still get NCs
      var bp = {};
      (planes || []).forEach(function (p) { (bp[p.prod] || (bp[p.prod] = [])).push(p); });
      Object.keys(bp).forEach(function (prod) {
        var cum = function (p) { var s = 0; for (var j = 0; j <= last; j++) s += p.w[j] || 0; return s; };
        var done = bp[prod].filter(function (p) { return p.end <= last; }).map(cum).sort(function (a, b) { return a - b; });
        if (done.length < P.planeMin) return;
        var med = done[Math.floor(done.length / 2)], q90 = done[Math.floor(0.9 * (done.length - 1))], lim = Math.max(P.planeK * med, q90 + P.planePlus);
        bp[prod].forEach(function (p) {
          var c = cum(p), r = sum(p, last - P.recent + 1, last).x; if (c <= lim || !r) return;
          var s = 0, since = 0; for (var j = 0; j <= last; j++) { s += p.w[j] || 0; if (s > lim) { since = j; break; } }
          out.push({ key: 'M|' + p.key, kind: 'plane', line: p.line, head: { kind: 'plane', lv: 'msn', v: p.msn, prod: prod, n: c, med: med, it: p, ncs: ids(p, 0, last) }, also: [], lvl: 1, since: since, ex: c - med });
        });
      });
      // a problem an action in progress already covers (more than half of its defect lines): the action is named with it
      (acts || []).forEach(function (ac) {
        out.forEach(function (g) {
          var it = g.head.it; if (g.act || !it || !it.d || g.line.split(' + ').indexOf(ac.line) < 0 || ac.start > last) return;
          var k = 0, n = 0; for (var j = last - (g.kind === 'creep' ? P.block : P.recent) + 1; j <= last; j++) (it.d[j] || []).forEach(function (dk) { n++; if (ac.defs[dk]) k++; });
          if (n && k / n > P.share) g.act = ac;
        });
      });
      var KIND = { rise: 0, cross: 1, creep: 2, plane: 3 };
      return out.sort(function (a, b) { return b.lvl - a.lvl || KIND[a.kind] - KIND[b.kind] || b.ex - a.ex; });
    }
    // a problem marked as seen stays out of the list unless it got worse since: a higher level, half again as many extra defects
    // (5 at least), or it closed and opened again
    function seen(g, m) { return !!m && m.since === g.since && g.lvl <= (m.lvl || 0) && !(g.ex >= 1.5 * (m.ex || 0) && g.ex >= (m.ex || 0) + 5); }
    function docId(key) { var h = 5381; for (var i = 0; i < key.length; i++) h = ((h * 33) ^ key.charCodeAt(i)) >>> 0; return 'a' + h.toString(36) + '-' + key.length; }
    // the last 16 weeks of a problem, per MSN built (counts for an aircraft), as a small line: the last 4 weeks stand out
    function spark(g, last, col) {
      var it = g.head.it, W = 56, H = 18, n = 16, pts = [], mx = 0, i, v;
      for (i = last - n + 1; i <= last; i++) { v = it.e ? (it.e[i] > 0 ? (it.w[i] || 0) / it.e[i] : null) : it.w[i] || 0; pts.push(v); if (v != null && v > mx) mx = v; }
      if (!mx) return '';
      var xy = function (k) { return (2 + k / (n - 1) * (W - 4)).toFixed(1) + ',' + (H - 2 - pts[k] / mx * (H - 4)).toFixed(1); }, a = '', b = '';
      for (i = 0; i < n; i++) if (pts[i] != null) { var s = xy(i); if (i <= n - P.recent) a += (a ? 'L' : 'M') + s; if (i >= n - P.recent) b += (b ? 'L' : 'M') + s; }
      return '<svg class="al-sp" width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '" aria-hidden="true"><path d="' + a + '" fill="none" stroke="var(--dim)" stroke-width="1.5"/><path d="' + b + '" fill="none" stroke="' + col + '" stroke-width="2"/></svg>';
    }
    return { P: P, run: run, seen: seen, week: week, lastDone: lastDone, docId: docId, sig: sig, spark: spark };
  })();
  /* ===== ALARM ENGINE END ===== */
    // ================================================================ the views' model, computed for one set of filters
    // Every block below mirrors the computing part of a dashboard chart (named in its comment); the drawing stays in the page.
    // The functions it calls (selection, production plan, forecast, targets, 2025, alarms) are the dashboard's own, copied in
    // unchanged by build/views/build_way2.py, so a rule changed in the dashboard reaches this model at the next build.

    function round1(x) { return Math.round(x * 10) / 10; }
    function inYtd(fn) {   // Détail: its charts run from January (or the period's start if earlier) to the period's end
      var k = [GF.preset, GF.from, GF.to], y0 = GF.to.slice(0, 4) + '-01-01';
      GF.preset = 'custom'; if (y0 < GF.from) GF.from = y0; select(); prod();
      try { return fn(); } finally { GF.preset = k[0]; GF.from = k[1]; GF.to = k[2]; select(); prod(); }
    }
    function prod() { PD = pSrc() ? pData() : null; PA = PD ? pAgg(PD) : null; }

    // trend of the year (v2Trend): actual months, forecast months, target month by month, 2025 at the same date, bars by line
    function trend(fv, f25, f26) {
      var S2 = v2Series(fv), all = S2.act.concat(S2.fc); if (!S2.act.length) return null;
      var R5 = y25Sel(), n25 = R5 ? sumA(R5.map(f25)) : 0, real = n25 > 0;
      var T = real ? v2Tgt(f25, f26) : null;
      var year = S2.tot + S2.ftot, y25 = real ? n25 : year, tgt = T ? T.year : y25 * V2CUT, c25 = real ? y25Cum(R5, f25, all.map(function (x) { return x.m; })) : null;
      var wsum = 0; for (var mm = 1; mm <= 12; mm++) wsum += V2W[mm] || 1;
      var mTgt = T ? T.tm : function (m) { return tgt * (V2W[+m.slice(5, 7)] || 1) / wsum; };
      var cum = [0], ct = [0], c = 0, t = 0;
      all.forEach(function (x) { c += x.v; cum.push(c); t += mTgt(x.m); ct.push(t); });
      return { months: all.map(function (x) { return { m: x.m, v: x.v, fc: !!x.f, tgt: mTgt(x.m) }; }), na: S2.act.length, now: S2.tot, year: year, tgt: tgt, y25: y25,
        real: real, byLine: !!T, cum: cum, ct: ct, c25: c25,
        bars: T ? [['2025', T.lines.map(function (a) { return { l: a.l, v: a.v25 + a.n25o + a.x25, out: a.x25 }; })],
                   ['target', T.lines.map(function (a) { return { l: a.l, v: a.year + a.xT, out: a.xT }; })]] : null,
        lines: T ? T.lines.map(function (a) { return { l: a.l, ph: !!a.ph }; }) : [] };
    }

    // NC per MSN against the target, line by line (v2Target); all lines: the sum of the lines' targets
    function target() {
      if (!PD || !PA) return null;
      var by = {}; P_().forEach(function (o) { var l = o.line || '—', a = by[l] || (by[l] = { l: l, nc: 0, eq: 0 }); a.nc += o.NC; a.eq += o.EQ; });
      var rows = lineOrder(Object.keys(by)).map(function (l) { return by[l]; }).filter(function (a) { return a.eq >= 0.5; });
      if (!rows.length) return null;
      if (rows.length > 1) rows.unshift({ l: '', nc: sumA(rows.map(function (r) { return r.nc; })), eq: sumA(rows.map(function (r) { return r.eq; })), all: true });
      var B = y25Lines();
      rows.forEach(function (r) {
        if (r.all) return; var b = B && B[r.l]; r.v = r.nc / r.eq;
        if (b && b.eq >= 0.5 && b.nc > 0) { r.b = b.nc / b.eq; r.t = r.b * V2CUT; } else { r.t = r.v * V2CUT; r.ph = true; }
      });
      var A0 = rows[0] && rows[0].all ? rows[0] : null;
      if (A0) {
        var ln = rows.slice(1), bn = ln.filter(function (r) { return r.b != null; }); A0.v = A0.nc / A0.eq;
        A0.tn = sumA(ln.map(function (r) { return r.t * r.eq; })); A0.t = A0.tn / A0.eq; A0.ph = ln.some(function (r) { return r.ph; });
        A0.stack = ln.map(function (r) { return { l: r.l, nc: r.nc }; });
        if (bn.length) A0.b = sumA(bn.map(function (r) { return r.b * r.eq; })) / sumA(bn.map(function (r) { return r.eq; }));
      }
      return rows.map(function (r) { return { l: r.l, all: !!r.all, nc: r.nc, eq: r.eq, v: r.v, t: r.t, tn: r.tn == null ? null : r.tn, b: r.b == null ? null : r.b, ph: !!r.ph, stack: r.stack || null }; });
    }
    function rateOf(rows, l) { if (!rows) return null; var r = rows.filter(function (x) { return l ? x.l === l : x.all || rows.length === 1; })[0]; return r ? { v: r.v, t: r.t } : null; }

    // 2025 against 2026 per MSN, A330 and A350 (v2Quarters): the top 10 causes of either year
    function quarters() {
      if (GF.line && !CONN_LINES[GF.line]) return { none: 'conn' };
      var keep = function (p) { return !!CONN_LINES[PD.line[p]]; };
      var R = y25Rca(), e26 = PD && PA ? sumA(P_().filter(function (o) { return o.EQ > 0 && connOk(o); }).map(function (o) { return o.EQ; })) : 0; if (!R || !e26) return null;
      var a = {}, b = {}, tot = {}, all = {};
      PD.defs.forEach(function (d) { if (keep(PD.ncs[d.n].p) && PA[PD.ncs[d.n].p].EQ > 0) tot[d.rca] = (tot[d.rca] || 0) + 1; });
      Object.keys(tot).forEach(function (c) { all[c] = 1; }); R.forEach(function (x) { if (x.rca) all[x.rca] = 1; });
      Object.keys(all).forEach(function (c) { var q = y25Rate(R.filter(function (x) { return x.rca === c; }), function (x) { return x.d; }, keep); a[c] = q ? q.r : 0; b[c] = (tot[c] || 0) / e26; });
      var by = function (o) { return Object.keys(all).sort(function (x, y) { return o[y] - o[x]; }).slice(0, 10); }, pick = {};
      by(a).concat(by(b)).forEach(function (c) { if (a[c] || b[c]) pick[c] = 1; });
      var top = Object.keys(pick).sort(function (x, y) { return Math.max(b[y], a[y]) - Math.max(b[x], a[x]); });
      return { rows: top.map(function (r) { return { rca: r, cat: RCA_CAT[r] || 'aside', a: a[r] || 0, b: b[r] || 0 }; }) };
    }

    // ranking of the causes month by month (vBump): the 8 biggest causes of the period, their rank each month
    function bump() {
      var rs = D.defects.filter(function (r) { return keepMinor(r) && SEL[r[0]]; }), cnt = {}, tot = {}, vol = {}, cof = {};
      rs.forEach(function (r) { var m = r[2].slice(0, 7), a = dRca(r); (cnt[m] || (cnt[m] = {}))[a] = (cnt[m][a] || 0) + 1; tot[a] = (tot[a] || 0) + 1; vol[m] = (vol[m] || 0) + 1; cof[a] = catKey(dCat(r)); });
      var months = Object.keys(cnt).sort(); if (months.length < 2) return null;
      var top = Object.keys(tot).sort(function (a, b) { return tot[b] - tot[a] || (a < b ? -1 : 1); }).slice(0, 8), rank = {};
      months.forEach(function (m) { Object.keys(cnt[m]).sort(function (a, b) { return cnt[m][b] - cnt[m][a] || (a < b ? -1 : 1); }).forEach(function (a, i) { (rank[m] || (rank[m] = {}))[a] = i + 1; }); });
      var vs = months.map(function (m) { return vol[m]; }).sort(function (a, b) { return a - b; }), med = vs[Math.floor(vs.length / 2)];
      return { months: months.map(function (m) { return { m: m, vol: vol[m], low: vol[m] < med * 0.5 }; }),
        causes: top.map(function (a) { return { rca: a, cat: cof[a], ranks: months.map(function (m) { return rank[m][a] || null; }), n: months.map(function (m) { return cnt[m][a] || 0; }) }; }) };
    }

    // volume or unit cost, one bubble per cause with 3 defects or more (vBub)
    function bubbles() {
      var st = {}; D.defects.forEach(function (r) { if (!keepMinor(r) || !SEL[r[0]]) return; var a = dRca(r), s = st[a] || (st[a] = { n: 0, c: 0, cat: dCat(r) }); s.n++; s.c += dAlloc(r); });
      var list = Object.keys(st).filter(function (x) { return st[x].n >= 3; }).map(function (x) { var s = st[x]; return { rca: x, n: s.n, c: s.c, a: s.c / s.n, cat: s.cat }; });
      return list.length < 2 ? null : list.sort(function (a, b) { return b.c - a.c; });
    }

    // connection errors per MSN, month by month, A330 and A350 (g78 and the rate chart it draws with): mean, 3-month mean, 2025
    function connections() {
      if (GF.line && !CONN_LINES[GF.line]) return { none: 'conn' };
      if (!PD || !PA) return null;
      var R = y25Rca(), q = R ? y25Rate(R.filter(function (x) { return x.cat === 'Erreur Branchement'; }), function (x) { return x.d; }, function (p) { return !!CONN_LINES[PD.line[p]]; }) : null;
      var rows = pMonthly(function (o, i) { return o.connm[i]; }, connOk); if (rows.length < 2) return null;
      var r = rows.map(function (x) { return x.v / x.e; }), mean = sumA(rows.map(function (x) { return x.v; })) / sumA(rows.map(function (x) { return x.e; }));
      var roll = r.map(function (v, j) { var a = r.slice(Math.max(0, j - 2), j + 1); return sumA(a) / a.length; });
      return { months: rows.map(function (x, j) { return { m: PD.months[x.i], v: x.v, e: x.e, r: r[j], roll: roll[j] }; }), mean: mean, y25: q ? q.r : null };
    }

    // the three first causes of each product, per MSN (g54)
    function topCauses() {
      if (!PD || !PA) return null;
      var os = pOk().filter(function (o) { return o.DEF; }).sort(function (a, b) { return b.DEF / b.EQ - a.DEF / a.EQ; }); if (!os.length) return null;
      var cat = {}; PD.defs.forEach(function (d) { cat[d.rca] = catKey(d.cat); });
      return os.map(function (o) {
        return { p: o.p, rate: o.DEF / o.EQ, top: Object.keys(o.rcas).sort(function (a, b) { return o.rcas[b] - o.rcas[a]; }).slice(0, 3).map(function (r) { return { rca: r, cat: cat[r], n: o.rcas[r], v: o.rcas[r] / o.EQ }; }) };
      });
    }

    // the Pareto (the Pareto tab's two boards): every unit of the selection, three levels, in volume and in cost
    function pareto() {
      var nl = {}; D.defects.forEach(function (r) { nl[r[0]] = (nl[r[0]] || 0) + 1; });
      var has = {}, units = [];
      D.defects.forEach(function (r) { if (NC[r[0]]) has[r[0]] = 1; if (NC[r[0]] && SEL[r[0]] && keepMinor(r)) { var cb = dCable(r) ? 1 : 0;
        units.push({ cat: dCat(r), rca: dRca(r), code: dCode(r), d: 1, nc: 1 / nl[r[0]], cost: dAlloc(r), cb: cb, cbc: cb ? dAlloc(r) : 0 }); } });
      REP.forEach(function (n) { if (!has[n[0]] && SEL[n[0]]) units.push({ cat: '__none', rca: '', code: '', d: 0, nc: 1, cost: n[12], cb: 0, cbc: 0 }); });   // an NC with no defect line counts in cost
      function level(keys) {   // d, nc, cost; cb, cbc: the cable defects in it (count, cost), the bars' cable shading
        var m = {}; units.forEach(function (u) { if (keys.some(function (k) { return !u[k]; }) && keys.length > 1) return;
          var id = keys.map(function (k) { return u[k]; }).join('\u0001'), o = m[id] || (m[id] = { d: 0, nc: 0, cost: 0, cb: 0, cbc: 0 });
          keys.forEach(function (k) { o[k] = u[k]; }); o.d += u.d; o.nc += u.nc; o.cost += u.cost; o.cb += u.cb; o.cbc += u.cbc; });
        return Object.keys(m).map(function (k) { return m[k]; });
      }
      return { cat: level(['cat']), rca: level(['cat', 'rca']), code: level(['cat', 'rca', 'code']) };
    }

    // the tables (rows of the selection, newest first): every NC; every defect line
    function ncRows() {
      return SEL_NC.slice().sort(function (a, b) { return a[1] < b[1] ? 1 : a[1] > b[1] ? -1 : 0; })
        .map(function (n) { return [n[0], n[1], n[3], n[26] || 'Other', ncType(n), n[7] || '', n[38] || '', n[27] || '', n[22] || '']; });
    }
    function defRows() {   // [nc, seq, date, line, cat, rca, sub, code, fin, cable, text, cost, NC share]
      var nl = {}; D.defects.forEach(function (r) { nl[r[0]] = (nl[r[0]] || 0) + 1; });
      return D.defects.filter(function (r) { return SEL[r[0]] && keepMinor(r); })
        .sort(function (a, b) { return a[2] < b[2] ? 1 : a[2] > b[2] ? -1 : (a[0] < b[0] ? 1 : a[0] > b[0] ? -1 : a[1] - b[1]); })
        .map(function (r) { return [r[0], r[1], r[2], r[4], dCat(r), dRca(r), dSub(r), dCode(r), dFin(r), dCable(r) ? 1 : 0, tidy(r[18]), dAlloc(r), 1 / nl[r[0]]]; });
    }
    function noLineRows() {   // the cost table's NCs with no defect line: [nc, date, line, cost, title]
      var has = {}; D.defects.forEach(function (r) { has[r[0]] = 1; });
      return SEL_NC.filter(function (n) { return !has[n[0]]; }).map(function (n) { return [n[0], n[1], n[3], n[12] || 0, n[22] || '']; });
    }
    function unplanned() {   // the NCs whose product is not in the production plan, counted in the totals (v2UnplannedNote): [nc, date, line, product, title]
      if (!PA) return [];
      return SEL_NC.filter(function (n) { return !v2InPlan(n); }).sort(function (a, b) { return a[1] < b[1] ? 1 : -1; }).map(function (n) { return [n[0], n[1], n[3], n[26] || 'Other', n[22] || '']; });
    }

    // the bell (alCompute and the dashboard's alarm engine): what to look at as of the period's last finished week
    function alarms() {
      var res = alCompute(); if (!res) return null;
      var onLine = function (g) { return !GF.line || g.line.split(' + ').indexOf(GF.line) >= 0; }, mine = res.filter(onLine);
      function go(g) {
        var a = g.head, f = {}, r = null;
        if (a.lv === 'cat') f.cat = a.v;
        else if (a.lv === 'rca' || a.lv === 'code') {
          D.defects.some(function (x) { if ((a.lv === 'rca' ? dRca(x) : dCode(x)) === a.v) { r = x; return true; } return false; });
          if (r) { f.cat = dCat(r); f.rca = dRca(r); if (a.lv === 'code') f.code = a.v; }
        }
        return { line: g.line.indexOf(' + ') >= 0 ? '' : g.line, f: f };
      }
      function spark(g) { var it = g.head.it, out = []; if (!it) return null; for (var i = AL.last - 15; i <= AL.last; i++) out.push(it.e ? (it.e[i] > 0 ? (it.w[i] || 0) / it.e[i] : null) : it.w[i] || 0); return out; }
      return { week: AL.last, first: AL.first, short: AL.last < AL.first, other: res.length - mine.length, recent: ALARM.P.recent, show: ALARM.P.show,
        rows: mine.map(function (g) {
          var a = g.head, sub = [], also = (g.also || []).filter(function (x) { return x.lv !== 'prod'; });
          if (a.kids) sub.push(S('alDont', { l: a.kids.map(function (v) { return alName({ lv: a.lv === 'all' ? 'cat' : a.lv === 'cat' ? 'rca' : 'code', v: v }); }).join(', ') }));
          if (also.length) sub.push(S('alAlso', { l: also.map(alName).join(', ') }));
          if (g.act) sub.push(S('alAct', { t: g.act.title }));
          return { key: g.key, line: g.line, lvl: g.lvl, text: alText(g), sub: sub, spark: spark(g), go: go(g) };
        }) };
    }

    // ---------------------------------------------------------------- the model
    select(); prod();
    var out = { meta: { to: D.meta.to, from: GF.from, end: GF.to, lines: LINES, presets: PRESETS.filter(function (p) { return p !== 'custom'; }), dmin: DMIN, dmax: DMAX,
      filters: { line: GF.line, preset: GF.preset, from: GF.from, to: GF.to, phase: GF.phase, fto2: GF.fto2, minor: G.minor, src: GF.src, org: GF.org, lang: G.lang },
      nSel: SEL_NC.length, nDef: D.defects.filter(function (r) { return SEL[r[0]] && keepMinor(r); }).length,
      codes: {}, catOrder: CAT_ORDER, aside: ASIDE } };
    D.defects.forEach(function (r) { var c = dCode(r); if (c && !out.meta.codes[c]) out.meta.codes[c] = codeDesc(c); });

    // Synthèse: the selection as it is
    var tN = trend(function () { return 1; }, function (x) { return x.nc; }, function (o) { return o.NC; });
    var tC = trend(function (n) { return n[12]; }, function (x) { return x.cost; }, function (o) { return o.COST; });
    var tg = target(), rc = 0; CLI_NC.forEach(function (x) { rc += x[12] || 0; });
    out.syn = {
      figs: { nc: tN ? tN.now : SEL_NC.length, ncFc: tN ? tN.year : null, ncTgt: tN ? tN.tgt : null, rate: rateOf(tg, GF.line),
        cost: tC ? tC.now : null, costFc: tC ? tC.year : null, costBud: tC ? tC.tgt : null, ret: CLI_NC.length, retCost: rc },
      trend: tN, target: tg, unplanned: unplanned(), bump: bump(), quarters: quarters(), bubbles: bubbles(), ncs: ncRows() };

    // Détail: the period, against the period just before it; its charts from January
    var now = { n: SEL_NC.length, d: out.meta.nDef, c: sumA(SEL_NC.map(function (n) { return n[12] || 0; })) }, prev = null;
    var days = Math.round((Date.parse(GF.to) - Date.parse(GF.from)) / 864e5) + 1, p0 = plusDays(GF.from, -days);
    if (p0 >= DMIN) {
      var kk = [GF.preset, GF.from, GF.to]; GF.preset = 'custom'; GF.from = p0; GF.to = plusDays(kk[1], -1); select();
      prev = { n: SEL_NC.length, d: D.defects.filter(function (r) { return SEL[r[0]] && keepMinor(r); }).length, c: sumA(SEL_NC.map(function (n) { return n[12] || 0; })) };
      GF.preset = kk[0]; GF.from = kk[1]; GF.to = kk[2]; select();
    }
    out.det = { figs: { now: now, prev: prev }, pareto: pareto(), defects: defRows(), noLine: noLineRows() };
    inYtd(function () { out.det.figs.rate = rateOf(target(), GF.line); out.det.bump = bump(); out.det.connections = connections(); out.det.top = topCauses(); out.det.ytdFrom = GF.from; });
    out.alarms = alarms();
    return out;

  }
  return { model: model };
})();
if (typeof module !== 'undefined' && module.exports) module.exports = FTO2Views;

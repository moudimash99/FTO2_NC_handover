/* @@STAMP@@ */
// Fixed references, written at the build: sub-code names, the production plan's products and their alias rules, MSN built per
// line and week, the end of build of each MSN (the alarms), and the MFT trackers' actions (the store's first content).
window.FTO2_MFT_REF = @@REF@@;

// ---------------------------------------------------------------- the two Slate tables -> the page's data
// As 07_scripts/mft/build_mft.py data() does from the CSV files: NCs raised at FTO2 (plant FTO2 or FT02) created in 2026, their
// defect lines, values numbered in dictionaries. Tables as Slate gives them (one array per column) or as rows.
function mftFromTables(ncIn, defIn, R) {
  function rows(t) {
    if (!t) return [];
    if (Array.isArray(t)) return t;
    var cols = Object.keys(t), n = 0, out = [];
    cols.forEach(function (c) { if (t[c] && t[c].length > n) n = t[c].length; });
    for (var i = 0; i < n; i++) { var o = {}; cols.forEach(function (c) { o[c] = t[c] ? t[c][i] : null; }); out.push(o); }
    return out;
  }
  function str(v) { return v == null ? '' : String(v); }
  function tidy(v, n) { return str(v).replace(/\s+/g, ' ').trim().slice(0, n || 320); }
  function id(v) { return str(v).trim().replace(/\.0$/, ''); }
  function isoWeek(s) { var d = new Date(s.slice(0, 10) + 'T00:00:00Z'), dw = (d.getUTCDay() + 6) % 7; d.setUTCDate(d.getUTCDate() - dw + 3);
    var y = d.getUTCFullYear(), j4 = new Date(Date.UTC(y, 0, 4)), w = 1 + Math.round(((d - j4) / 864e5 - 3 + ((j4.getUTCDay() + 6) % 7)) / 7); return y + '-W' + (w < 10 ? '0' : '') + w; }
  var plan = R.plan || {}, alias = R.alias || [];
  function planProd(line, prod, station) {   // build_all.alias_product, then the plan's name; '' when not in the plan
    var p = prod || 'Other';
    if (!plan[p.toUpperCase()]) for (var i = 0; i < alias.length; i++) { var x = alias[i];
      if (x[0] === line && new RegExp(x[1]).test(p) && (!x[2] || new RegExp(x[2], 'i').test(station || ''))) { p = x[3]; break; } }
    return plan[p.toUpperCase()] || '';
  }
  var keys = ['line', 'phase', 'msn', 'station', 'where', 'cat', 'rca', 'sub', 'code', 'fin', 'prod'], dic = {}, idx = {};
  keys.forEach(function (k) { dic[k] = []; idx[k] = {}; });
  function code(k, v) { v = tidy(v, 120); if (!(v in idx[k])) { idx[k][v] = dic[k].length; dic[k].push(v); } return idx[k][v]; }
  var n = rows(ncIn).map(function (r) { return { r: r, created: str(r.created), plant: str(r.plant).trim().toUpperCase() }; })
    .filter(function (x) { return (x.plant === 'FTO2' || x.plant === 'FT02') && x.created >= '2026-01-01'; });
  n.sort(function (a, b) { return a.created < b.created ? -1 : a.created > b.created ? 1 : 0; });
  var ncs = [], pos = {}, to = '';
  n.forEach(function (x) { var r = x.r, c = x.created.slice(0, 10), k = id(r.nc); pos[k] = ncs.length; if (c > to) to = c;
    ncs.push([k, c, code('line', str(r.line) || '—'), code('phase', r.phase), code('msn', id(r.msn)), code('station', r.station), code('where', r.where_found),
      code('prod', planProd(str(r.line), str(r.product), str(r.station)))]); });
  var defs = [];
  rows(defIn).forEach(function (r) { var i = pos[id(r.nc)]; if (i == null) return;
    defs.push([i, code('cat', r.cat), code('rca', r.rca), code('sub', r.sub), code('code', r.subcode), code('fin', r.fin), Math.round(parseFloat(r.minor) || 0), tidy(r.text)]); });
  var codes = {}; dic.code.forEach(function (c) { if (c) codes[c] = tidy((R.codes || {})[c] || '', 90); });
  return { to: to, toWeek: to ? isoWeek(to) : '', ncs: ncs, defs: defs, dic: dic, codes: codes, vol: R.vol || null, msnEnd: R.msnEnd || {} };
}

// ---------------------------------------------------------------- the store: the page's actions and alarm marks, in this browser
// Same calls as the page's shared store (collection, doc, set, update, delete, onSnapshot). Slate gives a code sandbox no shared
// store, so they are kept in this browser's storage; the first time, the actions are the trackers' (FTO2_MFT_REF.actions).
window.FTO2_STORE = (function () {
  var mem = {}, subs = {}, ok = true, KEY = 'mft-fto2-slate-';
  function copy(o) { return JSON.parse(JSON.stringify(o)); }
  function save(c) { try { localStorage.setItem(KEY + c, JSON.stringify(mem[c])); } catch (e) { ok = false; } }
  function load(c) {
    if (mem[c]) return mem[c];
    var v = null; try { v = JSON.parse(localStorage.getItem(KEY + c) || 'null'); } catch (e) { ok = false; }
    if (!v) { v = {}; if (c === 'actions') (window.FTO2_MFT_REF.actions || []).forEach(function (a) { v[a.id] = copy(a); }); }
    mem[c] = v; save(c); return v;
  }
  function emit(c) { setTimeout(function () {
    var docs = Object.keys(mem[c]).map(function (k) { var x = mem[c][k]; return { id: k, data: function () { return copy(x); } }; });
    (subs[c] || []).forEach(function (f) { try { f({ docs: docs }); } catch (e) { } }); }, 0); }
  function collection(c) {
    load(c);
    return {
      doc: function (k) {
        k = k || 'a' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
        return {
          id: k,
          set: function (b) { mem[c][k] = copy(b); save(c); emit(c); return Promise.resolve(); },
          update: function (f) { if (!mem[c][k]) return Promise.reject(new Error('introuvable')); Object.assign(mem[c][k], copy(f)); save(c); emit(c); return Promise.resolve(); },
          delete: function () { delete mem[c][k]; save(c); emit(c); return Promise.resolve(); }
        };
      },
      onSnapshot: function (f) { (subs[c] = subs[c] || []).push(f); emit(c); return function () { subs[c] = subs[c].filter(function (g) { return g !== f; }); }; }
    };
  }
  return {
    use: function (k) { return Promise.resolve(k === 'db' ? { collection: collection } : null); },
    note: function () { return ok ? 'Actions enregistrées dans ce navigateur, sur ce poste : elles ne sont pas partagées avec les autres utilisateurs de l’app.'
      : 'Le navigateur bloque l’enregistrement : les actions modifiées ici seront perdues au rechargement.'; }
  };
})();

// ---------------------------------------------------------------- the page (07_scripts/mft/mft_template.html), started once the tables are in
function mftMain() {
@@MAIN@@
}

// ---------------------------------------------------------------- Slate: wait for the two queries, then start the page
(function () {
  var MSG = {
    wait: 'Chargement des données Slate… / Loading the Slate data…',
    empty: 'La requête q_fto2_nc n’a renvoyé aucune ligne : vérifiez la requête et son jeu de données. / The q_fto2_nc query returned no row: check the query and its dataset.',
    noapi: 'État Slate introuvable : ce JavaScript doit tourner dans un code sandbox Slate dont l’état contient les deux requêtes (voir state.json). / No Slate state: this JavaScript must run in a Slate code sandbox whose state holds the two queries (see state.json).',
    slow: 'Toujours en attente de {q} : vérifiez que la requête existe, porte ce nom et s’exécute sans erreur. / Still waiting for {q}: check that the query exists, has this name and runs without error.'
  };
  function showError(msg) {
    var e = document.getElementById('fto2-err');
    if (e) { e.hidden = false; e.textContent = 'La page MFT n\'a pas pu s\'afficher / The MFT page could not load: ' + msg; }
    var w = document.getElementById('fto2-wait'); if (w) w.hidden = true;
    if (window.console) console.error('[FTO2 MFT]', msg);
  }
  function status(msg, warn) { var e = document.getElementById('fto2-wait'); if (!e) return; e.hidden = !msg; e.textContent = msg || ''; e.className = 'fto2-wait' + (warn ? ' warn' : ''); }
  window.addEventListener('error', function (ev) { showError((ev && ev.message) || 'unknown error'); });
  function parse(v) { if (typeof v !== 'string') return v; var s = v.trim(); if (!s) return null; try { return JSON.parse(s); } catch (e) { return null; } }
  function count(t) { if (!t) return 0; if (Array.isArray(t)) return t.length; var k = Object.keys(t); for (var i = 0; i < k.length; i++) if (t[k[i]] && t[k[i]].length) return t[k[i]].length; return 0; }
  function loaded(t) { return !!t && (Array.isArray(t) || Object.keys(t).length > 0); }
  var got = {}, started = false;
  function tryStart() {
    if (started) return;
    var nc = parse(got.nc), def = parse(got.def);
    if (loaded(nc) && !count(nc)) { status(MSG.empty, true); return; }
    if (!count(nc) || !loaded(def)) { status(MSG.wait); return; }   // both queries are needed: they can arrive one after the other
    started = true;
    try {
      var D = window.FTO2_MFT_D = mftFromTables(nc, def, window.FTO2_MFT_REF);
      if (!D.ncs.length) {   // rows arrived but none is a 2026 FTO2 NC: say what came, to fix the query or the state
        var c = Array.isArray(nc) ? Object.keys(nc[0] || {}) : Object.keys(nc);
        showError('aucune NC FTO2 de 2026 lisible dans q_fto2_nc (colonnes reçues : ' + c.join(', ') + ') / no readable 2026 FTO2 NC in q_fto2_nc (columns received: ' + c.join(', ') + ')');
        return;
      }
      status(''); mftMain();
    } catch (e) { showError((e && e.message) || String(e)); }
  }
  function boot() {
    if (!document.getElementById('lines')) { showError('HTML part missing: paste fto2_mft.html into the HTML tab.'); return; }
    var api = window.SlateFunctions;
    if (!api || !api.watch) { showError(MSG.noapi); return; }
    status(MSG.wait);
    ['nc', 'def'].forEach(function (k) { api.watch(k, function (v) { got[k] = v; tryStart(); }); });
    setTimeout(function () {
      if (started) return;
      var miss = []; if (!count(parse(got.nc))) miss.push('q_fto2_nc'); if (!loaded(parse(got.def))) miss.push('q_fto2_def');
      if (miss.length) status(MSG.slow.replace(/\{q\}/g, miss.join(', ')), true);
    }, 20000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();

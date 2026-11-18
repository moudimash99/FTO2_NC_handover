/* @@STAMP@@ */
// The reference data (sub-code names, the production plan's products and their alias rules, MSN built per line and week, the
// end of build of each MSN, the MFT actions) comes from the query q_fto2_ref, part "mft" (dataset fto2_dash_ref).
@@REF_READER@@
@@REGLAGES@@
// ---------------------------------------------------------------- the two Slate tables -> the page's data
// NCs raised at FTO2 (plant FTO2 or FT02) created in the year
// followed (config/2_parametres.csv, annee: it comes with the settings), their
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
  // the NC's Responsabilité group, as the dashboard decides it (model.js liabCat): f FTO2 liable, s a supplier's number, o the others
  function liabGroup(r) { if (Math.round(parseFloat(r.on_aec) || 0) === 1) return 'f'; var c = str(r.liability).replace(/[\[\]\s]/g, '').replace(/^0+/, ''); return /^\d+$/.test(c) ? 's' : 'o'; }
  function planProd(line, prod, station) {   // the settings' product aliases, then the plan's name; '' when not in the plan
    var p = prod || 'Other';
    if (!plan[p.toUpperCase()]) for (var i = 0; i < alias.length; i++) { var x = alias[i];
      if (x[0] === line && new RegExp(x[1]).test(p) && (!x[2] || new RegExp(x[2], 'i').test(station || ''))) { p = x[3]; break; } }
    return plan[p.toUpperCase()] || '';
  }
  var keys = ['line', 'phase', 'msn', 'station', 'where', 'cat', 'rca', 'sub', 'code', 'fin', 'prod'], dic = {}, idx = {};
  keys.forEach(function (k) { dic[k] = []; idx[k] = {}; });
  function code(k, v) { v = tidy(v, 120); if (!(v in idx[k])) { idx[k][v] = dic[k].length; dic[k].push(v); } return idx[k][v]; }
  // the comparison year too: a week, a month or an action is compared with the weeks before it, across the new year
  var year = R.settings && (R.settings.annee_ref || R.settings.annee), since = year ? year + '-01-01' : '';
  var n = rows(ncIn).map(function (r) { return { r: r, created: str(r.created), plant: str(r.plant).trim().toUpperCase() }; })
    .filter(function (x) { return (x.plant === 'FTO2' || x.plant === 'FT02') && x.created >= since; });
  n.sort(function (a, b) { return a.created < b.created ? -1 : a.created > b.created ? 1 : 0; });
  var ncs = [], pos = {}, to = '';
  n.forEach(function (x) { var r = x.r, c = x.created.slice(0, 10), k = id(r.nc); pos[k] = ncs.length; if (c > to) to = c;
    ncs.push([k, c, code('line', str(r.line) || '—'), code('phase', r.phase), code('msn', id(r.msn)), code('station', r.station), code('where', r.where_found),
      code('prod', planProd(str(r.line), str(r.product), str(r.station))), liabGroup(r)]); });   // last: the Responsabilité group
  var defs = [];
  rows(defIn).forEach(function (r) { var i = pos[id(r.nc)]; if (i == null) return;
    defs.push([i, code('cat', r.cat), code('rca', r.rca), code('sub', r.sub), code('code', r.subcode), code('fin', r.fin), Math.round(parseFloat(r.minor) || 0), tidy(r.text)]); });
  var codes = {}; dic.code.forEach(function (c) { if (c) codes[c] = tidy((R.codes || {})[c] || '', 90); });
  var codesEn = {}; dic.code.forEach(function (c) { if (c && (R.codesEn || {})[c]) codesEn[c] = R.codesEn[c]; });   // the English page (2 Nov)
  return { to: to, toWeek: to ? isoWeek(to) : '', ncs: ncs, defs: defs, dic: dic, codes: codes, codesEn: codesEn, vol: R.vol || null, msnEnd: R.msnEnd || {}, settings: R.settings };
}

// ---------------------------------------------------------------- the store: the page's actions and alarm marks, in this browser
/* ===== STORE START ===== */
// The store of the MFT page. Its calls:
// use('db') gives collection(name), then doc(id) with set, update and delete, and onSnapshot; note(lang) says where the actions
// are kept. Neither page has a shared store: the shared actions are the table config/1_actions_mft.csv (they reach the page in
// FTO2_MFT_REF.actions and replace this browser's copy at every load); an action typed on the page is kept in this browser
// only, until it is added to the table.
window.FTO2_STORE = (function () {
  var mem = {}, subs = {}, ok = true, KEY = 'mft-fto2-slate-';
  function copy(o) { return JSON.parse(JSON.stringify(o)); }
  function save(c) { try { localStorage.setItem(KEY + c, JSON.stringify(mem[c])); } catch (e) { ok = false; } }
  function load(c) {
    if (mem[c]) return mem[c];
    var v = null; try { v = JSON.parse(localStorage.getItem(KEY + c) || 'null'); } catch (e) { ok = false; }
    v = v || {};
    if (c === 'actions') (window.FTO2_MFT_REF.actions || []).forEach(function (a) { v[a.id] = copy(a); });   // the table wins
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
    note: function (lang) { try { localStorage.setItem(KEY + 'probe', '1'); localStorage.removeItem(KEY + 'probe'); } catch (e) { ok = false; }
      if (lang === 'en') return ok ? 'Actions saved in this browser, on this computer: they are not shared with the app’s other users.'
        : 'The browser blocks saving: actions changed here will be lost on reload.';
      return ok ? 'Actions enregistrées dans ce navigateur, sur ce poste : elles ne sont pas partagées avec les autres utilisateurs de l’app.'
      : 'Le navigateur bloque l’enregistrement : les actions modifiées ici seront perdues au rechargement.'; }
  };
})();
/* ===== STORE END ===== */

// ---------------------------------------------------------------- the shared store: the actions kept for everyone (Slate only)
// Used when the sandbox's state has the key "store" (the query q_fto2_mft_store); without it, the browser store above. The
// actions are kept in one object of the NC writer's object type ("a30 Nc Writer Dataset"): the object whose Msn is MFT-ACTIONS,
// its Texte Sap holding every action as JSON {page, saved_at, actions}. Each save adds such an object; the page reads the one
// saved last (saved_at). A row without the page's mark is not read. With no row at
// all, the page starts from the table's actions (config/1_actions_mft.csv), and its first save writes them into the store.
// Writing takes the NC writer's route: at each change the page fires the event "save" with the row to write (and puts it in
// its state, key "store_row"); a Slate event copies it into a variable, the object type's Action widget takes its default
// values from that variable, and the user presses Submit. Meanwhile the page keeps its own copy, and its note asks to press
// Submit until the query brings back a row saved at or after that copy.
// Same calls as the browser store (use, collection, doc, set, update, delete, onSnapshot, note), so the page itself does not
// change. The alarms' marks (collection 'alarmes') stay in the browser store.
//   api: SlateFunctions; local: the browser store; seed: the table's actions (FTO2_MFT_REF.actions)
function fto2SharedStore(api, local, seed) {
  var MSN = 'MFT-ACTIONS', PAGE = 'MFT', LIMIT = 30000;
  var mem = {}, subs = [], ready = false, cur = '', pending = '', size = 0, bad = 0, open = null;
  var whenRead = new Promise(function (res) { open = res; });   // the page gets the store once the query has answered
  function copy(o) { return JSON.parse(JSON.stringify(o)); }
  function key(t) { return String(t == null ? '' : t).normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^0-9a-z]/g, ''); }
  // a property of a row: msn, Msn, MSN, texte_sap, texteSap...; an object of an Ontology query may hold them one level down
  // (properties, ...)
  function cell(r, name) {
    var ks = Object.keys(r), i;
    for (i = 0; i < ks.length; i++) if (key(ks[i]) === name) return r[ks[i]];
    for (i = 0; i < ks.length; i++) { var o = r[ks[i]]; if (o && typeof o === 'object' && !Array.isArray(o)) { var x = cell(o, name); if (x != null) return x; } }
    return null;
  }
  function rowsOf(v) {   // rows, or one array per column, or (an Ontology query) the objects under data / objects
    if (Array.isArray(v)) return v;
    var list = v.data || v.objects || v.results || v.result;   // result: an HTTP query's extractor ("result": "$") wraps the answer
    if (Array.isArray(list) && (!list.length || (list[0] && typeof list[0] === 'object' && !Array.isArray(list[0])))) return list;
    if (list && typeof list === 'object' && !Array.isArray(list)) return rowsOf(list);
    var cols = Object.keys(v), n = 0, out = [];
    cols.forEach(function (c) { if (Array.isArray(v[c]) && v[c].length > n) n = v[c].length; });
    for (var i = 0; i < n; i++) { var o = {}; cols.forEach(function (c) { o[c] = Array.isArray(v[c]) ? v[c][i] : null; }); out.push(o); }
    return out;
  }
  // a value of the state key: the latest store row, and how many later store rows could not be read; null before the query answers
  function read(v) {
    if (typeof v === 'string') { var s = v.trim(); if (!s) return null; try { v = JSON.parse(s); } catch (e) { return null; } }
    if (!v || typeof v !== 'object' || (!Array.isArray(v) && !Object.keys(v).length)) return null;
    var best = null, cut = [];
    rowsOf(v).forEach(function (r) {
      if (!r || typeof r !== 'object' || String(cell(r, 'msn') == null ? '' : cell(r, 'msn')).trim().toUpperCase() !== MSN) return;
      var t = cell(r, 'textesap'), x = null;
      try { x = typeof t === 'string' ? JSON.parse(t) : t; } catch (e) {   // a text cut short: kept aside, to say so if it is the latest
        var raw = String(t), at = /"saved_at":"([^"]*)"/.exec(raw);
        if (raw.indexOf('"page":"' + PAGE + '"') >= 0) cut.push(at ? at[1] : '');
        return;
      }
      if (!x || typeof x !== 'object' || x.page !== PAGE || !Array.isArray(x.actions)) return;   // another tool's row
      x.saved_at = String(x.saved_at || ''); x.size = typeof t === 'string' ? t.length : JSON.stringify(x).length;
      if (!best || x.saved_at > best.saved_at) best = x;
    });
    return { best: best, bad: cut.filter(function (at) { return !best || !at || at > best.saved_at; }).length };
  }
  function adopt(list, at, n) {   // this copy becomes a row's actions (or the table's)
    mem = {}; (list || []).forEach(function (a) { if (a && a.id != null) { var o = copy(a); delete o.id; mem[String(a.id)] = o; } });
    cur = at; size = n || 0;
  }
  function emit() { setTimeout(function () {
    var docs = Object.keys(mem).map(function (k) { var x = mem[k]; return { id: k, data: function () { return copy(x); } }; });
    subs.slice().forEach(function (f) { try { f({ docs: docs }); } catch (e) { } }); }, 0); }
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function send() {   // the whole list as one row, the way the NC writer hands over an NC: state key "store_row", then the event "save"
    var t = Date.now(), c = Date.parse(cur); if (isFinite(c) && t <= c) t = c + 1;   // later than the copy it changes, whatever this computer's clock says
    var d = new Date(t), at = d.toISOString(), list = Object.keys(mem).map(function (k) { return Object.assign({ id: k }, mem[k]); });
    var text = JSON.stringify({ page: PAGE, saved_at: at, actions: list });
    var row = { timestamp: d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()),
      msn: MSN, produit: 'MFT', detection: 'store', total_defauts: list.length, texte_sap: text };
    if (api.setState.length >= 2) api.setState('store_row', row); else { var st = {}; st.store_row = row; api.setState(st); }
    api.triggerEvent('save', row);
    cur = pending = at; size = text.length;
    if (size > LIMIT && window.console) console.warn('[FTO2 MFT] the actions take ' + size + ' characters: beyond ' + LIMIT + ', the save may cut them');
  }
  function change(f) {   // a change of the actions: on this copy at once (the page redraws), then sent
    if (!ready) return Promise.reject(new Error('the shared actions are not read yet'));
    if (!api || typeof api.setState !== 'function' || typeof api.triggerEvent !== 'function') return Promise.reject(new Error('SlateFunctions.setState / triggerEvent missing'));
    var keep = copy(mem), was = [cur, pending, size], err = f(); if (err) return err;
    try { send(); } catch (e) {
      mem = keep; cur = was[0]; pending = was[1]; size = was[2];
      if (window.console) console.error('[FTO2 MFT] the actions could not be sent', e);
      return Promise.reject(e);
    }
    emit(); return Promise.resolve();
  }
  var actions = {
    doc: function (k) {
      k = k || 'a' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
      return {
        id: k,
        set: function (b) { return change(function () { mem[k] = copy(b); }); },
        update: function (f) { return change(function () { if (!mem[k]) return Promise.reject(new Error('introuvable')); Object.assign(mem[k], copy(f)); }); },
        delete: function () { return change(function () { delete mem[k]; }); }
      };
    },
    onSnapshot: function (f) { subs.push(f); if (ready) emit(); return function () { subs = subs.filter(function (g) { return g !== f; }); }; }
  };
  return {
    use: function (k) {
      if (k !== 'db') return Promise.resolve(null);
      return Promise.all([whenRead, local && local.use ? local.use('db') : null]).then(function (x) {
        var ldb = x[1];
        return { collection: function (c) { return c === 'actions' ? actions : ldb ? ldb.collection(c) : null; } };
      });
    },
    note: function (lang) {
      var en = lang === 'en', out = [], n = size.toLocaleString(en ? 'en-GB' : 'fr-FR');
      if (pending) out.push(en ? 'Saving the change for everyone… (if this note stays, press Submit in the actions’ save form)'
        : 'Enregistrement de la modification pour tous… (si cette note reste, appuyez sur « Submit » dans le formulaire d’enregistrement des actions)');
      if (size > LIMIT) out.push(en ? 'Warning: the actions take ' + n + ' characters; beyond 30,000 the save may cut them. Delete some closed actions.'
        : 'Attention : les actions font ' + n + ' caractères ; au-delà de 30 000, l’enregistrement risque de les couper. Supprimez des actions closes.');
      if (bad) out.push(en ? 'A later save of the actions cannot be read (its text was cut?): the page shows the last one it can read.'
        : 'Un enregistrement plus récent des actions est illisible (texte coupé ?) : la page montre le dernier lisible.');
      return out.join(' ');
    },
    // a value of the state key "store": the first one gives the actions; then a later save replaces this copy, and a row
    // saved at or after this copy's last change ends the note asking for Submit
    take: function (v) {
      var r = read(v), b = r && r.best; if (!r) return;
      bad = r.bad;
      if (!ready) { if (b) adopt(b.actions, b.saved_at, b.size); else adopt(seed, '', 0); ready = true; open(); }
      else if (b && b.saved_at > cur) adopt(b.actions, b.saved_at, b.size);
      if (pending && b && b.saved_at >= pending) pending = '';
      emit();
    },
    ready: function () { return ready; }
  };
}

// ---------------------------------------------------------------- the page, started once the tables are in
function mftMain() {
@@MAIN@@
}

// ---------------------------------------------------------------- Slate: wait for the two queries, then start the page
// Optional state keys: "reglages" (q_fto2_set_targets, the Fusion sheet's settings: the page waits a few seconds for them, then
// applies them before it starts) and "store" (q_fto2_mft_store, the actions kept for everyone: the shared store above).
(function () {
  var MSG = {
    wait: 'Chargement des données Slate… / Loading the Slate data…',
    nostore: ['Enregistrement impossible : la requête q_fto2_mft_store n’a pas répondu (vérifiez qu’elle existe dans l’app et s’exécute, et la ligne "store" de l’état). Les actions modifiées ici seront perdues au rechargement.',
      'Saving impossible: the query q_fto2_mft_store did not answer (check it exists in the app and runs, and the line "store" of the state). Actions changed here will be lost on reload.'],
    empty: 'La requête q_fto2_nc n’a renvoyé aucune ligne : vérifiez la requête et son jeu de données. / The q_fto2_nc query returned no row: check the query and its dataset.',
    noapi: 'État Slate introuvable : ce JavaScript doit tourner dans un code sandbox Slate dont l’état contient les deux requêtes (voir state.json). / No Slate state: this JavaScript must run in a Slate code sandbox whose state holds the two queries (see state.json).',
    slow: 'Toujours en attente de {q} : vérifiez que la requête existe, porte ce nom et s’exécute sans erreur. / Still waiting for {q}: check that the query exists, has this name and runs without error.',
    store: 'Les actions partagées ne sont pas encore lues : vérifiez la requête q_fto2_mft_store. D’ici là, les actions ne s’affichent pas et ne peuvent pas être modifiées. / The shared actions are not read yet: check the query q_fto2_mft_store. Until then the actions are not shown and cannot be changed.'
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
  var got = {}, started = false, api = null, rgTimer = null, stTimer = null, shared = null, storeLate = false;
  function stateKeys() { var st = {}; try { st = (api.getState && api.getState()) || {}; } catch (e) { } return st; }
  function tryStart() {
    if (started) return;
    var nc = parse(got.nc), def = parse(got.def), R = fto2RefBlocks(got.ref);
    if (loaded(nc) && !count(nc)) { status(MSG.empty, true); return; }
    if (!count(nc) || !loaded(def) || !R) { status(MSG.wait); return; }   // the queries can arrive one after the other
    var st0 = stateKeys(), has = function (k) { return k in st0 || got[k] != null; };   // a key of the state, or a value arrived for it
    if (has('reglages') && !loaded(parse(got.reglages)) && rgTimer !== 'over') {   // the Fusion sheet's settings: a few seconds to arrive
      if (!rgTimer) rgTimer = setTimeout(function () { rgTimer = 'over'; tryStart(); }, 8000);
      return;
    }
    // the actions kept for everyone: the query q_fto2_mft_store may answer after the NCs, and with no row while the store is
    // empty: a few seconds for it, and any answer counts (17 Nov: a page started before it had answered kept the actions in the
    // browser, which Slate blocks)
    if (!has('store') && stTimer !== 'over') {
      if (!stTimer) stTimer = setTimeout(function () { stTimer = 'over'; tryStart(); }, 8000);
      return;
    }
    started = true;
    try {
      var D = window.FTO2_MFT_D = mftFromTables(nc, def, window.FTO2_MFT_REF = R.mft);
      if (has('reglages')) fto2Reglages(D.settings, got.reglages);   // before the page reads its settings (the action target)
      if (!D.ncs.length) {   // rows arrived but none is an FTO2 NC of the year followed: say what came, to fix the query or the state
        var c = Array.isArray(nc) ? Object.keys(nc[0] || {}) : Object.keys(nc);
        showError('aucune NC FTO2 de l’année suivie lisible dans q_fto2_nc (colonnes reçues : ' + c.join(', ') + ') / no readable FTO2 NC of the year followed in q_fto2_nc (columns received: ' + c.join(', ') + ')');
        return;
      }
      if (has('store')) {   // the actions kept for everyone; without the key, in this browser (the browser store)
        shared = window.FTO2_STORE = fto2SharedStore(api, window.FTO2_STORE, R.mft.actions || []);
        if (got.store !== undefined) shared.take(got.store);
        setTimeout(function () { if (!shared.ready()) { storeLate = true; status(MSG.store, true); } }, 20000);
      } else if (window.FTO2_STORE && window.FTO2_STORE.note) {   // no answer from q_fto2_mft_store: say so, rather than blame the browser
        var note0 = window.FTO2_STORE.note;
        window.FTO2_STORE.note = function (lang) { var t = note0(lang); return /bloque|blocks/.test(t) ? MSG.nostore[lang === 'en' ? 1 : 0] : t; };
      }
      status(''); mftMain();
    } catch (e) { showError((e && e.message) || String(e)); }
  }
  function boot() {
    if (!document.getElementById('lines')) { showError('HTML part missing: paste fto2_mft.html into the HTML tab.'); return; }
    api = window.SlateFunctions;
    if (!api || !api.watch) { showError(MSG.noapi); return; }
    status(MSG.wait);
    api.watch('store', function (v) {   // each answer of q_fto2_mft_store: after a Submit, once the query has run again
      got.store = v; if (!shared) { tryStart(); return; }
      shared.take(v);
      if (storeLate && shared.ready()) { storeLate = false; status(''); }
    });
    ['reglages', 'nc', 'def', 'ref'].forEach(function (k) { api.watch(k, function (v) { got[k] = v; tryStart(); }); });   // the optional keys first
    setTimeout(function () {
      if (started) return;
      var miss = []; if (!count(parse(got.nc))) miss.push('q_fto2_nc'); if (!loaded(parse(got.def))) miss.push('q_fto2_def'); if (!fto2RefBlocks(got.ref)) miss.push('q_fto2_ref');
      if (miss.length) status(MSG.slow.replace(/\{q\}/g, miss.join(', ')), true);
    }, 20000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();

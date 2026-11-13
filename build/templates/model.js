  /* ===== MODEL START ===== */
  // ================================================================================================================
  // The calculations of the dashboard, with no drawing. This file is inserted into the page (build/templates/dashboard.html,
  // at /*@@MODEL@@*/) and into the three Slate functions (03_reports/skywise/level3_datasets/fonctions/), so the page and
  // Skywise compute with the same code. It reads D (the data from fto2FromTables), SET (the settings), GF (the filters) and
  // G (language, minor defects); it touches no page element.
  //
  //   1. helpers           read a defect line or an NC, group NC types, the categories
  //   2. selection         the filters: which NCs are shown (GF), the period, the responsibility ticks, a clicked value
  //   3. production        the production plan matched to the NCs of the selection: MSN built per product and month
  //   4. targets, forecast 2025 under the same filters, the target line by line, the forecast to December
  //   5. cost explanation  minutes and euros of each step of an NC, for "Expliquer le calcul"
  //   6. alarms            the bell's list (the statistics themselves are in the alarm engine, ALARM)
  //   7. results           what the Slate functions return: objectifs(), alarmes(), cout()
  //   8. requests          in a Slate function: the filters the page asks for, and the answer
  // ================================================================================================================

  // ---------------------------------------------------------------- 1. helpers
  function lineOrder(vals) { return ['A350', 'A330', 'A320', 'A400M', 'Autre'].filter(function (c) { return vals.indexOf(c) >= 0; }); }
  function dCat(r) { return r[11]; } function dRca(r) { return r[12]; } function dSub(r) { return r[13]; }
  function dMinor(r) { return r[14]; } function dCable(r) { return r[15]; } function dAlloc(r) { return r[17]; }
  function keepMinor(r) { return G.minor || !dMinor(r); }
  function dCode(r) { return r[22] || ''; }
  function dFin(r) { return r[23] || ''; }
  var NC = {}; D.ncs.forEach(function (n) { NC[n[0]] = n; });
  function isoDay(dt) { return dt.toISOString().slice(0, 10); }
  function sumA(a) { return a.reduce(function (s, v) { return s + v; }, 0); }
  var CAT_ORDER = SET.categories.map(function (c) { return c.nom; });   // config/2_categories.csv
  var ASIDE = { '__none': 1 }; SET.categories.forEach(function (c) { if (c.a_part) ASIDE[c.nom] = 1; });   // shown aside, no category colour
  var CATC = {}; SET.categories.forEach(function (c) { if (c.couleur) CATC[c.nom] = c.couleur; });   // colour 1-9 of each category (config/2_categories.csv)
  var MAIN_CATS = CAT_ORDER.filter(function (c) { return !ASIDE[c]; }).concat(['aside']);
  function catKey(c) { return ASIDE[c] ? 'aside' : c; }
  var NCTYPES = ['cab', 'fin', 'test', 'int', 'sup', 'oth'];
  function ncType(n) { var t = String(n[33] || '').toUpperCase(); return t === 'CABLES' ? 'cab' : t === 'CONTROLE FINAL' ? 'fin' : t === 'TEST' ? 'test' : /INTERNE/.test(t) ? 'int' : t === 'FOURNISSEUR' ? 'sup' : 'oth'; }
  function wGroup(w) { return w === 'Final inspection' ? 'fin' : w === 'TEST' ? 'test' : w === 'Cables' ? 'cab' : (w === 'In-process (internal)' || w === 'NC Interne') ? 'int' : 'oth'; }
  function dGroup(r) { return r === 'Rework to drawing' ? 'rw' : (r === 'Rejection' || r === 'Scrap') ? 'rej' : r === 'Exchange' ? 'exc' : 'oth'; }

  // ---------------------------------------------------------------- 2. selection
  // ---------------------------------------------------------------- global filters (bar under the title): every tab reads its NCs through them
  // every NC of the pipeline's selection counts (decided 20 Oct). [23] where it was raised: 'serie' = at FTO2, 'client' = customer return,
  // 'autre' = another plant; [39] data source: 'sky' Skywise only, 'gps' / 'test' also in that manual list
  var REP = D.ncs;
  var DMAX = D.meta.to, DMIN = REP.reduce(function (m, n) { return n[1] < m ? n[1] : m; }, DMAX);
  var LINES = lineOrder(REP.map(function (n) { return n[3]; }));
  var GF0 = { pick: null, src: 'all', org: '', fto2: true, liab: SET.defauts.liab, cost: 'fto2', phase: SET.defauts.phase, line: '', preset: PAGE === 'suivi' ? 'all' : SET.defauts.preset, from: '', to: '' }, GF = Object.assign({}, GF0);
  var PRESETS = ['ytd', 'm1', 'm3', 'm6', 'm12', 'all', 'custom'];
  function plusDays(iso, k) { var d = new Date(iso + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + k); return isoDay(d); }
  function minusMonths(iso, k) { var d = new Date(iso + 'T12:00:00Z'), dd = d.getUTCDate(); d.setUTCDate(1); d.setUTCMonth(d.getUTCMonth() - k); d.setUTCDate(Math.min(dd, new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0)).getUTCDate())); return isoDay(d); }
  // presets end on the last NC of the extract
  function presetRange(p) {
    var k = { m1: 1, m3: 3, m6: 6, m12: 12 }[p];
    if (p === 'ytd') return [DMAX.slice(0, 4) + '-01-01', DMAX];
    if (k) return [plusDays(minusMonths(DMAX, k), 1), DMAX];
    return [DMIN, DMAX];
  }
  // who is liable (3 Nov, Mohammad), the three ticks of "Responsabilité": f FTO2 ([5], FTO2 in the liability), s a supplier (a code made
  // of digits only: 129 of the 133 SUPPLIER NCs of 2026), o anyone else (another Airbus site such as FFF1 or TO, other, blank)
  function liabCat(n) { if (n[5] === 1) return 'f'; var c = String(n[34] || '').replace(/[\[\]\s]/g, '').replace(/^0+/, ''); return /^\d+$/.test(c) ? 's' : 'o'; }
  var LIABS = ['f', 's', 'o'];
  // the cost of the NCs FTO2 is not liable for: 0 (FTO2's cost), or the cost of their work (REC only, "Toutes les NC", 3 Nov). The adapter
  // keeps both ([5] 0: the costs at 0, _w the cost of the work); select() puts in the ones asked for
  var COSTALL = false;
  function costed(n) { return n[5] === 1 || COSTALL; }
  function costMode() {
    var all = GF.cost === 'all' && GF.phase === 'REC'; if (all === COSTALL) return; COSTALL = all;
    D.ncs.forEach(function (n) { var w = n._w; if (n[5] === 1 || !w) return;
      [9, 10, 12, 13, 15, 17, 18, 46].forEach(function (k, j) { n[k] = all ? w[j] : 0; }); n[43] = all ? 0 : w[2]; });
    D.defects.forEach(function (r) { if (r._w != null) r[17] = all ? r._w : 0; });
  }
  function gNc(n, anyLine) {
    if (!n) return false;
    if (GF.src !== 'all' && (GF.src === 'man' ? n[39] === 'sky' : n[39] !== GF.src)) return false;
    if (GF.org && (n[41] || 'normal') !== GF.org) return false;   // [41] the pipeline output the NC comes from: normal or missing_ids
    if (GF.liab !== 'fso' && GF.liab.indexOf(liabCat(n)) < 0) return false;   // "Responsabilité" ticks (3 Nov): FTO2 only by default
    if (GF.pick && !pickNc(n)) return false;
    if (GF.phase && n[24] !== GF.phase) return false;
    if (GF.line && !anyLine && n[3] !== GF.line) return false;
    return n[1] >= GF.from && n[1] <= GF.to;
  }
  // a value clicked in a chart filters every tab: GF.pick = {k: field, v: value}. NC fields are tested on the NC; category, cause,
  // sub-category, FIN and sub-code mean "NCs with at least one such defect line" (PICK_NC, made when the pick changes)
  var PICK_DEF = { cat: function (r) { return dCat(r); }, rca: function (r) { return dRca(r); }, sub: function (r) { return dSub(r); }, fin: function (r) { return dFin(r); }, code: function (r) { return dCode(r); },
    stcat: function (r) { var n = NC[r[0]]; return ((n && n[27]) || '') + '§' + catKey(dCat(r)); }, finmsn: function (r) { var n = NC[r[0]]; return dFin(r) + '§' + ((n && n[25]) || ''); } };   // a cell: station and category, FIN and aircraft
  var PICK_NCF = { month: function (n) { return n[1].slice(0, 7); }, week: function (n) { return n[2]; }, day: function (n) { return n[1]; }, prod: function (n) { return n[26] || 'Other'; },
    pprod: function (n) { return D.eqmsn && D.eqmsn.map ? D.eqmsn.map[String(n[26] || '').toUpperCase()] || '' : ''; }, msn: function (n) { return n[25]; }, station: function (n) { return n[27]; },
    type: function (n) { return n[33]; }, ntype: function (n) { return ncType(n); }, rule: function (n) { return n[6]; }, where: function (n) { return n[8]; }, nc: function (n) { return String(n[0]); },
    hour: function (n) { return String(n[28]); }, wgrp: function (n) { return wGroup(n[8]); }, dgrp: function (n) { return dGroup(n[7]); },
    lgrp: function (n) { var g = dGroup(n[7]); return g === 'exc' ? 'oth' : g; }, open: function (n) { return n[30] ? '1' : '0'; } };
  var PICK_NC = null;
  function pickNc(n) { var p = GF.pick; if (PICK_DEF[p.k]) return !!(PICK_NC && PICK_NC[n[0]]); if (p.k === 'age') return ncAgeOver(n, +p.v); var f = PICK_NCF[p.k]; return !f || String(f(n)) === String(p.v); }
  // still open N days after creation (a click on the open-time chart): closed after more than N days, or still open and older than N days
  function ncAgeOver(n, d) { var t = n[29] != null ? n[29] : n[31]; return t != null && Math.round(t * 10) / 10 > d; }   // days to a tenth, as the chart
  function pickPrep() {
    PICK_NC = null; var p = GF.pick; if (!p || !PICK_DEF[p.k]) return;
    PICK_NC = {}; D.defects.forEach(function (r) { if (String(PICK_DEF[p.k](r)) === String(p.v)) PICK_NC[r[0]] = 1; });
  }
  function ours(n) { var p = String(n[42] || '').trim().toUpperCase(); return p === 'FTO2' || p === 'FT02'; }   // FTO2's NCs: [42] plant FTO2 / FT02 (as Type_NC_auto); on a GPS / Test list too only if at that plant (Mohammad, 20 Oct)
  function gScope(n) { return !GF.fto2 || ours(n); }   // FTO2 plant only: the plant column, nothing else
  // the selection: SEL follows every filter; SER = SEL's FTO2 NCs without the customer returns; CLI = the customer returns, whatever the switch (the tabs that show both apart)
  var SEL_NC = [], SER_NC = [], CLI_NC = [], SEL = {}, SER = {}, CLI = {};
  function ids(a) { var o = {}; a.forEach(function (n) { o[n[0]] = 1; }); return o; }
  function select() {
    if (GF.preset !== 'custom') { var r = presetRange(GF.preset); GF.from = r[0]; GF.to = r[1]; }
    costMode();
    SEL_NC = REP.filter(function (n) { return gNc(n) && gScope(n); });
    SER_NC = SEL_NC.filter(function (n) { return ours(n) && n[23] !== 'client'; });   // FTO2's, without the customer returns (shown apart, never counted twice)
    CLI_NC = REP.filter(function (n) { return n[23] === 'client' && gNc(n); });
    SEL = ids(SEL_NC); SER = ids(SER_NC); CLI = ids(CLI_NC);
  }
  function inSelAnyLine(r) { var n = NC[r[0]]; return gNc(n, true) && gScope(n); }
  select();

  // ---------------------------------------------------------------- 3. production
  var PR = { src: D.eqmsn ? 'real' : 'dummy', ver: D.eqmsn && D.eqmsn.wd ? 'wd' : 'std' }, PD = null, PA = null, PCOL = {};
  function pSrc() { return PR.src === 'real' && D.eqmsn ? D.eqmsn : DM && DM.eqmsn ? DM.eqmsn : null; }
  var CABLE_RCA = { 'Câble Endommagé': 1, 'Câble ou Élément Manquant': 1 };   // fictitious data only: no cable flag there
  // the NCs of the selection matched to a product of the output table, months of the period that are not forecast. When the NCs
  // reach into the plan's forecast months (export of 7 Oct, NCs to mid-October), those months count as built up to the last NC
  // day: the month of the last NC with its planned volume × the share of its days gone (P.part), the rest of it goes to the
  // forecast. Before (20 Oct) October's NCs fell out of every per-MSN total: Localisation 930 NCs against 994 on the Overview.
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
  function pOk() { return P_().filter(function (o) { return o.EQ >= EQMIN; }); }
  function P_() { return PD.prods.map(function (p) { return PA[p]; }); }

  // ---------------------------------------------------------------- 4. targets and forecast
  var V2CUT = SET.objectif_coef;   // target = 2025 rate x V2CUT (config/2_reglages_pages.csv: objectif_baisse)
  function v2Months() {
    var a = [], d = new Date(GF.from.slice(0, 7) + '-01T00:00:00Z'), end = (GF.to < D.meta.to ? GF.to : D.meta.to).slice(0, 7), fc = [];
    while (d.toISOString().slice(0, 7) <= end) { a.push(d.toISOString().slice(0, 7)); d.setUTCMonth(d.getUTCMonth() + 1); }
    if (GF.to >= D.meta.to) { var y = end.slice(0, 4); d = new Date(end + '-01T00:00:00Z'); d.setUTCMonth(d.getUTCMonth() + 1); while (d.toISOString().slice(0, 4) === y) { fc.push(d.toISOString().slice(0, 7)); d.setUTCMonth(d.getUTCMonth() + 1); } }
    return { act: a, fc: fc };
  }
  function v2Plan(m) { if (!PD) return null; var i = PD.months.indexOf(m); return i < 0 ? null : sumA(PD.prods.map(function (p) { return PD.prod[p][i] || 0; })); }
  // the forecast, the same on every chart (20 Oct): product by product, the product's value per MSN built in the period × its MSN planned
  // that month, plus the NCs out of the production plan at their own monthly pace (July and August as V2W). A single overall pace over-
  // forecasts: A320's planned volume grows at the end of the year while A320 has few NCs per unit. null without the real production plan.
  function v2Fc(f, M) {
    var E = pSrc(); if (!PD || !PA || !E || E !== D.eqmsn) return null;
    var byP = {}, out = 0, w = function (m) { return V2W[+m.slice(5, 7)] || 1; }, K = v2OutK(M), C = K.cur;
    SEL_NC.forEach(function (n) { var v = f(n), p = v2InPlan(n); if (p) byP[p] = (byP[p] || 0) + v; else out += v; });
    var pace = K.a ? out / K.a : 0, res = {}, per = function (i, sh) { return sumA(Object.keys(byP).map(function (p) { return i < 0 ? 0 : byP[p] / PA[p].EQ * (PD.prod[p][i] || 0) * sh; })); };
    M.fc.forEach(function (m) { res[m] = per(PD.months.indexOf(m), 1) + pace * w(m); });
    if (C) res[M.fc[0]] += per(C.i, 1 - C.part) + pace * w(C.m) * (1 - C.part);   // the rest of the running month, with the first month to come
    return { m: res, out: out, outFc: pace * K.f };
  }
  // the product of the plan an NC is counted under (its product has ≥ 0.5 MSN built in the period and the NC is in the per-MSN
  // data), else null: the NC is out of the plan. One test for every total, so the rows always add up to the Overview.
  function v2InPlan(n) { var E = pSrc(), p = E && E.map && E.map[String(n[26] || '').toUpperCase()]; return p && PA && PA[p] && PA[p].EQ >= EQMIN && PD.idx[n[0]] != null ? p : null; }
  // weights of the months done (a) and to come (f) for the out-of-plan NCs, July and August lighter (V2W); the running month
  // (pData) counts in both, by the share of its days gone and left
  function v2OutK(M) {
    var w = function (m) { return V2W[+m.slice(5, 7)] || 1; }, C = PD && PD.cur != null && M.fc.length && M.act[M.act.length - 1] === PD.months[PD.cur] ? { m: PD.months[PD.cur], i: PD.cur, part: PD.part[PD.cur] } : null;
    var a = sumA(M.act.map(w)) - (C ? w(C.m) * (1 - C.part) : 0), f = sumA(M.fc.map(w)) + (C ? w(C.m) * (1 - C.part) : 0);
    return { a: a, f: f, k: a ? f / a : 0, cur: C };
  }
  // monthly sums of f over the selection; forecast months: v2Fc (else the period's value per planned MSN × the MSN planned that month, else the last 3 months' mean)
  function v2Series(f) {
    var M = v2Months(), by = {}; SEL_NC.forEach(function (n) { var m = n[1].slice(0, 7); by[m] = (by[m] || 0) + f(n); });
    var act = M.act.map(function (m) { return { m: m, v: by[m] || 0 }; }), pa = 0, va = 0;
    act.forEach(function (x) { var p = v2Plan(x.m); if (p) { pa += p; va += x.v; } });
    var l3 = act.slice(-3), m3 = l3.length ? sumA(l3.map(function (x) { return x.v; })) / l3.length : 0;
    var F = v2Fc(f, M), fc = M.fc.map(function (m) { var p = v2Plan(m); return { m: m, v: F ? F.m[m] : pa && p != null ? va / pa * p : m3, f: true }; });
    return { act: act, fc: fc, tot: sumA(act.map(function (x) { return x.v; })), ftot: sumA(fc.map(function (x) { return x.v; })) };
  }
  // 2025 under the same filters (plant switch, phase, line); null when there is no 2025 block, the data-source filter is on (the
  // 2025 extract is not split by manual list) or only the missing-ID NCs are shown. The 2025 extract holds no customer return.
  function y25Sel() {
    var Y = D.y25; if (!Y || !Y.rows || GF.src !== 'all' || GF.org === 'missing_ids') return null;
    var c = {}, P = GF.pick; Y.cols.forEach(function (k, i) { c[k] = i; });
    if (GF.liab !== 'fso' && c.liab == null) return null;   // the "Responsabilité" ticks: 2025 needs its liability column
    if (P && ['month', 'prod', 'pprod'].indexOf(P.k) < 0) return null;   // a pick the 2025 extract cannot follow: no 2025 comparison
    var pOk = !P ? null : P.k === 'month' ? function (r) { return String(r[c.month]).slice(5, 7) === P.v.slice(5, 7); } : P.k === 'prod' ? function (r) { return (r[c.product] || 'Other') === P.v; } :
      function (r) { return !!(D.eqmsn && D.eqmsn.map && D.eqmsn.map[String(r[c.product] || '').toUpperCase()] === P.v); };
    return Y.rows.filter(function (r) { return (r[c.scope] === 'serie' || !GF.fto2) && (GF.liab === 'fso' || GF.liab.indexOf(r[c.liab]) >= 0) && (!GF.phase || r[c.phase] === GF.phase) && (!GF.line || r[c.line] === GF.line) && (!pOk || pOk(r)); })
      .map(function (r) { return { m: r[c.month], line: r[c.line], p: r[c.product], nc: r[c.nc], def: G.minor ? r[c.def] : r[c.defMajor], cost: COSTALL && c.costAll != null ? r[c.costAll] : r[c.cost] }; });
  }
  // 2025 defects by cause (parser labels) under the same filters as y25Sel; picks on a category or a cause apply too
  function y25Rca() {
    var Y = D.y25; if (!Y || !Y.rca || GF.src !== 'all' || GF.org === 'missing_ids') return null;
    var c = {}, P = GF.pick; Y.rcaCols.forEach(function (k, i) { c[k] = i; });
    if (GF.liab !== 'fso' && c.liab == null) return null;
    if (P && ['month', 'prod', 'pprod', 'cat', 'rca'].indexOf(P.k) < 0) return null;
    var ok = !P ? null : P.k === 'month' ? function (r) { return String(r[c.month]).slice(5, 7) === P.v.slice(5, 7); } : P.k === 'prod' ? function (r) { return (r[c.product] || 'Other') === P.v; } :
      P.k === 'cat' ? function (r) { return r[c.cat] === P.v; } : P.k === 'rca' ? function (r) { return r[c.rca] === P.v; } :
      function (r) { return !!(D.eqmsn && D.eqmsn.map && D.eqmsn.map[String(r[c.product] || '').toUpperCase()] === P.v); };
    return Y.rca.filter(function (r) { return (r[c.scope] === 'serie' || !GF.fto2) && (GF.liab === 'fso' || GF.liab.indexOf(r[c.liab]) >= 0) && (!GF.phase || r[c.phase] === GF.phase) && (!GF.line || r[c.line] === GF.line) && (!ok || ok(r)); })
      .map(function (r) { return { m: r[c.month], p: r[c.product], cat: r[c.cat], rca: r[c.rca], d: G.minor ? r[c.def] : r[c.defMajor] }; });
  }
  // a 2025 rate per product delivered, on the production plan's products that had 2025 deliveries (as the line targets): f summed ÷ deliveries
  function y25Rate(rows, f, keep) {   // keep(p): only these products of the plan (connection errors: A330 and A350)
    var L = D.y25 && D.y25.prod, E = pSrc(); if (!rows || !L || !PD || E !== D.eqmsn) return null;
    var has = function (p) { return L[p] && sumA(L[p]) > 0 && PD.prods.indexOf(p) >= 0 && (!keep || keep(p)); }, del = 0, v = 0;
    PD.prods.forEach(function (p) { if (has(p)) del += sumA(L[p]); });
    rows.forEach(function (x) { var p = E.map[String(x.p || '').toUpperCase()]; if (p && has(p)) v += f(x); });
    return del > 0 ? { v: v, del: del, r: v / del } : null;
  }
  // a 2025 sum by month of the year ('01'..'12'), and its running total over the months shown (actual + forecast, 'YYYY-MM')
  function y25Cum(Y, f, months) { var by = {}, c = 0; Y.forEach(function (x) { var k = x.m.slice(5, 7); by[k] = (by[k] || 0) + f(x); }); return [0].concat(months.map(function (m) { c += by[m.slice(5, 7)] || 0; return c; })); }
  // 2025 NCs per product delivered, per line, on the products of the 2025 deliveries (Livraisons 2025) mapped as the 2026 production plan
  function y25Lines() {
    var Y = y25Sel(), L = D.y25 && D.y25.prod, E = pSrc(); if (!Y || !L || !PD || E !== D.eqmsn) return null;
    var out = {}, has = function (p) { return L[p] && sumA(L[p]) > 0 && PD.prods.indexOf(p) >= 0; };
    PD.prods.forEach(function (p) { if (!has(p)) return; var l = PD.line[p] || '—', a = out[l] || (out[l] = { nc: 0, eq: 0 }); a.eq += sumA(L[p]); });
    Y.forEach(function (x) { var p = E.map[String(x.p || '').toUpperCase()]; if (p && has(p) && out[PD.line[p] || '—']) out[PD.line[p] || '—'].nc += x.nc; });
    return out;
  }
  var V2W = SET.poids_mois;   // weight of a month in the monthly target (config/2_reglages_pages.csv): July and August lighter
  // the year's target line by line (Mohammad, 20 Oct): each line's 2025 rate per product delivered - 25 %, times the line's 2026
  // volume month by month, summed over the lines; the NCs whose product is not in the production plan (no volume) keep their 2025
  // value - 25 %, spread over the months like a normal year. f25 / f26: the measure of a 2025 row / of a 2026 product (NCs or cost).
  // null without 2025 under the filters or without the real production plan (the charts then keep their former target).
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

  // ---------------------------------------------------------------- 5. cost explanation
  var CXP = D.cnqp || null;   // the cost model's settings (config/2_cout_*.csv, 3_cout_*.csv), from the backend
  var CX_STEPS = [['alert', 'alert'], ['writing', 'write'], ['support', 'support'], ['setup', 'work'], ['hands', 'work'], ['recheck', 'recheck']];
  var CX_RF = { alert: 0, write: 1, support: 2, work: 3, recheck: 4, eng: 5, part: 6, label: 7, basis: 8 };
  function cxSteps(n) { return n[40] || [0, 0, 0, 0, 0, 0, 0, 0]; }
  // EUR per hour of a step, by who does it (production, quality, ME); one rate before 20 Oct
  function cxRate(k) { var P = CXP.p, R = P.rates || {}; return R[k] != null ? R[k] : P.rate; }
  function cxEur(st) { return CX_STEPS.reduce(function (a, s2, j) { return a + (st[j] || 0) / 60 * cxRate(s2[0]); }, 0); }
  function cxRule(n) { return CXP.rules[n[6]] || null; }
  function cxAdj(n) {   // customer return: the flat extra or the real amount, i.e. what the level-3 cost holds beyond the steps, the material and the part (0 today)
    var f = cxRule(n), st = cxSteps(n); if (!f || !costed(n)) return 0;   // not FTO2's liability: cost 0, shown as its own line
    var on = [f[0], f[1], f[2], f[3], f[3], f[4]], e = CX_STEPS.reduce(function (a, s2, j) { return a + (on[j] ? st[j] / 60 * cxRate(s2[0]) : 0); }, 0), d = n[12] - (e + n[18] + n[17] + (n[46] || 0));
    return Math.abs(d) >= 0.05 ? d : 0;
  }
  function cxLines(nc) { return D.defects.filter(function (r) { return r[0] === nc; }).sort(function (a, b2) { return a[1] - b2[1]; }); }
  // minutes and material of one defect line, from its class (root-cause labelling, the one behind the figures); seen counts the
  // connection errors met so far in the NC: only the first takes its class time, each following one P.connNext
  function cxLine(r, seen) {
    var P = CXP.p, c = CXP.cls[dSub(r)], q = CXP.qty[r[0] + '|' + r[1]] || 1, per = c ? c[0] : P.defDefault, m = per * q;
    if (seen && P.connCls && P.connCls.indexOf(dSub(r)) >= 0) { var first = Math.max(0, Math.min(q, 1 - seen.n)); seen.n += q; m = per * first + P.connNext * (q - first); }
    return { m: m, a: (c ? c[1] : 0) * q, cls: dSub(r) && G.lang === 'en' && c ? c[2] : (dSub(r) || '—') };
  }
  function cxFactor(n) { var P = CXP.p, t = String(n[33] || '').toUpperCase(); return (P.intTypes || []).some(function (x) { return String(x).toUpperCase() === t; }) ? (P.intFactor || 1) : 1; }

  // ---------------------------------------------------------------- 6. alarms
  var ALC = { sigK: '', res: null, first: 0, last: -1 };   // the last computation: its key, the alarms, the weeks it covers
  // a sub-code that only says the defect has none yet: "T04 (non précisé)" (a new line not yet labelled by the AI pass), "Non codé".
  // New lines all land there until they are labelled, which looks like a rise: no alarm on them (3 Nov)
  var PLACEHOLDER = new RegExp(window.FTO2_PLACEHOLDER);   // sub-codes "not specified": no alarm on them (config/2_reglages_pages.csv)
  function alNc(n) { return ours(n) && n[23] !== 'client' && (!GF.phase || n[24] === GF.phase) && (GF.src === 'all' || (GF.src === 'man' ? n[39] !== 'sky' : n[39] === GF.src)) && (!GF.org || (n[41] || 'normal') === GF.org) && (GF.liab === 'fso' || GF.liab.indexOf(liabCat(n)) >= 0); }
  function alCompute(at) {   // at: a week index instead of the period's end (checks)
    var E = D.eqmsn && D.eqmsn.wdw; if (!E) return null;
    var last = at != null ? at : ALARM.lastDone(GF.to < D.meta.to ? GF.to : D.meta.to), k = [GF.phase, GF.src, GF.org, GF.liab, last, G.lang].join('|');
    if (k === ALC.sigK) return ALC.res;
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
      if (co && !PLACEHOLDER.test(co)) { add(it(l, 'code', co, e), i, n[0], dk); tally(cnt.code, l + '|' + co, ca); }   // no alarm on a placeholder sub-code (3 Nov)
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
    ALC.first = first; ALC.last = last; ALC.sigK = k;
    ALC.res = last < first ? [] : ALARM.run(Object.keys(items).map(function (x) { return items[x]; }), first, last, function (a) {
      return a.lv === 'cat' ? a.line + '|all|' : a.lv === 'rca' ? a.line + '|cat|' + dom(cnt.rca[a.line + '|' + a.v]) : a.lv === 'code' ? a.line + '|rca|' + dom(cnt.code[a.line + '|' + a.v]) : ''; },
      Object.keys(planes).map(function (x) { return planes[x]; }), acts);
    return ALC.res;
  }

  // ---------------------------------------------------------------- 7. results (what the Slate functions return)
  // Each result is plain data (no function inside), so that a Slate function can hand it to the page. The page computes the
  // same results itself when no Slate function is used (the laptop, or Skywise without the functions).

  // the measures the targets are computed for: [value of a 2026 NC, value of a 2025 row, value of a 2026 product]
  var MEASURES = {
    nc: [function () { return 1; }, function (x) { return x.nc; }, function (o) { return o.NC; }],
    cost: [function (n) { return n[12]; }, function (x) { return x.cost; }, function (o) { return o.COST; }]
  };
  // the targets and the forecast for the current filters: per measure, the months (done and to come) and the target line by line
  function objectifs() {
    var out = { months: v2Months() }, all = out.months.act.concat(out.months.fc);
    Object.keys(MEASURES).forEach(function (k) {
      var m = MEASURES[k], S2 = v2Series(m[0]), T = v2Tgt(m[1], m[2]);
      if (T) {   // the target of each month as a table: tm(m) is a function, which a Slate function cannot hand over
        var tmm = {}; all.concat(PD ? PD.months : []).forEach(function (mm) { tmm[mm] = T.tm(mm); });
        T = { lines: T.lines, out25: T.out25, outT: T.outT, year: T.year, tmm: tmm };
      }
      out[k] = { S2: S2, T: T };
    });
    out.lines = lineTargets();
    out.outK = PD ? v2OutK(out.months).k : 0;   // the NCs out of the production plan: months to come against months done
    return out;
  }
  // each line's NCs per MSN against its target: 2026 rate (v), 2025 rate (b), target (t = b x V2CUT, or v x V2CUT as a placeholder (ph)
  // when the line has no 2025); lines with less than EQMIN MSN built are left out
  function lineTargets() {
    if (!PD || !PA) return null;
    var by = {}; P_().forEach(function (o) { var l = o.line || '—', a = by[l] || (by[l] = { l: l, nc: 0, eq: 0 }); a.nc += o.NC; a.eq += o.EQ; });
    var B = y25Lines();
    return lineOrder(Object.keys(by)).map(function (l) { return by[l]; }).filter(function (a) { return a.eq >= EQMIN; }).map(function (r) {
      var b = B && B[r.l]; r.v = r.nc / r.eq;
      if (b && b.eq >= EQMIN && b.nc > 0) { r.b = b.nc / b.eq; r.t = r.b * V2CUT; } else { r.t = r.v * V2CUT; r.ph = true; }
      return r;
    });
  }
  // the bell's list for the current filters: the alarms and the weeks they cover
  function alarmes() { var res = alCompute(); return { res: res, first: ALC.first, last: ALC.last }; }
  // "Expliquer le calcul" for one NC: euros of each step, work factor, adjustment (customer return: what the cost holds beyond the
  // steps; for the current cost mode) and each defect line [seq, minutes, material EUR, class in French, class in English]
  function coutNc(n, lines) {   // lines: the NC's defect lines in order (cxLines), when already at hand
    var st = cxSteps(n), seen = { n: 0 };
    return { eur: CX_STEPS.map(function (s2, j) { return (st[j] || 0) / 60 * cxRate(s2[0]); }), factor: cxFactor(n), adj: cxAdj(n),
      lines: (lines || cxLines(n[0])).map(function (r) { var c = cxLine(r, seen), sub = dSub(r), k = CXP.cls[sub]; return [r[1], c.m, c.a, sub || '—', sub && k ? k[2] : sub || '—']; }) };
  }
  // every NC, for the Slate function: the adjustment for FTO2's cost (adj) and for the cost of every NC (adjAll: REC phase, "Toutes les NC")
  function cout() {
    if (!CXP) return null;
    var out = {}, keep = [GF.cost, GF.phase], by = {};
    D.defects.forEach(function (r) { (by[r[0]] || (by[r[0]] = [])).push(r); });   // each NC's lines, in the order of cxLines
    D.ncs.forEach(function (n) { out[n[0]] = coutNc(n, (by[n[0]] || []).sort(function (a, b2) { return a[1] - b2[1]; })); });
    GF.cost = 'all'; GF.phase = 'REC'; costMode();   // only the adjustment changes with the cost mode
    D.ncs.forEach(function (n) { out[n[0]].adjAll = cxAdj(n); });
    GF.cost = keep[0]; GF.phase = keep[1]; costMode();
    return out;
  }

  // ---------------------------------------------------------------- 8. in a Slate function: the filters the page asks for
  // The page sends a list of requests through the Slate variable v_fto2_filtres: {n: calculation, k: its key, f: the filters}.
  // Each function computes the requests for its own calculation, for each set of filters, and answers {results: {key: result}}.
  function appliquer(f) {   // put the page's filters in place, then the selection and the production that follow from them
    var g = f.gf || {}; Object.keys(g).forEach(function (k) { GF[k] = g[k]; }); GF.preset = 'custom';
    G.minor = f.minor !== false; G.lang = f.lang === 'en' ? 'en' : 'fr';
    if (f.pr) { PR.src = f.pr[0]; PR.ver = f.pr[1]; }
    pickPrep(); select(); PD = pSrc() ? pData() : null; PA = PD ? pAgg(PD) : null;
  }
  function repondre(name, requests) {
    var run = { objectifs: objectifs, alarmes: alarmes }[name], out = {};
    (requests || []).forEach(function (q) { if (q && q.n === name && !(q.k in out)) { appliquer(q.f || {}); out[q.k] = run(); } });
    return { results: out };
  }
  /* ===== MODEL END ===== */

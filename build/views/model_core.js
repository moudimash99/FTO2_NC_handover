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

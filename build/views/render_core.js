  // ================================================================ the views' display (way 2): draws the model, computes nothing
  // It receives the model (the Slate function's result) and sends the filters back; every number it shows is in the model. The
  // words are the dashboard's (STR, GX, GSTR, copied in above by build_way2.py) and the page uses the dashboard's ids and classes,
  // so its CSS applies unchanged. Each chart is drawn as the dashboard draws it in its 'vues' mode (v2Trend, v2Target, vBump,
  // the slope chart of v2Quarters, vBub, g78 through pTrend, g54, the Pareto boards), from the model instead of the tables:
  // a change to one of those drawings in the dashboard has to be copied here.
  Object.assign(STR.fr, { vuLoading: 'Calcul…', vuErr: 'Le calcul a échoué : {m}' });
  Object.assign(STR.en, { vuLoading: 'Computing…', vuErr: 'The computation failed: {m}' });
  var G = { lang: 'fr', cab: false }, TIP = null, CODES = {};
  function pk() { return ''; }   // the dashboard's click-to-filter on chart marks: not on this page
  function codeName(c) { var x = CODES[c]; return x ? c + ' · ' + x : c; }
  function segHtml(items, cur, attr) { return items.map(function (p) { return '<button type="button" ' + attr + '="' + p[0] + '" aria-pressed="' + (String(cur) === String(p[0])) + '">' + esc(p[1]) + '</button>'; }).join(''); }
  function opts(el, items, cur) { el.innerHTML = items.map(function (p) { return '<option value="' + esc(p[0]) + '"' + (p[0] === cur ? ' selected' : '') + '>' + esc(p[1]) + '</option>'; }).join(''); }
  function sumA(a) { var s = 0; a.forEach(function (v) { s += v || 0; }); return s; }
  function words(q, h) { h = h.toLowerCase(); return !q || q.split(/\s+/).every(function (w) { return h.indexOf(w) >= 0; }); }
  var GF0 = { src: 'all', org: '', fto2: true, phase: 'SERIE', line: '', preset: 'ytd' };
  var SLOTS = { syn: ['VN', 'VT', 'a:bump', 'VQ', 'a:bub'], det: ['a:bump', '78', '54'] }, VCARD = { 'a:bump': 1, 'a:bub': 1 };

  function create(root, send) {
    var M = null, F = null, TAB = 'syn', PMODE = 'vol', PF = {}, PQ = '', PLIM = 100, NQ = '', NLIM = 100, PIN = null;
    var ALS = { open: false, more: false }, OPEN = null, RUN = [], OPENED = 0, lastTap = 0;
    var REDUCE = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var $ = function (id) { return document.getElementById(id); };
    function band(v, k) {
      var body = VCARD[k] ? '<article class="vcard"><div class="vbody"></div><div class="vlegend" hidden></div><details class="vdata"><summary></summary><div class="table-wrap"><table class="mini"></table></div></details></article>'
        : '<article class="gcard"><div class="vbody"></div><div class="vlegend" hidden></div></article>';
      return '<div class="vu-slot" data-slot="' + k + '"><div class="card wide mk-band v2-band vu-band" data-v2="' + k + '" data-view="' + v + '"><div class="bhead"><span class="kicker"></span><h3></h3><p class="sub"></p>' +
        '<button type="button" class="vu-x" data-vux="' + v + '|' + k + '"></button></div><div class="custom mk-body">' + body + '</div></div></div>';
    }
    function table(id, n) { return '<details class="detail" id="' + id + 'd"><summary><span id="' + id + 'T"></span><span class="count" id="' + n + '"></span></summary><div class="inner"><input type="search" id="' + id + 'q" autocomplete="off">' +
      '<div class="table-wrap"><table><thead><tr id="' + id + 'th"></tr></thead><tbody id="' + id + 'tb"></tbody></table></div><button type="button" class="more" id="' + id + 'm" hidden></button></div></details>'; }
    root.innerHTML =
      '<div class="wrap"><header><div class="topbar"><div class="unit">FTO2 · <span id="vUnit"></span></div><div class="right"><span class="asof" id="asof"></span>' +
      '<div class="al-wrap" id="alWrap"><button type="button" class="al-btn" id="alBtn" aria-haspopup="dialog" aria-expanded="false" aria-controls="alPop" hidden><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M12 2.5a6.5 6.5 0 0 0-6.5 6.5v3.4l-1.8 3.1A1 1 0 0 0 4.6 17h14.8a1 1 0 0 0 .9-1.5l-1.8-3.1V9A6.5 6.5 0 0 0 12 2.5zm-2.6 16a2.7 2.7 0 0 0 5.2 0z"/></svg><span class="al-n" id="alN" hidden></span></button>' +
      '<div class="al-pop" id="alPop" role="dialog" aria-labelledby="alT" hidden></div></div>' +
      '<div class="seg lang" role="group" aria-label="Langue / Language"><button type="button" data-lang="fr">FR</button><button type="button" data-lang="en">EN</button></div></div></div>' +
      '<div class="titles"><h1 id="vTitle"></h1><p class="period" id="period"></p></div>' +
      '<section class="fbar" aria-labelledby="fbLab"><h2 class="fb-title" id="fbLab"></h2><div class="fb-row">' +
      '<div class="fb"><label for="gSrc" id="lSrc"></label><select id="gSrc"></select></div>' +
      '<div class="fb"><label for="gOrg" id="lOrg"></label><select id="gOrg"></select></div>' +
      '<div class="fb"><span id="gPlantLab"></span><button type="button" role="switch" class="switch" id="gPlant" aria-labelledby="gPlantLab"><i aria-hidden="true"></i><b id="gPlantTxt"></b></button></div>' +
      '<div class="fb"><span id="gPhLab"></span><div class="seg" role="radiogroup" aria-labelledby="gPhLab" id="gPhase"></div></div>' +
      '<div class="fb"><label for="gLine" id="lLine"></label><select id="gLine"></select></div>' +
      '<div class="fb"><label for="gPreset" id="lPer"></label><div class="fb-dates"><select id="gPreset"></select><input type="date" id="gFrom"><span class="mu" aria-hidden="true">→</span><input type="date" id="gTo"></div></div>' +
      '<div class="fb"><span id="miLab"></span><div class="seg" role="group" aria-labelledby="miLab" id="gMinor"></div></div>' +
      '<button type="button" class="fb-reset" id="gReset" hidden></button></div><div class="fb-sumrow"><p class="fb-sum" id="fbSum" aria-live="polite"></p></div></section></header>' +
      '<div class="tabs" role="tablist" id="tabs"><button type="button" role="tab" id="tab-syn" aria-controls="p-syn" data-tab="syn"></button><button type="button" role="tab" id="tab-det" aria-controls="p-det" data-tab="det"></button></div>' +
      '<div class="panel vu" role="tabpanel" id="p-syn" aria-labelledby="tab-syn"><div class="figs" id="vuSF"></div><div class="vu-grid" id="vuSynGrid">' + SLOTS.syn.map(function (k) { return band('syn', k); }).join('') + '</div>' + table('n', 'nn') + '</div>' +
      '<div class="panel vu" role="tabpanel" id="p-det" aria-labelledby="tab-det" hidden><div class="figs" id="vuDF"></div><div class="vu-par" id="vuPar">' +
      '<div class="controls"><div class="ctl"><span class="label" id="pmLab"></span><div class="seg" role="group" aria-labelledby="pmLab" id="pMode"></div></div>' +
      '<div class="ctl"><span class="label" id="pcLab"></span><div class="seg" role="group" aria-labelledby="pcLab" id="pCab"></div></div></div>' +
      '<section class="psec" id="pVol"><div class="chips" id="pc" hidden></div><div class="grid" id="pg"></div><div class="vu-grid" id="vuDetGrid">' + SLOTS.det.map(function (k) { return band('det', k); }).join('') + '</div>' +
      table('p', 'pn') + '</section></div></div>' +
      '<div class="vu-ov" id="vuOv" hidden><div class="vu-scrim" id="vuScrim"></div><div class="vu-panel" id="vuPanel" role="dialog" aria-modal="true"><div class="vu-top"><button type="button" class="vu-close" id="vuClose"></button></div><div id="vuHold"></div></div></div>' +
      '<div id="tip" role="tooltip" hidden></div></div>';
    TIP = $('tip');

    // ---------------------------------------------------------------- header and filter bar (the dashboard's renderBar)
    function header() {
      var f = M.meta.filters, ph = [['', 'ph_all'], ['SERIE', 'ph_SERIE'], ['REC', 'ph_REC'], ['FTI', 'ph_FTI']];
      $('vUnit').textContent = S('unit'); $('vTitle').textContent = S('title'); document.documentElement.lang = G.lang;
      $('asof').textContent = S('asof', { to: day(M.meta.to) }); $('period').textContent = S('period', { from: day(M.meta.from), to: day(M.meta.end) });
      $('fbLab').textContent = S('fbTitle'); $('lSrc').textContent = S('fSrc'); $('lOrg').textContent = S('fOrg'); $('gPlantLab').textContent = S('fPlant'); $('gPhLab').textContent = S('fPhase');
      $('lLine').textContent = S('fLine'); $('lPer').textContent = S('fPeriod'); $('miLab').textContent = S('minorLabel'); $('gReset').textContent = S('fReset');
      opts($('gSrc'), ['all', 'sky', 'man', 'gps', 'test'].map(function (k) { return [k, S('src_' + k)]; }), f.src);
      opts($('gOrg'), ['', 'normal', 'missing_ids'].map(function (k) { return [k, S('org_' + (k || 'all'))]; }), f.org);
      opts($('gLine'), [['', S('line_all')]].concat(M.meta.lines.map(function (l) { return [l, l]; })), f.line);
      opts($('gPreset'), M.meta.presets.concat(['custom']).map(function (k) { return [k, S('pr_' + k)]; }), f.preset);
      $('gPhase').innerHTML = ph.map(function (p) { return '<button type="button" role="radio" data-ph="' + p[0] + '" aria-checked="' + (f.phase === p[0]) + '" tabindex="' + (f.phase === p[0] ? 0 : -1) + '">' + esc(S(p[1])) + '</button>'; }).join('');
      $('gPlant').setAttribute('aria-checked', String(!!f.fto2)); $('gPlantTxt').textContent = S(f.fto2 ? 'fYes' : 'fNo');
      ['gFrom', 'gTo'].forEach(function (id, i) { var el = $(id); el.value = i ? M.meta.end : M.meta.from; el.min = M.meta.dmin; el.max = M.meta.dmax; });
      $('gMinor').innerHTML = segHtml([['1', S('minorIn')], ['0', S('minorOut')]], f.minor ? '1' : '0', 'data-min');
      $('gReset').hidden = Object.keys(GF0).every(function (k) { return f[k] === GF0[k]; });
      $('fbSum').textContent = S('fbSum', { n: num(M.meta.nSel), d: num(M.meta.nDef) });
      root.querySelectorAll('.seg.lang button').forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-lang') === G.lang)); });
      $('tab-syn').textContent = S('tabSyn'); $('tab-det').textContent = S('tabDet'); $('vuClose').textContent = S('vuClose');
      $('tab-syn').setAttribute('aria-selected', String(TAB === 'syn')); $('tab-det').setAttribute('aria-selected', String(TAB === 'det'));
      $('p-syn').hidden = TAB !== 'syn'; $('p-det').hidden = TAB !== 'det';
    }
    function ask(ch) {   // a filter changed: the new filters go to Slate (the function computes a new model)
      F = Object.assign({}, M ? M.meta.filters : {}, ch); if (ch.preset && ch.preset !== 'custom') { delete F.from; delete F.to; }
      $('fbSum').textContent = S('vuLoading'); send(F);
    }

    // ---------------------------------------------------------------- headline figures (the dashboard's vuFigs)
    function fig(v, lab, sub) { return '<div class="fig"><b>' + esc(v) + '</b><span>' + esc(lab) + '</span>' + (sub ? '<small>' + sub + '</small>' : '') + '</div>'; }
    function gapTx(r) { if (!r || !r.t) return ''; var g = r.v / r.t - 1; return '<span class="' + (g > 0 ? 'vu-up' : 'vu-down') + '">' + (g > 0 ? '+' : '') + pct0(g * 100) + '</span> ' + esc(S('vuVsT', { t: f2(r.t) })); }
    function figs() {
      var f = M.syn.figs, nl = S(M.meta.filters.preset === 'ytd' ? 'vuNcY' : 'vuNcP');
      $('vuSF').innerHTML = fig(num(f.nc), nl, f.ncFc != null ? esc(S('vuFc', { f: num(Math.round(f.ncFc)), t: num(Math.round(f.ncTgt)) })) : '') +
        fig(f.rate ? f2(f.rate.v) : '—', S('vuRate'), gapTx(f.rate)) +
        fig(f.cost != null ? kE(f.cost) : '—', S('vuCost'), f.costFc != null ? esc(S('vuFc', { f: kE(f.costFc), t: kE(f.costBud) })) : '') + fig(num(f.ret), S('vuRet'), esc(eur(f.retCost)));
      var d = M.det.figs, pv = function (v) { return d.prev ? esc(S('vuPrevP', { v: v })) : ''; };
      $('vuDF').innerHTML = fig(num(d.now.n), nl, pv(d.prev && num(d.prev.n))) + fig(num(d.now.d), S('vuDef'), pv(d.prev && num(d.prev.d))) +
        fig(d.rate ? f2(d.rate.v) : '—', S('vuRateY'), gapTx(d.rate)) + fig(eurK(d.now.c), S('vuCost'), pv(d.prev && eurK(d.prev.c)));
    }

    // ---------------------------------------------------------------- the charts, drawn as the dashboard draws them, from the model
    function card(v, k) { return root.querySelector('.vu-band[data-view="' + v + '"][data-v2="' + k + '"]'); }
    function set(c, html, legend, tbl) {
      c.querySelector('.vbody').innerHTML = html; var l = c.querySelector('.vlegend'); l.innerHTML = legend || ''; l.hidden = !legend;
      var d = c.querySelector('article > details.vdata'); if (d) { d.querySelector('summary').textContent = S('dataView'); c.querySelector('table.mini').innerHTML = tbl || ''; d.hidden = !tbl; }
    }
    function none(c, msg) { set(c, '<p class="empty">' + esc(msg) + '</p>'); }
    function wd(c, min) { return Math.max(c.querySelector('.vbody').clientWidth || 520, min || 300); }
    function drawCard(v, k) {
      var c = card(v, k); if (!c) return; var h = v2Head(k), X = v === 'syn' ? M.syn : M.det;
      c.querySelector('.kicker').textContent = h[0]; c.querySelector('h3').textContent = h[1]; c.querySelector('.sub').textContent = h[2];
      var vx = c.querySelector('.vu-x'); vx.innerHTML = '<span aria-hidden="true">⤢</span>'; vx.title = S('vuOpen'); vx.setAttribute('aria-label', S('vuOpen'));
      ({ VN: function () { drawTrend(c, M.syn.trend); }, VT: function () { drawTarget(c, M.syn.target, M.syn.unplanned); }, 'a:bump': function () { drawBump(c, X.bump); },
         VQ: function () { drawVq(c, M.syn.quarters); }, 'a:bub': function () { drawBub(c, M.syn.bubbles); }, '78': function () { drawConn(c, M.det.connections); }, '54': function () { drawTop(c, M.det.top); } })[k]();
    }
    // v2TgtBars: 2025 and the year's target as two stacked bars, one colour per line
    function tgtBars(bars, Y, x0, bw, fmt, H, key) {
      var g = '';
      bars.forEach(function (b, j) { var x = x0 + j * (bw + 8), acc = 0, lab = j ? S(key) : '2025', tot = sumA(b[1].map(function (s2) { return s2.v; }));
        b[1].forEach(function (s2) { if (s2.v <= 0) return; var y1 = Y(acc + s2.v), y0 = Y(acc);
          g += '<rect x="' + r1(x) + '" y="' + r1(y1) + '" width="' + r1(bw) + '" height="' + r1(Math.max(0.5, y0 - y1 - 1)) + '" fill="' + lineCol(s2.l) + '"' + tip(lab + ' · ' + s2.l, [fmt(s2.v)].concat(s2.out > 0.5 ? [S('v2InclOut', { n: fmt(s2.out) })] : [])) + '/>'; acc += s2.v; });
        g += tx(x + bw / 2, Y(tot) - 6, fmt(tot), 'ink b', 'middle') + tx(x + bw / 2, H - 6, lab, 'ink', 'middle'); });
      return g;
    }
    function drawTrend(c, T) {   // v2Trend
      if (!T) { none(c, gx('noData')); return; }
      var all = T.months, na = T.na, n = all.length, year = T.year, tgt = T.tgt, y25 = T.y25, real = T.real, byL = T.byLine, cum = T.cum, ct = T.ct, c25 = T.c25;
      var W0 = wd(c, 300), cp = W0 < 560, ml = cp ? 34 : 40, lb = byL ? (cp ? 70 : 112) : (cp ? 44 : 70), gap = cp ? 14 : 34, mr = cp ? 54 : 118, mt = 22, mb = 26, H = cp ? 260 : 300, ph = H - mt - mb, x1 = ml + lb + gap, pw = W0 - x1 - mr;
      var nt = pNice(Math.max(y25, year, tgt, 1) * 1.08), g = '';
      function Y(v) { return mt + ph - v / nt.top * ph; } function X(i) { return x1 + i / n * pw; }
      for (var tk = 0; tk <= nt.top + 1e-9; tk += nt.step) g += '<line x1="' + ml + '" x2="' + r1(x1 + pw) + '" y1="' + r1(Y(tk)) + '" y2="' + r1(Y(tk)) + '" stroke="var(--grid)"/>' + tx(ml - 6, Y(tk) + 4, num(tk), 'mu', 'end');
      if (byL) g += tgtBars(T.bars, Y, ml + (cp ? 6 : 10), cp ? 26 : 42, function (v) { return num(Math.round(v)); }, H, 'v2TgtBar');
      else {
        var bx = ml + (cp ? 8 : 14), bwd = lb - (cp ? 16 : 28);
        g += '<rect x="' + bx + '" y="' + r1(Y(y25)) + '" width="' + bwd + '" height="' + r1(mt + ph - Y(y25)) + '" rx="2" fill="' + tint('--ink-2', real ? 30 : 18) + '"' + (real ? '' : ' stroke="var(--ink-2)" stroke-opacity=".5" stroke-dasharray="3 3"') + tip('2025', [gx('ncCount', { n: num(Math.round(y25)) }), S(real ? 'v2Y25b' : 'v2Ph')]) + '/>' +
          tx(bx + bwd / 2, Y(y25) - 6, num(Math.round(y25)), 'ink b', 'middle') + tx(bx + bwd / 2, H - 6, '2025', 'ink', 'middle');
      }
      all.forEach(function (x, i) { g += tx(X(i + 0.5), H - 6, v2Mo(x.m, pw / n, i), 'mu', 'middle'); });
      g += '<path d="M' + r1(X(0)) + ',' + r1(Y(0)) + 'L' + cum.slice(0, na + 1).map(function (v, i) { return r1(X(i)) + ',' + r1(Y(v)); }).join('L') + 'L' + r1(X(na)) + ',' + r1(Y(0)) + 'Z" fill="' + tint('--s1', 10) + '"/>';
      g += '<path d="M' + cum.slice(0, na + 1).map(function (v, i) { return r1(X(i)) + ',' + r1(Y(v)); }).join('L') + '" fill="none" stroke="var(--s1)" stroke-width="2"/>';
      if (n > na) g += '<path d="M' + cum.slice(na).map(function (v, i) { return r1(X(na + i)) + ',' + r1(Y(v)); }).join('L') + '" fill="none" stroke="var(--s1)" stroke-width="2" stroke-dasharray="1 5" stroke-linecap="round"/>';
      if (c25) g += '<path d="M' + c25.map(function (v, i) { return r1(X(i)) + ',' + r1(Y(v)); }).join('L') + '" fill="none" stroke="' + tint('--ink-2', 55) + '" stroke-width="1.5"/>';
      g += '<path d="M' + ct.map(function (v, i) { return r1(X(i)) + ',' + r1(Y(v)); }).join('L') + '" fill="none" stroke="var(--ink)" stroke-width="1.3" stroke-dasharray="5 4"/>';
      all.slice(0, na).forEach(function (x, i) { var over = x.v > x.tgt;
        g += '<circle cx="' + r1(X(i + 1)) + '" cy="' + r1(Y(cum[i + 1])) + '" r="4.5" fill="' + (over ? 'var(--up)' : 'var(--down)') + '" stroke="var(--surface)" stroke-width="1.8"' +
          tip(monthName(x.m) + ' ' + x.m.slice(0, 4), [gx('ncCount', { n: num(x.v) }) + ' · ' + S('v2MonTgt', { v: num(Math.round(x.tgt)) }), S('v2Cum', { v: num(cum[i + 1]) })].concat(c25 ? [S('v2Y25at', { v: num(c25[i + 1]) })] : [])) + '/>'; });
      if (n > na) g += '<circle cx="' + r1(X(n)) + '" cy="' + r1(Y(year)) + '" r="4" fill="var(--surface)" stroke="var(--s1)" stroke-width="2"' + tip(gx('fcLeg'), [num(Math.round(year))]) + '/>';
      var ly = spread([Y(year) + 4, Y(tgt) + 4], 16, mt + 6, mt + ph);
      g += tx(X(n) + 8, ly[0], num(Math.round(year)) + (cp ? '' : ' ' + S('v2Fc')), 'ink b') + tx(X(n) + 8, ly[1], num(Math.round(tgt)) + (cp ? '' : ' ' + S('v2TgtShort')), 'ink');
      set(c, svg(W0, H, g, v2Head('VN')[1]), '<span><i class="sw" style="background:var(--down);border-radius:50%"></i>' + esc(S('v2Under')) + '</span><span><i class="sw" style="background:var(--up);border-radius:50%"></i>' + esc(S('v2Over')) + '</span>' +
        swl('var(--s1)', S('v2CumLeg')) + '<span><i class="dash" style="border-top:2px dotted var(--s1)"></i>' + esc(gx('fcLeg')) + '</span>' + swl('var(--ink)', S(byL ? 'v2TgtCumL' : real ? 'v2TgtCumR' : 'v2TgtCum'), true) +
        (byL ? T.lines.map(function (a) { return sw(lineCol(a.l), a.l + (a.ph ? ' (' + S('v2Ph') + ')' : '')); }).join('') : '') +
        (real ? (byL ? '' : '<span><i class="sw" style="background:' + tint('--ink-2', 30) + '"></i>' + esc(S('v2Y25b')) + '</span>') + swl(tint('--ink-2', 55), S('v2Y25c'))
          : '<span><i class="sw" style="background:' + tint('--ink-2', 18) + ';border:1px dashed var(--ink-2)"></i>' + esc(S('v2Ph25')) + '</span>') +
        (real && !M.meta.filters.fto2 ? '<span class="mu">' + esc(S('v2NoCli25')) + '</span>' : '') + '<span class="mu">' + esc(S('v2Summer')) + '</span>');
    }
    function drawTarget(c, rows, unpl) {   // v2Target, and its note on the NCs out of the production plan (v2UnplannedNote)
      if (!rows || !rows.length) { none(c, gx('noData')); return; }
      var byL = {}; rows.forEach(function (r) { if (!r.all) byL[r.l] = r; });
      var anyPh = rows.some(function (r) { return !r.all && r.ph; }), name = function (r) { return r.all ? S('allLines') : r.l; };
      var tipT = function (r) { return r.all ? [gx('perEq', { v: f2(r.v) }), S('v2TgtN', { a: num(r.nc), t: num(Math.round(r.tn)) }), r.b != null ? S('v2Mix', { v: f2(r.b) }) : S('v2Ph'), gx('ncEq', { n: num(r.nc), e: f1(r.eq) })]
        : [gx('perEq', { v: f2(r.v) }), (r.ph ? S('v2TgtPh') : S('v2Tgt')) + ' : ' + f2(r.t), r.b != null ? S('v2Rate25', { v: f2(r.b) }) : S('v2Ph'), gx('ncEq', { n: num(r.nc), e: f1(r.eq) })]; };
      var vbar = function (r, X, x0, yy) {
        if (r.all && r.stack) { var acc = x0, o = ''; r.stack.forEach(function (s2) { var w = X(s2.nc / r.eq) - X(0), lr = byL[s2.l] || s2;
          o += '<rect x="' + r1(acc) + '" y="' + yy + '" width="' + r1(Math.max(0, w - 1)) + '" height="8" fill="' + lineCol(s2.l) + '"' + tip(s2.l, tipT(lr)) + '/>'; acc += w; }); return o; }
        return '<rect x="' + r1(x0) + '" y="' + yy + '" width="' + r1(Math.max(2, X(r.v) - x0)) + '" height="8" rx="4" fill="' + lineCol(r.l) + '"' + tip(name(r), tipT(r)) + '/>'; };
      var tick = function (r) { return '" stroke="var(--ink)" stroke-width="2"' + (r.ph ? ' stroke-dasharray="2 2"' : '') + '/>'; };
      var W0 = wd(c, 200), stack = W0 < 440, narrow = W0 < 640, lab = stack ? 0 : narrow ? 104 : 112, mr = stack ? 0 : narrow ? 104 : 214, rh = stack ? 44 : 36, H = rows.length * rh + 6, pw = W0 - lab - mr, g = '';
      rows.forEach(function (r, i) {
        var y = i * rh + (stack ? 22 : 8), mx = Math.max(r.v, r.t, r.b || 0) * 1.18 || 1, X = function (v) { return lab + v / mx * pw; }, gap = r.t ? r.v / r.t - 1 : null;
        var gt = gap == null ? '—' : (gap > 0 ? '+' : '') + pct0(gap * 100), gs = ' style="fill:' + (gap == null ? 'var(--muted)' : gap > 0 ? 'var(--up)' : 'var(--down)') + '"';
        var b25 = r.b != null ? '<circle cx="' + r1(X(r.b)) + '" cy="' + (y + 6) + '" r="3.5" fill="var(--surface)" stroke="var(--muted)" stroke-width="1.6"' + tip(name(r), tipT(r)) + '/>' : '';
        if (stack) {
          g += tx(0, y - 6, name(r), r.all ? 'ink b' : 'ink') + tx(W0 - 10 - gt.length * 7.5, y - 6, f2(r.v), 'ink b', 'end') + tx(W0 - 2, y - 6, gt, 'b', 'end', gs);
          g += '<rect x="0" y="' + (y + 2) + '" width="' + r1(pw) + '" height="8" rx="4" fill="var(--track)"/>' + vbar(r, X, 0, y + 2) + b25 + '<line x1="' + r1(X(r.t)) + '" x2="' + r1(X(r.t)) + '" y1="' + (y - 3) + '" y2="' + (y + 15) + tick(r);
          return;
        }
        g += tx(lab - 12, y + 10, name(r), r.all ? 'ink b' : 'ink', 'end') + '<rect x="' + lab + '" y="' + (y + 2) + '" width="' + r1(pw) + '" height="8" rx="4" fill="var(--track)"/>' + vbar(r, X, lab, y + 2);
        g += b25 + '<line x1="' + r1(X(r.t)) + '" x2="' + r1(X(r.t)) + '" y1="' + (y - 3) + '" y2="' + (y + 15) + tick(r);
        g += tx(lab + pw + 12, y + 10, f2(r.v), 'ink b') + (narrow ? '' : tx(lab + pw + 58, y + 10, S('v2Tgt').toLowerCase() + ' ' + f2(r.t), 'mu')) + tx(W0 - 2, y + 10, gt, 'b', 'end', gs);
      });
      var note = unpl && unpl.length ? '<details class="vdata vnote"><summary>' + esc(S('vpOut', { n: num(unpl.length) })) + '</summary><div class="table-wrap"><table class="mini"><tbody>' +
        unpl.map(function (n) { return '<tr><td class="nc">' + esc(n[0]) + '</td><td class="num">' + esc(shortDay(n[1])) + '</td><td>' + esc(n[2]) + '</td><td>' + esc(prodName(n[3])) + '</td><td>' + esc(n[4]) + '</td></tr>'; }).join('') + '</tbody></table></div></details>' : '';
      set(c, svg(W0, H, g, v2Head('VT')[1]), sw('var(--ink-2)', S('nKR')) + (rows.some(function (r) { return !r.ph; }) ? '<span><i class="ln" style="width:2px;height:12px;background:var(--ink)"></i>' + esc(S('v2TgtR')) + '</span>' : '') +
        (anyPh ? '<span><i class="ln" style="width:0;height:12px;border-left:2px dotted var(--ink)"></i>' + esc(S('v2TgtPh')) + '</span>' : '') +
        (rows.some(function (r) { return r.b != null; }) ? '<span><i class="sw" style="border-radius:50%;background:var(--surface);border:1.6px solid var(--muted)"></i>' + esc(S('v2Rate25s')) + '</span>' : '') + note);
    }
    function drawBump(c, B) {   // vBump: the cause pressed (a line or its name) is drawn in its category's colour
      if (!B) { none(c, '—'); return; }
      var months = B.months, cs = B.causes, by = {}; cs.forEach(function (x) { by[x.rca] = x; });
      var pin = PIN && by[PIN] ? PIN : cs[0].rca, MAXR = 10;
      var W0 = wd(c, 520), right = W0 < 700 ? 160 : 210, left = 40, mt = 30, rowH = 25, H = mt + (MAXR + 1) * rowH + 8, sx = (W0 - left - right - 24) / (months.length - 1), g = '';
      function X(j) { return left + 12 + j * sx; } function row(x, j) { var k = x.ranks[j]; return k && k <= MAXR ? k : MAXR + 1; } function Y(rw) { return mt + (rw - 0.5) * rowH; }
      months.forEach(function (m, j) {
        if (m.low) g += '<rect x="' + r1(X(j) - sx / 2) + '" y="' + (mt - 4) + '" width="' + r1(sx) + '" height="' + ((MAXR + 1) * rowH + 4) + '" fill="var(--track)"' + tip(monthName(m.m), [S('lowTip', { n: num(m.vol) })]) + '/>' + tx(X(j), H - 2, S('lowVol'), 'mu', 'middle');
        g += tx(X(j), 14, monthName(m.m), 'mu', 'middle'); });
      for (var k = 1; k <= MAXR + 1; k++) g += tx(left - 8, Y(k) + 4, k <= MAXR ? String(k) : S('beyond'), 'mu', 'end');
      var order = cs.filter(function (x) { return x.rca !== pin; }).concat([by[pin]]), ends = [];
      order.forEach(function (x) {
        var hl = x.rca === pin, col = hl ? (x.cat === 'aside' ? 'var(--ink-2)' : catFill(x.cat)) : 'var(--dim)', d = '';
        months.forEach(function (m, j) { var xx = X(j), y = Y(row(x, j)); if (!j) d = 'M' + r1(xx) + ',' + r1(y); else { var x0 = X(j - 1), y0 = Y(row(x, j - 1)), xm = (x0 + xx) / 2; d += 'C' + r1(xm) + ',' + r1(y0) + ' ' + r1(xm) + ',' + r1(y) + ' ' + r1(xx) + ',' + r1(y); } });
        g += '<g class="bline' + (hl ? ' hl' : '') + '" data-pin="' + esc(x.rca) + '"><path d="' + d + '" fill="none" stroke="transparent" stroke-width="14"/><path d="' + d + '" fill="none" stroke="' + col + '" stroke-width="' + (hl ? 3 : 2) + '" stroke-linecap="round"/>';
        months.forEach(function (m, j) { var rk = x.ranks[j];
          g += '<circle cx="' + r1(X(j)) + '" cy="' + r1(Y(row(x, j))) + '" r="10" fill="transparent"' + tip(L(x.rca) + ' · ' + monthName(m.m), [rk ? S('bumpTip', { r: ord(rk), n: num(x.n[j]) }) : S('bumpNone')]) + '/>' +
            '<circle cx="' + r1(X(j)) + '" cy="' + r1(Y(row(x, j))) + '" r="' + (hl ? 5 : 4) + '" fill="' + col + '" stroke="var(--surface)" stroke-width="2" pointer-events="none"/>'; });
        g += '</g>'; ends.push({ a: x.rca, y: Y(row(x, months.length - 1)) + 4, hl: hl });
      });
      var ys = spread(ends.map(function (e) { return e.y; }), 14, mt, H - 4), xe = X(months.length - 1) + 12, maxCh = Math.floor((right - 16) / 6.6);
      ends.forEach(function (e, i) { var t = L(e.a); if (t.length > maxCh) t = t.slice(0, maxCh - 1) + '…'; g += '<text class="halo' + (e.hl ? ' ink b' : '') + '" x="' + r1(xe) + '" y="' + r1(ys[i]) + '" data-pin="' + esc(e.a) + '">' + esc(t) + '</text>'; });
      var pc = by[pin].cat;
      set(c, svg(W0, H, g, S('t_bump')), pc ? sw(pc === 'aside' ? 'var(--ink-2)' : catFill(pc), L(pin) + ' · ' + catLabel(pc)) : '',
        miniTable([S('rRca')].concat(months.map(function (m) { return monthName(m.m); })), cs.map(function (x) { return [L(x.rca)].concat(x.ranks.map(function (r, j) { return r ? ord(r) + ' (' + num(x.n[j]) + ')' : '—'; })); }), 1));
    }
    function drawVq(c, Q) {   // v2Quarters, drawn as the slope chart the dashboard shows (VQR.a)
      if (Q && Q.none) { none(c, S('vqOnly')); return; }
      if (!Q || !Q.rows.length) { none(c, gx('noData')); return; }
      var top = Q.rows, mx = 1e-9; top.forEach(function (r) { mx = Math.max(mx, r.a, r.b); });
      var dir = function (va, vb) { return vb > va * 1.1 ? 1 : vb < va * 0.9 ? -1 : 0; }, col = function (r) { return r.cat === 'aside' ? 'var(--ink-2)' : catFill(r.cat); };
      var arrow = function (d, x, y) { return d ? tx(x, y, d > 0 ? '▲' : '▼', 'b', null, ' style="fill:var(--' + (d > 0 ? 'up' : 'down') + ')"') : tx(x, y, '=', 'mu'); };
      var vtip = function (r) { var d = r.b - r.a, p = r.a > 0 ? Math.round(d / r.a * 100) : null; return tip(L(r.rca), [gx('vq25', { v: f2(r.a) }), gx('vq26', { v: f2(r.b) }), (d >= 0 ? '+' : '') + f2(d) + (p != null ? ' (' + (p >= 0 ? '+' : '') + p + ' %)' : '')]); };
      var W0 = wd(c), H = Math.max(360, top.length * 30 + 50), mt = 30, ph = H - mt - 14, xa = Math.min(250, W0 * 0.46), xb = W0 - 96, g = '';
      function Y(v) { return mt + ph - v / mx * ph; }
      g += tx(xa, 14, '2025', 'ink b', 'middle') + tx(xb, 14, '2026', 'ink b', 'middle') + '<line x1="' + xa + '" x2="' + xa + '" y1="' + mt + '" y2="' + (mt + ph) + '" stroke="var(--grid)"/><line x1="' + xb + '" x2="' + xb + '" y1="' + mt + '" y2="' + (mt + ph) + '" stroke="var(--grid)"/>';
      var la = spread(top.map(function (r) { return Y(r.a) + 4; }), 17, mt, mt + ph + 4), lb = spread(top.map(function (r) { return Y(r.b) + 4; }), 17, mt, mt + ph + 4);
      top.forEach(function (r, i) { var cc = col(r), nm = L(r.rca), mc = Math.floor((xa - 52) / 6.4); if (nm.length > mc) nm = nm.slice(0, mc - 1) + '…';
        g += '<line x1="' + xa + '" y1="' + r1(Y(r.a)) + '" x2="' + xb + '" y2="' + r1(Y(r.b)) + '" stroke="' + cc + '" stroke-width="2.2"' + vtip(r) + '/>' + '<circle cx="' + xa + '" cy="' + r1(Y(r.a)) + '" r="3.5" fill="' + cc + '"/><circle cx="' + xb + '" cy="' + r1(Y(r.b)) + '" r="3.5" fill="' + cc + '"/>';
        g += '<line x1="' + (xa - 8) + '" x2="' + xa + '" y1="' + r1(la[i] - 4) + '" y2="' + r1(Y(r.a)) + '" stroke="var(--grid)"/><line x1="' + xb + '" x2="' + (xb + 8) + '" y1="' + r1(Y(r.b)) + '" y2="' + r1(lb[i] - 4) + '" stroke="var(--grid)"/>';
        g += tx(xa - 12, la[i], nm + '  ' + f2(r.a), 'ink', 'end') + tx(xb + 12, lb[i], f2(r.b), 'ink') + arrow(dir(r.a, r.b), xb + 52, lb[i]); });
      set(c, svg(W0, H, g, v2Head('VQ')[1]), '<span><b style="color:var(--up)">▲</b> ' + esc(gx('vqUp')) + '</span><span><b style="color:var(--down)">▼</b> ' + esc(gx('vqDown')) + '</span><span>= ' + esc(gx('vqFlat')) + '</span>');
    }
    function drawBub(c, list) {   // vBub
      if (!list) { none(c, '—'); return; }
      var W0 = wd(c, 300), wide = W0 >= 900, H = W0 < 520 ? 320 : wide ? 480 : 380, ml = G.lang === 'en' ? 76 : 62, mr = 16, mt = 12, mb = 46, pw = W0 - ml - mr, ph = H - mt - mb;
      var nMin = Math.min.apply(null, list.map(function (s) { return s.n; })), nMax = Math.max.apply(null, list.map(function (s) { return s.n; })), lo = Math.log10(nMin / 1.5), hi = Math.log10(nMax * 1.5);
      var aMax = Math.max.apply(null, list.map(function (s) { return s.a; })), step = aMax <= 60 ? 10 : aMax <= 120 ? 20 : aMax <= 300 ? 50 : 100, yMax = Math.ceil(aMax * 1.12 / step) * step;
      var cMax = Math.max.apply(null, list.map(function (s) { return s.c; }));
      function X(n) { return ml + (Math.log10(n) - lo) / (hi - lo) * pw; } function Y(a) { return mt + ph - a / yMax * ph; } function R(cc) { return 3 + (wide ? 28 : 21) * Math.sqrt(cc / cMax); }
      var g = '';
      for (var y = 0; y <= yMax; y += step) g += '<line class="gl" x1="' + ml + '" x2="' + (ml + pw) + '" y1="' + r1(Y(y)) + '" y2="' + r1(Y(y)) + '"/>' + tx(ml - 8, Y(y) + 4, eur(y), 'mu', 'end');
      [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000].forEach(function (t) { if (Math.log10(t) < lo || Math.log10(t) > hi) return; g += '<line class="gl" y1="' + mt + '" y2="' + (mt + ph) + '" x1="' + r1(X(t)) + '" x2="' + r1(X(t)) + '"/>' + tx(X(t), mt + ph + 16, num(t), 'mu', 'middle'); });
      g += tx(ml + pw / 2, H - 6, S('axDef'), 'mu', 'middle') + tx(14, mt + ph / 2, S('axAvg'), 'mu', 'middle', ' transform="rotate(-90 14 ' + r1(mt + ph / 2) + ')"');
      var iso = '', nHi = Math.pow(10, hi), nLo = Math.pow(10, lo), isoBox = [];
      [1000, 5000, 20000, 50000].forEach(function (C) {
        if (C / nHi > yMax || C / nLo < yMax * 0.12) return;
        var n0 = Math.max(nLo, C / yMax), pts = [];
        for (var i = 0; i <= 40; i++) { var n = Math.pow(10, Math.log10(n0) + (hi - Math.log10(n0)) * i / 40); pts.push(r1(X(n)) + ',' + r1(Y(C / n))); }
        iso += '<path class="iso" d="M' + pts.join('L') + '"/>';
        var lx = n0 > nLo ? X(n0) + 4 : ml + 4, ly = n0 > nLo ? mt + 11 : Y(C / nLo) - 4;
        iso += tx(lx, ly, kEur(C), 'mu halo'); isoBox.push([lx - 2, ly - 11, lx + 40, ly + 3]);
      });
      var dots = list.map(function (s) { var x = X(s.n), yy = Y(s.a), r = R(s.c), gray = ASIDE[s.cat], col = gray ? 'var(--muted)' : catFill(s.cat);
        return '<g class="bub"' + tip(L(s.rca), [S('bubTip', { n: num(s.n), c: eur(s.c), a: eur(s.a) }), L(s.cat)]) + '><circle cx="' + r1(x) + '" cy="' + r1(yy) + '" r="' + r1(Math.max(r, 12)) + '" fill="transparent"/>' +
          '<circle class="dot" cx="' + r1(x) + '" cy="' + r1(yy) + '" r="' + r1(r) + '" fill="' + (gray ? 'var(--dim)' : col) + '" fill-opacity=".32" stroke="' + col + '" stroke-width="1.5"/></g>'; }).join('');
      var placed = isoBox.slice(), labs = '';
      function clear(b, p) { return b[2] < p[0] || b[0] > p[2] || b[3] < p[1] || b[1] > p[3]; }
      function free(b, self) {
        if (b[0] < ml || b[2] > ml + pw || b[1] < mt || b[3] > mt + ph) return false;
        return placed.every(function (p) { return clear(b, p); }) && list.every(function (s) { if (s === self) return true; var r = R(s.c) * 0.7; return clear(b, [X(s.n) - r, Y(s.a) - r, X(s.n) + r, Y(s.a) + r]); });
      }
      var byAvg = list.filter(function (s) { return s.n >= 10; }).sort(function (a, b) { return b.a - a.a; })[0];
      var nLab = wide ? 15 : 9;
      list.slice(0, nLab).concat(byAvg && list.indexOf(byAvg) >= nLab ? [byAvg] : []).forEach(function (s) {
        var x = X(s.n), yy = Y(s.a), r = R(s.c), t = L(s.rca), w = t.length * 6.3 + 4;
        var tries = [[x + r + 4, yy + 4, 'start', [x + r + 2, yy - 9, x + r + 6 + w, yy + 5]], [x - r - 4, yy + 4, 'end', [x - r - 6 - w, yy - 9, x - r - 2, yy + 5]],
          [x, yy - r - 5, 'middle', [x - w / 2, yy - r - 18, x + w / 2, yy - r - 3]], [x, yy + r + 14, 'middle', [x - w / 2, yy + r + 2, x + w / 2, yy + r + 17]]];
        for (var i = 0; i < tries.length; i++) { if (free(tries[i][3], s)) { placed.push(tries[i][3]); labs += tx(tries[i][0], tries[i][1], t, 'ink halo', tries[i][2] === 'start' ? null : tries[i][2]); break; } }
      });
      var cin = {}; list.forEach(function (s) { cin[catKey(s.cat)] = 1; });
      var leg = MAIN_CATS.filter(function (k) { return cin[k]; }).map(function (k) { var cc = k === 'aside' ? 'var(--muted)' : catFill(k); return '<span><i class="sw ring" style="background:' + tint(k === 'aside' ? '--dim' : '--c' + CATC[k], 32) + ';border-color:' + cc + '"></i>' + esc(catLabel(k)) + '</span>'; }).join('') +
        '<span class="mu">' + esc(S('bubLeg')) + '</span><span><i class="dash"></i>' + esc(S('isoLeg')) + '</span>';
      set(c, svg(W0, H, g + iso + dots + labs, S('t_bub')), leg, miniTable([S('rRca'), S('rCat'), S('hDef'), S('hCost'), S('hPerDef')], list.map(function (s) { return [L(s.rca), L(s.cat), num(s.n), eur(s.c), eur(s.a)]; }), 2));
    }
    function drawConn(c, C) {   // g78, drawn by pTrend: the month, the period's mean, the 3-month mean, 2025
      if (C && C.none) { none(c, S('connOnly')); return; }
      if (!C) { none(c, gx('noData')); return; }
      var rows = C.months, col = tint('--c2', 100), W0 = wd(c), ml = 46, mr = 92, mt = 16, h = 220, H = mt + h + 26, pw = W0 - ml - mr, r = rows.map(function (x) { return x.r; }), mean = C.mean, ref = C.y25;
      var nt = pNice(Math.max.apply(null, r.concat(ref != null ? [ref] : [])) * 1.1), g = '';
      function X(j) { return ml + j / (rows.length - 1) * pw; } function Y(v) { return mt + h - v / nt.top * h; }
      g += pGridY(ml, pw, Y, nt, f2) + '<line x1="' + ml + '" x2="' + (ml + pw) + '" y1="' + r1(Y(mean)) + '" y2="' + r1(Y(mean)) + '" stroke="var(--ink-2)"/>';
      g += '<path d="' + rows.map(function (x, j) { return (j ? 'L' : 'M') + r1(X(j)) + ',' + r1(Y(x.roll)); }).join('') + '" fill="none" stroke="var(--ink-2)" stroke-width="1.5" stroke-dasharray="4 3"/>';
      g += '<path d="' + r.map(function (v, j) { return (j ? 'L' : 'M') + r1(X(j)) + ',' + r1(Y(v)); }).join('') + '" fill="none" stroke="' + col + '" stroke-width="2.2"/>';
      rows.forEach(function (x, j) { g += '<circle cx="' + r1(X(j)) + '" cy="' + r1(Y(x.r)) + '" r="4" fill="' + col + '" stroke="var(--surface)" stroke-width="1.5"' + tip(monthName(x.m), [gx('perEq', { v: f2(x.r) }), gx('rollTip', { v: f2(x.roll) }), gx('eqTip', { v: f1(x.e) })]) + '/>' + tx(X(j), H - 6, monthName(x.m), 'mu', 'middle'); });
      g += tx(ml + pw + 8, Y(mean) + 4, gx('mean') + ' ' + f2(mean), 'mu');
      if (ref != null) { var yr = spread([Y(mean) + 4, Y(ref) + 4], 14, mt, mt + h)[1]; g += '<line x1="' + ml + '" x2="' + (ml + pw) + '" y1="' + r1(Y(ref)) + '" y2="' + r1(Y(ref)) + '" stroke="var(--up)" stroke-width="1.5" stroke-dasharray="6 4"/>' + tx(ml + pw + 8, yr, '2025 ' + f2(ref), 'b', null, ' style="fill:var(--up)"'); }
      set(c, svg(W0, H, g, gT('78')), swl(col, gx('monthLeg')) + swl('var(--ink-2)', gx('mean')) + swl('var(--ink-2)', gx('roll3'), true) + (ref != null ? swl('var(--up)', S('v2Avg25'), true) : ''));
    }
    function drawTop(c, os) {   // g54
      if (!os) { none(c, gx('noData')); return; }
      var W0 = wd(c), cols = W0 >= 480 ? 2 : 1, gap = 26, pw = (W0 - gap * (cols - 1)) / cols, cellH = 100, H = Math.ceil(os.length / cols) * cellH, g = '', mx = 1e-9;
      os.forEach(function (o) { o.top.forEach(function (t) { mx = Math.max(mx, t.v); }); });
      os.forEach(function (o, n) {
        var x0 = (n % cols) * (pw + gap), y0 = Math.floor(n / cols) * cellH, lw = Math.min(150, pw * 0.48);
        g += tx(x0, y0 + 14, o.p, 'ink b') + tx(x0 + pw, y0 + 14, gx('perEq', { v: f2(o.rate) }), 'mu', 'end');
        o.top.forEach(function (t, j) { var y = y0 + 24 + j * 22, w = t.v / mx * (pw - lw - 40);
          g += tx(x0 + lw - 6, y + 12, trunc(L(t.rca), lw - 8), 'ink', 'end', ' style="font-size:11.5px"') + '<rect x="' + r1(x0 + lw) + '" y="' + (y + 3) + '" width="' + r1(Math.max(1.5, w)) + '" height="12" rx="2" fill="' + catFill(t.cat) + '"' + tip(o.p + ' · ' + L(t.rca), [gx('perEq', { v: f2(t.v) }), gx('defN', { n: num(t.n) })]) + '/>' + tx(x0 + lw + w + 5, y + 13, f2(t.v), 'mu', null, ' style="font-size:11px"'); });
      });
      set(c, svg(W0, H, g, gT('54')));
    }

    // ---------------------------------------------------------------- Détail's Pareto (the dashboard's two boards), one level at a time, full width
    var LV = { cat: { t: 'dCat', sub: 'paretoSub', pareto: true, key: true }, rca: { t: 'dRca', top: 15, key: true }, code: { t: 'dCode', sub: 'codeSub', top: 15, longName: true, ckey: true } };
    function showV(k, v) { return k === 'cat' ? (v === '__none' ? S('noLine') : L(v)) : k === 'rca' ? L(v) : codeName(v); }
    function paretoDraw() {
      var vol = PMODE === 'vol', f = PF, lvl = !f.cat ? 'cat' : !f.rca ? 'rca' : 'code', d = LV[lvl], sp = G.cab, fmt = vol ? num : eurK;
      $('pmLab').textContent = S('measureLabel'); $('pcLab').textContent = S('cabLabel');
      $('pMode').innerHTML = segHtml([['vol', S('mVol')], ['cost', S('mCost')]], PMODE, 'data-pmode');
      $('pCab').innerHTML = segHtml([['0', S('cabHide')], ['1', S('cabShow')]], G.cab ? '1' : '0', 'data-pcab');
      var m = {}, m2 = {}, e0 = {}, e1 = {}, ck = {};
      M.det.pareto[lvl].forEach(function (u) {
        if ((lvl !== 'cat' && u.cat !== f.cat) || (lvl === 'code' && u.rca !== f.rca) || (vol && !u.d)) return;   // the volume counts defect lines: an NC with no line is in the cost only
        var v = u[lvl]; m[v] = (m[v] || 0) + (vol ? u.d : u.cost); m2[v] = (m2[v] || 0) + (vol ? u.cb : u.cbc);
        if (vol) e0[v] = (e0[v] || 0) + u.nc; else { e0[v] = (e0[v] || 0) + u.d; e1[v] = (e1[v] || 0) + u.nc; }
        ck[v] = catKey(u.cat);
      });
      var vals = Object.keys(m).sort(function (x, y) { return m[y] - m[x] || (x < y ? -1 : 1); });
      if (d.pareto) vals = vals.filter(function (v) { return !ASIDE[v]; }).concat(vals.filter(function (v) { return ASIDE[v]; }));
      if (d.top) vals = vals.slice(0, d.top);
      var max = Math.max.apply(null, vals.map(function (v) { return m[v]; }).concat([1e-9])), totMain = 0, cum = 0, sepDone = false, act = lvl in f;
      if (d.pareto) vals.forEach(function (v) { if (!ASIDE[v]) totMain += m[v]; });
      var ex = vol ? [['hNc', e0, ncShareFmt]] : [['hDef', e0, num], ['hNc', e1, ncShareFmt]];
      var keys = d.key ? '<div class="key" data-key="1"' + (sp ? '' : ' hidden') + '><span><i></i>' + esc(S('keyOther')) + '</span><span><i class="c"></i>' + esc(S('keyCable')) + '</span></div>' : '';
      var cin = {}; vals.forEach(function (v) { cin[ck[v]] = 1; });
      if (d.ckey) keys += '<div class="key" data-ckey="1"' + (sp ? ' hidden' : '') + '>' + MAIN_CATS.filter(function (k) { return cin[k]; }).map(function (k) { return '<span><i style="background:' + catFill(k) + '"></i>' + esc(catLabel(k)) + '</span>'; }).join('') + '</div>';
      var hd = '<div class="barhead" aria-hidden="true"><span></span><span></span><span>' + esc(S(vol ? 'hDef' : 'hCost')) + '</span>' + ex.map(function (x) { return '<span>' + esc(S(x[0])) + '</span>'; }).join('') + (d.pareto ? '<span class="cumh">' + esc(S('hCum')) + '</span>' : '') + '</div>';
      $('pg').innerHTML = '<div class="card wide" data-card="' + lvl + '"><div class="bhead"><span class="kicker">' + esc(S(vol ? 'kmDef' : 'kmEur')) + '</span><div class="card-head"><h3>' + esc(S(d.t)) + '</h3>' +
        '<button type="button" class="clear-one" data-dim="' + lvl + '"' + (act ? '' : ' hidden') + '>' + esc(S('clear')) + '</button></div>' + (d.sub ? '<p class="sub">' + esc(S(lvl === 'cat' && !vol ? 'ncShareNote' : d.sub)) + '</p>' : '') + keys + '</div>' +
        '<div class="bars' + (d.pareto ? ' pareto' : '') + (d.longName ? ' longname' : '') + (vol ? '' : ' money') + ' x' + ex.length + '">' + hd + (vals.length ? vals.map(function (v) {
          var n = m[v], on = f[lvl] === v, lab = esc(showV(lvl, v)), aside = d.pareto && ASIDE[v], head = '';
          if (aside && !sepDone) { sepDone = true; head = '<div class="sep">' + esc(S('aside')) + '</div>'; }
          if (d.pareto && !aside) cum += n;
          var c2 = sp ? m2[v] || 0 : 0, cab = c2 && n ? '<span class="cab" style="width:' + (c2 / n * 100) + '%"></span>' : '', t = sp ? lab + ' : ' + esc(S('ofWhichCable', { n: fmt(n), c: fmt(c2) })) : lab;
          var col = lvl === 'cat' ? catFill(v) : catFill(ck[v]);
          return head + '<button type="button" class="bar' + (n ? '' : ' zero') + (aside ? ' aside' : '') + '" data-dim="' + lvl + '" data-v="' + esc(v) + '" aria-pressed="' + on + '" title="' + t + '" aria-label="' + t + '">' +
            '<span class="name">' + lab + '</span><span class="track"><span class="fill" style="width:' + (n / max * 100) + '%' + (sp ? '' : ';--bc:' + col) + '">' + cab + '</span></span><span class="val">' + fmt(n) + '</span>' +
            ex.map(function (x) { return '<span class="ext">' + x[2](x[1][v] || 0) + '</span>'; }).join('') + (d.pareto ? '<span class="cum">' + (aside || !totMain ? '' : pct0(cum / totMain * 100)) + '</span>' : '') + '</button>';
        }).join('') : '<p class="empty">—</p>') + '</div></div>';
      var ch = ['cat', 'rca', 'code'].filter(function (k) { return f[k]; });
      $('pc').hidden = !ch.length;
      $('pc').innerHTML = ch.map(function (k) { return '<button type="button" class="chip" data-k="' + k + '"><i>' + esc(S(LV[k].t)) + '</i>' + esc(showV(k, f[k])) + ' <span aria-hidden="true">×</span></button>'; }).join('') +
        (ch.length ? '<button type="button" class="chip reset">' + esc(S('clearAll')) + '</button>' : '');
      defTable();
    }
    function share(s) { return s < 0.999 ? '1/' + Math.round(1 / s) : '1'; }
    function defTable() {   // the board's table: the defect lines (volume) or the cost units (cost) of the levels picked
      var vol = PMODE === 'vol', f = PF, q = PQ.toLowerCase(), all = M.det.defects, rs;
      var txt = function (r) { return [r[0], r[10], r[8], r[7], CODES[r[7]] || '', r[6], r[5], L(r[5]), r[4], L(r[4])].join(' '); };
      var keep = function (r) { return (!f.cat || r[4] === f.cat) && (!f.rca || r[5] === f.rca) && (!f.code || r[7] === f.code) && words(q, txt(r)); };
      var cell = function (r) { return '<td class="nc">' + esc(r[0]) + (r[1] > 1 ? ' · ' + r[1] : '') + '</td><td class="num">' + esc(shortDay(r[2])) + '</td><td>' + esc(r[3]) + '</td><td>' + esc(L(r[4])) + '</td><td>' + esc(L(r[5])) + '</td>'; };
      var cab = function (r) { return '<td>' + (r[9] ? '<span class="tag">' + esc(S('yes')) + '</span>' : '') + '</td>'; };
      var code = function (r) { return '<td class="nc" title="' + esc(CODES[r[7]] || '') + '">' + esc(r[7]) + '</td>'; };
      if (vol) {
        rs = all.filter(keep);
        $('pth').innerHTML = ['cNc', 'cDate', 'cLine', 'cCat', 'cRca', 'cSub', 'cCode', 'cFin', 'cCab', 'cText'].map(function (k) { return '<th scope="col">' + esc(S(k)) + '</th>'; }).join('');
        $('ptb').innerHTML = rs.slice(0, PLIM).map(function (r) { return '<tr>' + cell(r) + '<td>' + esc(r[6]) + '</td>' + code(r) + '<td class="nc">' + esc(r[8]) + '</td>' + cab(r) + '<td class="txt">' + esc(r[10]) + '</td></tr>'; }).join('') || '<tr><td colspan="12" class="empty">—</td></tr>';
      } else {
        var nl = M.det.noLine.filter(function (n) { return (!f.cat || f.cat === '__none') && !f.rca && !f.code && words(q, n[0] + ' ' + n[4]); });
        rs = (f.cat === '__none' ? [] : all.filter(keep)).map(function (r) { return { r: r, c: r[11] }; }).concat(nl.map(function (n) { return { n: n, c: n[3] }; })).sort(function (a, b) { return b.c - a.c; });
        $('pth').innerHTML = [['cNc'], ['cDate'], ['cLine'], ['cCat'], ['cRca'], ['cCode'], ['cCab'], ['cCost', 'r'], ['cShare', 'r'], ['cText']].map(function (p) { return '<th scope="col"' + (p[1] ? ' class="r"' : '') + '>' + esc(S(p[0])) + '</th>'; }).join('');
        $('ptb').innerHTML = rs.slice(0, PLIM).map(function (u) {
          if (u.n) return '<tr><td class="nc">' + esc(u.n[0]) + '</td><td class="num">' + esc(shortDay(u.n[1])) + '</td><td>' + esc(u.n[2]) + '</td><td colspan="4">' + esc(S('noLine')) + '</td><td class="num r">' + eur(u.c) + '</td><td class="num r">1</td><td class="txt">' + esc(u.n[4]) + '</td></tr>';
          var r = u.r; return '<tr>' + cell(r) + code(r) + cab(r) + '<td class="num r">' + eur(r[11]) + '</td><td class="num r">' + share(r[12]) + '</td><td class="txt">' + esc(r[10]) + '</td></tr>'; }).join('') || '<tr><td colspan="12" class="empty">—</td></tr>';
      }
      $('pT').textContent = S(vol ? 'tblDefects' : 'tblCost'); $('pn').textContent = '· ' + S('shown', { n: num(rs.length), t: num(all.length + (vol ? 0 : M.det.noLine.length)) });
      var rest = rs.length - PLIM; $('pm').hidden = rest <= 0; if (rest > 0) $('pm').textContent = S('more', { n: num(Math.min(200, rest)) });
    }
    function ncTable() {   // Synthèse: every NC of the selection (the overview's table)
      var q = NQ.toLowerCase(), all = M.syn.ncs, rs = all.filter(function (n) { return words(q, [n[0], n[8], n[3], n[7], n[2], n[4], typeName(n[4])].join(' ')); });
      $('nT').textContent = S('tblNcs'); $('nn').textContent = '· ' + S('shown', { n: num(rs.length), t: num(all.length) });
      $('nth').innerHTML = ['cNc', 'cDate', 'cLine', 'hProd', 'nType', 'kRule', 'nStatus', 'hStation', 'kTitle'].map(function (k) { return '<th scope="col">' + esc(S(k)) + '</th>'; }).join('');
      $('ntb').innerHTML = rs.slice(0, NLIM).map(function (n) { return '<tr><td class="nc">' + esc(n[0]) + '</td><td class="num">' + esc(shortDay(n[1])) + '</td><td>' + esc(n[2]) + '</td><td>' + esc(prodName(n[3])) + '</td><td>' + esc(typeName(n[4])) +
        '</td><td>' + esc(ruleName(n[5])) + '</td><td>' + esc(stName(n[6])) + '</td><td>' + esc(n[7]) + '</td><td class="txt">' + esc(n[8]) + '</td></tr>'; }).join('') || '<tr><td colspan="12" class="empty">—</td></tr>';
      var rest = rs.length - NLIM; $('nm').hidden = rest <= 0; if (rest > 0) $('nm').textContent = S('more', { n: num(Math.min(200, rest)) });
    }

    // ---------------------------------------------------------------- the bell (the dashboard's alRender; the alarms come computed in the model)
    function bell() {
      var A = M.alarms, btn = $('alBtn'), pop = $('alPop'); btn.hidden = !A; if (!A) { pop.hidden = true; return; }
      var n = A.rows.length, maj = A.rows.some(function (g) { return g.lvl === 2; }); btn.classList.toggle('maj', maj); $('alN').hidden = !n; $('alN').textContent = n;
      btn.setAttribute('aria-expanded', String(ALS.open)); btn.title = S('alBtn') + (n ? ' · ' + n : ''); btn.setAttribute('aria-label', S('alBtn'));
      pop.hidden = !ALS.open; if (!ALS.open) return;
      var wr = $('alWrap').getBoundingClientRect(), PW = document.documentElement.clientWidth, pw = Math.min(460, PW - 32), px = Math.max(16, Math.min(wr.right - pw, PW - pw - 16));
      pop.style.width = pw + 'px'; pop.style.left = Math.round(px - wr.left) + 'px'; pop.style.right = 'auto';
      var spark = function (g) {   // ALARM.spark: the 16 last weeks, the recent ones in colour
        var p = g.spark, Wd = 56, Hd = 18, nn = 16, mx = 0, a = '', b = ''; if (!p) return '';
        p.forEach(function (v) { if (v != null && v > mx) mx = v; }); if (!mx) return '';
        p.forEach(function (v, i) { if (v == null) return; var s = (2 + i / (nn - 1) * (Wd - 4)).toFixed(1) + ',' + (Hd - 2 - v / mx * (Hd - 4)).toFixed(1); if (i <= nn - A.recent) a += (a ? 'L' : 'M') + s; if (i >= nn - A.recent) b += (b ? 'L' : 'M') + s; });
        return '<svg class="al-sp" width="' + Wd + '" height="' + Hd + '" viewBox="0 0 ' + Wd + ' ' + Hd + '" aria-hidden="true"><path d="' + a + '" fill="none" stroke="var(--dim)" stroke-width="1.5"/><path d="' + b + '" fill="none" stroke="' + (g.lvl === 2 ? 'var(--up)' : 'var(--ink-2)') + '" stroke-width="2"/></svg>'; };
      var row = function (g, i) { return '<div class="al-row"><button type="button" class="al-go" data-algo="' + i + '"><i class="al-dot ' + (g.lvl === 2 ? 'maj' : 'min') + '" title="' + esc(S(g.lvl === 2 ? 'alMaj' : 'alMin')) + '"></i>' +
        '<span class="al-what"><b>' + esc(g.line) + '</b> · ' + esc(g.text) + '</span>' + (g.sub.length ? '<span class="al-sub">' + esc(g.sub.join(' · ')) + '</span>' : '') + '<span class="al-sub">→ ' + esc(S('tabDet')) + '</span></button><span class="al-ops">' + spark(g) + '</span></div>'; };
      var top = A.rows.slice(0, A.show), rest = A.rows.slice(A.show);
      pop.innerHTML = '<div class="al-head"><h3 id="alT">' + esc(S('alT', { w: S('alWk', { n: A.week + 1 }) })) + '</h3><button type="button" class="al-x" id="alX" aria-label="' + esc(S('alClose')) + '">✕</button></div>' +
        (A.short ? '<p class="mu">' + esc(S('alShort')) + '</p>' : top.length ? top.map(function (g, i) { return row(g, i); }).join('') : '<p class="mu">' + esc(S('alNone')) + '</p>') +
        (rest.length ? '<details class="al-seen"' + (ALS.more ? ' open' : '') + ' id="alMore"><summary>' + esc(S('alMore', { n: rest.length })) + '</summary>' + rest.map(function (g, i) { return row(g, A.show + i); }).join('') + '</details>' : '') +
        (A.other ? '<p class="mu al-other">' + esc(S('alOther', { n: A.other })) + '</p>' : '');
      var mo = $('alMore'); if (mo) mo.addEventListener('toggle', function () { ALS.more = mo.open; });
    }

    // ---------------------------------------------------------------- the complete chart: the band grows over the page; a double click or a double tap skips
    function anim(el, kf, o) { if (REDUCE || !el.animate) return null; var a = el.animate(kf, o); RUN.push(a); var off = function () { RUN = RUN.filter(function (x) { return x !== a; }); }; a.finished.then(off, off); return a; }
    function skip() { RUN.slice().forEach(function (a) { try { a.finish(); } catch (e) {} }); }
    function vuOpen(id) {
      var p = id.split('|'), b = card(p[0], p[1]); if (!b || OPEN) return;
      var q0 = b.getBoundingClientRect(), ph = document.createElement('div'); ph.style.height = q0.height + 'px'; b.parentNode.insertBefore(ph, b);
      OPEN = { v: p[0], k: p[1], b: b, ph: ph }; OPENED = Date.now();
      $('vuHold').appendChild(b); b.classList.add('vu-full'); $('vuOv').hidden = false; $('vuOv').scrollTop = 0; document.documentElement.classList.add('vu-lock');
      $('vuPanel').setAttribute('aria-label', b.querySelector('h3').textContent);
      drawCard(p[0], p[1]);
      var q1 = b.getBoundingClientRect(), sx = q0.width / q1.width, dx = q0.left - q1.left, dy = q0.top - q1.top, E = 'cubic-bezier(.2,.8,.2,1)';
      anim($('vuScrim'), [{ opacity: 0 }, { opacity: 1 }], { duration: 420, easing: 'ease-out' });
      anim(b, [{ transform: 'translate(' + dx + 'px,' + dy + 'px) scale(' + sx + ')' }, { transform: 'translate(' + r1(dx * .3) + 'px,' + r1(dy * .3 - 16) + 'px) scale(' + (sx + (1 - sx) * .78) + ')', offset: .6 }, { transform: 'none' }], { duration: 720, easing: E });
      b.querySelectorAll('.bhead > .kicker, .bhead > .sub, .vlegend, details').forEach(function (e, i) { anim(e, [{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }], { duration: 320, delay: 520 + i * 70, easing: E, fill: 'backwards' }); });
      $('vuClose').focus();
    }
    function vuClose(now) {
      if (!OPEN) return; var o = OPEN; OPEN = null;
      var done = function () { o.b.classList.remove('vu-full'); o.ph.parentNode.insertBefore(o.b, o.ph); o.ph.remove(); $('vuOv').hidden = true; document.documentElement.classList.remove('vu-lock'); if (M) drawCard(o.v, o.k); };
      if (now || REDUCE || !o.b.animate) { skip(); done(); return; }
      anim($('vuScrim'), [{ opacity: 1 }, { opacity: 0 }], { duration: 220, easing: 'ease-in', fill: 'forwards' });
      var a = anim(o.b, [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(10px) scale(.98)' }], { duration: 200, easing: 'ease-in', fill: 'forwards' });
      a.finished.then(function () { done(); [$('vuScrim'), o.b].forEach(function (e) { e.getAnimations().forEach(function (x) { x.cancel(); }); }); }, done);
    }

    // ---------------------------------------------------------------- events: a filter of the bar goes back to Slate; the rest is drawing
    root.addEventListener('change', function (e) {
      var id = e.target.id, v = e.target.value; if (!M) return;
      if (id === 'gSrc') ask({ src: v }); else if (id === 'gOrg') ask({ org: v }); else if (id === 'gLine') ask({ line: v });
      else if (id === 'gPreset') ask(v === 'custom' ? { preset: 'custom', from: M.meta.from, to: M.meta.end } : { preset: v });
      else if (id === 'gFrom' || id === 'gTo') ask({ preset: 'custom', from: $('gFrom').value || M.meta.from, to: $('gTo').value || M.meta.end });
    });
    var qt;
    root.addEventListener('input', function (e) {
      var id = e.target.id; if (id !== 'pq' && id !== 'nq') return; clearTimeout(qt);
      qt = setTimeout(function () { if (id === 'pq') { PQ = e.target.value.trim(); PLIM = 100; defTable(); } else { NQ = e.target.value.trim(); NLIM = 100; ncTable(); } }, 120);
    });
    root.addEventListener('click', function (e) {
      if (!M) return;
      var pin = e.target.closest('[data-pin]'); if (pin) { PIN = pin.getAttribute('data-pin'); var bc = pin.closest('.vu-band'); drawCard(bc.getAttribute('data-view'), 'a:bump'); return; }
      var b = e.target.closest('button'); if (!b) { if (e.target.id === 'vuScrim' || e.target.id === 'vuOv') { if (RUN.length || Date.now() - OPENED < 900) skip(); else vuClose(); } return; }
      var a = function (k) { return b.getAttribute(k); };
      if (a('data-lang')) { if (a('data-lang') !== G.lang) ask({ lang: a('data-lang') }); return; }
      if (a('data-ph') != null) { ask({ phase: a('data-ph') }); return; }
      if (b.id === 'gPlant') { ask({ fto2: !M.meta.filters.fto2 }); return; }
      if (a('data-min') != null) { ask({ minor: a('data-min') === '1' }); return; }
      if (b.id === 'gReset') { ask(Object.assign({}, GF0)); return; }
      if (a('data-tab')) { if (OPEN) vuClose(true); TAB = a('data-tab'); render(); return; }
      if (a('data-pmode')) { PMODE = a('data-pmode'); PLIM = 100; paretoDraw(); return; }
      if (a('data-pcab')) { G.cab = a('data-pcab') === '1'; paretoDraw(); return; }
      if (a('data-dim') && a('data-v') != null) { var k = a('data-dim'), v = a('data-v'); if (PF[k] === v) delete PF[k]; else PF[k] = v;
        if (!PF.cat) { delete PF.rca; delete PF.code; } else if (!PF.rca) delete PF.code; PLIM = 100; paretoDraw(); return; }
      if (b.classList.contains('clear-one')) { delete PF[a('data-dim')]; if (!PF.cat) { delete PF.rca; delete PF.code; } else if (!PF.rca) delete PF.code; PLIM = 100; paretoDraw(); return; }
      if (b.classList.contains('reset')) { PF = {}; PLIM = 100; paretoDraw(); return; }
      if (a('data-k')) { delete PF[a('data-k')]; if (!PF.cat) { delete PF.rca; delete PF.code; } else if (!PF.rca) delete PF.code; PLIM = 100; paretoDraw(); return; }
      if (b.id === 'pm') { PLIM += 200; defTable(); return; }
      if (b.id === 'nm') { NLIM += 200; ncTable(); return; }
      if (b.id === 'alBtn') { ALS.open = !ALS.open; bell(); return; }
      if (b.id === 'alX') { ALS.open = false; bell(); return; }
      if (a('data-algo') != null) {   // the dashboard's alGo on this page: Détail, on the alarm's line (all lines for several), its item picked in the Pareto
        var g = M.alarms.rows[+a('data-algo')]; ALS.open = false; PF = Object.assign({}, g.go.f); PLIM = 100; TAB = 'det';
        if (g.go.line !== M.meta.filters.line) ask({ line: g.go.line }); else render();
        var el = $('vuPar'); if (el && el.scrollIntoView) el.scrollIntoView({ block: 'start' }); return;
      }
      if (a('data-vux')) { vuOpen(a('data-vux')); return; }
      if (b.id === 'vuClose') vuClose();
    });
    document.addEventListener('click', function (e) { if (ALS.open && !$('alWrap').contains(e.target)) { ALS.open = false; bell(); } });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { if (OPEN) { skip(); vuClose(); } else if (ALS.open) { ALS.open = false; bell(); } } });
    document.addEventListener('dblclick', function () { if (RUN.length) skip(); });
    document.addEventListener('pointerdown', function (e) { if (e.pointerType !== 'touch') return; var t = Date.now(); if (RUN.length && t - lastTap < 320) skip(); lastTap = t; });
    root.addEventListener('pointermove', function (e) { var t = e.target.closest && e.target.closest('[data-tip]'); if (!t) { TIP.hidden = true; return; }
      var ps = t.getAttribute('data-tip').split('|'); TIP.innerHTML = '<b>' + esc(ps[0]) + '</b>' + ps.slice(1).map(function (x) { return '<span>' + esc(x) + '</span>'; }).join('');
      TIP.hidden = false; var x = e.clientX + 14, y = e.clientY + 14, r = TIP.getBoundingClientRect(); if (x + r.width > innerWidth - 8) x = e.clientX - r.width - 14; if (y + r.height > innerHeight - 8) y = e.clientY - r.height - 14;
      TIP.style.left = x + 'px'; TIP.style.top = y + 'px'; });
    root.addEventListener('pointerleave', function () { TIP.hidden = true; });
    var rt, lw = 0; window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { var w = document.documentElement.clientWidth; if (M && w !== lw) { lw = w; render(); } }, 150); });

    function render() {
      header(); figs();
      SLOTS[TAB].forEach(function (k) { drawCard(TAB, k); });
      if (TAB === 'det') paretoDraw(); else ncTable();
      bell();
      if (OPEN) drawCard(OPEN.v, OPEN.k);
    }
    return {
      setModel: function (m) {
        if (!m) return;
        if (m.error) { if (M) $('fbSum').textContent = S('vuErr', { m: m.error }); return; }
        M = m; G.lang = m.meta.filters.lang; CODES = m.meta.codes || {}; render();
      },
      filters: function () { return F || (M && M.meta.filters) || {}; }
    };
  }
  return { create: create };

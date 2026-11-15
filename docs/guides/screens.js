// The pictures of the guides (docs/guides/img/), taken on the pages themselves.
//
//   node docs/guides/screens.js [folder with the pages] [picture name ...]
//
// Default folder: 03_reports (FTO2_NC_Dashboard.html and FTO2_MFT.html, written by the laptop build). No picture name: all of
// them. Each picture is one entry of SHOTS below: the page, the mode and the tab to open, what to click first, the part of the
// page to frame and the numbered marks to put on it (the guides refer to these numbers).
//
// The figures in the pictures are those of the data the pages were built with. After a change of the pages, run this again
// and look at every picture before rebuilding the guides (build_guides.py): a mark sits on the element named in its entry,
// so it follows the layout, but a card that was renamed or removed makes the script stop and say which.
//
// Needs Playwright with Chromium, and the Python package Pillow (the pictures are reduced to 256 colours to keep the PDF light).

const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const HERE = __dirname;
const ROOT = path.resolve(HERE, '..', '..');
const OUT = path.join(HERE, 'img');
const args = process.argv.slice(2);
const PAGES = path.resolve(args[0] && fs.existsSync(args[0]) && fs.statSync(args[0]).isDirectory() ? args.shift() : path.join(ROOT, '03_reports'));
const ONLY = args;
const WIDTH = 1280, SCALE = 2;

// A place on the page: 'css selector' | { card: 'start of a card title' } | { text: 'words', in: place } (the smallest element
// holding these words) | { nth: [selector, i] } | { block: selector } (a heading with what follows it). A mark sits on the
// place's top-left corner, moved by { dx, dy }; { at: 'r' } starts from its right side, 'b' from its bottom; { fx, fy } puts
// the mark at that share of the place's width and height (for a spot inside a chart).
const card = (title) => ({ card: title });

const C = { dx: -9, dy: -11 };   // a mark on the top-left corner of a control

const SHOTS = [
  // ------------------------------------------------------------------ the dashboard, Essentiel
  { name: 'd_top', page: 'dash', mode: 'simple', tab: 'syn', frame: ['header', '#tabs', '#vuSF'], pad: [14, 20, 10, 36],
    marks: [['#asof', 1, { dx: -28, dy: -3 }], ['#alBtn', 2, { dx: -12, dy: 28 }], ['.seg.lang', 3, { dx: 62, dy: 28 }], ['#modeSw', 4, { dx: -30, dy: 10 }],
      ['.fbar .fb-row', 5, { dx: -32, dy: 44 }], ['#gInfoBtn', 6, { at: 'r', dx: 6, dy: 2 }], ['#tabs', 7, { dx: 210, dy: 10 }], ['#vuSF', 8, { dx: -32, dy: 44 }]] },
  { name: 'd_filters', page: 'dash', mode: 'simple', tab: 'syn', frame: ['.fbar'], pad: [18, 20, 8, 36],
    marks: [['#gSrc', 1, C], ['#gOrg', 2, C], ['#gPlant', 3, C], ['#gLiab', 4, C], ['#gPhase', 5, C], ['#gLine', 6, C], ['#gDateBox select', 7, C], ['#minorCtl .seg', 8, C], ['#fbSum', 9, { dx: -30, dy: -3 }]] },
  { name: 'd_info', page: 'dash', mode: 'simple', tab: 'syn', act: [['click', '#gInfoBtn']], frame: ['#fbSum', '#gInfoBtn', '#gInfo'], pad: [8, 16, 12, 16] },
  { name: 'd_syn_kpi', page: 'dash', mode: 'simple', tab: 'syn', frame: ['#vuSF'], pad: [8, 12, 8, 12],
    marks: [[{ nth: ['#vuSF .fig', 0] }, 1, { dx: 250, dy: 12 }], [{ nth: ['#vuSF .fig', 1] }, 2, { dx: 250, dy: 12 }], [{ nth: ['#vuSF .fig', 2] }, 3, { dx: 250, dy: 12 }], [{ nth: ['#vuSF .fig', 3] }, 4, { dx: 250, dy: 12 }]] },
  { name: 'd_syn_cumul', page: 'dash', mode: 'simple', tab: 'syn', frame: [card('NC cumulées sur l’année')], pad: 10,
    marks: [[{ text: '2025', in: card('NC cumulées sur l’année'), svg: true }, 1, { dx: -34, dy: -88 }], [{ text: 'Objectif', in: card('NC cumulées sur l’année'), svg: true }, 2, { dx: 44, dy: -160 }],
      [{ text: 'mai', in: card('NC cumulées sur l’année'), svg: true }, 3, { dx: 2, dy: -128 }], [{ text: 'prévues', in: card('NC cumulées sur l’année'), svg: true }, 4, { at: 'r', dx: 8, dy: -4 }],
      [{ text: 'objectif', in: card('NC cumulées sur l’année'), svg: true, last: true }, 5, { at: 'r', dx: 8, dy: -4 }]] },
  { name: 'd_syn_target', page: 'dash', mode: 'simple', tab: 'syn', frame: [card('Chaque ligne face à son objectif')], pad: 10,
    marks: [[card('Chaque ligne face à son objectif'), 1, { fx: 0.24, fy: 0.405 }], [{ text: 'Objectif : taux', in: card('Chaque ligne face à son objectif') }, 2, { dx: -8, dy: -25 }],
      [{ text: 'Taux 2025', in: card('Chaque ligne face à son objectif') }, 3, { dx: -8, dy: -25 }], [card('Chaque ligne face à son objectif'), 4, { fx: 0.93, fy: 0.215 }]] },
  { name: 'd_syn_rank', page: 'dash', mode: 'simple', tab: 'syn', frame: [card('Classement mensuel des causes')], pad: 10 },
  { name: 'd_syn_slope', page: 'dash', mode: 'simple', tab: 'syn', frame: [card('Causes : 2025 contre 2026')], pad: 10 },
  { name: 'd_syn_bubble', page: 'dash', mode: 'simple', tab: 'syn', frame: [card('Volume ou coût unitaire')], pad: 10 },
  { name: 'd_table', page: 'dash', mode: 'simple', tab: 'syn', act: [['open', '#p-syn details.detail']], frame: ['#p-syn details.detail'], pad: 10, maxHeight: 470,
    marks: [['#p-syn details.detail input', 1, { at: 'r', dx: 8, dy: 6 }]] },
  { name: 'd_det_top', page: 'dash', mode: 'simple', tab: 'det', frame: ['#p-det .figs', '#pg'], pad: 10,
    marks: [[{ text: 'Mesure', in: '#p-det' }, 1, { dx: -4, dy: -24 }], [{ text: 'Défauts câble dans les barres', in: '#p-det' }, 2, { dx: -4, dy: -24 }], [{ text: 'Cumul', in: '#pg' }, 3, { dx: 8, dy: -24 }]] },
  { name: 'd_det_conn', page: 'dash', mode: 'simple', tab: 'det', frame: [card('Erreurs de branchement par MSN')], pad: 10 },
  { name: 'd_det_top3', page: 'dash', mode: 'simple', tab: 'det', frame: [card('Les trois premières causes de chaque produit')], pad: 10 },

  // ------------------------------------------------------------------ the dashboard, Deep dive
  { name: 'd_ov', page: 'dash', mode: 'expert', tab: 'ov', frame: ['#tabs', '#p-ov .lead', '#p-ov .figs'], pad: [10, 20, 10, 20] },
  { name: 'd_ov_open', page: 'dash', mode: 'expert', tab: 'ov', frame: [card('Combien de temps une NC reste ouverte')], pad: 10 },
  { name: 'd_ov_control', page: 'dash', mode: 'expert', tab: 'ov', frame: [card('NC par semaine, avec leurs limites')], pad: 10 },
  { name: 'd_pareto', page: 'dash', mode: 'expert', tab: 'pareto', act: [['clickText', '#p-pareto button', 'Volume (défauts)']], frame: ['#p-pareto .lead', { card: 'Catégorie', in: '#p-pareto' }], pad: 10,
    marks: [[{ text: 'Mesure', in: '#p-pareto' }, 1, { dx: -4, dy: -24 }], [{ text: 'Défauts câble dans les barres', in: '#p-pareto' }, 2, { dx: -4, dy: -24 }]] },
  { name: 'd_pareto_cards', page: 'dash', mode: 'expert', tab: 'pareto', act: [['clickText', '#p-pareto button', 'Volume (défauts)']], frame: [{ card: 'Cause (RCA)' }, { card: 'FIN (repère)' }], pad: 10, maxHeight: 500 },
  { name: 'd_pick', page: 'dash', mode: 'expert', tab: 'where', act: [['pick', '#p-where', 'prod|']], frame: ['.fbar'], pad: [16, 20, 8, 36],
    marks: [['#gPick', 1, { dx: -26, dy: 2 }], ['#gReset', 2, { at: 'r', dx: 6, dy: 4 }], ['#fbSum', 3, { dx: -30, dy: -3 }]] },
  { name: 'd_pick_tab', page: 'dash', mode: 'expert', tab: 'pareto', act: [['clickText', '#p-pareto button', 'Volume (défauts)'], ['bar', '#p-pareto', 'Erreur Branchement']],
    frame: ['#p-pareto .lead', { card: 'Catégorie', in: '#p-pareto' }], pad: 10, marks: [[{ text: 'Tout effacer', in: '#p-pareto' }, 1, { at: 'r', dx: 18, dy: -4 }], ['#p-pareto button.bar[aria-pressed="true"]', 2, { dx: -24, dy: -1 }]] },
  { name: 'd_pareto_flow', page: 'dash', mode: 'expert', tab: 'pareto', frame: [card('Du lieu de détection à la décision')], pad: 10 },
  { name: 'd_where_products', page: 'dash', mode: 'expert', tab: 'where', frame: [card('NC, défauts et coût attendus'), card('Taux mensuel, produit par produit')], pad: 10 },
  { name: 'd_where_msn', page: 'dash', mode: 'expert', tab: 'where', frame: [card('Coût par avion (MSN)')], pad: 10 },
  { name: 'd_where_fin', page: 'dash', mode: 'expert', tab: 'where', frame: [card('Les FIN qui reviennent')], pad: 10 },
  { name: 'd_cnq_top', page: 'dash', mode: 'expert', tab: 'cnq', frame: ['#p-cnq .lead', '#p-cnq .figs', card('Répartition du coût par type de NC')], pad: 10 },
  { name: 'd_cnq_parts', page: 'dash', mode: 'expert', tab: 'cnq', frame: [card('De quoi est fait le coût')], pad: 10 },
  { name: 'd_cnq_explain', page: 'dash', mode: 'expert', tab: 'cnq', act: [['open', '#cx']], frame: ['#cx summary', { nth: ['#cx .cx-sec', 0] }], pad: [10, 10, 10, 36],
    marks: [[{ text: 'avec leur temps et leur coût', in: '#cx' }, 1, { at: 'r', dx: 10, dy: 2 }], [{ text: 'Ce que coûtent', in: '#cx' }, 2, { dx: -31, dy: -3 }], [{ text: 'Règles particulières', in: '#cx' }, 3, { dx: -44, dy: -3 }]] },
  { name: 'd_cnq_nc', page: 'dash', mode: 'expert', tab: 'cnq', act: [['open', '#cx']], frame: ['#cx .cx-nc'], pad: 10,
    marks: [[{ text: 'Afficher', in: '#cx .cx-nc' }, 1, { at: 'r', dx: 22, dy: -3 }], [{ text: 'Rejet avec ordre de retouche', in: '#cx .cx-nc' }, 2, { at: 'r', dx: 22, dy: -3 }], [{ text: 'Niveau 1, standard Airbus', in: '#cx .cx-nc' }, 3, { dx: -30, dy: -14 }]] },
  { name: 'd_cnq_aleas', page: 'dash', mode: 'expert', tab: 'cnq', frame: ['#cDis'], pad: 10 },
  { name: 'd_client', page: 'dash', mode: 'expert', tab: 'client', frame: ['#p-client .lead', '#p-client .figs', { card: 'Catégorie', in: '#p-client' }, { card: 'Cause (RCA)', in: '#p-client' }], pad: 10 },
  { name: 'd_cbl', page: 'dash', mode: 'expert', tab: 'cbl', frame: ['#p-cbl .lead', '#p-cbl .figs', card('Demandes par mois et imputation')], pad: 10 },
  { name: 'd_cbl_tables', page: 'dash', mode: 'expert', tab: 'cbl', frame: [card('Motif × imputation'), card('Types de câble')], pad: 10 },
  { name: 'd_rca', page: 'dash', mode: 'expert', tab: 'rca', frame: [card('Comment un défaut reçoit sa cause')], pad: 10, maxHeight: 520 },
  { name: 'd_rca_cause', page: 'dash', mode: 'expert', tab: 'rca', frame: [{ block: '#rca-inversion' }], pad: 10 },
  { name: 'd_pplan', page: 'dash', mode: 'expert', tab: 'pplan', frame: [card('Par ligne')], pad: 10 },
  { name: 'd_pplan_months', page: 'dash', mode: 'expert', tab: 'pplan', frame: [card('2025 et 2026, mois par mois')], pad: 10 },
  { name: 'd_bell', page: 'dash', mode: 'expert', tab: 'ov', act: [['click', '#alBtn']], frame: ['#asof', '.seg.lang', '#alWrap .al-pop, #alPop, #alWrap > div'], pad: [10, 14, 14, 6] },

  // ------------------------------------------------------------------ the MFT page
  { name: 'm_top', page: 'mft', tab: 'pareto', frame: ['header, .top', '#tb-pareto', '.figs, .kpis'], pad: [10, 16, 10, 16],
    marks: [['#lines', 1, C], ['#phases', 2, C], ['#per', 3, C], ['#wk', 4, C], ['#alBtn', 5, { dx: -28, dy: 4 }], ['#tb-actions', 6, { at: 'r', dx: 10, dy: 8 }]] },
  { name: 'm_pareto', page: 'mft', tab: 'pareto', frame: [{ card: 'Catégories', in: 'main, body' }, { card: 'FIN (repères)', in: 'main, body' }], pad: 10,
    marks: [[{ text: 'moy.', in: { card: 'Catégories', in: 'main, body' } }, 1, { dx: -40, dy: -4 }]] },
  { name: 'm_analyse', page: 'mft', tab: 'analyse', frame: [{ card: 'Défauts par semaine', in: 'main, body' }, { card: 'Ce qui monte', in: 'main, body' }, { card: 'Ce qui baisse', in: 'main, body' }], pad: 10,
    marks: [[{ text: 'Débuts d’action', in: 'main, body' }, 1, { dx: 36, dy: 30 }], [{ text: '+ Action', in: { card: 'Ce qui monte', in: 'main, body' } }, 2, { at: 'r', dx: -6, dy: -15 }]] },
  { name: 'm_analyse2', page: 'mft', tab: 'analyse', frame: [{ card: 'Nouveau cette semaine', in: 'main, body' }, { card: 'FIN récurrents', in: 'main, body' }], pad: 10, maxHeight: 330 },
  { name: 'm_form', page: 'mft', tab: 'analyse', act: [['clickText', 'button', '+ Action']], frame: ['#frm'], pad: 0 },
  { name: 'm_actions', page: 'mft', tab: 'actions', frame: ['#tb-actions', 'article.act'], pad: [10, 16, 10, 16],
    marks: [[{ text: 'Ouvertes', in: 'main, body' }, 1, { dx: -8, dy: -24 }], [{ text: '+ Nouvelle action', in: 'main, body' }, 2, { dx: -42, dy: -3 }], [{ text: 'Problème suivi', in: 'article.act' }, 3, { dx: -27, dy: -3 }],
      [{ text: 'Réf.', in: 'article.act' }, 4, { dx: -27, dy: -3 }], [{ text: 'En hausse', in: 'article.act' }, 5, { dx: -22, dy: 22 }]] },
  { name: 'm_bell', page: 'mft', tab: 'pareto', act: [['click', '#alBtn']], frame: ['#alBtn', '#alPop'], pad: [10, 14, 14, 14] },
];

// ---------------------------------------------------------------- in the page
// Runs in the page: finds a place and returns its rectangle on the whole page, or null.
function locate(spec) {
  function vis(e) { return !!(e && e.getClientRects().length); }
  function find(s, root) {
    root = root || document;
    if (typeof s === 'string') { var all = root.querySelectorAll(s); for (var i = 0; i < all.length; i++) if (vis(all[i])) return all[i]; return null; }
    if (s.nth) { var l = [].filter.call(root.querySelectorAll(s.nth[0]), vis); return l[s.nth[1]] || null; }
    if (s.block) return find(s.block, root);
    var within = s.in ? find(s.in) : root;
    if (!within) return null;
    if (s.card) {
      var hs = within.querySelectorAll('h2, h3');
      for (var j = 0; j < hs.length; j++) {
        if (!vis(hs[j]) || hs[j].textContent.trim().indexOf(s.card) !== 0) continue;
        return hs[j].closest('.card, section.dis, section.rcagroup, .cx-sec, article, section') || hs[j].parentElement;
      }
      return null;
    }
    if (s.text) {
      var best = null, bestLen = 1e9, nodes = within.querySelectorAll(s.svg ? 'text, tspan' : '*');
      for (var k = 0; k < nodes.length; k++) {
        var n = nodes[k], t = n.textContent;
        if (!vis(n) || t.indexOf(s.text) < 0) continue;
        if (t.length < bestLen || (s.last && t.length <= bestLen)) { best = n; bestLen = t.length; }
      }
      return best;
    }
    return null;
  }
  var e = find(spec);
  if (!e) return null;
  var r = e.getBoundingClientRect(), x0 = r.left, y0 = r.top, x1 = r.right, y1 = r.bottom;
  if (spec.text && !spec.svg) {   // the words themselves, not the whole line that holds them
    var w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT), tn;
    while ((tn = w.nextNode())) {
      var at = tn.nodeValue.indexOf(spec.text);
      if (at < 0) continue;
      var rg = document.createRange(); rg.setStart(tn, at); rg.setEnd(tn, at + spec.text.length);
      var q0 = rg.getBoundingClientRect();
      if (q0.width) { x0 = q0.left; y0 = q0.top; x1 = q0.right; y1 = q0.bottom; }
      break;
    }
  }
  if (spec.block) {   // a heading with what follows it, up to the next heading of its level
    for (var nx = e.nextElementSibling; nx && nx.tagName !== e.tagName; nx = nx.nextElementSibling) {
      var q = nx.getBoundingClientRect(); if (!q.width) continue;
      x0 = Math.min(x0, q.left); y0 = Math.min(y0, q.top); x1 = Math.max(x1, q.right); y1 = Math.max(y1, q.bottom);
    }
  }
  return { x: x0 + window.scrollX, y: y0 + window.scrollY, w: x1 - x0, h: y1 - y0 };
}

function addMarks(marks) {
  var layer = document.createElement('div');
  layer.id = 'guide-marks';
  layer.style.cssText = 'position:absolute;left:0;top:0;width:0;height:0;z-index:2147483000;pointer-events:none';
  marks.forEach(function (m) {
    var d = document.createElement('div');
    d.textContent = m.n;
    d.style.cssText = 'position:absolute;left:' + m.x + 'px;top:' + m.y + 'px;width:22px;height:22px;border-radius:50%;background:#c2410c;color:#fff;' +
      'font:700 12.5px/22px Inter,Arial,sans-serif;text-align:center;box-shadow:0 0 0 2px #fff,0 1px 4px rgba(0,0,0,.35)';
    layer.appendChild(d);
  });
  document.body.appendChild(layer);
}

function addFade(r) {
  var d = document.createElement('div');
  d.style.cssText = 'position:absolute;left:' + r.x + 'px;top:' + r.y + 'px;width:' + r.w + 'px;height:' + r.h + 'px;z-index:2147483001;pointer-events:none;' +
    'background:linear-gradient(to bottom, rgba(255,255,255,0), #fff 85%)';
  document.body.appendChild(d);
}

// ---------------------------------------------------------------- the browser side
async function open(browser, shot) {
  const ctx = await browser.newContext({ viewport: { width: WIDTH, height: 900 }, deviceScaleFactor: SCALE, locale: 'fr-FR' });
  const page = await ctx.newPage();
  await page.addInitScript((mode) => { try { localStorage.clear(); if (mode) { localStorage.setItem('fto2-dash-mode', mode); localStorage.setItem('fto2-dash-lang', 'fr'); } } catch (e) {} }, shot.mode || '');
  const file = path.join(PAGES, shot.page === 'dash' ? 'FTO2_NC_Dashboard.html' : 'FTO2_MFT.html');
  if (!fs.existsSync(file)) throw new Error('page not found: ' + file);
  await page.goto('file://' + file);
  await page.waitForTimeout(shot.page === 'dash' ? 4500 : 3500);
  if (shot.page === 'dash') await page.evaluate((id) => document.getElementById(id).click(), 'tab-' + shot.tab);
  else await page.click('#tb-' + shot.tab);
  await page.waitForTimeout(shot.mode === 'simple' ? 2500 : 1200);
  for (const [what, sel, arg] of shot.act || []) {
    if (what === 'click') await page.click(sel);
    else if (what === 'open') await page.evaluate((s) => { const d = document.querySelector(s); d.open = true; d.dispatchEvent(new Event('toggle')); }, sel);
    else if (what === 'clickText') await page.evaluate(([s, t]) => { const b = [].find.call(document.querySelectorAll(s), (x) => x.getClientRects().length && x.textContent.trim() === t); if (!b) throw new Error('no button "' + t + '"'); b.click(); }, [sel, arg]);
    else if (what === 'pick') await page.evaluate(([s, t]) => { const e = [].find.call(document.querySelectorAll(s + ' [data-pick]'), (x) => x.getClientRects().length && x.getAttribute('data-pick').indexOf(t) === 0); if (!e) throw new Error('nothing to click for "' + t + '"'); e.dispatchEvent(new MouseEvent('click', { bubbles: true })); }, [sel, arg]);
    else if (what === 'bar') await page.evaluate(([s, t]) => { const e = [].find.call(document.querySelectorAll(s + ' button.bar'), (x) => x.getClientRects().length && x.getAttribute('data-v') === t); if (!e) throw new Error('no bar "' + t + '"'); e.click(); }, [sel, arg]);
    await page.waitForTimeout(900);
  }
  return { ctx, page };
}

async function take(browser, shot) {
  const { ctx, page } = await open(browser, shot);
  try {
    const rects = [];
    for (const f of shot.frame) {
      const r = await page.evaluate(locate, f);
      if (!r) throw new Error(shot.name + ': not found on the page: ' + JSON.stringify(f));
      rects.push(r);
    }
    const pad = Array.isArray(shot.pad) ? shot.pad : [shot.pad || 0, shot.pad || 0, shot.pad || 0, shot.pad || 0];   // top, right, bottom, left
    const full = await page.evaluate(() => ({ w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight }));
    let x0 = Math.min(...rects.map((r) => r.x)) - pad[3], y0 = Math.min(...rects.map((r) => r.y)) - pad[0];
    let x1 = Math.max(...rects.map((r) => r.x + r.w)) + pad[1], y1 = Math.max(...rects.map((r) => r.y + r.h)) + pad[2];
    x0 = Math.max(0, Math.floor(x0)); y0 = Math.max(0, Math.floor(y0)); x1 = Math.min(full.w, Math.ceil(x1)); y1 = Math.min(full.h, Math.ceil(y1));
    const cut = shot.maxHeight && y1 > y0 + shot.maxHeight;
    if (cut) y1 = y0 + shot.maxHeight;
    const marks = [];
    for (const [where, n, o] of shot.marks || []) {
      const r = await page.evaluate(locate, where);
      if (!r) throw new Error(shot.name + ': mark ' + n + ' not found on the page: ' + JSON.stringify(where));
      const opt = o || {};
      const bx = opt.fx != null ? r.x + r.w * opt.fx - 11 : opt.at === 'r' ? r.x + r.w : r.x, by = opt.fy != null ? r.y + r.h * opt.fy - 11 : opt.at === 'b' ? r.y + r.h : r.y;
      marks.push({ n, x: Math.round(bx + (opt.dx || 0)), y: Math.round(by + (opt.dy || 0)) });
    }
    if (marks.length) await page.evaluate(addMarks, marks);
    if (cut) await page.evaluate(addFade, { x: x0, y: y1 - 56, w: x1 - x0, h: 56 });   // the picture goes on: it fades out
    const out = path.join(OUT, shot.name + '.png');
    await page.screenshot({ path: out, fullPage: true, clip: { x: x0, y: y0, width: x1 - x0, height: y1 - y0 } });
    return out;
  } finally { await ctx.close(); }
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const list = SHOTS.filter((s) => !ONLY.length || ONLY.includes(s.name));
  const unknown = ONLY.filter((n) => !SHOTS.some((s) => s.name === n));
  if (unknown.length) { console.error('no picture named: ' + unknown.join(', ')); process.exit(2); }
  // dates the French way in the date boxes, as on the team's computers
  const browser = await chromium.launch({ args: ['--lang=fr-FR'], env: Object.assign({}, process.env, { LANG: 'fr_FR.UTF-8', LC_ALL: 'fr_FR.UTF-8', LANGUAGE: 'fr' }) });
  const done = [], failed = [];
  for (const shot of list) {
    try { done.push(await take(browser, shot)); console.log('ok   ' + shot.name); } catch (e) { failed.push(shot.name); console.log('FAIL ' + shot.name + ': ' + String(e.message).split('\n')[0]); }
  }
  await browser.close();
  if (done.length) {
    // 256 colours: screenshots of flat pages lose nothing visible and weigh a third
    const py = 'import sys\nfrom PIL import Image\nfor f in sys.argv[1:]:\n    im = Image.open(f).convert("RGB")\n    im.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(f, optimize=True)\n';
    execFileSync('python3', ['-I', '-c', py, ...done]);
  }
  console.log(done.length + ' picture(s) in ' + path.relative(ROOT, OUT) + (failed.length ? '; FAILED: ' + failed.join(', ') : ''));
  process.exit(failed.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });

// Page check for FTO2_Vision.html: no script error, and the figures the page computes for four filter settings
// equal the ones build_vision.py wrote to expected.json. Also checks the page never scrolls sideways at phone width.
//   NODE_PATH=$(npm root -g) node 09_vision/check_vision.js [screenshot folder]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const page = path.join(__dirname, 'FTO2_Vision.html');
const exp = JSON.parse(fs.readFileSync(path.join(__dirname, 'expected.json'), 'utf8'));
const shots = process.argv[2];
let fails = 0;
function eq(name, got, want, tol) {
  const ok = tol ? Math.abs(got - want) <= tol : got === want;
  if (!ok) { fails++; console.log('FAIL', name, 'page', got, 'expected', want); }
}
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto('file://' + page);
  await p.waitForTimeout(800);
  const pick = async (group, label) => { await p.click(`#${group} button:text-is("${label}")`); await p.waitForTimeout(250); };
  const read = () => p.evaluate(() => {
    const V = window.__V, D = null;
    return { kpi: V.kpi, M: V.net.M, mean: V.anat.mean, methods: V.methods, cat: window.__CAT };
  });
  async function check(name, e) {
    const r = await read();
    eq(name + ' NC', r.kpi.nc, e.nc); eq(name + ' defects', r.kpi.def, e.defects); eq(name + ' cost', Math.round(r.kpi.cost), e.cost, 1);
    eq(name + ' customer NCs', r.kpi.cli, e.clientNc); eq(name + ' customer defects', r.kpi.dcli, e.clientDefects);
    eq(name + ' cable defects', r.kpi.cable, e.cableDefects);
    eq(name + ' NC 2025', r.kpi.nc25, e.nc2025); eq(name + ' defects 2025', r.kpi.def25, e.defects2025);
    for (const [cat, n] of Object.entries(e.escapesByCat)) { const k = r.cat.indexOf(cat); eq(name + ' escapes ' + cat, r.M[k + '|client'] || 0, n); }
    for (const [st, v] of Object.entries(e.minutesPerNc)) eq(name + ' minutes ' + st, Math.round(r.mean[st] * 10) / 10, v, 0.05);
    eq(name + ' Airbus method', r.methods[0], e.methods.airbus, 1); eq(name + ' detail method', r.methods[1], e.methods.detail, 1); eq(name + ' AEC method', r.methods[2], e.methods.aec, 1);
  }
  await check('default', exp.default);
  if (shots) await p.screenshot({ path: path.join(shots, 'check_default.png'), fullPage: true });
  await pick('fLine', 'A350'); await check('A350', exp.A350);
  await pick('fLine', 'Toutes'); await pick('fNature', 'Câble'); await check('cable', exp.cable);
  if (shots) await p.screenshot({ path: path.join(shots, 'check_cable.png'), fullPage: true });
  await pick('fNature', 'Tous'); await pick('fPhase', 'Tous types'); await check('all phases', exp.allPhases);
  await pick('fPhase', 'Série');
  // every line, both languages, both units: no script error
  for (const l of ['A350', 'A330', 'A320', 'A400M', 'Toutes']) { await pick('fLine', l); }
  await p.click('#fLang button[data-v="en"]'); await p.waitForTimeout(300);
  await pick('fUnit', 'Defects'); await pick('fFind', 'Names'); await pick('fFind', 'Findings'); await pick('fUnit', 'NCs');
  if (shots) await p.screenshot({ path: path.join(shots, 'check_en.png'), fullPage: true });
  // presentation mode: six slides, arrow keys
  await p.click('#bPresent'); await p.waitForTimeout(400);
  const deck = ['s0', 's1', 's2', 's2', 's3', 's4', 's4', 's5'];
  for (let k = 0; k < deck.length; k++) {
    const on = await p.evaluate(() => Array.from(document.querySelectorAll('[data-slide].on')).map(e => e.id));
    eq('slide ' + k, on.join(','), deck[k]);
    const fits = await p.evaluate(() => { const s = document.querySelector('[data-slide].on'); return s.getBoundingClientRect().height <= innerHeight + 2; });
    eq('slide ' + k + ' fits the screen', fits, true);
    if (shots) await p.screenshot({ path: path.join(shots, 'slide_' + k + '.png') });
    await p.keyboard.press('ArrowRight'); await p.waitForTimeout(250);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(200);
  await p.click('#bCopy'); await p.waitForTimeout(200);
  await p.click('#fLang button[data-v="fr"]');
  // phone width
  const m = await b.newPage({ viewport: { width: 390, height: 844 } });
  m.on('pageerror', e => errs.push('phone: ' + e.message));
  await m.goto('file://' + page); await m.waitForTimeout(800);
  const sw = await m.evaluate(() => document.documentElement.scrollWidth);
  eq('phone scroll width', sw, 390);
  if (shots) await m.screenshot({ path: path.join(shots, 'check_phone.png'), fullPage: true });
  // dark theme
  const dk = await b.newPage({ viewport: { width: 1440, height: 900 }, colorScheme: 'dark' });
  await dk.goto('file://' + page); await dk.waitForTimeout(800);
  if (shots) await dk.screenshot({ path: path.join(shots, 'check_dark.png'), fullPage: true });
  errs.forEach(e => { fails++; console.log('ERROR', e); });
  console.log(fails ? fails + ' check(s) failed' : 'all checks passed');
  await b.close();
  process.exit(fails ? 1 : 0);
})();

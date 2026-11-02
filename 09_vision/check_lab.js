// Page check for FTO2_Visual_Lab.html: no script error, and the figures the lab draws for three line settings (defects
// in the journey and the rain, aircraft and NC dots in the lifelines, the river and its outline at equal production)
// equal the ones build_vision.py wrote to expected.json. Also checks the page never scrolls sideways at phone width.
//   NODE_PATH=$(npm root -g) node 09_vision/check_lab.js [screenshot folder]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const page = 'file://' + path.join(__dirname, 'FTO2_Visual_Lab.html');
const exp = JSON.parse(fs.readFileSync(path.join(__dirname, 'expected.json'), 'utf8')).lab;
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
  await p.goto(page);
  await p.waitForTimeout(900);
  const pick = async (label) => { await p.click(`#fLine button:text-is("${label}")`); await p.waitForTimeout(300); };
  async function check(name, e) {
    const r = await p.evaluate(() => window.__lab);
    eq(name + ' journey defects', r.journey.total, e.journey);
    eq(name + ' rain dots', r.rain.dots, e.journey);
    eq(name + ' aircraft', r.lifelines.planes, e.planes);
    eq(name + ' NC dots', r.lifelines.ncDots, e.ncDots); eq(name + ' customer dots', r.lifelines.cliDots, e.cliDots);
    eq(name + ' river weeks', r.river.weeks, e.weeks); eq(name + ' river defects', r.river.total, e.riverTotal);
    eq(name + ' river outline', r.river.ghost, e.ghost, 0.15); eq(name + ' river base', r.river.hasBase, e.hasBase);
  }
  await check('all lines', exp.all);
  if (shots) for (const v of ['v1', 'v2', 'v3', 'v4', 'v5']) await p.locator('#' + v).screenshot({ path: path.join(shots, 'lab_' + v + '.png') });
  await pick('A350'); await check('A350', exp.A350);
  await pick('A320'); await check('A320', exp.A320);
  await pick('A400M'); await pick('A330');
  // the rain mid-year, then the whole animation
  await p.evaluate(() => window.__lab.rainObj.draw(0.45));
  if (shots) await p.locator('#v2 .stage').screenshot({ path: path.join(shots, 'lab_rain_mid.png') });
  await p.evaluate(() => window.__lab.rainObj.draw(1));
  await p.click('#fLang button[data-v="en"]'); await p.waitForTimeout(300);
  await pick('All');
  await p.click('#rPlay'); await p.waitForTimeout(9600);
  eq('rain finished', await p.evaluate(() => window.__lab.rainObj.t), 1);
  // hover a block of the journey and a stream of the river: no error
  await p.locator('#jChart g.hit').first().hover({ force: true }); await p.waitForTimeout(150);
  await p.locator('#sChart svg').hover({ position: { x: 300, y: 190 }, force: true }); await p.waitForTimeout(150);
  if (shots) await p.screenshot({ path: path.join(shots, 'lab_en.png'), fullPage: true });
  await p.click('#fLang button[data-v="fr"]');
  // phone width
  const m = await b.newPage({ viewport: { width: 390, height: 844 } });
  m.on('pageerror', e => errs.push('phone: ' + e.message));
  await m.goto(page); await m.waitForTimeout(900);
  eq('phone scroll width', await m.evaluate(() => document.documentElement.scrollWidth), 390);
  if (shots) await m.screenshot({ path: path.join(shots, 'lab_phone.png'), fullPage: true });
  // dark theme
  const dk = await b.newPage({ viewport: { width: 1440, height: 900 }, colorScheme: 'dark' });
  dk.on('pageerror', e => errs.push('dark: ' + e.message));
  await dk.goto(page); await dk.waitForTimeout(900);
  if (shots) await dk.screenshot({ path: path.join(shots, 'lab_dark.png'), fullPage: true });
  errs.forEach(e => { fails++; console.log('ERROR', e); });
  console.log(fails ? fails + ' check(s) failed' : 'all checks passed');
  await b.close();
  process.exit(fails ? 1 : 0);
})();

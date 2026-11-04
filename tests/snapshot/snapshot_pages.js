// Records what the three pages show for a fixed list of filter views, so a change in the code can be checked
// against it: every tab's text (numbers, labels, chart text) and every tooltip, plus the filter summary and
// the alarm list.
//
//   node tests/snapshot/snapshot_pages.js <output folder> [dashboard|mft|elizabeth ...]
//
// Writes <output folder>/<page>.json.gz. Compare two folders with tests/snapshot/compare.py.
// Needs Playwright with Chromium (installed on the build machine).

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
const DIR = process.env.FTO2_PAGES || path.join(ROOT, '03_reports');   // FTO2_PAGES: another folder holding the three pages
const PAGES = {
  dashboard: path.join(DIR, 'FTO2_NC_Dashboard.html'),
  mft: path.join(DIR, 'FTO2_MFT.html'),
  elizabeth: path.join(DIR, 'FTO2_Elizabeth.html'),
};
const WAIT = { load: 3000, tab: 700, mode: 2500, click: 600 };

const clean = (s) => String(s || '').replace(/\s+/g, ' ').trim();

// ------------------------------------------------------------------ dashboard
// Each view starts from a fresh page. mode: 'expert' (Deep dive) or 'simple' (Essentiel); steps run in order.
const DASH_VIEWS = [
  { name: 'default', mode: 'expert' },
  { name: 'essentiel', mode: 'simple' },
  { name: 'phase REC', steps: [['phase', 'REC']] },
  { name: 'phase REC, cost all', steps: [['phase', 'REC'], ['cost', 'all']] },
  { name: 'phase FTI', steps: [['phase', 'FTI']] },
  { name: 'phase all', steps: [['phase', '']] },
  { name: 'responsibility f+s', steps: [['liab', 'fs']] },
  { name: 'responsibility s', steps: [['liab', 's']] },
  { name: 'responsibility o', steps: [['liab', 'o']] },
  { name: 'responsibility f+s+o', steps: [['liab', 'fso']] },
  { name: 'line A350', steps: [['line', 'A350']] },
  { name: 'line A330', steps: [['line', 'A330']] },
  { name: 'line A320', steps: [['line', 'A320']] },
  { name: 'line A400M', steps: [['line', 'A400M']] },
  { name: 'last month', steps: [['preset', 'm1']] },
  { name: 'last 3 months', steps: [['preset', 'm3']] },
  { name: 'last 12 months', steps: [['preset', 'm12']] },
  { name: 'all dates', steps: [['preset', 'all']] },
  { name: 'custom dates', steps: [['dates', '2026-03-01', '2026-06-15']] },
  { name: 'plant switch off', steps: [['plant']] },
  { name: 'source gps', steps: [['src', 'gps']] },
  { name: 'source test', steps: [['src', 'test']] },
  { name: 'source manual lists', steps: [['src', 'man']] },
  { name: 'source skywise', steps: [['src', 'sky']] },
  { name: 'origin missing ids', steps: [['org', 'missing_ids']] },
  { name: 'minor defects out', steps: [['minor', false]] },
  { name: 'pick category', steps: [['pick', 'cat|Erreur Branchement']] },
  { name: 'pick cause', steps: [['pick', 'rca|Inversion']] },
  { name: 'pick month', steps: [['pick', 'month|2026-06']] },
  { name: 'pick product', steps: [['pick', 'pprod|MIP A350']] },
  { name: 'pick msn', steps: [['pick', 'msn|810']] },
  { name: 'pick station', steps: [['pick', 'station|FINITION WF492']] },
  { name: 'pick where found', steps: [['pick', 'wgrp|fin']] },
  { name: 'english', lang: 'en' },
  { name: 'A330 REC 3 months cause', steps: [['line', 'A330'], ['phase', 'REC'], ['preset', 'm3'], ['pick', 'rca|*']] },
  { name: 'essentiel A350 last month', mode: 'simple', steps: [['line', 'A350'], ['preset', 'm1']] },
];

async function dashStep(p, s) {
  const [kind, a, b] = s;
  if (kind === 'phase') await p.click(`#gPhase [data-ph="${a}"]`);
  else if (kind === 'cost') await p.click(`#gCost [data-cost="${a}"]`);
  else if (kind === 'line') await p.selectOption('#gLine', a);
  else if (kind === 'preset') await p.selectOption('#gPreset', a);
  else if (kind === 'src') await p.selectOption('#gSrc', a);
  else if (kind === 'org') await p.selectOption('#gOrg', a);
  else if (kind === 'plant') await p.click('#gPlant');
  else if (kind === 'minor') await p.evaluate((id) => document.getElementById(id).click(), a ? 'miIn' : 'miOut');   // the switch is hidden on some tabs
  else if (kind === 'dates') {
    for (const [id, v] of [['#gFrom', a], ['#gTo', b]]) {
      await p.evaluate(([id, v]) => { const e = document.querySelector(id); e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); }, [id, v]);
      await p.waitForTimeout(WAIT.click);
    }
  } else if (kind === 'liab') {
    // tick the wanted ones first, then untick the others (at least one tick always stays on)
    await p.click('#gLiabTxt');
    for (const k of 'fso') if (a.includes(k)) await p.check(`[data-liab="${k}"]`);
    for (const k of 'fso') if (!a.includes(k)) await p.uncheck(`[data-liab="${k}"]`);
    await p.click('#gLiabTxt');
  } else if (kind === 'pick') {
    // the chart element carrying this value, on whichever tab shows it
    const tabs = await visibleTabs(p);
    let done = false;
    for (const t of tabs) {
      await p.evaluate((id) => document.getElementById(id).click(), t);
      await p.waitForTimeout(WAIT.tab);
      done = await p.evaluate((v) => {
        const want = (x) => (v.endsWith('|*') ? x.getAttribute('data-pick').startsWith(v.slice(0, -1)) : x.getAttribute('data-pick') === v);   // 'rca|*': the first cause shown
        const e = [...document.querySelectorAll('[data-pick]')].find((x) => want(x) && x.closest('[hidden]') == null);
        if (!e) return false;
        e.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        return true;
      }, a);
      if (done) break;
    }
    if (!done) throw new Error('pick not found on any tab: ' + a);
  } else throw new Error('unknown step ' + kind);
  await p.waitForTimeout(WAIT.click);
}

function visibleTabs(p) {
  return p.evaluate(() => [...document.querySelectorAll('#tabs [role=tab]')].filter((t) => !t.hidden).map((t) => t.id));
}

async function capturePanel(p, sel) {
  return p.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const tips = [...el.querySelectorAll('[data-tip]')].map((e) => e.getAttribute('data-tip'));
    return { text: el.textContent.replace(/\s+/g, ' ').trim(), tips };
  }, sel);
}

async function dashboard(browser) {
  const out = {};
  for (const v of DASH_VIEWS) {
    const p = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
    const errors = [];
    p.on('pageerror', (e) => errors.push(String(e)));
    await p.addInitScript(([mode, lang]) => {
      try { localStorage.clear(); localStorage.setItem('fto2-dash-mode', mode); localStorage.setItem('fto2-dash-lang', lang); } catch (e) {}
    }, [v.mode || 'expert', v.lang || 'fr']);
    await p.goto('file://' + PAGES.dashboard);
    await p.waitForTimeout(v.mode === 'simple' ? WAIT.mode : WAIT.load);
    for (const s of v.steps || []) await dashStep(p, s);
    const rec = { summary: clean(await p.textContent('#fbSum')), liab: clean(await p.textContent('#gLiabTxt')), tabs: {} };
    for (const t of await visibleTabs(p)) {
      await p.evaluate((id) => document.getElementById(id).click(), t);
      await p.waitForTimeout(v.mode === 'simple' ? WAIT.mode : WAIT.tab);
      rec.tabs[t] = await capturePanel(p, '#p-' + t.slice(4));
    }
    await p.click('#gInfoBtn').catch(() => {});
    await p.waitForTimeout(300);
    rec.info = clean(await p.textContent('#gInfo').catch(() => ''));
    const bell = await p.$('#alBtn:not([hidden])');
    if (bell) { await bell.click(); await p.waitForTimeout(400); rec.alarms = await capturePanel(p, '#alPop'); }
    rec.errors = errors;
    out[v.name] = rec;
    process.stdout.write('dashboard: ' + v.name + (errors.length ? '  (page errors: ' + errors.length + ')' : '') + '\n');
    await p.close();
  }
  return out;
}

// ------------------------------------------------------------------ MFT page
async function mft(browser) {
  const out = {};
  const p = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
  const errors = [];
  p.on('pageerror', (e) => errors.push(String(e)));
  await p.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
  await p.goto('file://' + PAGES.mft);
  await p.waitForTimeout(WAIT.load);
  const grab = async (name) => {
    const rec = { title: clean(await p.textContent('#pTitle')), figs: clean(await p.textContent('#pFigs')), tabs: {} };
    for (const t of ['pareto', 'analyse', 'actions']) {
      await p.click('#tb-' + t); await p.waitForTimeout(300);
      rec.tabs[t] = await capturePanel(p, '#t-' + t);
    }
    await p.click('#tb-pareto'); await p.waitForTimeout(200);
    out[name] = rec;
  };
  await grab('opening view');
  const lines = await p.evaluate(() => [...document.querySelectorAll('#lines [data-line]')].map((b) => b.getAttribute('data-line')));
  for (const l of lines) {
    await p.click(`#lines [data-line="${l}"]`); await p.waitForTimeout(250);
    for (const ph of ['SERIE', 'REC', 'FTI', '']) {
      await p.click(`#phases [data-ph="${ph}"]`); await p.waitForTimeout(250);
      for (const per of ['1', '4', '13']) {
        await p.click(`[data-per="${per}"]`); await p.waitForTimeout(250);
        await grab(`line ${l}, phase ${ph || 'all'}, period ${per}`);
      }
    }
  }
  await p.click('#lines [data-line="A330"]'); await p.click('#phases [data-ph="SERIE"]'); await p.click('[data-per="1"]'); await p.waitForTimeout(300);
  await p.click('[data-cnt="nc"]'); await p.waitForTimeout(300); await grab('A330 counting NCs');
  await p.click('[data-cnt="def"]'); await p.waitForTimeout(300);
  const bar = await p.$('#bCat .bar');
  if (bar) { await bar.click(); await p.waitForTimeout(400); await grab('A330 with a category picked'); await p.locator('[data-unsel="cat"]:visible').first().click(); await p.waitForTimeout(300); }
  await p.click('[data-per="0"]'); await p.waitForTimeout(300); await p.selectOption('#wkF', { index: 8 }); await p.waitForTimeout(400); await grab('A330 custom range');
  await p.click('[data-per="1"]'); await p.waitForTimeout(300);
  await p.click('[data-lang="en"]'); await p.waitForTimeout(400); await grab('A330 english');
  await p.click('[data-lang="fr"]'); await p.waitForTimeout(300);
  await p.click('#alBtn'); await p.waitForTimeout(400); out.alarms = await capturePanel(p, '#alPop');
  out.errors = errors;
  process.stdout.write('mft: ' + Object.keys(out).length + ' views' + (errors.length ? '  (page errors: ' + errors.length + ')' : '') + '\n');
  await p.close();
  return out;
}

// ------------------------------------------------------------------ Tableau Elizabeth
async function elizabeth(browser) {
  const out = {};
  const p = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
  const errors = [];
  p.on('pageerror', (e) => errors.push(String(e)));
  await p.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
  await p.goto('file://' + PAGES.elizabeth);
  await p.waitForTimeout(WAIT.load);
  out.families = await p.evaluate(() => (window.ELZ_CHECK ? window.ELZ_CHECK() : null));
  const grab = async (name) => { out[name] = { head: clean(await p.textContent('header.top')), main: await capturePanel(p, 'main') }; };
  await grab('opening view');
  const lines = await p.evaluate(() => [...document.querySelectorAll('#lines [data-line]')].map((b) => b.getAttribute('data-line')));
  for (const l of lines) {
    await p.click(`#lines [data-line="${l}"]`); await p.waitForTimeout(250);
    for (const ph of ['SERIE', 'REC', 'FTI', '']) {
      await p.click(`#phases [data-ph="${ph}"]`); await p.waitForTimeout(250);
      for (const per of ['1', '4', '13', '26']) {
        await p.click(`[data-per="${per}"]`); await p.waitForTimeout(250);
        await grab(`line ${l}, phase ${ph || 'all'}, period ${per}`);
      }
    }
  }
  await p.click('[data-tm="nc"]'); await p.waitForTimeout(300); await grab('threshold in NCs');
  const fam = await p.$('#bFam [data-fam]');
  if (fam) { await fam.click(); await p.waitForTimeout(300); await grab('a family picked'); }
  out.errors = errors;
  process.stdout.write('elizabeth: ' + Object.keys(out).length + ' views' + (errors.length ? '  (page errors: ' + errors.length + ')' : '') + '\n');
  await p.close();
  return out;
}

(async () => {
  const dir = process.argv[2];
  if (!dir) { console.error('usage: node tests/snapshot/snapshot_pages.js <output folder> [dashboard|mft|elizabeth ...]'); process.exit(2); }
  const which = process.argv.slice(3).length ? process.argv.slice(3) : ['dashboard', 'mft', 'elizabeth'];
  fs.mkdirSync(dir, { recursive: true });
  const browser = await chromium.launch();
  const run = { dashboard, mft, elizabeth };
  for (const name of which) {
    const data = await run[name](browser);
    fs.writeFileSync(path.join(dir, name + '.json.gz'), zlib.gzipSync(JSON.stringify(data)));
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });

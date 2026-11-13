// The dashboard page in another year: does it follow the year of the settings?
//
//   python3 -I tests/notebook_rehearsal.py  /tmp/this_year      the page on the laptop's data (2026)
//   python3 -I tests/next_year_rehearsal.py /tmp/next_year      the same data moved 53 weeks later (2027)
//   node tests/next_year_page.js /tmp/this_year /tmp/next_year
//
// Opens the dashboard of both folders (FTO2_NC_Dashboard.html), in both modes and both languages, and checks the second one:
//   - no page error, every tab shows something;
//   - it names its own two years (the year followed and the comparison year) and never the comparison year of the first
//     page; no text placeholder ({YEAR}, {PREV}, {CUT}) is left;
//   - it counts the same NCs and defects as the first page (the same NCs, one year later);
//   - its bell works: it covers the same week and lists about the same alarms (the weeks are the same; the volume of a week
//     differs a little, because public holidays fall on other days).
// Then the MFT page of both folders (FTO2_MFT.html): no page error, the same week, the same figures, the same bell.
// Exits 1 if a check fails. Needs Playwright with Chromium.

const path = require('path');
const { chromium } = require('playwright');

const clean = (s) => String(s || '').replace(/\s+/g, ' ').trim();
const count = (text, year) => (text.match(new RegExp('(?<!\\d)' + year + '(?!\\d)', 'g')) || []).length;

async function read(browser, file, mode, lang) {
  const p = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  const out = { errors: [], tabs: {} };
  p.on('pageerror', (e) => out.errors.push(String(e)));
  await p.addInitScript(([mode, lang]) => {
    try { localStorage.clear(); localStorage.setItem('fto2-dash-mode', mode); localStorage.setItem('fto2-dash-lang', lang); } catch (e) {}
  }, [mode, lang]);
  await p.goto('file://' + file);
  await p.waitForTimeout(4500);
  out.year = await p.evaluate(() => window.FTO2_YEAR);
  out.summary = clean(await p.textContent('#fbSum'));
  const tabs = await p.evaluate(() => [...document.querySelectorAll('#tabs [role=tab]')].filter((t) => !t.hidden).map((t) => t.id));
  for (const t of tabs) {
    await p.evaluate((id) => document.getElementById(id).click(), t);
    await p.waitForTimeout(mode === 'simple' ? 2500 : 900);
    out.tabs[t] = await p.evaluate((sel) => {
      const el = document.querySelector(sel);
      return el.textContent.replace(/\s+/g, ' ').trim() + ' ' + [...el.querySelectorAll('[data-tip]')].map((e) => e.getAttribute('data-tip')).join(' ');
    }, '#p-' + t.slice(4));
  }
  const bell = await p.$('#alBtn:not([hidden])');
  if (bell) {
    out.bellCount = +(String(await bell.getAttribute('title')).split('·')[1] || 0);
    await bell.click();
    await p.waitForTimeout(500);
    out.bell = clean(await p.textContent('#alPop'));
  }
  await p.close();
  return out;
}

async function readMft(browser, file) {
  const p = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
  const out = { errors: [] };
  p.on('pageerror', (e) => out.errors.push(String(e)));
  await p.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
  await p.goto('file://' + file);
  await p.waitForTimeout(4000);
  out.asof = clean(await p.textContent('#asof'));
  out.title = clean(await p.textContent('#pTitle'));
  out.figs = clean(await p.textContent('#pFigs'));
  await p.click('#alBtn');
  await p.waitForTimeout(500);
  out.bell = clean(await p.textContent('#alPop'));
  out.alarms = (out.bell.match(/→/g) || []).length;   // one arrow per alarm shown
  await p.close();
  return out;
}

(async () => {
  if (process.argv.length !== 4) { console.log('usage: node tests/next_year_page.js <folder of the first page> <folder of the page one year later>'); process.exit(2); }
  const [first, second] = process.argv.slice(2).map((d) => path.resolve(d, 'FTO2_NC_Dashboard.html'));
  const browser = await chromium.launch();
  let bad = 0;
  const expect = (ok, text) => { console.log((ok ? '  ok   ' : '  FAIL ') + text); if (!ok) bad++; };
  for (const [mode, lang] of [['expert', 'fr'], ['simple', 'fr'], ['expert', 'en']]) {
    const a = await read(browser, first, mode, lang), b = await read(browser, second, mode, lang);
    const all = Object.values(b.tabs).join(' ') + ' ' + (b.bell || '');
    console.log(`\n${mode}, ${lang}: ${a.year} -> ${b.year}`);
    expect(b.year === a.year + 1, `the page follows ${b.year}`);
    expect(!b.errors.length, 'no page error' + (b.errors.length ? ': ' + b.errors[0] : ''));
    expect(Object.keys(b.tabs).length === Object.keys(a.tabs).length && Object.values(b.tabs).every((t) => t.length > 500), `every tab shows something (${Object.keys(b.tabs).length} tabs)`);
    expect(count(all, b.year) > 20 && count(all, b.year - 1) > 20, `it names ${b.year} (${count(all, b.year)} times) and ${b.year - 1} (${count(all, b.year - 1)})`);
    expect(count(all, a.year - 1) === 0, `it never names ${a.year - 1}`);
    expect(!/\{(YEAR|PREV|CUT)\}/.test(all), 'no text placeholder is left');
    expect(b.summary === a.summary, `the same NCs and defects: ${b.summary}`);
    const week = (t) => (String(t).match(/· ([SW]\d+)/) || [])[1];
    expect(!!b.bell && week(b.bell) && week(b.bell) === week(a.bell), `the bell covers the same week (${week(b.bell)})`);
    expect(b.bellCount > 0 && Math.abs(b.bellCount - a.bellCount) <= 1, `and lists about the same alarms (${b.bellCount}, ${a.bellCount} the year before)`);
  }
  const week = (t) => (String(t).match(/· ([SW]\d+)/) || [])[1];
  const m = await readMft(browser, path.resolve(process.argv[2], 'FTO2_MFT.html')), n = await readMft(browser, path.resolve(process.argv[3], 'FTO2_MFT.html'));
  console.log('\nMFT page: ' + m.asof + ' -> ' + n.asof);
  expect(!n.errors.length, 'no page error' + (n.errors.length ? ': ' + n.errors[0] : ''));
  expect(count(n.asof, +(m.asof.match(/\d{4}/) || [0])[0] + 1) === 1, 'its data are one year later');
  expect(!!week(n.title) && week(n.title) === week(m.title), `it opens on the same week (${week(n.title)})`);
  expect(n.figs.length > 40 && n.figs === m.figs, 'with the same figures: ' + n.figs.slice(0, 60) + '...');
  expect(week(n.bell) === week(m.bell) && n.alarms > 0 && Math.abs(n.alarms - m.alarms) <= 1, `its bell covers the same week (${week(n.bell)}) and lists about the same alarms (${n.alarms}, ${m.alarms} the year before)`);
  await browser.close();
  console.log(bad ? '\nDIFFERENCES above' : '\nOK: the page follows the year of the settings');
  process.exit(bad ? 1 : 0);
})();

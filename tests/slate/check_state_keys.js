// Checks the two optional keys of the Skywise pages' state, with the fake Slate (tests/slate/make_pages.py writes the pages):
//   "reglages", the Fusion sheet "Target and pages": the dashboard's target texts and figures follow its cut, the Slate functions
//   compute with the page's cut, the filters at opening follow it, a wrong line keeps the reference value; the MFT page's action
//   target follows it;
//   "store", the MFT actions kept for everyone: the MFT page shows the latest store row's actions, a change fires the event
//   "save" with the whole list as compact JSON and asks for Submit until the query brings the row back; with no store row it
//   starts from the table's actions; the alarms' marks stay in the browser.
// Without the keys the pages are as before: that is the snapshot's job (set-ups sans_fonction, 3_fonctions, 2_fonctions).
//
//   python3 -I tests/slate/make_pages.py /tmp/slate
//   node tests/slate/check_state_keys.js /tmp/slate
//
// Prints one line per check; exits 1 when one fails. Needs Playwright with Chromium, as the snapshot.
const path = require('path');
const { chromium } = require('playwright');

const DIR = process.argv[2];
if (!DIR) { console.error('usage: node tests/slate/check_state_keys.js <folder written by tests/slate/make_pages.py>'); process.exit(2); }
let failed = 0;
function ok(cond, what, more) { console.log((cond ? 'ok    ' : 'FAIL  ') + what + (!cond && more ? '\n      ' + more : '')); if (!cond) failed++; }
const clean = (s) => String(s || '').replace(/\s+/g, ' ').trim();

async function settle(p) {   // the answers of the Slate functions and events still on their way
  for (let i = 0, calm = 0; i < 200 && calm < 3; i++) {
    const n = await p.evaluate(() => (window.FTO2_SLATE && window.FTO2_SLATE.waiting ? window.FTO2_SLATE.waiting() : 0) + (window.SlateFunctions && window.SlateFunctions._busy ? window.SlateFunctions._busy() : 0));
    calm = n ? 0 : calm + 1;
    await p.waitForTimeout(100);
  }
}

async function open(browser, file, wait) {
  const p = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  const logs = [], errors = [];
  p.on('console', (m) => logs.push(m.type() + ': ' + m.text()));
  p.on('pageerror', (e) => errors.push(String(e)));
  await p.addInitScript(() => { try { localStorage.clear(); localStorage.setItem('fto2-dash-mode', 'expert'); localStorage.setItem('fto2-dash-lang', 'fr'); } catch (e) {} });
  await p.goto('file://' + path.resolve(DIR, file));
  await p.waitForTimeout(wait || 3000);
  await settle(p);
  return { p, logs, errors };
}

// ------------------------------------------------------------------ the dashboard
async function dashTabs(p) {
  const out = {};
  for (const t of ['ov', 'pplan']) {
    await p.evaluate((id) => document.getElementById('tab-' + id).click(), t);
    await p.waitForTimeout(800); await settle(p);
    out[t] = await p.evaluate((id) => { const el = document.getElementById('p-' + id); return { text: el.textContent.replace(/\s+/g, ' ').trim(), tips: [...el.querySelectorAll('[data-tip]')].map((e) => e.getAttribute('data-tip')) }; }, t);
  }
  return out;
}

async function dashboard(browser) {
  const base = await open(browser, 'sans_fonction/FTO2_NC_Dashboard.html'), b = await dashTabs(base.p);
  const fus = await open(browser, 'fusion_partage/FTO2_NC_Dashboard.html'), f = await dashTabs(fus.p);
  const fn = await open(browser, 'fusion_3_fonctions/FTO2_NC_Dashboard.html'), g = await dashTabs(fn.p);
  ok(b.pplan.text.includes('Objectif = taux 2025 − 25 %') && b.ov.text.includes('moins 25 %'), 'dashboard without the key: the target is the reference one (−25 %)');
  ok(f.pplan.text.includes('Objectif = taux 2025 − 30 %') && f.ov.text.includes('moins 30 %') && !f.pplan.text.includes('− 25 %'),
    'dashboard with the Fusion sheet (objectif_baisse "30 %"): the texts say −30 %');
  const tipsB = b.ov.tips.concat(b.pplan.tips), tipsF = f.ov.tips.concat(f.pplan.tips);
  const changed = tipsB.map((t, i) => [t, tipsF[i]]).filter((x) => x[0] !== x[1]);
  ok(changed.length > 0 && changed.some((x) => /objectif/i.test(x[0])), 'dashboard with the Fusion sheet: the target figures change (' + changed.length + ' tooltips differ)',
    changed.length ? 'first: ' + changed[0][0].slice(0, 120) + ' -> ' + String(changed[0][1]).slice(0, 120) : 'no tooltip differs');
  const eg = changed.find((x) => /objectif/i.test(x[0]));
  if (eg) console.log('      e.g. "' + eg[0].slice(0, 110) + '"\n        -> "' + String(eg[1]).slice(0, 110) + '"');
  const ncs = (t) => (t.match(/nombre de défauts\. ([\d\s]+)NC/) || [])[1];   // the first figure of the Vue d'ensemble
  ok(ncs(b.ov.text) && ncs(f.ov.text) === ncs(b.ov.text), 'dashboard with the Fusion sheet: the same NCs counted (' + ncs(f.ov.text) + ' NC: the filters at opening are the reference ones, written differently)',
    JSON.stringify([ncs(b.ov.text), ncs(f.ov.text)]));
  const firstDiff = (a, c) => { let i = 0; while (i < a.length && a[i] === c[i]) i++; return a.slice(Math.max(0, i - 80), i + 80) + ' | ' + c.slice(Math.max(0, i - 80), i + 80); };
  ok(JSON.stringify(g) === JSON.stringify(f), 'dashboard with three Slate functions and the Fusion sheet: the same texts and figures as the page computing them (the functions take the page\'s cut)',
    'first difference: ' + firstDiff(JSON.stringify(f), JSON.stringify(g)));
  const asked = await fn.p.evaluate(() => { const v = window.SlateFunctions._variable('v_fto2_filtres'); return v && v.demandes ? v.demandes.map((q) => q.f && q.f.coef) : null; });
  ok(asked && asked.length && asked.every((c) => Math.abs(c - 0.7) < 1e-9), 'dashboard with Slate functions: each request carries the page\'s cut (coef 0.7)', JSON.stringify(asked));
  const answered = await fn.p.evaluate(() => { const L = window.FTO2_SLATE && window.FTO2_SLATE.latest, w = document.getElementById('fto2-wait');
    return { n: L && L.objectifs && L.objectifs.results ? Object.keys(L.objectifs.results).length : 0, box: w && !w.hidden ? w.textContent : '' }; });
  ok(answered.n > 0 && !/fonction Slate/.test(answered.box), 'dashboard with Slate functions: the figures come from f_fto2_objectifs, not from the page itself', JSON.stringify(answered));
  ok(fus.logs.some((l) => l.startsWith('warning') && l.includes('defaut_periode') && l.includes('3 mois')), 'a wrong line (defaut_periode "3 mois") keeps the reference value and says so in the console',
    fus.logs.filter((l) => l.includes('Fusion')).join(' | '));
  ok(fus.logs.some((l) => l.includes('taken from the sheet') && l.includes('objectif_baisse 0.3')), 'the console says which lines were taken from the sheet', fus.logs.filter((l) => l.includes('Fusion')).join(' | '));
  ok(!base.errors.length && !fus.errors.length && !fn.errors.length, 'no page error', base.errors.concat(fus.errors, fn.errors).join(' | '));
  for (const x of [base, fus, fn]) await x.p.close();

  const op = await open(browser, 'fusion_ouverture/FTO2_NC_Dashboard.html');
  const st = await op.p.evaluate(() => ({ phase: (document.querySelector('#gPhase [aria-checked="true"]') || {}).getAttribute ? document.querySelector('#gPhase [aria-checked="true"]').getAttribute('data-ph') : null,
    preset: document.getElementById('gPreset').value, liab: [...document.querySelectorAll('#gLiabMenu [data-liab]')].filter((i) => i.checked).map((i) => i.getAttribute('data-liab')).join('') }));
  ok(st.phase === 'REC' && st.preset === 'm3' && st.liab === 'fs', 'dashboard: the filters at opening follow the sheet (rec, sf, M3 -> REC, FTO2 + suppliers, last 3 months)', JSON.stringify(st));
  await op.p.close();
}

// ------------------------------------------------------------------ the MFT page
async function actionsTab(p) {
  await p.click('#lines [data-line="all"]'); await p.click('#tb-actions'); await p.click('[data-fst="all"]'); await p.waitForTimeout(400);
  return p.evaluate(() => ({ titles: [...document.querySelectorAll('#acts article.act h3')].map((h) => h.textContent), ids: [...document.querySelectorAll('#acts article.act')].map((a) => a.getAttribute('data-id')),
    note: document.getElementById('dbNote').hidden ? '' : document.getElementById('dbNote').textContent, text: document.getElementById('t-actions').textContent.replace(/\s+/g, ' ') }));
}

async function mft(browser) {
  const plain = await open(browser, 'sans_fonction/FTO2_MFT.html'), a0 = await actionsTab(plain.p);
  ok(a0.ids.length === 9 && a0.note.includes('ce navigateur'), 'MFT page without the key "store": the table\'s 9 actions, kept in this browser (note as before)', JSON.stringify([a0.ids.length, a0.note]));
  ok(a0.text.includes('objectif −30 %'), 'MFT page without the key "reglages": the action target is the reference one (−30 %)');
  await plain.p.close();

  const sh = await open(browser, 'fusion_partage/FTO2_MFT.html'), p = sh.p, a1 = await actionsTab(p);
  ok(a1.ids.join() === 'trk-a330-1,a-partage-1' || a1.ids.sort().join() === 'a-partage-1,trk-a330-1', 'MFT page with the key "store": the actions of the latest store row (2), not the table\'s nor the test box\'s', JSON.stringify(a1.ids));
  ok(a1.titles.some((t) => t.includes('(copie partagée)')), 'MFT page with the key "store": the store\'s text of the actions');
  ok(/illisible/.test(a1.note), 'MFT page: a later store row whose text was cut is said on screen', a1.note);
  ok(a1.text.includes('objectif −50 %') && !a1.text.includes('objectif −30 %'), 'MFT page with the Fusion sheet (action_objectif_baisse "0,5"): the action target is −50 %');
  ok(sh.logs.some((l) => l.includes('action_semaines_tenues 2')), 'MFT page: action_semaines_tenues "2" taken from the sheet', sh.logs.filter((l) => l.includes('Fusion')).join(' | '));

  // a change: close the action typed on the page
  const before = await p.evaluate(() => window.SlateFunctions._events().length);
  await p.click('#acts [data-close="a-partage-1"]'); await p.waitForTimeout(600); await settle(p);
  const ev = await p.evaluate(() => window.SlateFunctions._events());
  const row = ev.length > before ? ev[ev.length - 1] : null, v = row && row.value;
  let doc = null; try { doc = JSON.parse(v.texte_sap); } catch (e) {}
  ok(row && row.event === 'save' && v.msn === 'MFT-ACTIONS' && v.produit === 'MFT' && v.detection === 'store' && v.total_defauts === 2, 'a change fires the event "save" with the row of the NC writer (Msn MFT-ACTIONS)', JSON.stringify(v && { msn: v.msn, produit: v.produit, detection: v.detection, total_defauts: v.total_defauts }));
  ok(doc && doc.page === 'MFT' && doc.saved_at > '2026-11-16T09:00:00.000Z' && doc.actions.length === 2 && doc.actions.find((x) => x.id === 'a-partage-1').status === 'Clos' && doc.actions.find((x) => x.id === 'trk-a330-1').log.length === 1,
    'its Texte Sap holds the whole list as JSON, with the change (' + (v ? v.texte_sap.length : 0) + ' characters)', v && v.texte_sap.slice(0, 200));
  ok(doc && JSON.stringify(doc) === v.texte_sap, 'the JSON is compact');
  const sent = await p.evaluate(() => ({ variable: window.SlateFunctions._variable('v_mft_store'), state: window.SlateFunctions.getState().store_row }));
  ok(sent.variable && sent.variable.texte_sap === v.texte_sap && sent.state && sent.state.texte_sap === v.texte_sap, 'the Slate event copies the row into the variable v_mft_store, and the page\'s state key store_row holds it');
  const a2 = await actionsTab(p);
  ok(/Submit/.test(a2.note) && a2.text.includes('Clos'), 'the page shows the change at once and asks to press Submit', a2.note);
  await p.click('[data-lang="en"]'); await p.waitForTimeout(300);
  const en = await p.evaluate(() => document.getElementById('dbNote').textContent);
  ok(/press Submit/.test(en), 'the note in English', en);
  await p.click('[data-lang="fr"]'); await p.waitForTimeout(300);

  // Submit, then the query runs again: the row comes back; the cut row is gone
  const rows = await p.evaluate((sentRow) => {
    const q = window.FAKE_SLATE_SETUP.queries.q_fto2_mft_store, cols = Object.keys(q), out = {};
    cols.forEach((c) => { out[c] = q[c].filter((x, i) => !String(q['Texte Sap'][i]).startsWith('{"page":"MFT","saved_at":"2026-11-17')); });
    out.Timestamp.push(sentRow.timestamp); out.Msn.push(sentRow.msn); out.Produit.push(sentRow.produit); out.Detection.push(sentRow.detection);
    out['Total Defauts'].push(sentRow.total_defauts); out['Texte Sap'].push(sentRow.texte_sap);
    window.SlateFunctions._query('q_fto2_mft_store', out);
    return out;
  }, v);
  await p.waitForTimeout(500);
  const a3 = await actionsTab(p);
  ok(a3.note === '' && a3.ids.length === 2 && a3.text.includes('Clos'), 'once the query brings back the row saved, the note goes', JSON.stringify(a3.note));

  // someone else saves later: the page follows
  await p.evaluate((rows) => {
    const last = JSON.parse(rows['Texte Sap'][rows['Texte Sap'].length - 1]), later = new Date(Date.parse(last.saved_at) + 60000).toISOString();
    last.saved_at = later; last.actions.push({ id: 'a-autre', line: 'A330', title: 'Action d’un autre poste', problem: { mode: 'simple', codes: [] }, status: 'En cours', log: [] });
    const out = JSON.parse(JSON.stringify(rows));
    out.Timestamp.push(''); out.Msn.push('MFT-ACTIONS'); out.Produit.push('MFT'); out.Detection.push('store'); out['Total Defauts'].push(3); out['Texte Sap'].push(JSON.stringify(last));
    window.SlateFunctions._query('q_fto2_mft_store', out);
  }, rows);
  await p.waitForTimeout(500);
  const a4 = await actionsTab(p);
  ok(a4.ids.length === 3 && a4.ids.includes('a-autre') && a4.note === '', 'a later save made elsewhere replaces this copy', JSON.stringify(a4.ids));

  // a list over 30 000 characters: said on screen
  await p.evaluate(() => window.FTO2_STORE.use('db').then((db) => db.collection('actions').doc('a-autre').update({ note: 'x'.repeat(31000) })));
  await p.waitForTimeout(500);
  const a5 = await actionsTab(p);
  ok(/30 000/.test(a5.note) && /Submit/.test(a5.note), 'a list over 30 000 characters is said on screen', a5.note);

  // the alarms' marks stay in this browser: no event
  const n0 = await p.evaluate(() => window.SlateFunctions._events().length);
  await p.click('#tb-pareto'); await p.click('#lines [data-line="A330"]'); await p.waitForTimeout(300);
  await p.click('#alBtn'); await p.waitForTimeout(400);
  const vu = await p.$('#alPop [data-alvu]');
  if (vu) {
    await vu.click(); await p.waitForTimeout(500);
    const after = await p.evaluate(() => ({ n: window.SlateFunctions._events().length, kept: Object.keys(JSON.parse(localStorage.getItem('mft-fto2-slate-alarmes') || '{}')).length }));
    ok(after.n === n0 && after.kept > 0, 'an alarm marked as seen stays in this browser (no event)', JSON.stringify(after));
  } else ok(false, 'an alarm to mark as seen (none in the bell)');
  ok(!sh.errors.length, 'no page error', sh.errors.join(' | '));
  await p.close();

  // no store row yet: the table's actions, written in full at the first change
  const em = await open(browser, 'partage_vide/FTO2_MFT.html'), a6 = await actionsTab(em.p);
  ok(a6.ids.length === 9 && a6.note === '', 'MFT page with an empty store: the table\'s 9 actions, no note', JSON.stringify([a6.ids.length, a6.note]));
  await em.p.click('#acts [data-close="trk-a350-1"]'); await em.p.waitForTimeout(600);
  const e2 = await em.p.evaluate(() => window.SlateFunctions._events());
  let d2 = null; try { d2 = JSON.parse(e2[e2.length - 1].value.texte_sap); } catch (e) {}
  ok(e2.length === 1 && d2 && d2.actions.length === 9 && d2.actions.find((x) => x.id === 'trk-a350-1').status === 'Clos', 'its first change writes the table\'s 9 actions into the store', JSON.stringify(e2.length));
  ok(!em.errors.length, 'no page error', em.errors.join(' | '));
  await em.p.close();
}

(async () => {
  const browser = await chromium.launch();
  try { await dashboard(browser); await mft(browser); }
  finally { await browser.close(); }
  console.log(failed ? failed + ' check(s) failed' : 'all checks passed');
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });

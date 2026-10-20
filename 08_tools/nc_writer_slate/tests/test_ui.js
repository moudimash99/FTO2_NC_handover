// Click through nc_writer_standalone.html in Chromium, as an operator would, three times:
// inside a fake Slate (records what the widget hands to Slate), outside Slate, and with a broken Slate API.
//
//   python build_standalone.py && node tests/test_ui.js
//
// Needs playwright-core (npm install playwright-core) and a Chromium; set CHROMIUM=/path/to/chrome if needed.
const path = require("path");
const assert = require("assert");
const { chromium } = require(process.env.PW_CORE || "playwright-core");

const PAGE = "file://" + path.join(__dirname, "..", "nc_writer_standalone.html");
const SHOTS = process.env.SHOTS;  // optional folder for screenshots

const FAKE_SLATE = `window.__calls = [];
  window.SlateFunctions = {
    setState: function (s) { window.__calls.push(["setState", JSON.parse(JSON.stringify(s))]); },
    triggerEvent: function (e) { window.__calls.push(["triggerEvent", e]); }
  };`;
const BROKEN_SLATE = `window.SlateFunctions = { setState: function () {} };`;

async function open(browser, initScript) {
  const page = await browser.newPage({ viewport: { width: 820, height: 900 }, acceptDownloads: true });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  if (initScript) await page.addInitScript(initScript);
  await page.goto(PAGE);
  return { page, errors };
}

const act = (page, name) => page.click(`[data-act="${name}"]`);
const field = (name) => `[data-field="${name}"]`;
const text = (page, sel) => page.textContent(sel);
async function shot(page, name) { if (SHOTS) await page.screenshot({ path: path.join(SHOTS, name + ".png"), fullPage: true }); }

async function header(page, msn, detection) {
  assert.ok(await page.isDisabled('[data-act="header-continue"]'), "Continuer is off until the header is filled");
  await page.type(field("hd.msn"), msn);  // key by key: the field must keep the focus
  assert.strictEqual(await page.inputValue(field("hd.msn")), msn);
  await page.selectOption(field("hd.detectionSel"), detection);
  await shot(page, "1_header");
  await act(page, "header-continue");
}

async function fullFlow(browser) {
  const { page, errors } = await open(browser, FAKE_SLATE);
  await header(page, "2160", "Test");
  assert.match(await text(page, ".nc-info"), /MSN 2160 \| MIP A350 \| Test/);

  await page.selectOption(field("ctxCombo"), "Lors du contrôle après test");
  await page.fill(field("ctxText"), "sur le banc 3,");

  // defect 1: search a test code, pick a suggested FIN
  await act(page, "add-defect");
  assert.match(await text(page, ".tile-code"), /^T01$/, "test natures come first when found at test");
  await page.type(field("query"), "element");
  assert.ok((await page.locator(".pick").count()) > 0, "search ignores accents (Élément)");
  await page.fill(field("query"), "T04");
  await page.click('[data-act="pick-object"][data-sub="T04"]');
  assert.strictEqual(await page.inputValue(field("fd.locSel")), "", "no FIN is chosen for the operator");
  await page.selectOption(field("fd.locSel"), "3RN1B");
  await page.type(field("fd.detail"), "J <-> H");
  await page.fill(field("fd.qty"), "2");
  assert.strictEqual(await page.inputValue(field("fd.sev")), "MAJEURE");
  assert.strictEqual(await text(page, "#ncw-preview"), "DEF 1 - T04 - QTE 2 : 3RN1B — Inversion de connexion — J <-> H");
  await shot(page, "2_detail");
  await act(page, "save-defect");

  // defect 2: browse nature -> object, CDVE switch, "Autre" needs a typed location
  await act(page, "add-defect");
  await page.click('[data-act="pick-nature"][data-code="Q01"]');
  await page.click('[data-act="pick-object"][data-sub="Q01-001"]');
  assert.strictEqual(await page.inputValue(field("fd.sev")), "MINEURE");
  await page.check(field("fd.cdve"));
  assert.strictEqual(await page.inputValue(field("fd.sev")), "MAJEURE", "CDVE raises severity to 10");
  await page.selectOption(field("fd.locSel"), "Autre");
  assert.ok(await page.isDisabled('[data-act="save-defect"]'), "Autre without a typed location is refused");
  await page.type(field("fd.locCustom"), "100VG999");
  assert.ok(!(await page.isDisabled('[data-act="save-defect"]')));
  assert.strictEqual(await text(page, "#ncw-preview"), "DEF 2 - Q01-003 : 100VG999 — Contact");
  await act(page, "save-defect");

  // defect 3: duplicate the last one, bad quantity first
  await act(page, "duplicate-last");
  assert.strictEqual(await page.inputValue(field("fd.locCustom")), "100VG999");
  assert.ok(await page.isChecked(field("fd.cdve")));
  await page.fill(field("fd.qty"), "0");
  assert.ok(await page.isDisabled('[data-act="save-defect"]'));
  await page.fill(field("fd.qty"), "3");
  await page.fill(field("fd.comment"), "même défaut, autre connecteur");
  await act(page, "save-defect");
  assert.strictEqual(await page.locator(".defect").count(), 3);
  await shot(page, "3_list");

  // delete the first: the others are renumbered
  await page.click('[data-act="delete-defect"][data-i="0"]');
  const lines = await page.locator(".defect pre.line").allTextContents();
  assert.deepStrictEqual(lines, [
    "DEF 1 - Q01-003 : 100VG999 — Contact",
    "DEF 2 - Q01-003 - QTE 3 : 100VG999 — Contact — même défaut, autre connecteur",
  ]);

  // edit the first, cancel once, then really change it
  await page.click('[data-act="edit-defect"][data-i="0"]');
  await act(page, "cancel-detail");
  await page.click('[data-act="edit-defect"][data-i="0"]');
  await page.fill(field("fd.detail"), "contact 12 non verrouillé");
  await act(page, "save-defect");
  assert.match(await text(page, ".defect pre.line"), /^DEF 1 - Q01-003 : 100VG999 — Contact — contact 12 non verrouillé$/);

  // the context typed before survived all the screens
  assert.strictEqual(await page.inputValue(field("ctxText")), "sur le banc 3,");
  await page.selectOption(field("actCombo"), "Merci de remettre en conformité");
  await act(page, "finish");

  const sap = await text(page, "#ncw-sap");
  assert.strictEqual(sap, [
    "### DEFAUTS v1 | PRODUIT: MIP A350 | DETECTION: TEST",
    "",
    "Lors du contrôle après test sur le banc 3,",
    "",
    "DEF 1 - Q01-003 : 100VG999 — Contact — contact 12 non verrouillé",
    "DEF 2 - Q01-003 - QTE 3 : 100VG999 — Contact — même défaut, autre connecteur",
    "",
    "Merci de remettre en conformité",
    "",
    "### TOTAL: 4",
  ].join("\n"));
  await shot(page, "4_review");
  await act(page, "submit");

  const calls = await page.evaluate(() => window.__calls);
  assert.strictEqual(calls.length, 2);
  assert.strictEqual(calls[0][0], "setState");
  assert.deepStrictEqual(calls[1], ["triggerEvent", "submit"]);
  const row = calls[0][1].submission;
  assert.deepStrictEqual(Object.keys(row), ["submission_id", "timestamp", "msn", "produit", "detection", "total_defauts", "texte_sap", "defauts_json"]);
  assert.strictEqual(row.msn, "2160");
  assert.strictEqual(row.total_defauts, 4);
  assert.strictEqual(row.texte_sap, sap);
  assert.match(row.timestamp, /^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$/);
  const defs = JSON.parse(row.defauts_json);
  assert.strictEqual(defs.length, 2);
  assert.strictEqual(defs[1].qte, 3);
  assert.strictEqual(defs[1].cdve, true);
  assert.match(await text(page, ".ok"), /NC transmise à Slate/);
  await shot(page, "5_done");

  await act(page, "new-nc");
  assert.strictEqual(await page.inputValue(field("hd.msn")), "");
  assert.deepStrictEqual(errors, []);
  await page.close();
  return row;
}

async function standalone(browser) {
  const { page, errors } = await open(browser, null);
  await header(page, "MSN-77", "Poste");
  await act(page, "add-defect");
  await page.fill(field("query"), "obturateur");
  await page.click('[data-act="pick-object"][data-sub="Q03-001"]');
  assert.strictEqual(await text(page, "#ncw-preview"), "DEF 1 - Q03-001 : - — Obturateur", "no location prints a dash, as in the Python app");
  await act(page, "save-defect");
  await act(page, "finish");
  await act(page, "submit");
  assert.match(await text(page, ".warn"), /Hors Slate/);
  const [dl] = await Promise.all([page.waitForEvent("download"), act(page, "download")]);
  assert.match(dl.suggestedFilename(), /^nc_NCW-\d{14}-[A-Z0-9]+\.csv$/);
  assert.deepStrictEqual(errors, []);
  await page.close();
}

async function brokenSlate(browser) {
  const { page } = await open(browser, BROKEN_SLATE);
  await header(page, "1", "Poste");
  await act(page, "add-defect");
  await page.click('[data-act="pick-nature"][data-code="Q16"]');
  await page.click('[data-act="pick-object"][data-sub="Q16-001"]');
  await act(page, "save-defect");
  await act(page, "finish");
  await act(page, "submit");
  assert.match(await text(page, ".error"), /Envoi impossible.*n'est pas perdue/);
  assert.ok(await page.isVisible("#ncw-sap"), "the text stays on screen");
  assert.ok(!(await page.isDisabled('[data-act="submit"]')), "the operator can try again");
  await page.close();
}

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || "/opt/pw-browsers/chromium" });
  try {
    const row = await fullFlow(browser);
    console.log("ok   full flow in a fake Slate; Slate receives:\n" + JSON.stringify(row, null, 2));
    await standalone(browser);
    console.log("ok   outside Slate: warning + CSV download");
    await brokenSlate(browser);
    console.log("ok   broken Slate API: error shown, NC kept");
  } finally {
    await browser.close();
  }
})().catch((e) => { console.error("FAIL", e); process.exit(1); });

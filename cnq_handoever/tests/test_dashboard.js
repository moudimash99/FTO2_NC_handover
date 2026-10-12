// Check that the dashboard's JavaScript gives the same figures as the pipeline.   node tests/test_dashboard.js
const fs = require("fs"), path = require("path");
const root = path.dirname(__dirname);
const { computeAll, NC } = require(path.join(root, "dashboard", "dashboard_logic.js"));
const { DATA, P } = JSON.parse(fs.readFileSync(path.join(root, "dashboard", "dashboard_data.json"), "utf8"));
const exp = JSON.parse(fs.readFileSync(path.join(__dirname, "expected_totals.json"), "utf8"));
const res = computeAll(DATA, P);
const sum = k => res.rows.filter(x => DATA.nc[x.i][NC.aec] === 1).reduce((a, x) => a + x[k], 0);
const got = { level1_airbus_aec: sum("l1"), level2_global_aec: sum("l2"), level3_detailed_aec: sum("l3") };
let ok = true;
for (const k of Object.keys(got)) {
  const d = Math.abs(got[k] - exp[k]);
  console.log(k.padEnd(22), got[k].toFixed(2).padStart(12), "pipeline", String(exp[k]).padStart(12), d < 0.01 ? "OK" : "DIFFERENT");
  if (d >= 0.01) ok = false;
}
// per-NC check against the pipeline output
const csv = fs.readFileSync(path.join(root, "sample_output", "fto2_nc_cnq.csv"), "utf8").split("\n");
const head = csv[0].split(","), iN = head.indexOf("notification_number"), iT = head.indexOf("cnq_cost_total"), iG = head.indexOf("cnq_cost_global"), iA = head.indexOf("cnq_cost_airbus");
const byNum = {}; DATA.nc.forEach((r, i) => byNum[r[0]] = res.rows[i]);
let bad = 0, n = 0;
for (const line of csv.slice(1)) {
  if (!line) continue;
  const c = line.split(","); // the cost columns come after any quoted text columns, so index from the end
  const off = c.length - head.length, x = byNum[c[iN]];
  n++;
  if (Math.abs(x.l3 - +c[iT + off]) > 0.005 || Math.abs(x.l2 - +c[iG + off]) > 0.005 || Math.abs(x.l1 - +c[iA + off]) > 0.005) bad++;
}
console.log("per-NC check:", n, "NCs,", bad, "different");
if (!ok || bad) { console.log("FAILED"); process.exit(1); }
console.log("Dashboard and pipeline agree.");

#!/usr/bin/env node
// FTO2 Synthèse et détail, way 2: the views' model computed outside Slate, with the same file the Slate function runs.
//   node precompute_node.js <data> [filters] [out.json]
//     data     the dashboard page (03_reports/FTO2_NC_Dashboard.html: its data block) or a JSON file {tables: {nc, def, dis}, ref}
//     filters  JSON, e.g. '{"line": "A350", "preset": "m1"}' (default: the page's: all lines, since 1 January, Série, FTO2 plant)
//     out      where to write the model (default: the screen)
// Use it to check the model against the dashboard, or to pre-compute models for a set of filters on a schedule.
var fs = require('fs'), path = require('path');
var V = require(path.join(__dirname, 'fto2_views_model.js'));
var a = process.argv.slice(2);
if (!a[0]) { console.error('usage: node precompute_node.js <dashboard.html | data.json> [filters-json] [out.json]'); process.exit(2); }
var src = fs.readFileSync(a[0], 'utf8'), data;
if (/\.html?$/i.test(a[0])) {
  var i = src.indexOf('window.DASH = ') + 'window.DASH = '.length, j = src.indexOf(';\nwindow.FTO2_PAGE', i);
  if (i < 'window.DASH = '.length || j < 0) { console.error('no data block (window.DASH) in ' + a[0]); process.exit(1); }
  data = JSON.parse(src.slice(i, j).split('<\\/').join('</'));
} else data = JSON.parse(src);
var t0 = Date.now(), m = V.model(data.tables, data.ref, a[1] ? JSON.parse(a[1]) : {}), out = JSON.stringify(m);
if (a[2]) { fs.writeFileSync(a[2], out); console.error('model written to ' + a[2] + ' (' + Math.round(out.length / 1024) + ' KB, ' + (Date.now() - t0) + ' ms)'); }
else process.stdout.write(out + '\n');

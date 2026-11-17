// Test box: the MFT actions kept in one object of the NC writer's object type.
// Reading: the state key "rows" receives the objects (a query on their dataset, or an object set), in any of these forms:
// a list of rows, one array per column, or the same as JSON text. The store is the row whose Msn is MFT-ACTIONS; its
// Texte Sap holds the actions as JSON. When several rows have that Msn, the one saved last (saved_at in the JSON) wins.
// Writing: button 2 fires the event "save" with the row to write (same six fields as an NC). In Slate, the event fills a
// variable, and the action of the object type reads the variable, as for the NC writer.

var STORE_MSN = "MFT-ACTIONS";
var store = { saved_at: "", actions: [] };

function log(t) { var b = document.getElementById("log"); b.textContent = b.textContent + new Date().toTimeString().slice(0, 8) + "  " + t + "\n"; }
function api() { return typeof SlateFunctions === "undefined" ? null : SlateFunctions; }
function pad(n) { return (n < 10 ? "0" : "") + n; }
function now() { var d = new Date(); return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + " " + pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds()); }

function rowsOf(v) {
  if (typeof v === "string") { try { v = JSON.parse(v); } catch (e) { return []; } }
  if (!v) return [];
  if (Array.isArray(v)) return v;
  var cols = Object.keys(v), n = 0, out = [];
  cols.forEach(function (c) { if (Array.isArray(v[c]) && v[c].length > n) n = v[c].length; });
  for (var i = 0; i < n; i++) { var o = {}; cols.forEach(function (c) { o[c] = Array.isArray(v[c]) ? v[c][i] : null; }); out.push(o); }
  return out;
}

function field(r, names) { for (var i = 0; i < names.length; i++) if (r[names[i]] != null) return r[names[i]]; return null; }

function read(v) {
  var rows = rowsOf(v), best = null;
  rows.forEach(function (r) {
    var msn = field(r, ["msn", "Msn", "MSN"]);
    if (String(msn) !== STORE_MSN) return;
    var t = field(r, ["texte_sap", "Texte Sap", "texteSap", "texte sap"]), s;
    try { s = JSON.parse(t); } catch (e) { return; }
    if (!best || String(s.saved_at) > String(best.saved_at)) best = s;
  });
  document.getElementById("readState").textContent = rows.length + " row(s) received, " + (best ? "store found, saved " + best.saved_at + ", " + best.actions.length + " action(s)" : "no store row (Msn " + STORE_MSN + ") yet");
  if (best) { store = best; render(); }
  if (rows.length) log("read: " + rows.length + " row(s); columns of the first: " + Object.keys(rows[0]).join(", "));
}

function render() {
  document.getElementById("list").innerHTML = store.actions.length ? "<ul>" + store.actions.map(function (a) { return "<li>" + a.id + " · " + a.title.replace(/</g, "&lt;") + " (" + a.at + ")</li>"; }).join("") + "</ul>" : "<p>No action in the store.</p>";
}

function add() {
  var t = document.getElementById("title").value.trim() || "Test action";
  store.actions.push({ id: "a" + Date.now().toString(36), title: t, at: now() });
  render();
  log("1. added locally: " + t + " (" + store.actions.length + " action(s)); now press 2");
}

function save() {
  var sf = api();
  store.saved_at = now();
  var row = { timestamp: store.saved_at, msn: STORE_MSN, produit: "MFT", detection: "store", total_defauts: store.actions.length, texte_sap: JSON.stringify(store) };
  if (!sf || typeof sf.triggerEvent !== "function") { log("2. not in Slate: nothing sent"); return; }
  if (sf.setState.length >= 2) sf.setState("store_row", row); else { var st = {}; st.store_row = row; sf.setState(st); }
  sf.triggerEvent("save", row);
  log("2. event save sent: " + row.texte_sap.length + " characters, " + store.actions.length + " action(s). Submit the action, then reload the page.");
}

function start() {
  render();
  var sf = api();
  if (!sf) { log("Not in Slate: this box only works in a Code Sandbox."); return; }
  if (typeof sf.watch === "function") { try { sf.watch("rows", read); } catch (e) { log("watch error: " + e.message); } }
  else if (typeof sf.getState === "function") read((sf.getState() || {}).rows);
}

document.getElementById("btnAdd").addEventListener("click", add);
document.getElementById("btnSave").addEventListener("click", save);
start();

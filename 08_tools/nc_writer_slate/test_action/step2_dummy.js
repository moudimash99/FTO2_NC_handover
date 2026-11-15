// Test box for the NC writer's action. Button 1 fills the widget's state with a test row, as the real NC writer does:
// SlateFunctions.setState("submission", row). The values are easy to tell from those typed in the State field: they all
// say CODE, and they change at every click. Button 2 fires the event "submit", with the row as its value.
// The action's fields read the row from this widget's state: <widget name>.state.submission.<field>.

var clicks = 0;
var lastRow = null;

function pad(n) { return (n < 10 ? "0" : "") + n; }

function now() {
  var d = new Date();
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + " " +
    pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
}

function line(text) {
  var box = document.getElementById("log");
  box.textContent = box.textContent + now().slice(11) + "  " + text + "\n";
}

function short(v) {
  var s;
  try { s = typeof v === "string" ? v : JSON.stringify(v); } catch (e) { s = String(v); }
  if (s === undefined) s = "undefined";
  return s.length > 300 ? s.slice(0, 300) + "..." : s;
}

function testRow() {
  var stamp = now();
  var hms = stamp.slice(11).replace(/:/g, "");
  clicks = clicks + 1;
  var row = {};
  row.timestamp = stamp;
  row.msn = "CODE-" + hms;
  row.produit = "PRODUIT-CODE";
  row.detection = "DETECTION-CODE";
  row.total_defauts = clicks;
  row.texte_sap = "ECRIT PAR LE CODE, clic " + clicks + ", " + stamp;
  return row;
}

function api() { return typeof SlateFunctions === "undefined" ? null : SlateFunctions; }

function readBack() {
  var sf = api();
  if (!sf || typeof sf.getState !== "function") { line("   getState : absent"); return; }
  try { line("   l'etat contient maintenant : " + short(sf.getState())); } catch (e) { line("   getState() erreur : " + e.message); }
}

function fill() {
  var sf = api();
  var row = testRow();
  if (!sf || typeof sf.setState !== "function") { line("setState introuvable : pas dans un Code Sandbox Slate."); return; }
  try {
    sf.setState("submission", row);
    lastRow = row;
    document.getElementById("now").textContent = "Valeurs envoyees : Msn = " + row.msn + ", Total Defauts = " + row.total_defauts;
    line("1. etat rempli : Msn " + row.msn + ", Total Defauts " + row.total_defauts);
  } catch (e) { line("1. erreur : " + e.message); }
  setTimeout(readBack, 400);
}

function sendEvent() {
  var sf = api();
  if (!sf || typeof sf.triggerEvent !== "function") { line("triggerEvent introuvable."); return; }
  try { sf.triggerEvent("submit", lastRow); line("2. evenement submit envoye" + (lastRow ? " (Msn " + lastRow.msn + ")" : " (aucune valeur : appuyer d'abord sur 1)")); }
  catch (e) { line("2. erreur : " + e.message); }
}

function start() {
  var sf = api();
  if (!sf) { line("SlateFunctions : absent (cette page n'est pas dans un Code Sandbox Slate)"); return; }
  readBack();
}

document.getElementById("btnFill").addEventListener("click", fill);
document.getElementById("btnEvent").addEventListener("click", sendEvent);
start();

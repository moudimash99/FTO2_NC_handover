// Test box for the NC writer's action. It fills the widget's state with a test row, as the real NC writer does, and
// writes on the screen what Slate answers. Two ways of filling are tried, because Slate versions differ:
//   A. SlateFunctions.setState("submission", row)        key, then value
//   B. SlateFunctions.setState(an object with submission) one object
// The action's fields read the row from this widget's state: <widget name>.state.submission.<field>.

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

function testRow(tag) {
  var stamp = now();
  var row = {};
  row.timestamp = stamp;
  row.msn = "TEST";
  row.produit = "MIP A350";
  row.detection = "Poste";
  row.total_defauts = 2;
  row.texte_sap = "TEST " + tag + " " + stamp + " - ligne de test, a supprimer";
  return row;
}

function api() { return typeof SlateFunctions === "undefined" ? null : SlateFunctions; }

function readBack() {
  var sf = api();
  if (!sf || typeof sf.getState !== "function") { line("   getState : absent"); return; }
  try { line("   getState() -> " + short(sf.getState())); } catch (e) { line("   getState() erreur : " + e.message); }
}

function fill(way) {
  var sf = api();
  var row = testRow(way);
  if (!sf || typeof sf.setState !== "function") { line("setState introuvable : pas dans un Code Sandbox Slate."); return; }
  try {
    if (way === "A") {
      sf.setState("submission", row);
      line("A. setState(\"submission\", row) appele, timestamp " + row.timestamp);
    } else {
      var state = {};
      state.submission = row;
      sf.setState(state);
      line("B. setState(objet) appele, timestamp " + row.timestamp);
    }
  } catch (e) { line(way + ". erreur : " + e.message); }
  setTimeout(readBack, 400);
}

function sendEvent() {
  var sf = api();
  if (!sf || typeof sf.triggerEvent !== "function") { line("triggerEvent introuvable."); return; }
  try { sf.triggerEvent("submit"); line("C. evenement submit envoye"); } catch (e) { line("C. erreur : " + e.message); }
}

function start() {
  var sf = api();
  if (!sf) { line("SlateFunctions : absent (cette page n'est pas dans un Code Sandbox Slate)"); return; }
  var names = ["watch", "setState", "getState", "triggerEvent"];
  var found = [];
  for (var i = 0; i < names.length; i++) {
    var f = sf[names[i]];
    found.push(names[i] + (typeof f === "function" ? "(" + f.length + ")" : " absent"));
  }
  var others = [];
  try { others = Object.keys(sf); } catch (e) { others = []; }
  line("SlateFunctions : " + found.join(", ") + " | cles : " + others.join(", "));
  if (typeof sf.watch === "function") {
    try { sf.watch("submission", function (v) { line("   Slate dit : submission = " + short(v)); }); } catch (e) { line("watch erreur : " + e.message); }
  }
  readBack();
}

document.getElementById("btnA").addEventListener("click", function () { fill("A"); });
document.getElementById("btnB").addEventListener("click", function () { fill("B"); });
document.getElementById("btnC").addEventListener("click", sendEvent);
start();

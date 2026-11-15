// Test box for the NC writer's action: it only fills the widget's state with a test row, as the real NC writer does.
// Button 1: fills the state. Button 2: fills the state, then fires the event "submit".
// The action's fields read the row from this widget's state: <widget name>.state.submission.<field>.

function pad(n) { return (n < 10 ? "0" : "") + n; }

function testRow() {
  var d = new Date();
  var stamp = d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + " " +
    pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
  var row = {};
  row.timestamp = stamp;
  row.msn = "TEST";
  row.produit = "MIP A350";
  row.detection = "Poste";
  row.total_defauts = 2;
  row.texte_sap = "TEST " + stamp + " - ligne de test, a supprimer";
  return row;
}

function show(text, row) {
  document.getElementById("msg").textContent = text;
  document.getElementById("out").textContent = row ? JSON.stringify(row, null, 2) : "";
}

function fill(sendEvent) {
  var row = testRow();
  if (typeof SlateFunctions === "undefined" || typeof SlateFunctions.setState !== "function") {
    show("SlateFunctions.setState introuvable : cette page n'est pas dans un Code Sandbox Slate.", row);
    return;
  }
  var state = {};
  state.submission = row;
  SlateFunctions.setState(state);
  if (!sendEvent) { show("Etat rempli. Les champs de l'action doivent maintenant montrer ces valeurs :", row); return; }
  if (typeof SlateFunctions.triggerEvent !== "function") { show("Etat rempli, mais SlateFunctions.triggerEvent est introuvable.", row); return; }
  SlateFunctions.triggerEvent("submit");
  show("Etat rempli et evenement submit envoye avec ces valeurs :", row);
}

document.getElementById("btnFill").addEventListener("click", function () { fill(false); });
document.getElementById("btnSend").addEventListener("click", function () { fill(true); });

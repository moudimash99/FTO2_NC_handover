// Test box: which ways of getting an image or data out of a Slate Code Sandbox work. One button per way; each writes
// on screen what happened. A file that arrives in Downloads, or a paste that works, is the answer.

var DATA = [["Month", "Swapped wires", "Wrong terminal", "Unlocked contact"], ["2026-08", 12, 7, 3], ["2026-09", 15, 9, 2], ["2026-10", 11, 6, 4]];

function log(t) { var b = document.getElementById("log"); b.textContent = b.textContent + new Date().toTimeString().slice(0, 8) + "  " + t + "\n"; }

function draw() {
  var c = document.getElementById("chart"), x = c.getContext("2d");
  x.fillStyle = "#fff"; x.fillRect(0, 0, c.width, c.height);
  x.fillStyle = "#1b2430"; x.font = "14px Arial"; x.fillText("Test: causes per month", 12, 22);
  var cols = ["#2f6db5", "#1d9a6c", "#e3a008"];
  for (var m = 1; m < DATA.length; m++) for (var k = 1; k < 4; k++) {
    var v = DATA[m][k], left = 40 + (m - 1) * 140 + (k - 1) * 36;
    x.fillStyle = cols[k - 1]; x.fillRect(left, 180 - v * 8, 28, v * 8);
  }
  x.fillStyle = "#555"; x.font = "11px Arial";
  for (var j = 1; j < DATA.length; j++) x.fillText(DATA[j][0], 60 + (j - 1) * 140, 195);
}

function pngUrl() { return document.getElementById("chart").toDataURL("image/png"); }
function pngBlob(cb) { document.getElementById("chart").toBlob(cb, "image/png"); }
function csv() { return DATA.map(function (r) { return r.join(";"); }).join("\r\n"); }
function tsv() { return DATA.map(function (r) { return r.join("\t"); }).join("\n"); }
function svgText() {
  var s = '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="200"><rect width="480" height="200" fill="#fff"/>';
  s += '<text x="12" y="22" font-family="Arial" font-size="14">Test: causes per month</text>';
  var cols = ["#2f6db5", "#1d9a6c", "#e3a008"];
  for (var m = 1; m < DATA.length; m++) for (var k = 1; k < 4; k++) {
    var v = DATA[m][k]; s += '<rect x="' + (40 + (m - 1) * 140 + (k - 1) * 36) + '" y="' + (180 - v * 8) + '" width="28" height="' + v * 8 + '" fill="' + cols[k - 1] + '"/>';
  }
  return s + "</svg>";
}

function clickLink(href, name) {
  var a = document.createElement("a"); a.href = href; a.download = name; a.style.display = "none";
  document.body.appendChild(a); a.click(); setTimeout(function () { a.remove(); }, 1000);
}

var WAYS = [
  ["1. PNG: data link", function () { clickLink(pngUrl(), "test_1_data.png"); log("1. data link clicked: did test_1_data.png arrive in Downloads?"); }],
  ["2. PNG: blob link", function () { pngBlob(function (b) { var u = URL.createObjectURL(b); clickLink(u, "test_2_blob.png"); log("2. blob link clicked: did test_2_blob.png arrive?"); }); }],
  ["3. PNG: new tab", function () { pngBlob(function (b) { var w = window.open(URL.createObjectURL(b), "_blank"); log("3. new tab: " + (w ? "opened (right-click > Save image as)" : "blocked")); }); }],
  ["4. PNG: new tab (data)", function () { var w = window.open(""); if (!w) { log("4. blocked"); return; } w.document.write('<img src="' + pngUrl() + '">'); log("4. tab opened with the image"); }],
  ["5. PNG: copy the image", function () {
    if (!navigator.clipboard || !window.ClipboardItem) { log("5. image clipboard: not available"); return; }
    pngBlob(function (b) { navigator.clipboard.write([new ClipboardItem({ "image/png": b })]).then(function () { log("5. image copied: paste it into PowerPoint or Teams"); }, function (e) { log("5. refused: " + e.message); }); });
  }],
  ["6. Show the image (right-click)", function () { document.getElementById("shown").innerHTML = '<p>Right-click the image > Save image as / Copy image:</p><img src="' + pngUrl() + '" style="border:1px solid #ccc">'; log("6. image shown under the buttons"); }],
  ["7. SVG: blob link", function () { var u = URL.createObjectURL(new Blob([svgText()], { type: "image/svg+xml" })); clickLink(u, "test_7.svg"); log("7. did test_7.svg arrive?"); }],
  ["8. Data: CSV (blob)", function () { var u = URL.createObjectURL(new Blob(["﻿" + csv()], { type: "text/csv" })); clickLink(u, "test_8.csv"); log("8. did test_8.csv arrive?"); }],
  ["9. Data: CSV (data)", function () { clickLink("data:text/csv;charset=utf-8," + encodeURIComponent("﻿" + csv()), "test_9.csv"); log("9. did test_9.csv arrive?"); }],
  ["10. Data: copy (modern)", function () {
    if (!navigator.clipboard) { log("10. clipboard: not available"); return; }
    navigator.clipboard.writeText(tsv()).then(function () { log("10. copied: paste into Excel"); }, function (e) { log("10. refused: " + e.message); });
  }],
  ["11. Data: copy (older way)", function () {
    var t = document.createElement("textarea"); t.value = tsv(); document.body.appendChild(t); t.select();
    var ok = false; try { ok = document.execCommand("copy"); } catch (e) { } t.remove(); log("11. copy " + (ok ? "done: paste into Excel" : "refused"));
  }],
  ["12. Print (PDF)", function () { try { window.print(); log("12. print window asked for"); } catch (e) { log("12. refused: " + e.message); } }]
];

function start() {
  draw();
  var box = document.getElementById("btns");
  WAYS.forEach(function (w) {
    var b = document.createElement("button"); b.type = "button"; b.textContent = w[0]; b.style.padding = "6px 10px";
    b.addEventListener("click", function () { try { w[1](); } catch (e) { log(w[0] + ": error " + e.message); } });
    box.appendChild(b);
  });
  log("Ready. Browser: " + navigator.userAgent.slice(0, 80));
}
start();
